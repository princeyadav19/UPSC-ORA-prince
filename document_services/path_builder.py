from __future__ import annotations

import os

from document_services.doc_rules import DOC_RULES, DEFAULT_RULE
from document_services.dtos import S3Headers


def build_prefix(headers: S3Headers) -> str:
    """S3 KEY PREFIX (bucket is decided separately).

    user:
      applicant_id/folder/

    recruitment:
      recruitment/post_id/applicant_id/folder/
    """
    rule = DOC_RULES.get(headers.type_of_document, DEFAULT_RULE)

    if headers.type == "recruitment":
        # post_id is guaranteed by DTO validator
        return f"{headers.post_id}/{headers.applicant_id}/{rule.folder}/"

    # type == user
    return f"{headers.applicant_id}/{rule.folder}/"


def safe_filename(filename: str) -> str:
    return os.path.basename(filename)
