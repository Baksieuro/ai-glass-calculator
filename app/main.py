"""
Точка входа FastAPI: роутеры, статика, редирект с / на /manager.
Логирование инициализируется при старте.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.api.routes import router
from app.web.manager_routes import router as manager_router
from app.web.pdf_routes import router as pdf_router
from app.web.history_routes import router as history_router
from app.logging_config import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация при старте приложения."""
    logger.info("application_start | title=%s", settings.PROJECT_NAME)
    yield
    logger.info("application_shutdown")


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

if settings.STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")


@app.get("/")
async def index():
    """Главная: редирект в панель менеджера."""
    return RedirectResponse(url="/manager", status_code=302)


app.include_router(router, prefix="/api")
app.include_router(manager_router)
app.include_router(pdf_router)
app.include_router(history_router)
