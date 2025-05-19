import motor.motor_asyncio
from pymongo.errors import ServerSelectionTimeoutError, OperationFailure
import logging

logger = logging.getLogger(__name__)
_mongo_clients = {}

async def get_mongo_client(uri: str, max_pool_size: int = 10, min_pool_size: int = 1):
    if uri not in _mongo_clients:
        logger.debug("Creating new MongoDB client", extra={"uri": uri})
        client = motor.motor_asyncio.AsyncIOMotorClient(
            uri,
            maxPoolSize=max_pool_size,
            minPoolSize=min_pool_size,
            serverSelectionTimeoutMS=5000,
        )
        _mongo_clients[uri] = client
    return _mongo_clients[uri]

async def validate_mongo_connection(uri: str, db_name: str) -> bool:
    try:
        client = await get_mongo_client(uri)
        # Force connection by calling ping
        await client.admin.command("ping")
        # Check if database exists
        dbs = await client.list_database_names()
        if db_name in dbs:
            logger.info(f"✅ Database '{db_name}' exists.")
            return True
        else:
            logger.warning(f"⚠️ Database '{db_name}' does NOT exist.")
            return False
    except ServerSelectionTimeoutError as e:
        logger.error(f"❌ MongoDB connection timeout: {e}")
        return False
    except OperationFailure as e:
        logger.error(f"❌ MongoDB operation failed: {e}")
        return False


import asyncio

if __name__ == "__main__":
    mongo_uri = "mongodb://admin:password@localhost:27017/chat_assistant"
    db_name = "chat_assistant"

    result = asyncio.run(validate_mongo_connection(mongo_uri, db_name))
    print("Connected:", result)