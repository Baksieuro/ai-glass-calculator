"""
Маршруты менеджера: форма /manager, превью /manager/preview.
Форма отправляет JSON с items; расчёт через calc(), данные для PDF — response_to_pdf_data().
"""

import json

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.core.calculator import calc, load_products, response_to_pdf_data
from app.core.schemas import CalcRequest

router = APIRouter()
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))


@router.get("/manager", response_class=HTMLResponse)
async def manager_form(request: Request):
    """Форма: добавление/удаление товаров, отправка JSON на превью."""
    products = load_products()
    return templates.TemplateResponse(
        "manager_form.html",
        {"request": request, "products": products},
    )


@router.post("/manager/preview", response_class=HTMLResponse)
async def manager_preview(request: Request, data_json: str = Form(...)):
    """Превью расчёта: парсинг items из JSON → calc() → response_to_pdf_data() → шаблон."""
    try:
        data = json.loads(data_json)
        items_payload = data.get("items", [])
    except Exception as e:
        return HTMLResponse(content=f"Invalid JSON: {e}", status_code=400)

    try:
        req = CalcRequest(items=items_payload)
        result = calc(req)
        data_for_pdf = response_to_pdf_data(result)
    except Exception as e:
        return HTMLResponse(content=f"Calculation error: {e}", status_code=400)

    data_json_out = json.dumps(data_for_pdf, ensure_ascii=False)
    return templates.TemplateResponse(
        "manager_preview.html",
        {
            "request": request,
            "result": result,
            "items": data_for_pdf["items"],
            "deliveries": data_for_pdf["deliveries"],
            "total": data_for_pdf["total"],
            "data_json": data_json_out,
        },
    )
