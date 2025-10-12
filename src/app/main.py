from typing import List

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.schemas.item import ItemCreate, ItemRead

app = FastAPI(title="Quiz Builder API", version="0.1.0")


class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return JSONResponse(
        status_code=exc.status,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else "http_error"
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "http_error", "message": detail}},
    )


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to Quiz Builder API",
        "health_check": "/health",
        "items_endpoint": "/items",
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}


_DB = {"items": []}


@app.post("/items", response_model=ItemRead, tags=["Items"])
async def create_item(data: ItemCreate):
    item = {"id": len(_DB["items"]) + 1, "name": data.name}
    _DB["items"].append(item)
    return item


@app.get("/items", response_model=List[ItemRead], tags=["Items"])
async def list_items(limit: int = 10, offset: int = 0):
    return _DB["items"][offset : offset + limit]


@app.get("/items/{item_id}", response_model=ItemRead, tags=["Items"])
async def get_item(item_id: int):
    for it in _DB["items"]:
        if it["id"] == item_id:
            return it
    raise HTTPException(status_code=404, detail="item not found")
