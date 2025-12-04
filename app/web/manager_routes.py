"""
Менеджер: форма /manager и preview /manager/preview
Теперь форма собирает массив items на клиенте (JS) и отправляет JSON в data_json на сервер.
"""
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import json

from app.core.calculator import calc, load_products
from app.core.schemas import CalcRequest
from app.config import settings

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@router.get("/manager", response_class=HTMLResponse)
async def manager_form(request: Request):
    """Отображение формы менеджера (JS добавляет/удаляет товары)."""
    products = load_products()
    return templates.TemplateResponse(
        "manager_form.html",
        {"request": request, "products": products}
    )


@router.post("/manager/preview", response_class=HTMLResponse)
async def manager_preview(request: Request, data_json: str = Form(...)):
    """
    Принимает data_json — JSON-строку с ключом "items" — список изделий.
    Пример структуры items (каждый элемент):
    {
      "product_key": "mirror_standart_4mm",
      "width_mm": 2500,
      "height_mm": 1000,
      "quantity": 2,
      "options": {...}
    }
    """
    try:
        data = json.loads(data_json)
        items_payload = data.get("items", [])
    except Exception as e:
        # неверный JSON
        return HTMLResponse(content=f"Invalid JSON: {e}", status_code=400)

    # Валидация и расчёт через calc
    try:
        req = CalcRequest(items=items_payload)
        result = calc(req)
    except Exception as e:
        return HTMLResponse(content=f"Calculation error: {e}", status_code=400)

    # Подготовка items_for_template — парсинг result.positions по item_index
    items_map = {}
    for pos in result.positions:
        idx = getattr(pos, "item_index", None)
        if idx is None:
            continue
        if idx not in items_map:
            items_map[idx] = {
                "product_name": "",
                "thickness": "",
                "width": None,
                "height": None,
                "quantity": 1,
                "services": [],
                "item_total": 0.0
            }
        # определим материал (первый элемент обычно)
        if "мм" in str(pos.name) and "[" in pos.name:
            # формат как в калькуляторе: "Label (4.0 мм) [2500 × 1000 мм]"
            main_part = str(pos.name).split("[")[0].strip()
            dims = str(pos.name).split("[")[1].split("]")[0]
            width_str, height_str = dims.split("×")
            def clean_num(s): return float(''.join(ch for ch in str(s) if (ch.isdigit() or ch == '.')))
            items_map[idx]["product_name"] = main_part.split("(")[0].strip()
            items_map[idx]["thickness"] = main_part.split("(")[1].replace("мм)", "").strip()
            items_map[idx]["width"] = clean_num(width_str)
            items_map[idx]["height"] = clean_num(height_str)
            items_map[idx]["quantity"] = int(pos.quantity)
        elif str(pos.name).startswith("Итого по изделию"):
            items_map[idx]["item_total"] = pos.total
        else:
            # служебная позиция — добавим в services
            items_map[idx]["services"].append(pos.name)

    items_list = [items_map[k] for k in sorted(items_map.keys())]

    # deliveries
    deliveries = []
    for pos in result.positions:
        if getattr(pos, "item_index", None) is None:
            # pos.name like "Доставка (center_центр)"
            deliveries.append({"label": pos.name, "price": pos.total})

    # подготовим data_json для формы preview -> manager/pdf
    data_for_pdf = {
        "items": items_list,
        "deliveries": deliveries,
        "total": result.total
    }
    data_json_out = json.dumps(data_for_pdf, ensure_ascii=False)

    return templates.TemplateResponse(
        "manager_preview.html",
        {
            "request": request,
            "result": result,
            "items": items_list,
            "deliveries": deliveries,
            "total": result.total,
            "data_json": data_json_out
        }
    )