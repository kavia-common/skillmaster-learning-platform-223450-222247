"""MongoDB connection management using environment MONGODB_URI.

This module centralizes MongoDB connection initialization and access for the app.
"""

from __future__ import annotations

import os
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


# PUBLIC_INTERFACE
def get_mongo_uri() -> str:
    """Return the MongoDB connection URI from env variable MONGODB_URI."""
    uri = os.getenv("MONGODB_URI")
    if not uri:
        # Keep explicit message to aid local setup; do not raise to allow app start without DB
        # Downstream code should handle None DB gracefully where appropriate.
        raise RuntimeError("MONGODB_URI is not set. Please configure it in the environment.")
    return uri


# PUBLIC_INTERFACE
async def init_mongo(database_name: str = "skillmaster") -> AsyncIOMotorDatabase:
    """Initialize global async Mongo client and return database handle.

    Args:
        database_name: The logical database name to use.

    Returns:
        AsyncIOMotorDatabase: Connected database instance.
    """
    global _client, _db
    if _db is not None:
        return _db
    uri = get_mongo_uri()
    _client = AsyncIOMotorClient(uri)
    _db = _client[database_name]
    return _db


# PUBLIC_INTERFACE
def get_db() -> AsyncIOMotorDatabase:
    """Return previously initialized database instance.

    Raises:
        RuntimeError: If init_mongo was not called yet.
    """
    if _db is None:
        raise RuntimeError("MongoDB not initialized. Call init_mongo() first.")
    return _db


# PUBLIC_INTERFACE
async def close_mongo() -> None:
    """Close Mongo client connection if open."""
    global _client, _db
    if _client is not None:
        _client.close()
    _client = None
    _db = None
