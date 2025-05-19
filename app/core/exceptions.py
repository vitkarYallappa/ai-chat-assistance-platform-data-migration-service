"""
Exception handling for the Data Migration Service.

This module defines custom exceptions and provides utilities
for consistent error handling throughout the application.
"""
from http import HTTPStatus
from typing import Any, Dict, List, Optional, Type, Union

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.logging import get_logger

# Get logger for this module
logger = get_logger(__name__)


class ErrorDetail(BaseModel):
    """Model for error details in responses."""
    
    code: str
    message: str
    location: Optional[str] = None
    field: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    """Model for error responses."""
    
    request_id: str
    error_type: str
    message: str
    status_code: int
    details: Optional[List[ErrorDetail]] = None


# Base exception for all custom exceptions
class DataMigrationError(Exception):
    """Base exception for all Data Migration Service exceptions."""
    
    def __init__(
        self,
        message: str,
        status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        details: Optional[List[ErrorDetail]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details
        super().__init__(message)


# Validation errors
class ValidationError(DataMigrationError):
    """Exception for validation errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[List[ErrorDetail]] = None,
    ):
        super().__init__(
            message=message,
            status_code=HTTPStatus.BAD_REQUEST,
            error_code="VALIDATION_ERROR",
            details=details,
        )


# Database errors
class DatabaseError(DataMigrationError):
    """Exception for database errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[List[ErrorDetail]] = None,
    ):
        super().__init__(
            message=message,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            error_code="DATABASE_ERROR",
            details=details,
        )


class DatabaseConnectionError(DatabaseError):
    """Exception for database connection errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[List[ErrorDetail]] = None,
    ):
        super().__init__(
            message=message,
            details=details,
        )
        self.error_code = "DATABASE_CONNECTION_ERROR"


class DatabaseQueryError(DatabaseError):
    """Exception for database query errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[List[ErrorDetail]] = None,
    ):
        super().__init__(
            message=message,
            details=details,
        )
        self.error_code = "DATABASE_QUERY_ERROR"


# Migration errors
class MigrationError(DataMigrationError):
    """Exception for migration errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[List[ErrorDetail]] = None,
    ):
        super().__init__(
            message=message,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            error_code="MIGRATION_ERROR",
            details=details,
        )


class MigrationNotFoundError(MigrationError):
    """Exception for migration not found errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[List[ErrorDetail]] = None,
    ):
        super().__init__(
            message=message,
            details=details,
        )
        self.status_code = HTTPStatus.NOT_FOUND
        self.error_code = "MIGRATION_NOT_FOUND"


class MigrationAlreadyExistsError(MigrationError):
    """Exception for migration already exists errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[List[ErrorDetail]] = None,
    ):
        super().__init__(
            message=message,
            details=details,
        )
        self.status_code = HTTPStatus.CONFLICT
        self.error_code = "MIGRATION_ALREADY_EXISTS"


class MigrationInProgressError(MigrationError):
    """Exception for migration in progress errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[List[ErrorDetail]] = None,
    ):
        super().__init__(
            message=message,
            details=details,
        )
        self.status_code = HTTPStatus.CONFLICT
        self.error_code = "MIGRATION_IN_PROGRESS"


# Shard errors
class ShardError(DataMigrationError):
    """Exception for shard errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[List[ErrorDetail]] = None,
    ):
        super().__init__(
            message=message,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            error_code="SHARD_ERROR",
            details=details,
        )


class ShardNotFoundError(ShardError):
    """Exception for shard not found errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[List[ErrorDetail]] = None,
    ):
        super().__init__(
            message=message,
            details=details,
        )
        self.status_code = HTTPStatus.NOT_FOUND
        self.error_code = "SHARD_NOT_FOUND"


# External service errors
class ExternalServiceError(DataMigrationError):
    """Exception for external service errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[List[ErrorDetail]] = None,
    ):
        super().__init__(
            message=message,
            status_code=HTTPStatus.BAD_GATEWAY,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=details,
        )


class ExternalServiceTimeoutError(ExternalServiceError):
    """Exception for external service timeout errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[List[ErrorDetail]] = None,
    ):
        super().__init__(
            message=message,
            details=details,
        )
        self.error_code = "EXTERNAL_SERVICE_TIMEOUT"


class ExternalServiceUnavailableError(ExternalServiceError):
    """Exception for external service unavailable errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[List[ErrorDetail]] = None,
    ):
        super().__init__(
            message=message,
            details=details,
        )
        self.status_code = HTTPStatus.SERVICE_UNAVAILABLE
        self.error_code = "EXTERNAL_SERVICE_UNAVAILABLE"


# API errors
class APIError(DataMigrationError):
    """Exception for API errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int = HTTPStatus.BAD_REQUEST,
        error_code: str = "API_ERROR",
        details: Optional[List[ErrorDetail]] = None,
    ):
        super().__init__(
            message=message,
            status_code=status_code,
            error_code=error_code,
            details=details,
        )


class NotFoundError(APIError):
    """Exception for resource not found errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[List[ErrorDetail]] = None,
    ):
        super().__init__(
            message=message,
            status_code=HTTPStatus.NOT_FOUND,
            error_code="NOT_FOUND",
            details=details,
        )


class UnauthorizedError(APIError):
    """Exception for unauthorized errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[List[ErrorDetail]] = None,
    ):
        super().__init__(
            message=message,
            status_code=HTTPStatus.UNAUTHORIZED,
            error_code="UNAUTHORIZED",
            details=details,
        )


class ForbiddenError(APIError):
    """Exception for forbidden errors."""
    
    def __init__(
        self,
        message: str,
        details: Optional[List[ErrorDetail]] = None,
    ):
        super().__init__(
            message=message,
            status_code=HTTPStatus.FORBIDDEN,
            error_code="FORBIDDEN",
            details=details,
        )


# Exception handler for FastAPI
async def exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for FastAPI.
    
    Args:
        request: The FastAPI request object
        exc: The exception
        
    Returns:
        A JSON response with error details
    """
    from app.core.logging import get_request_id

    request_id = get_request_id()
    
    # Handle known exceptions
    if isinstance(exc, DataMigrationError):
        status_code = exc.status_code
        error_type = exc.__class__.__name__
        message = exc.message
        details = exc.details
    else:
        # Handle unknown exceptions
        status_code = HTTPStatus.INTERNAL_SERVER_ERROR
        error_type = "InternalServerError"
        message = "An unexpected error occurred"
        details = None
        
        # Log the unknown exception
        logger.exception(
            "Unhandled exception",
            exc_info=exc,
            status_code=status_code,
        )
    
    # Create error response
    error_response = ErrorResponse(
        request_id=request_id,
        error_type=error_type,
        message=message,
        status_code=status_code,
        details=details,
    )
    
    return JSONResponse(
        status_code=status_code,
        content=error_response.dict(),
    )


def setup_exception_handlers(app: Any) -> None:
    """
    Set up exception handlers for a FastAPI app.
    
    Args:
        app: The FastAPI app
    """
    app.add_exception_handler(Exception, exception_handler)