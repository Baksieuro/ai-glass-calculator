from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path


from app.config import settings # импорт настроек
from app.api.routes import router # импорт роутера API
from app.web.manager_routes import router as manager_router


app = FastAPI(title=settings.PROJECT_NAME)


BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get('/')
async def index(request):
    return templates.TemplateResponse('index.html', {"request": request})

# Подключение роутера API
app.include_router(router, prefix="/api")
app.include_router(manager_router)