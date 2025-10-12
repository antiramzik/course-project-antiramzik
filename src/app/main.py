from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import FileResponse, HTMLResponse, JSONResponse

from app.routers import auth as auth_router
from app.routers import items as items_router
from app.routers import quizzes as quizzes_router
from app.schemas.item import ItemCreate, ItemRead

app = FastAPI(title="Quiz Builder API", version="0.1.0")

# === Подключаем API-роутеры ===
app.include_router(auth_router.router)
app.include_router(items_router.router)
app.include_router(quizzes_router.router)


# === Кастомная ошибка домена ===
class ApiError(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status


# === Глобальные обработчики ошибок (единый контракт) ===
@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return JSONResponse(
        status_code=exc.status, content={"error": {"code": exc.code, "message": exc.message}}
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
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
        status_code=exc.status_code, content={"error": {"code": code, "message": message}}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
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
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "internal_error", "message": "internal server error"}},
    )


# === Health ===
@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}


# === Демонстрационный /items для автотестов ===
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


# === Статика и UI на "/" ===
BASE_DIR = Path(__file__).resolve().parents[2]  # корень репозитория
STATIC_DIR = (BASE_DIR / "static").resolve()
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse, tags=["UI"])
@app.get("/", response_class=HTMLResponse, tags=["UI"])
def ui_root():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))

    html = (
        "<!doctype html><html lang='ru'><meta charset='utf-8'>"
        "<title>Quiz Builder</title>"
        "<body style='font-family:sans-serif'>"
        "<h1>Quiz Builder UI</h1>"
        f"<p>Файл не найден: <code>{index_path}</code></p>"
        "<p>Создайте <code>static/index.html</code> в корне репозитория "
        'или откройте <a href="/docs">Swagger</a>.</p>'
        "</body></html>"
    )
    return HTMLResponse(html)
