"""
История КП: список /manager/history, просмотр /manager/history/{id}, скачивание PDF.
Ошибки и отсутствующие файлы логируются.
"""

import json

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates

from app import crud
from app.config import settings
from app.db import SessionLocal
from app.logging_config import get_logger

router = APIRouter()
logger = get_logger(__name__)
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))


@router.get("/manager/history", response_class=HTMLResponse)
def history_list(request: Request):
    db = SessionLocal()
    try:
        items = crud.list_proposals(db, limit=200)
        return templates.TemplateResponse(
            "history_list.html",
            {"request": request, "items": items},
        )
    finally:
        db.close()


@router.get("/manager/history/{proposal_id}", response_class=HTMLResponse)
def history_view(request: Request, proposal_id: int):
    db = SessionLocal()
    try:
        prop = crud.get_proposal(db, proposal_id)
        if not prop:
            logger.warning("history_view | proposal_not_found | proposal_id=%s", proposal_id)
            return HTMLResponse(content="Proposal not found", status_code=404)
        items = json.loads(prop.items_json) if prop.items_json else []
        deliveries = json.loads(prop.deliveries_json) if prop.deliveries_json else []
        return templates.TemplateResponse(
            "history_view.html",
            {
                "request": request,
                "prop": prop,
                "items": items,
                "deliveries": deliveries,
            },
        )
    finally:
        db.close()


@router.get("/manager/history/download/{filename}")
def history_download(filename: str):
    fpath = settings.PDF_DIR / filename
    if not fpath.exists():
        logger.warning("history_download | file_not_found | filename=%s", filename)
        return HTMLResponse(content="File not found", status_code=404)
    return FileResponse(path=fpath, media_type="application/pdf", filename=filename)
