from __future__ import annotations

import boto3
from botocore.config import Config as BotoConfig

from config import settings

_s3_client = None


def get_s3_client():
    global _s3_client
    if _s3_client is not None:
        return _s3_client

    boto_cfg = BotoConfig(
        s3={"addressing_style": settings.s3_addressing_style},
        retries={"max_attempts": 3, "mode": "standard"},
        signature_version="s3v4",
    )

    _s3_client = boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name=settings.s3_region,
        use_ssl=settings.s3_secure,
        config=boto_cfg,
    )
    return _s3_client


def bucket_for_type(t: str) -> str:
    """Header `type` decides only the bucket."""
    if t == "user":
        return settings.user_bucket
    if t == "recruitment":
        return settings.recruitment_bucket
    if t == "advertisement":
        return settings.advertisement_bucket
    raise ValueError("Invalid type header. Allowed: user, recruitment, advertisement")
