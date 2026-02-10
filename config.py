from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Minimal settings for the S3 service.

    Extra keys in the env file are ignored so old env files won't break startup.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General
    service_name: str = Field(default="s3-service", alias="SERVICE_NAME")
    environment: str = Field(default="local", alias="ENVIRONMENT")
    s3_expiry_seconds: int = Field(default=3600, alias="S3_EXPIRY_SECONDS")

    # RSYSLOG (comma-separated host:port)
    rsyslog_destinations: str = Field(default="localhost:514", alias="RSYSLOG_DESTINATIONS")

    # Redis
    redis_nodes: str = Field(default="localhost:6379", alias="REDIS_NODES")
    redis_username: str = Field(default="", alias="REDIS_USERNAME")
    redis_password: str = Field(default="", alias="REDIS_PASSWORD")
    redis_ssl: bool = Field(default=False, alias="REDIS_SSL")

    # Mongo (audit)
    mongo_host: str = Field(default="localhost", alias="MONGO_HOST")
    mongo_port: int = Field(default=27017, alias="MONGO_PORT")
    mongo_username: str = Field(default="", alias="MONGO_USERNAME")
    mongo_password: str = Field(default="", alias="MONGO_PASSWORD")
    mongo_auth_db: str = Field(default="admin", alias="MONGO_AUTH_DB")
    mongo_db_name: str = Field(default="audit_db", alias="MONGO_DB_NAME")
    mongo_audit_collection: str = Field(default="s3_audit_logs", alias="MONGO_AUDIT_COLLECTION")

    # S3 / MinIO
    s3_endpoint_url: str = Field(default="http://localhost:9000", alias="S3_ENDPOINT_URL")
    s3_access_key: str = Field(default="", alias="S3_ACCESS_KEY")
    s3_secret_key: str = Field(default="", alias="S3_SECRET_KEY")
    s3_region: str = Field(default="us-east-1", alias="S3_REGION")
    s3_secure: bool = Field(default=False, alias="S3_SECURE")
    s3_addressing_style: str = Field(default="path", alias="S3_ADDRESSING_STYLE")

    # Buckets
    user_bucket: str = Field(default="uploads", alias="USER_BUCKET")
    recruitment_bucket: str = Field(default="recruitment", alias="RECRUITMENT_BUCKET")
    advertisement_bucket: str = Field(default="advertisement", alias="ADVERTISEMENT_BUCKET")


settings = Settings()
