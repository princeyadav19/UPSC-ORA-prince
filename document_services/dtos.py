from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class S3Headers(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str = Field(..., description="user or recruitment")
    applicant_id: int = Field(..., ge=1, description="Decrypted applicant id")
    type_of_document: str = Field(..., min_length=1, description="Document type to decide path")
    post_id: Optional[str] = Field(default=None, description="Required when type=recruitment")

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if v not in ("user", "recruitment"):
            raise ValueError("type must be 'user' or 'recruitment'")
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

    @model_validator(mode="after")
    def require_post_id_for_recruitment(self):
        if self.type == "recruitment" and not self.post_id:
            raise ValueError("post_id header is required when type is 'recruitment'")
        return self
