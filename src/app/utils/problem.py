from typing import Any, Dict, Optional
from uuid import uuid4

from starlette.responses import JSONResponse

__all__ = ["problem"]


def problem(
    status: int,
    title: str,
    detail: str,
    type_: str = "about:blank",
    extras: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    cid = str(uuid4())
    payload: Dict[str, Any] = {
        "type": type_,
        "title": title,
        "status": status,
        "detail": detail,
        "correlation_id": cid,
    }
    if extras:
        payload.update(extras)
    return JSONResponse(payload, status_code=status)
