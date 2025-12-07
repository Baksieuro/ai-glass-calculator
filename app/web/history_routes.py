"""
Роуты для просмотра истории коммерческих предложений:
- GET /manager/history        — список КП
- GET /manager/history/{id}   — просмотр одного КП и ссылка на pdf
"""

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path
from app.db import SessionLocal
from app import crud
import json

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

PDF_DIR = BASE_DIR.parent / "pdf"

@router.get("/manager/history", response_class=HTMLResponse)
def history_list(request: Request):
    db = SessionLocal()
    try:
        items = crud.list_proposals(db, limit=200)
        return templates.TemplateResponse("history_list.html", {"request": request, "items": items})
    finally:
        db.close()

@router.get("/manager/history/{proposal_id}", response_class=HTMLResponse)
def history_view(request: Request, proposal_id: int):
    db = SessionLocal()
    try:
        prop = crud.get_proposal(db, proposal_id)
        if not prop:
            return HTMLResponse(content="Proposal not found", status_code=404)
        # распарсить JSON поля для отображения
        items = json.loads(prop.items_json) if prop.items_json else []
        deliveries = json.loads(prop.deliveries_json) if prop.deliveries_json else []
        return templates.TemplateResponse("history_view.html", {
            "request": request,
            "prop": prop,
            "items": items,
            "deliveries": deliveries
        })
    finally:
        db.close()

@router.get("/manager/history/download/{filename}")
def history_download(filename: str):
    fpath = PDF_DIR / filename
    if not fpath.exists():
        return HTMLResponse(content="File not found", status_code=404)
    return FileResponse(path=fpath, media_type="application/pdf", filename=filename)