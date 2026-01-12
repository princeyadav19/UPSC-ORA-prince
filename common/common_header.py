from __future__ import annotations

from typing import Optional

from fastapi import Header


async def common_headers(
    lang: Optional[str] = Header(default="en", alias="lang"),
    ip: Optional[str] = Header(default=None, alias="x-forwarded-for"),
) -> dict:
    return {"lang": lang or "en", "ip": ip}
