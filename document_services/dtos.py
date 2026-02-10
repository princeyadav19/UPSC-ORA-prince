from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class S3Headers(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str = Field(..., description="user, recruitment, or advertisement")
    applicant_id: Optional[int] = Field(default=None, ge=1, description="Decrypted applicant id (required for user/recruitment)")
    type_of_document: str = Field(..., min_length=1, description="Document type to decide path")
    post_id: Optional[str] = Field(default=None, description="Required when type=recruitment")
    advertisement_id: Optional[str] = Field(default=None, description="Required when type=advertisement")
    lang: Optional[str] = Field(default=None, description="Language code (en/hi), required when type=advertisement")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if v not in ("user", "recruitment", "advertisement"):
            raise ValueError("type must be 'user', 'recruitment', or 'advertisement'")
        return v

    @field_validator("type_of_document")
    @classmethod
    def validate_doc_type(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if "/" in v or ".." in v or v.startswith("."):
            raise ValueError("Invalid type_of_document")
        return v

    @field_validator("post_id")
    @classmethod
    def validate_post_id(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        # protect from path traversal
        if "/" in v or ".." in v or v.startswith("."):
            raise ValueError("Invalid post_id")
        return v

    @field_validator("advertisement_id")
    @classmethod
    def validate_advertisement_id(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        # protect from path traversal
        if "/" in v or ".." in v or v.startswith("."):
            raise ValueError("Invalid advertisement_id")
        return v

    @field_validator("lang")
    @classmethod
    def validate_lang(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip().lower()
        if not v:
            return None
        if v not in ("en", "hi"):
            raise ValueError("lang must be 'en' or 'hi'")
        return v

    @model_validator(mode="after")
    def validate_type_requirements(self):
        if self.type == "recruitment":
            if not self.post_id:
                raise ValueError("post_id header is required when type is 'recruitment'")
            if not self.applicant_id:
                raise ValueError("applicant_id header is required when type is 'recruitment'")
        elif self.type == "user":
            if not self.applicant_id:
                raise ValueError("applicant_id header is required when type is 'user'")
        elif self.type == "advertisement":
            if not self.advertisement_id:
                raise ValueError("advertisement_id header is required when type is 'advertisement'")
            if not self.lang:
                raise ValueError("lang header is required when type is 'advertisement'")
        return self
