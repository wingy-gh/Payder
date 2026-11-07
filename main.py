import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from app.admin.router import router as admin_router
from app.api.router import api_router
from app.core.config import get_settings
from app.core.headers import SecurityHeadersMiddleware
from app.database.db_core import init_db

logger = logging.getLogger("uvicorn.error")
STATIC_DIR = Path(__file__).resolve().parent / "app" / "static"

try:
    settings = get_settings()
except ValidationError as exc:
    # Вместо длинного traceback показываем, что именно не так с настройками.
    problems = "\n".join(
        f"  - {'.'.join(str(part) for part in error['loc']).upper()}: {error['msg'].removeprefix('Value error, ')}"
        for error in exc.errors()
    )
    raise SystemExit(
        "Приложение не запущено: проверьте настройки в файле .env (образец в .env.example).\n" + problems
    ) from None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


# Схема API (/docs, /redoc, /openapi.json) по умолчанию закрыта: в ней описана и админка.
_docs = {} if settings.enable_docs else {"docs_url": None, "redoc_url": None, "openapi_url": None}
app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan, **_docs)
app.add_middleware(SecurityHeadersMiddleware)
# CORS не включаем: фронтенд отдаётся этим же приложением, то есть с того же адреса.
# Раньше стояло allow_origins=["*"], что разрешало любому сайту обращаться к API.
app.include_router(api_router, prefix="/api")
app.include_router(admin_router, prefix="/api/admin")


@app.exception_handler(Exception)
async def unhandled_error(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, HTTPException):
        raise exc
    # Пользователю подробности не показываем, но в журнале они должны остаться.
    logger.error("Необработанная ошибка: %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "Внутренняя ошибка сервера"})


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/admin")
def admin_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "admin.html")


@app.get("/{full_path:path}")
def spa_fallback(full_path: str) -> FileResponse:
    if full_path.startswith("api/") or full_path.startswith("static/"):
        raise HTTPException(status_code=404, detail="Не найдено")
    if full_path == "admin" or full_path.startswith("admin/"):
        return FileResponse(STATIC_DIR / "admin.html")
    return FileResponse(STATIC_DIR / "index.html")