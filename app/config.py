"""
Configuration management for the Data Migration Service.

This module loads and manages application configuration from
environment variables, files, and default values.
"""
import os
from enum import Enum
from functools import lru_cache
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, Field, PostgresDsn, field_validator
from pydantic_core.core_schema import FieldValidationInfo
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevel(str, Enum):
    """Log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Environment(str, Enum):
    """Application environments."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class DatabaseType(str, Enum):
    """Database types."""

    MONGODB = "mongodb"
    POSTGRESQL = "postgresql"


class Settings(BaseSettings):
    """
    Application settings.

    Loads configuration from environment variables, .env file, and defaults.
    """

    # Application settings
    APP_NAME: str = "data-migration-service"
    API_PREFIX: str = "/api"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = False

    # Security settings
    SECRET_KEY: str = Field("changeme", description="Secret key for security")
    API_KEY_HEADER: str = "X-API-Key"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Logging settings
    LOG_LEVEL: LogLevel = LogLevel.INFO
    JSON_LOGS: bool = True

    # Database settings
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "chat_assistant"
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    # MongoDB settings
    # MONGODB_URI: str = "mongodb://localhost:27017"
    # MONGODB_DB: str = "chat_assistant"

    # MongoDB connection components
    MONGO_INITDB_ROOT_USERNAME: str = "admin"
    MONGO_INITDB_ROOT_PASSWORD: str = "password"
    MONGODB_HOST: str = "localhost"
    MONGODB_PORT: str = "27017"
    MONGODB_DB: str = "chat_assistant"
    MONGODB_URI: Optional[str] = None

    # Shard settings
    SHARD_CONFIG_PATH: Optional[str] = None
    SHARD_DISCOVERY_ENABLED: bool = False

    # Message broker settings
    MESSAGE_BROKER_TYPE: str = "rabbitmq"  # rabbitmq or kafka
    RABBITMQ_URI: str = "amqp://guest:guest@localhost:5672/"
    KAFKA_BOOTSTRAP_SERVERS: List[str] = ["localhost:9092"]

    # Integration settings
    MCP_SERVICE_URL: AnyHttpUrl = "http://localhost:8001"
    MCP_SERVICE_API_KEY: str = "dev-api-key"
    CHAT_SERVICE_URL: AnyHttpUrl = "http://localhost:8002"
    CHAT_SERVICE_API_KEY: str = "dev-api-key"
    ADAPTOR_SERVICE_URL: AnyHttpUrl = "http://localhost:8003"
    ADAPTOR_SERVICE_API_KEY: str = "dev-api-key"

    # Performance settings
    DEFAULT_BATCH_SIZE: int = 1000
    MAX_PARALLEL_MIGRATIONS: int = 10
    THROTTLE_MIGRATIONS: bool = False
    THROTTLE_RATE: int = 100  # operations per second

    # Retry settings
    MAX_RETRIES: int = 3
    RETRY_BACKOFF_FACTOR: float = 1.5

    # Generate SQLAlchemy URI
    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_postgres_uri(cls, v: Optional[str], info: FieldValidationInfo) -> Any:
        """Assemble PostgreSQL URI from components."""
        if isinstance(v, str):
            return v

        data = info.data
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=data.get("POSTGRES_USER"),
            password=data.get("POSTGRES_PASSWORD"),
            host=data.get("POSTGRES_SERVER"),
            port=int(data.get("POSTGRES_PORT")),
            path=f"{data.get('POSTGRES_DB') or ''}",
        )

    model_config = SettingsConfigDict(
        env_file=".env.example",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("MONGODB_URI", mode="before")
    @classmethod
    def assemble_mongodb_uri(cls, v: Optional[str], info: FieldValidationInfo) -> str:
        """Build MongoDB URI from components if not explicitly provided."""
        if isinstance(v, str) and v.startswith("mongodb://"):
            return v

        data = info.data
        return (
            f"mongodb://{data.get('MONGO_INITDB_ROOT_USERNAME')}:"
            f"{data.get('MONGO_INITDB_ROOT_PASSWORD')}@"
            f"{data.get('MONGODB_HOST')}:{data.get('MONGODB_PORT')}/"
            f"?authSource=admin"
        )
        # return (
        #     f"mongodb://{data.get('MONGODB_HOST')}:{data.get('MONGODB_PORT')}/"
        #     f"{data.get('MONGODB_DB')}"
        # )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
            

@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings with caching.
    
    Returns:
        The application settings
    """
    return Settings()


def get_mongodb_connection_string(database_name: Optional[str] = None) -> str:
    """
    Get MongoDB connection string.
    
    Args:
        database_name: The database name to use (optional)
        
    Returns:
        MongoDB connection string
    """
    settings = get_settings()
    uri = settings.MONGODB_URI
    db = database_name or settings.MONGODB_DB
    
    # If the URI already includes a database, replace it
    # if "/" in uri.split("//")[1]:
    #     parts = uri.split("/")
    #     if len(parts) > 3:  # has db name
    #         uri = "/".join(parts[:-1]) + "/" + db
    #     else:
    #         uri = uri + "/" + db
    # else:
    #     uri = uri + "/" + db
    
    return uri


def get_database_url_for_type(db_type: DatabaseType, name: Optional[str] = None) -> str:
    """
    Get database URL for a specific database type.
    
    Args:
        db_type: The database type
        name: The database name to use (optional)
        
    Returns:
        Database URL
    """
    settings = get_settings()
    
    if db_type == DatabaseType.MONGODB:
        return get_mongodb_connection_string(name)
    elif db_type == DatabaseType.POSTGRESQL:
        # Use the configured URI or build a new one
        uri = str(settings.SQLALCHEMY_DATABASE_URI)
        if name:
            # Replace the database name in the URI
            parts = uri.split("/")
            if len(parts) > 3:  # has db name
                uri = "/".join(parts[:-1]) + "/" + name
            else:
                uri = uri + "/" + name
        return uri
    else:
        raise ValueError(f"Unsupported database type: {db_type}")