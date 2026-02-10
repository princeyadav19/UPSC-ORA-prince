from __future__ import annotations

import os

from document_services.dtos import S3Headers


def build_prefix(headers: S3Headers) -> str:
    """S3 KEY PREFIX (bucket is decided separately).

    user:
      applicant_id/type_of_document/

    recruitment:
      post_id/applicant_id/type_of_document/

    advertisement:
      advertisement_id/type_of_document/
    """
    if headers.type == "recruitment":
        # post_id is guaranteed by DTO validator
        return f"{headers.post_id}/{headers.applicant_id}/{headers.type_of_document}/"

    if headers.type == "advertisement":
        # advertisement_id and lang are guaranteed by DTO validator
        # Uses type_of_document directly as folder name, then lang
        return f"{headers.advertisement_id}/{headers.type_of_document}/{headers.lang}/"

    # type == user
    return f"{headers.applicant_id}/{headers.type_of_document}/"


def safe_filename(filename: str) -> str:
    return os.path.basename(filename)
