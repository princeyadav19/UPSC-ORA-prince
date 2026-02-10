from __future__ import annotations

import os

from fastapi import HTTPException, Response
from botocore.exceptions import ClientError

from database.s3 import get_s3_client, bucket_for_type
from database.mongo import write_audit
from document_services.dtos import S3Headers
from document_services.path_builder import build_prefix
from document_services.validators import guess_media_type


def _pick_latest_key(contents: list[dict]) -> str:
    latest = max(contents, key=lambda x: x.get("LastModified"))
    return latest["Key"]


async def download_document(headers: S3Headers, filename: str | None = None) -> Response:
    bucket = bucket_for_type(headers.type)
    prefix = build_prefix(headers)

    s3 = get_s3_client()

    try:
        if filename:
            key = f"{prefix}{os.path.basename(filename)}"
        else:
            resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
            if "Contents" not in resp or not resp["Contents"]:
                raise HTTPException(status_code=404, detail="File not found")
            key = _pick_latest_key(resp["Contents"])

        obj = s3.get_object(Bucket=bucket, Key=key)
        content = obj["Body"].read()

        dl_name = os.path.basename(key) or headers.type_of_document
        media_type = guess_media_type(dl_name)

    except ClientError as e:
        raise HTTPException(status_code=400, detail=f"S3 error: {e.response['Error'].get('Message', 'unknown')}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

    await write_audit("download", {
        "type": headers.type,
        "applicant_id": headers.applicant_id,
        "advertisement_id": headers.advertisement_id,
        "lang": headers.lang,
        "type_of_document": headers.type_of_document,
        "bucket": bucket,
        "key": key,
        "size_bytes": len(content),
    })

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{dl_name}"'},
    )
