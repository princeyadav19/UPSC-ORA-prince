from __future__ import annotations

import mimetypes
import os

from fastapi import HTTPException, UploadFile

from document_services.doc_rules import DocRule


def guess_media_type(filename: str) -> str:
    mt, _ = mimetypes.guess_type(filename)
    return mt or "application/octet-stream"


async def read_and_validate(file: UploadFile, rule: DocRule) -> bytes:
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    filename = os.path.basename(file.filename)
    ext = os.path.splitext(filename)[1].lower()

    content = await file.read()
    size_kb = max(1, int(len(content) / 1024))

    if size_kb < rule.min_kb or size_kb > rule.max_kb:
        raise HTTPException(status_code=400, detail=f"Invalid file size: {size_kb}KB (allowed {rule.min_kb}-{rule.max_kb}KB)")

    if rule.allowed_exts and ext not in rule.allowed_exts:
        raise HTTPException(status_code=400, detail=f"Invalid file extension '{ext}'")

    if rule.allowed_mimes:
        mime = file.content_type or ""
        if mime not in rule.allowed_mimes:
            raise HTTPException(status_code=400, detail=f"Invalid content-type '{mime}'")

    return content
