from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

from config import settings

logger = logging.getLogger("s3-service.mongo")

_mongo_client: Optional[AsyncIOMotorClient] = None


def get_mongo_client() -> AsyncIOMotorClient:
    global _mongo_client
    if _mongo_client is not None:
        return _mongo_client

    auth = ""
    if settings.mongo_username and settings.mongo_password:
        auth = f"{settings.mongo_username}:{settings.mongo_password}@"

    uri = f"mongodb://{auth}{settings.mongo_host}:{settings.mongo_port}"
    kwargs: dict[str, Any] = {}
    if settings.mongo_username and settings.mongo_password:
        kwargs["authSource"] = settings.mongo_auth_db

    _mongo_client = AsyncIOMotorClient(uri, **kwargs)
    return _mongo_client


def get_audit_collection() -> AsyncIOMotorCollection:
    client = get_mongo_client()
    db = client[settings.mongo_db_name]
    return db[settings.mongo_audit_collection]


async def write_audit(event: str, payload: dict) -> None:
    try:
        col = get_audit_collection()
        doc = {"event": event, "ts": datetime.now(timezone.utc), **payload}
        await col.insert_one(doc)
    except Exception as e:
        logger.warning("audit_write_failed", extra={"error": str(e)})
