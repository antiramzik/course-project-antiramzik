from typing import List

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import JSONResponse

from app.routers import auth as auth_router
from app.routers import items as items_router
from app.schemas.item import ItemCreate, ItemRead

app = FastAPI(title="Quiz Builder API", version="0.1.0")

app.include_router(auth_router.router)
app.include_router(items_router.router)


# Кастомные ошибки домена (если пригодятся)
class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status


# === Глобальные обработчики в требуемом контракте ===
@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return JSONResponse(
        status_code=exc.status,
        content={"error": {"code": exc.code, "message": exc.message}},
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    # Маппинг кодов на требуемые "code"
    code_map = {
        400: "bad_request",
        401: "unauthorized",
        403: "forbidden",
        404: "not_found",
        405: "method_not_allowed",
        409: "conflict",
    }
    code = code_map.get(exc.status_code, "http_error")
    message = exc.detail if isinstance(exc.detail, str) else "http error"
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": code, "message": message}},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Оборачиваем стандартную 422 в нужный формат
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "validation_error",
                "message": "validation failed",
                "details": exc.errors(),
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # На всякий для неожиданных 500
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal_error", "message": "internal server error"}},
    )


# === Служебные эндпоинты ===
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


# === Простейшее "хранилище" ===
_DB = {"items": []}


# === Items CRUD ===
@app.post("/items", response_model=ItemRead, tags=["Items"])
async def create_item(data: ItemCreate):
    # ItemCreate должен валидировать name (пустая строка вызовет 422 через Pydantic/FastAPI)
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
    # Это превратится в {"error": {"code": "not_found", "message": "item not found"}}
    raise HTTPException(status_code=404, detail="item not found")
