"""
Генерация PDF из превью: POST /manager/pdf, скачивание /manager/pdf/download/{filename}.
Пути и ассеты — из config и core.assets.
"""

import json
from datetime import datetime

from fastapi import APIRouter, Request, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from weasyprint import HTML

from app import crud
from app.config import settings, DELIVERY_TERMS, PAYMENT_TERMS, ADDITIONAL_TERMS, FINAL_TERMS, get_company_info
from app.core.assets import get_logo_file_uri, get_works_file_uris
from app.db import SessionLocal

router = APIRouter()

settings.PDF_DIR.mkdir(parents=True, exist_ok=True)
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))


@router.post("/manager/pdf")
async def manager_generate_pdf(request: Request, data_json: str = Form(...)):
    """Генерация PDF по данным превью, сохранение в БД, ответ со страницей «Готово»."""
    try:
        data = json.loads(data_json)
    except Exception as e:
        return HTMLResponse(content=f"JSON error: {e}", status_code=400)

    items = data.get("items", [])
    deliveries = data.get("deliveries", [])
    total = data.get("total", 0)

    timestamp = datetime.now().strftime("%d%m%Y%H%M%S")
    proposal_number = f"КП_{timestamp}"
    pdf_filename = f"{proposal_number}.pdf"
    pdf_path = settings.PDF_DIR / pdf_filename

    html = templates.get_template("commercial_blue.html").render(
        items=items,
        deliveries=deliveries,
        total=total,
        date=datetime.now().strftime("%d.%m.%Y"),
        proposal_number=proposal_number,
        company_info=get_company_info(),
        logo=get_logo_file_uri(),
        works=get_works_file_uris(limit=8),
        delivery_terms=DELIVERY_TERMS,
        payment_terms=PAYMENT_TERMS,
        additional_terms=ADDITIONAL_TERMS,
        final_terms=FINAL_TERMS,
    )

    HTML(string=html).write_pdf(pdf_path)

    db = SessionLocal()
    try:
        crud.create_proposal(
            db=db,
            proposal_number=proposal_number,
            total=total,
            pdf_path=pdf_filename,
            items=items,
            deliveries=deliveries,
        )
    finally:
        db.close()

    return templates.TemplateResponse(
        "manager_pdf_ready.html",
        {
            "request": request,
            "proposal_number": proposal_number,
            "pdf_filename": pdf_filename,
        },
    )


@router.get("/manager/pdf/download/{filename}")
async def manager_download_pdf(filename: str):
    """Скачивание PDF по имени файла."""
    file_path = settings.PDF_DIR / filename
    if not file_path.exists():
        return HTMLResponse(content="File not found", status_code=404)
    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=filename,
    )
