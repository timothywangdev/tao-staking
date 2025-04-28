import motor.motor_asyncio
from app.config import settings
import logging
from typing import Any, Dict, Optional, List

logger = logging.getLogger(__name__)


class MongoDBClient:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
        self.db = self.client[settings.MONGODB_DB_NAME]
        logger.info(
            f"Connected to MongoDB at {settings.MONGODB_URL}, db: {settings.MONGODB_DB_NAME}"
        )

    def get_collection(self, collection_name: str):
        return self.db[collection_name]

    async def insert_one(self, collection_name: str, document: Dict[str, Any]) -> Optional[str]:
        try:
            result = await self.get_collection(collection_name).insert_one(document)
            logger.info(f"Inserted document into {collection_name} with id: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to insert document into {collection_name}: {e}")
            return None

    async def find_one(
        self, collection_name: str, query: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        try:
            result = await self.get_collection(collection_name).find_one(query)
            return result
        except Exception as e:
            logger.error(f"Failed to find document in {collection_name}: {e}")
            return None

    async def find_many(self, collection_name: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            cursor = self.get_collection(collection_name).find(query)
            return [doc async for doc in cursor]
        except Exception as e:
            logger.error(f"Failed to find documents in {collection_name}: {e}")
            return []

    async def update_one(
        self, collection_name: str, query: Dict[str, Any], update: Dict[str, Any]
    ) -> bool:
        try:
            result = await self.get_collection(collection_name).update_one(query, {"$set": update})
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Failed to update document in {collection_name}: {e}")
            return False

    async def delete_one(self, collection_name: str, query: Dict[str, Any]) -> bool:
        try:
            result = await self.get_collection(collection_name).delete_one(query)
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Failed to delete document in {collection_name}: {e}")
            return False
