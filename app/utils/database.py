"""
Database utilities for the Data Migration Service.

This module provides utilities for connecting to and interacting with
both MongoDB and PostgreSQL databases, with shard awareness.
"""
import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple, Type, TypeVar, Union

import motor.motor_asyncio
from motor.core import AgnosticClient, AgnosticDatabase
from pymongo.errors import ConnectionFailure, OperationFailure
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import DatabaseType, get_database_url_for_type, get_settings
from app.core.exceptions import DatabaseConnectionError, DatabaseError, DatabaseQueryError
from app.core.logging import get_logger, log_execution_time

# Get logger for this module
logger = get_logger(__name__)

# SQLAlchemy model base
Base = declarative_base()

# Type variables for database connections
T = TypeVar("T")

# Connection pools
_mongo_clients: Dict[str, AgnosticClient] = {}
_postgres_engines: Dict[str, AsyncEngine] = {}


class DatabaseConnectionManager:
    """
    Manager for database connections.
    
    Handles connection pooling and lifecycle management.
    """
    
    @staticmethod
    def get_mongo_client(
        uri: str, 
        max_pool_size: int = 10, 
        min_pool_size: int = 1
    ) -> AgnosticClient:
        """
        Get or create a MongoDB client.
        
        Args:
            uri: MongoDB connection URI
            max_pool_size: Maximum connection pool size
            min_pool_size: Minimum connection pool size
            
        Returns:
            MongoDB client instance
        """
        if uri not in _mongo_clients:
            logger.debug("Creating new MongoDB client", uri=uri)
            client = motor.motor_asyncio.AsyncIOMotorClient(
                uri,
                maxPoolSize=max_pool_size,
                minPoolSize=min_pool_size,
                serverSelectionTimeoutMS=5000,
            )
            _mongo_clients[uri] = client
        return _mongo_clients[uri]
    
    @staticmethod
    def get_postgres_engine(uri: str, pool_size: int = 10) -> AsyncEngine:
        """
        Get or create a PostgreSQL engine.
        
        Args:
            uri: PostgreSQL connection URI
            pool_size: Connection pool size
            
        Returns:
            SQLAlchemy AsyncEngine instance
        """
        if uri not in _postgres_engines:
            logger.debug("Creating new PostgreSQL engine", uri=uri)
            engine = create_async_engine(
                uri,
                pool_size=pool_size,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False,
            )
            _postgres_engines[uri] = engine
        return _postgres_engines[uri]

    @staticmethod
    async def verify_mongo_connection(client: AgnosticClient) -> bool:
        """
        Verify that a MongoDB connection is working.

        Args:
            client: MongoDB client to verify

        Returns:
            True if the connection is working, False otherwise
        """
        try:
            # Method 1: Try ping command first
            try:
                await client.admin.command("ping")
                logger.info("MongoDB connection successful using ping command")
                return True
            except Exception as e:
                logger.warning(
                    "MongoDB ping command failed, trying alternative methods",
                    error=str(e)
                )

            # Method 2: Try listing databases
            try:
                database_names = await client.list_database_names()
                logger.info(
                    "MongoDB connection successful using list_database_names",
                    databases=database_names
                )
                return True
            except Exception as e:
                logger.warning(
                    "MongoDB list_database_names failed",
                    error=str(e)
                )

            # Method 3: Try to access the server info
            try:
                server_info = await client.server_info()
                logger.info(
                    "MongoDB connection successful using server_info",
                    version=server_info.get("version")
                )
                return True
            except Exception as e:
                logger.error(
                    "All MongoDB connection methods failed",
                    error=str(e)
                )

            return False
        except Exception as e:
            # Log the full error details for any unexpected errors
            error_details = str(e)
            logger.error(
                "MongoDB connection verification failed with unexpected error",
                error=error_details
            )
            return False
    
    @staticmethod
    async def verify_postgres_connection(engine: AsyncEngine) -> bool:
        """
        Verify that a PostgreSQL connection is working.
        
        Args:
            engine: SQLAlchemy engine to verify
            
        Returns:
            True if the connection is working, False otherwise
        """
        try:
            async with engine.connect() as conn:
                await conn.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error("PostgreSQL connection verification failed", error=str(e))
            return False
    
    @staticmethod
    @asynccontextmanager
    async def get_mongo_database(
        database_name: Optional[str] = None,
        shard_key: Optional[str] = None,
        shard_id: Optional[str] = None,
    ) -> AsyncIterator[AgnosticDatabase]:
        """
        Get a MongoDB database.
        
        Args:
            database_name: The database name to use
            shard_key: Optional shard key for shard routing
            shard_id: Optional explicit shard ID to connect to
            
        Yields:
            MongoDB database instance
        """
        settings = get_settings()
        
        # Get connection URI, with shard awareness if necessary
        if shard_id:
            # TODO: Implement shard routing logic to get the URI for a specific shard
            # For now, we just use the default URI
            uri = get_database_url_for_type(DatabaseType.MONGODB, database_name)
        elif shard_key:
            # TODO: Route to the appropriate shard based on the key
            # For now, we just use the default URI
            uri = get_database_url_for_type(DatabaseType.MONGODB, database_name)
        else:
            uri = get_database_url_for_type(DatabaseType.MONGODB, database_name)
        
        try:
            # Get or create client
            client = DatabaseConnectionManager.get_mongo_client(uri)

            # Verify connection
            if not await DatabaseConnectionManager.verify_mongo_connection(client):
                raise DatabaseConnectionError(f"Failed to connect to MongoDB at {uri}")

            # Get database name from URI if not specified
            if not database_name:
                database_name = settings.MONGODB_DB

            # Get database
            database = client.get_database(database_name)

            yield database
        except Exception as e:
            logger.exception("Error getting MongoDB database", exc_info=e)
            if isinstance(e, DatabaseError):
                raise
            else:
                raise DatabaseConnectionError(f"Failed to connect to MongoDB: {str(e)}")
    
    @staticmethod
    @asynccontextmanager
    async def get_postgres_session(
        database_name: Optional[str] = None,
        shard_key: Optional[str] = None,
        shard_id: Optional[str] = None,
    ) -> AsyncIterator[AsyncSession]:
        """
        Get a PostgreSQL session.
        
        Args:
            database_name: The database name to use
            shard_key: Optional shard key for shard routing
            shard_id: Optional explicit shard ID to connect to
            
        Yields:
            SQLAlchemy session instance
        """
        # Get connection URI, with shard awareness if necessary
        if shard_id:
            # TODO: Implement shard routing logic to get the URI for a specific shard
            # For now, we just use the default URI
            uri = get_database_url_for_type(DatabaseType.POSTGRESQL, database_name)
        elif shard_key:
            # TODO: Route to the appropriate shard based on the key
            # For now, we just use the default URI
            uri = get_database_url_for_type(DatabaseType.POSTGRESQL, database_name)
        else:
            uri = get_database_url_for_type(DatabaseType.POSTGRESQL, database_name)
        
        try:
            # Get or create engine
            engine = DatabaseConnectionManager.get_postgres_engine(uri)
            
            # Verify connection
            if not await DatabaseConnectionManager.verify_postgres_connection(engine):
                raise DatabaseConnectionError(f"Failed to connect to PostgreSQL at {uri}")
            
            # Create session
            async_session = sessionmaker(
                engine, expire_on_commit=False, class_=AsyncSession
            )
            
            async with async_session() as session:
                try:
                    yield session
                except Exception as e:
                    await session.rollback()
                    logger.exception("Error in PostgreSQL session", exc_info=e)
                    if isinstance(e, DatabaseError):
                        raise
                    else:
                        raise DatabaseQueryError(f"Error executing PostgreSQL query: {str(e)}")
        except Exception as e:
            logger.exception("Error getting PostgreSQL session", exc_info=e)
            if isinstance(e, DatabaseError):
                raise
            else:
                raise DatabaseConnectionError(f"Failed to connect to PostgreSQL: {str(e)}")


@log_execution_time
async def init_database() -> None:
    """
    Initialize the database.
    
    Creates tables and indexes if they don't exist.
    """
    settings = get_settings()
    print(str(settings.SQLALCHEMY_DATABASE_URI))
    # Initialize PostgreSQL
    engine = DatabaseConnectionManager.get_postgres_engine(
        str(settings.SQLALCHEMY_DATABASE_URI)
    )
    
    try:
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("PostgreSQL database initialized")
    except Exception as e:
        logger.exception("Error initializing PostgreSQL database", exc_info=e)
        raise DatabaseError(f"Failed to initialize PostgreSQL database: {str(e)}")
    
    # Initialize MongoDB indexes
    try:
        async with DatabaseConnectionManager.get_mongo_database() as db:
            # Create indexes for migration collections
            await db.migration_state.create_index("name")
            await db.migration_state.create_index("status")

            await db.migration_events.create_index("migration_id")
            await db.migration_events.create_index("timestamp")

            await db.migration_locks.create_index("resource")
            await db.migration_locks.create_index(
                "expires_at", expireAfterSeconds=0
            )  # TTL index

        logger.info("MongoDB database initialized")
    except Exception as e:
        logger.exception("Error initializing MongoDB database", exc_info=e)
        raise DatabaseError(f"Failed to initialize MongoDB database: {str(e)}")


class DatabaseClient:
    """
    Generic database client interface.
    
    Abstracts database-specific operations to provide a unified interface.
    """
    
    def __init__(self, database_type: DatabaseType):
        """
        Initialize the database client.
        
        Args:
            database_type: The database type (MongoDB or PostgreSQL)
        """
        self.database_type = database_type
    
    @asynccontextmanager
    async def get_connection(self, 
        database_name: Optional[str] = None,
        shard_key: Optional[str] = None,
        shard_id: Optional[str] = None,
    ) -> AsyncIterator[Union[AsyncSession, AgnosticDatabase]]:
        """
        Get a database connection.
        
        Args:
            database_name: The database name to use
            shard_key: Optional shard key for shard routing
            shard_id: Optional explicit shard ID to connect to
            
        Yields:
            Database connection
        """
        if self.database_type == DatabaseType.MONGODB:
            async with DatabaseConnectionManager.get_mongo_database(
                database_name=database_name,
                shard_key=shard_key,
                shard_id=shard_id,
            ) as conn:
                yield conn
        elif self.database_type == DatabaseType.POSTGRESQL:
            async with DatabaseConnectionManager.get_postgres_session(
                database_name=database_name,
                shard_key=shard_key,
                shard_id=shard_id,
            ) as conn:
                yield conn
        else:
            raise ValueError(f"Unsupported database type: {self.database_type}")


def get_mongo_client() -> DatabaseClient:
    """
    Get a MongoDB client.
    
    Returns:
        MongoDB client
    """
    return DatabaseClient(DatabaseType.MONGODB)


def get_postgres_client() -> DatabaseClient:
    """
    Get a PostgreSQL client.
    
    Returns:
        PostgreSQL client
    """
    return DatabaseClient(DatabaseType.POSTGRESQL)