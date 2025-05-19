"""
Centralized logging configuration for the Data Migration Service.

This module provides a structured logging setup with context injection,
correlation IDs, and integration with monitoring systems.
"""
import asyncio
import json
import logging
import sys
import time
import uuid
from contextvars import ContextVar
from functools import wraps
from typing import Any, Callable, Dict, Optional, TypeVar, cast

import structlog
from fastapi import Request

# Context variables for request-scoped data
request_id_context: ContextVar[str] = ContextVar("request_id", default="")
tenant_id_context: ContextVar[str] = ContextVar("tenant_id", default="")
correlation_id_context: ContextVar[str] = ContextVar("correlation_id", default="")

# Type definitions
F = TypeVar("F", bound=Callable[..., Any])
LoggerAdapter = structlog.stdlib.BoundLogger


def get_request_id() -> str:
    """Get the current request ID from context."""
    return request_id_context.get()


def get_correlation_id() -> str:
    """Get the current correlation ID from context."""
    return correlation_id_context.get()


def get_tenant_id() -> str:
    """Get the current tenant ID from context."""
    return tenant_id_context.get()


def set_request_id(request_id: str) -> None:
    """Set the request ID in the current context."""
    request_id_context.set(request_id)


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID in the current context."""
    correlation_id_context.set(correlation_id)


def set_tenant_id(tenant_id: str) -> None:
    """Set the tenant ID in the current context."""
    tenant_id_context.set(tenant_id)


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return f"req-{uuid.uuid4()}"


def configure_logging(log_level: str = "INFO", json_logs: bool = True) -> None:
    """
    Configure the logging system for the application.
    
    Args:
        log_level: The log level to use
        json_logs: Whether to output logs in JSON format
    """
    # Set up structlog processors
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.format_exc_info,
    ]

    # Add JSON formatter for production or pretty printing for development
    if json_logs:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Set log level for noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> LoggerAdapter:
    """
    Get a structured logger with the given name.
    
    Args:
        name: The name of the logger, typically the module name
        
    Returns:
        A structured logger
    """
    return structlog.get_logger(name)


def log_execution_time(func: F) -> F:
    """
    Decorator to log the execution time of a function.
    
    Args:
        func: The function to decorate
        
    Returns:
        The decorated function
    """
    logger = get_logger(func.__module__)

    @wraps(func)
    async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result = await func(*args, **kwargs)
        execution_time = time.time() - start_time
        logger.info(
            "Function execution",
            function=func.__name__,
            execution_time_ms=round(execution_time * 1000, 2),
        )
        return result

    @wraps(func)
    def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        logger.info(
            "Function execution",
            function=func.__name__,
            execution_time_ms=round(execution_time * 1000, 2),
        )
        return result

    # Choose the appropriate wrapper based on whether the function is async or not
    if asyncio.iscoroutinefunction(func):
        return cast(F, async_wrapper)
    else:
        return cast(F, sync_wrapper)


async def request_middleware(request: Request, call_next: Callable) -> Any:
    """
    Middleware to add request context to logs.
    
    Args:
        request: The FastAPI request object
        call_next: The next middleware/handler to call
        
    Returns:
        The response
    """
    # Generate or extract request ID
    request_id = request.headers.get("X-Request-ID", generate_request_id())
    set_request_id(request_id)
    
    # Extract correlation ID if present, or use request ID
    correlation_id = request.headers.get("X-Correlation-ID", request_id)
    set_correlation_id(correlation_id)
    
    # Extract tenant ID if present
    tenant_id = request.headers.get("X-Tenant-ID", "")
    if tenant_id:
        set_tenant_id(tenant_id)
        
    # Add request information to the log context
    # This will be included in all logs during this request
    logger = get_logger(__name__)
    logger.info(
        "Request started",
        method=request.method,
        path=request.url.path,
        query_params=dict(request.query_params),
    )
    
    # Record start time
    start_time = time.time()
    
    try:
        # Process the request
        response = await call_next(request)
        
        # Calculate and log request processing time
        process_time = time.time() - start_time
        status_code = response.status_code
        logger.info(
            "Request completed",
            status_code=status_code,
            process_time_ms=round(process_time * 1000, 2),
        )
        
        # Add response headers for tracking
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response
    except Exception as e:
        # Log exceptions
        process_time = time.time() - start_time
        logger.exception(
            "Request failed",
            exc_info=e,
            process_time_ms=round(process_time * 1000, 2),
        )
        raise