from __future__ import annotations

import logging
from typing import Optional

import redis

from config import settings

logger = logging.getLogger("s3-service.redis")

_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    first = (settings.redis_nodes or "localhost:6379").split(",")[0].strip()
    host, port_s = first.split(":")
    port = int(port_s)

    _redis_client = redis.Redis(
        host=host,
        port=port,
        username=settings.redis_username or None,
        password=settings.redis_password or None,
        ssl=settings.redis_ssl,
        socket_connect_timeout=2,
        socket_timeout=2,
        decode_responses=True,
    )
    return _redis_client


def ping_redis() -> bool:
    try:
        return bool(get_redis_client().ping())
    except Exception as e:
        logger.warning("redis_ping_failed", extra={"error": str(e)})
        return False
