from fastapi import APIRouter, Request, Form
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
import json
from datetime import datetime

from fastapi.templating import Jinja2Templates

from app.core.schemas import CalcRequest
from app.core.calculator import calc
from app.db import SessionLocal
from app import crud
from app.config import settings

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
PDF_DIR = BASE_DIR.parent / "pdf"
PDF_DIR.mkdir(exist_ok=True)


@router.post("/manager/pdf")
async def manager_generate_pdf(request: Request, data_json: str = Form(...)):
    """
    Генерация PDF на основе данных превью.
    """
    try:
        data = json.loads(data_json)
    except Exception as e:
        return HTMLResponse(f"JSON error: {e}", status_code=400)

    items = data.get("items", [])
    deliveries = data.get("deliveries", [])
    total = data.get("total", 0)

    # Генерация номера КП
    timestamp = datetime.now().strftime("%d%m%Y%H%M%S")
    proposal_number = f"КП_{timestamp}"
    pdf_filename = f"{proposal_number}.pdf"
    pdf_path = PDF_DIR / pdf_filename

    # Jinja2 templates loader
    templates = Jinja2Templates(directory=TEMPLATES_DIR)

    # ----- ЛОГОТИП -----
    logo_file = None
    if settings.LOGO_FILE.exists():
        logo_file = f"file://{settings.LOGO_FILE.resolve()}"

    # ----- ИЗОБРАЖЕНИЯ РАБОТ -----
    works = []
    if settings.WORKS_DIR.exists():
        for f in settings.WORKS_DIR.iterdir():
            if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
                works.append(f"file://{f.resolve()}")

    # ----- Генерация HTML -----
    html = templates.get_template("commercial_blue.html").render(
        items=items,
        deliveries=deliveries,
        total=total,
        date=datetime.now().strftime("%d.%m.%Y"),
        proposal_number=proposal_number,

        # Данные компании
        company_info=settings.COMPANY_INFO,

        # Файлы изображений
        logo=logo_file,
        works=works,

        # Условия
        delivery_terms=settings.DELIVERY_TERMS,
        payment_terms=settings.PAYMENT_TERMS,
        additional_terms=settings.ADDITIONAL_TERMS,
        final_terms=settings.FINAL_TERMS
    )

    # ----- Генерация PDF через WeasyPrint -----
    from weasyprint import HTML
    HTML(string=html).write_pdf(pdf_path)

    # ----- Сохранение КП в БД -----
    db = SessionLocal()
    try:
        crud.create_proposal(
            db=db,
            proposal_number=proposal_number,
            total=total,
            pdf_path=pdf_filename,
            items=items,
            deliveries=deliveries
        )
    finally:
        db.close()

    return templates.TemplateResponse(
        "manager_pdf_ready.html",
        {
            "request": request,
            "proposal_number": proposal_number,
            "pdf_filename": pdf_filename
        }
    )


@router.get("/manager/pdf/download/{filename}")
async def manager_download_pdf(filename: str):
    """
    Отдаёт PDF файл менеджеру.
    """
    file_path = PDF_DIR / filename

    if not file_path.exists():
        return HTMLResponse("File not found", status_code=404)

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=filename
    )