"""
Роуты для менеджерской формы:
- GET /manager          — форма ввода
- POST /manager/preview — предпросмотр расчёта + подготовка JSON для генерации PDF
"""

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import json

from app.core.calculator import calc, load_products
from app.core.schemas import CalcItemFull, CalcOptions, CalcRequest
from app.config import settings

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@router.get("/manager", response_class=HTMLResponse)
async def manager_form(request: Request):
    """Отображение формы менеджера: подгружаем список товаров из products.txt"""
    products = load_products()
    # products — dict(key -> {"label":..., "thickness": ...})
    return templates.TemplateResponse(
        "manager_form.html",
        {"request": request, "products": products}
    )


@router.post("/manager/preview", response_class=HTMLResponse)
async def manager_preview(
    request: Request,
    product_key: str = Form(...),
    width_mm: float = Form(...),
    height_mm: float = Form(...),
    quantity: int = Form(1),
    edge: str = Form(None),
    film: str = Form(None),
    drill: str = Form(None),
    drill_qty: int = Form(0),
    pack: str = Form(None),
    delivery_city: str = Form(""),
    mount: str = Form(None),
):
    """
    Обработка формы — делаем расчёт (через calc), формируем JSON для POST /manager/pdf
    Замечание: checkbox приходит как 'on' если включён, или None если нет — приводим к bool.
    """

    # Приводим чекбоксы к булевому виду
    def _bool(v):
        return bool(v) and str(v).lower() not in ("false", "0", "")

    opts = CalcOptions(
        edge=_bool(edge),
        film=_bool(film),
        drill=_bool(drill),
        drill_qty=int(drill_qty or 0),
        pack=_bool(pack),
        delivery_city=delivery_city if delivery_city else None,
        mount=_bool(mount)
    )

    # Формируем CalcItemFull (модель, соответствующая API)
    item = {
        "product_key": product_key,
        "width_mm": float(width_mm),
        "height_mm": float(height_mm),
        "quantity": int(quantity),
        "options": opts.dict()
    }

    # Вызов калькулятора — используем CalcRequest из списка с одним элементом
    req = CalcRequest(items=[item])
    result = calc(req)

    # Подготовка списка items, который ждёт pdf_generator (product_name, thickness, width, height, quantity, services, item_total)
    products_map = load_products()
    product_label = products_map.get(product_key, {}).get("label", product_key)
    thickness = products_map.get(product_key, {}).get("thickness", "")

    # Соберём список услуг для данного изделия — парсим result.positions, где item_index == 0
    services = []
    item_total = 0.0
    for p in result.positions:
        # p is CalcPosition, has item_index
        if getattr(p, "item_index", None) == 0:
            # пропускаем сам материал (у него в name содержится label)
            if p.name.startswith("Итого по изделию"):
                item_total = p.total
            else:
                # если это не материал (и не итог) — считаем как услугу
                # но пропускаем строку с материалом, чтобы не дублировать
                # определим материал по совпадению: если в p.name есть product_label — пропускаем
                if product_label.lower() not in str(p.name).lower():
                    services.append(p.name)

    # Формируем массив items (на данный момент — один элемент)
    items_for_pdf = [{
        "product_name": product_label,
        "thickness": str(thickness),
        "width": float(width_mm),
        "height": float(height_mm),
        "quantity": int(quantity),
        "services": services,
        "item_total": float(item_total or result.total)
    }]

    # Формируем deliveries (если есть)
    deliveries = []
    for p in result.positions:
        if getattr(p, "item_index", None) is None:
            # p.name может выглядеть: "Доставка (center_центр)" — оставим её как есть,
            # pdf_routes позже обработает человеко-читаемую метку
            deliveries.append({"label": p.name, "price": p.total})

    # Собираем JSON для отправки в /manager/pdf
    data_json = json.dumps({
        "items": items_for_pdf,
        "options": opts.dict(),
        "deliveries": deliveries,
        "total": result.total,
        # для удобства сохраняем исходный item (может пригодиться)
        "item": {
            "product_key": product_key,
            "width_mm": width_mm,
            "height_mm": height_mm,
            "quantity": quantity
        }
    }, ensure_ascii=False)

    # Отдаём preview-страницу с подготовленным JSON (в скрытом поле форма отправит его на /manager/pdf)
    return templates.TemplateResponse(
        "manager_preview.html",
        {
            "request": request,
            "result": result,
            "item": item,
            "options": opts,
            "quantity": quantity,
            "data_json": data_json
        }
    )