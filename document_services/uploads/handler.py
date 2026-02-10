from __future__ import annotations

import os
from io import BytesIO

from fastapi import HTTPException, UploadFile
from botocore.exceptions import ClientError

from common.responses import ok
from database.s3 import get_s3_client, bucket_for_type
from database.mongo import write_audit
from document_services.dtos import S3Headers
from document_services.doc_rules import DOC_RULES, DEFAULT_RULE
from document_services.path_builder import build_prefix, safe_filename
from document_services.validators import read_and_validate


def _is_not_found(err: ClientError) -> bool:
    code = (err.response.get("Error", {}) or {}).get("Code", "")
    # MinIO/S3 can return: '404', 'NoSuchKey', 'NotFound'
    return code in ("404", "NoSuchKey", "NotFound")


def _split_name(filename: str) -> tuple[str, str]:
    base, ext = os.path.splitext(filename)
    return base, ext


def _next_archive_key(prefix: str, filename: str, s3, bucket: str) -> str:
    base, ext = _split_name(filename)

    # Try name_1.ext, name_2.ext ...
    for i in range(1, 10_000):
        candidate = f"{prefix}{base}_{i}{ext}"
        try:
            s3.head_object(Bucket=bucket, Key=candidate)
            # exists -> try next
            continue
        except ClientError as e:
            if _is_not_found(e):
                return candidate
            raise

    raise HTTPException(status_code=500, detail="Too many archived versions for this file.")


def _archive_if_exists(s3, bucket: str, key: str) -> str | None:
    """
    If key exists, move it to next available version: name_1.ext, name_2.ext ...
    Returns archived key if moved, else None.
    """
    try:
        s3.head_object(Bucket=bucket, Key=key)
    except ClientError as e:
        if _is_not_found(e):
            return None
        raise

    # Exists -> archive it
    prefix, filename = key.rsplit("/", 1) if "/" in key else ("", key)
    prefix = (prefix + "/") if prefix else ""
    archive_key = _next_archive_key(prefix, filename, s3, bucket)

    # Copy old -> archive, then delete old
    try:
        s3.copy_object(
            Bucket=bucket,
            Key=archive_key,
            CopySource={"Bucket": bucket, "Key": key},
        )
        s3.delete_object(Bucket=bucket, Key=key)
    except ClientError as e:
        raise HTTPException(status_code=400, detail=f"S3 error during archive: {e.response['Error'].get('Message', 'unknown')}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Archive failed: {str(e)}")

    return archive_key


async def upload_document(headers: S3Headers, file: UploadFile):
    rule = DOC_RULES.get(headers.type_of_document, DEFAULT_RULE)
    content = await read_and_validate(file, rule)

    bucket = bucket_for_type(headers.type)
    prefix = build_prefix(headers)

    filename = safe_filename(file.filename or headers.type_of_document)
    key = f"{prefix}{filename}"  # ✅ NO timestamp

    s3 = get_s3_client()

    # ✅ If same filename exists, rename old one to _1/_2...
    archived_to = None
    try:
        archived_to = _archive_if_exists(s3, bucket=bucket, key=key)
    except ClientError as e:
        raise HTTPException(status_code=400, detail=f"S3 error: {e.response['Error'].get('Message', 'unknown')}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Archive check failed: {str(e)}")

    # Upload new file to original name
    try:
        s3.upload_fileobj(Fileobj=BytesIO(content), Bucket=bucket, Key=key)
    except ClientError as e:
        raise HTTPException(status_code=400, detail=f"S3 error: {e.response['Error'].get('Message', 'unknown')}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    await write_audit(
        "upload",
        {
            "type": headers.type,
            "applicant_id": headers.applicant_id,
            "advertisement_id": headers.advertisement_id,
            "lang": headers.lang,
            "type_of_document": headers.type_of_document,
            "bucket": bucket,
            "key": key,
            "archived_to": archived_to,
            "size_bytes": len(content),
            "content_type": file.content_type,
        },
    )

    return ok(
        "File uploaded successfully",
        {
            "bucket": bucket,
            "key": key,
            "archived_to": archived_to,
            "type": headers.type,
            "applicant_id": headers.applicant_id,
            "advertisement_id": headers.advertisement_id,
            "lang": headers.lang,
            "type_of_document": headers.type_of_document,
        },
    )
