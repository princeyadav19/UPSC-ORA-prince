from __future__ import annotations

from fastapi.responses import JSONResponse


def ok(message: str, response: dict | None = None, status_code: int = 200) -> JSONResponse:
    payload: dict = {"status": True, "message": message}
    if response is not None:
        payload["response"] = response
    return JSONResponse(content=payload, status_code=status_code)
