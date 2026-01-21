from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from common.logging import setup_logging
from database.redis import ping_redis
from database.mongo import get_mongo_client
from database.s3 import get_s3_client
from document_services.route_s3 import router as s3_router

setup_logging()

app = FastAPI(title="S3 Service", docs_url="/docs", redoc_url=None, openapi_url="/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(s3_router)


@app.get("/health")
async def health():
    mongo_ok = True
    try:
        await get_mongo_client().admin.command("ping")
    except Exception:
        mongo_ok = False

    s3_ok = True
    try:
        get_s3_client()
    except Exception:
        s3_ok = False

    return {"status": True, "mongo": mongo_ok, "redis": ping_redis(), "s3_client": s3_ok, "fixed_by": "antigravity"}
