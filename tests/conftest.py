"""
Pytest configuration for the Data Migration Service.

This module provides test fixtures and configuration for pytest.
"""
import asyncio
import os
from typing import Any, AsyncGenerator, Callable, Dict, Generator, Optional

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import DatabaseType, Settings, get_settings
from app.core.logging import configure_logging
from app.main import create_app
from app.utils.database import Base, init_database


# Override settings for testing
@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """
    Get test settings with test-specific overrides.
    
    This fixture provides a separate test configuration to avoid
    interfering with development or production environments.
    
    Returns:
        Test settings
    """
    # Create test-specific settings
    return Settings(
        ENVIRONMENT="testing",
        DEBUG=True,
        LOG_LEVEL="DEBUG",
        JSON_LOGS=False,
        POSTGRES_DB="migrations_test",
        MONGODB_DB="migrations_test",
        SHARD_DISCOVERY_ENABLED=False,
        SHARD_CONFIG_PATH="tests/fixtures/shard_config.json",
        SECRET_KEY="test-secret-key",
        MCP_SERVICE_API_KEY="test-api-key",
        CHAT_SERVICE_API_KEY="test-api-key",
        ADAPTOR_SERVICE_API_KEY="test-api-key",
    )


# Setup and teardown for PostgreSQL test database
@pytest.fixture(scope="session")
def postgres_engine(test_settings: Settings) -> Generator[AsyncEngine, None, None]:
    """
    Create a PostgreSQL test database engine.
    
    This fixture provides a test database engine for PostgreSQL tests.
    
    Args:
        test_settings: Test settings
        
    Yields:
        SQLAlchemy AsyncEngine
    """
    # Create async engine
    engine = create_async_engine(
        test_settings.SQLALCHEMY_DATABASE_URI,
        echo=False,
        future=True,
    )
    yield engine
    
    # Clean up
    asyncio.run(engine.dispose())


@pytest_asyncio.fixture(scope="function")
async def postgres_session(postgres_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a PostgreSQL test database session.
    
    This fixture provides a fresh session for each test.
    
    Args:
        postgres_engine: PostgreSQL engine
        
    Yields:
        SQLAlchemy AsyncSession
    """
    # Create tables
    async with postgres_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session factory
    async_session = sessionmaker(
        postgres_engine, expire_on_commit=False, class_=AsyncSession
    )
    
    # Create session
    async with async_session() as session:
        yield session
        # Rollback any changes
        await session.rollback()


# Setup and teardown for MongoDB test database
@pytest_asyncio.fixture(scope="function")
async def mongodb_client(test_settings: Settings) -> AsyncGenerator[AsyncIOMotorClient, None]:
    """
    Create a MongoDB test client.
    
    This fixture provides a test client for MongoDB tests.
    
    Args:
        test_settings: Test settings
        
    Yields:
        MongoDB client
    """
    # Create client
    client = AsyncIOMotorClient(
        test_settings.MONGODB_URI,
        serverSelectionTimeoutMS=5000,
    )
    
    # Use a test database
    db_name = test_settings.MONGODB_DB
    db = client[db_name]
    
    # Drop database to start with a clean state
    await client.drop_database(db_name)
    
    yield client
    
    # Clean up
    await client.drop_database(db_name)
    client.close()


@pytest_asyncio.fixture(scope="function")
async def mongodb_database(mongodb_client: AsyncIOMotorClient, test_settings: Settings) -> AsyncGenerator[Any, None]:
    """
    Create a MongoDB test database.
    
    This fixture provides a fresh database for each test.
    
    Args:
        mongodb_client: MongoDB client
        test_settings: Test settings
        
    Yields:
        MongoDB database
    """
    # Get test database
    db = mongodb_client[test_settings.MONGODB_DB]
    
    # Set up collections and indexes
    await db.migration_state.create_index("name")
    await db.migration_state.create_index("status")
    
    await db.migration_events.create_index("migration_id")
    await db.migration_events.create_index("timestamp")
    
    await db.migration_locks.create_index("resource")
    await db.migration_locks.create_index(
        "expires_at", expireAfterSeconds=0
    )  # TTL index
    
    yield db


# App fixtures
@pytest.fixture(scope="session")
def app(test_settings: Settings) -> FastAPI:
    """
    Create a test FastAPI application.
    
    This fixture provides a test instance of the FastAPI app.
    
    Args:
        test_settings: Test settings
        
    Returns:
        FastAPI app
    """
    # Configure logging for tests
    configure_logging(log_level=test_settings.LOG_LEVEL, json_logs=test_settings.JSON_LOGS)
    
    # Create app with test settings
    app = create_app(test_settings)
    
    # Initialize database (this is normally done when the app starts)
    asyncio.run(init_database())
    
    return app


@pytest_asyncio.fixture(scope="function")
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test client for the FastAPI app.
    
    This fixture provides a test client for API tests.
    
    Args:
        app: FastAPI app
        
    Yields:
        HTTPX AsyncClient
    """
    # Get settings
    settings = get_settings()
    
    # Create HTTPX AsyncClient
    async with AsyncClient(
        app=app,
        base_url=f"http://test{settings.API_PREFIX}",
        headers={"Content-Type": "application/json"},
    ) as client:
        yield client


# Mock fixtures for external services
@pytest.fixture
def mock_mcp_service() -> Dict[str, Any]:
    """
    Mock responses for the MCP service.
    
    This fixture provides mock data for the MCP service.
    
    Returns:
        Dictionary of mock responses
    """
    return {
        "tenant_config": {
            "tenant_id": "test-tenant",
            "name": "Test Tenant",
            "settings": {
                "message_schema_version": "1.0.0",
                "channel_config": {
                    "timeout": 30,
                    "retry": 3,
                },
            },
        },
    }


@pytest.fixture
def mock_chat_service() -> Dict[str, Any]:
    """
    Mock responses for the Chat service.
    
    This fixture provides mock data for the Chat service.
    
    Returns:
        Dictionary of mock responses
    """
    return {
        "conversations": [
            {
                "conversation_id": "conv-1",
                "tenant_id": "test-tenant",
                "user_id": "user-1",
                "channel_id": "channel-1",
                "status": "active",
                "last_message_at": "2025-05-20T12:00:00Z",
            },
        ],
        "messages": [
            {
                "message_id": "msg-1",
                "conversation_id": "conv-1",
                "tenant_id": "test-tenant",
                "channel_id": "channel-1",
                "content": "Test message",
                "metadata": {},
                "direction": "inbound",
                "status": "delivered",
                "created_at": "2025-05-20T12:00:00Z",
            },
        ],
    }


@pytest.fixture
def mock_adaptor_service() -> Dict[str, Any]:
    """
    Mock responses for the Adaptor service.
    
    This fixture provides mock data for the Adaptor service.
    
    Returns:
        Dictionary of mock responses
    """
    return {
        "channels": [
            {
                "id": "channel-1",
                "tenant_id": "test-tenant",
                "channel_type": "sms",
                "status": "active",
            },
        ],
        "channel_configurations": [
            {
                "channel_id": "channel-1",
                "config_key": "provider",
                "config_value": "twilio",
            },
        ],
    }


# Mock fixtures for shard components
@pytest.fixture
def mock_shard_topology() -> Dict[str, Any]:
    """
    Mock shard topology.
    
    This fixture provides mock data for the shard topology.
    
    Returns:
        Dictionary of mock shard topology
    """
    return {
        DatabaseType.MONGODB: {
            "shards": [
                {
                    "id": "shard-1",
                    "uri": "mongodb://localhost:27017/migrations_test_shard1",
                    "key_range": {"min": None, "max": "5000000"},
                },
                {
                    "id": "shard-2",
                    "uri": "mongodb://localhost:27017/migrations_test_shard2",
                    "key_range": {"min": "5000000", "max": None},
                },
            ],
        },
        DatabaseType.POSTGRESQL: {
            "shards": [
                {
                    "id": "shard-1",
                    "uri": "postgresql://postgres:postgres@localhost:5432/migrations_test_shard1",
                    "key_range": {"min": None, "max": "5000000"},
                },
                {
                    "id": "shard-2",
                    "uri": "postgresql://postgres:postgres@localhost:5432/migrations_test_shard2",
                    "key_range": {"min": "5000000", "max": None},
                },
            ],
        },
    }


# Utility fixtures for common test operations
@pytest.fixture
def create_migration() -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """
    Create a test migration.
    
    This fixture provides a function to create a test migration record.
    
    Returns:
        Function to create a test migration
    """
    
    def _create_migration(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a test migration with optional overrides."""
        migration = {
            "id": "test-migration-1",
            "name": "Test Migration",
            "version": "1.0.0",
            "type": "schema",
            "database_type": "mongodb",
            "status": "pending",
            "created_at": "2025-05-20T12:00:00Z",
            "started_at": None,
            "completed_at": None,
            "error": None,
            "metadata": {},
        }
        
        if overrides:
            migration.update(overrides)
            
        return migration
    
    return _create_migration