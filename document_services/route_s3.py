from __future__ import annotations

from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Header, Query, UploadFile

from common.common_header import common_headers
from document_services.dtos import S3Headers
from document_services.uploads.handler import upload_document
from document_services.downloads.handler import download_document

router = APIRouter(prefix="/s3", tags=["S3 Documents"])


async def headers_dep(
    type_: Annotated[str, Header(alias="type")],
    applicant_id: Annotated[int, Header(alias="applicant_id")],
    type_of_document: Annotated[str, Header(alias="type_of_document")],
    post_id: Annotated[Optional[str], Header(alias="post_id")] = None,
) -> S3Headers:
    return S3Headers(
        type=type_,
        applicant_id=applicant_id,
        type_of_document=type_of_document,
        post_id=post_id,
    )


@router.post("/upload")
async def upload(
    headers: S3Headers = Depends(headers_dep),
    file: Optional[UploadFile] = File(default=None),
    commons: dict = Depends(common_headers),
):
    if file is None:
        # Debugging: Why is file missing?
        return {"ok": False, "source": "new-service", "error": "file field is missing in multipart body"}
    return await upload_document(headers=headers, file=file)


@router.get("/download")
async def download(
    headers: S3Headers = Depends(headers_dep),
    filename: Optional[str] = Query(default=None),
    commons: dict = Depends(common_headers),
):
    return await download_document(headers=headers, filename=filename)
