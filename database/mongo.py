from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection

from config import settings

logger = logging.getLogger("s3-service.mongo")

_mongo_client: Optional[AsyncIOMotorClient] = None


# -------------------------------
# Mongo Client
# -------------------------------
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


# -------------------------------
# Collections
# -------------------------------
def get_audit_collection() -> AsyncIOMotorCollection:
    client = get_mongo_client()
    db = client[settings.mongo_db_name]
    return db[settings.mongo_audit_collection]


def get_user_collection() -> AsyncIOMotorCollection:
    client = get_mongo_client()
    db = client[settings.mongo_db_name]
    return db["registerduser"]   # ✅ final collection


# -------------------------------
# Audit Log (already working)
# -------------------------------
async def write_audit(event: str, payload: dict) -> None:
    try:
        col = get_audit_collection()
        doc = {
            "event": event,
            "ts": datetime.now(timezone.utc),
            **payload
        }
        await col.insert_one(doc)
    except Exception as e:
        print("🔥 audit error:", str(e))


# -------------------------------
# 🔥 FINAL: User Document Update + Insert
# -------------------------------
async def write_doc(payload: dict) -> None:
    try:
        col = get_user_collection()

        applicant_id = payload.get("applicant_id")
        doc_type = payload.get("type_of_document")
        key = payload.get("key")
        bucket = payload.get("bucket")

        print("🔥 updating applicant:", applicant_id)

        # mapping for document types
        field_map = {
            "board_certificate": "bc",
            "photo": "photo",
            "signature": "s",
            "id_card": "pid",
            "caste_certificate": "cc",
            "disability_certificate": "dc",
            "aadhar_image": "aadhar_im",   # 🔥 NEW ADDED
        }

        short = field_map.get(doc_type)

        if not short:
            print("❌ invalid doc type:", doc_type)
            return

        await col.update_one(
            {"_id": applicant_id},   # 🔥 main identifier
            {
                "$set": {
                    f"docs.{short}": True,
                    f"docs.s3_{short}_url": f"s3://{bucket}/{key}",
                    f"docs.{short}_insert_ist": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            },
            upsert=True   # 🔥 VERY IMPORTANT (create if not exists)
        )

        print("✅ Mongo updated/created successfully")

    except Exception as e:
        print("🔥 ERROR in write_doc:", str(e))