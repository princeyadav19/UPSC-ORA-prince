from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class DocRule:
    folder: str
    min_kb: int
    max_kb: int
    allowed_exts: Tuple[str, ...]
    allowed_mimes: Tuple[str, ...]


DOC_RULES: Dict[str, DocRule] = {
    "name_change": DocRule("name_change", 50, 300, (".pdf",), ("application/pdf",)),
    "board_certificate": DocRule("board_certificate", 50, 300, (".pdf",), ("application/pdf",)),
    "id_card": DocRule("id_card", 20, 500, (".jpg", ".jpeg", ".png", ".pdf"), ("image/jpeg", "image/png", "application/pdf")),
}

DEFAULT_RULE = DocRule("others", 1, 2048, (), ())
