"""
Роуты для генерации PDF из менеджерского интерфейса:
- POST /manager/pdf         — принять data_json, сформировать PDF и сохранить в pdf/
- GET  /manager/pdf/download/{filename} — скачать PDF из архива
"""

from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path
import json
from datetime import datetime

from app.core.calculator import calc
from app.core.schemas import CalcRequest
from app.core.pdf_generator import generate_pdf
from app.config import settings

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent
PDF_DIR = BASE_DIR.parent / "pdf"
PDF_DIR.mkdir(parents=True, exist_ok=True)


def humanize_delivery_label(raw: str) -> str:
    """
    Приводит доставку к формату (центр), (пригород) — удаляем английские префиксы.
    Пример: "Доставка (center_центр)" -> "Доставка (центр)"
    """
    import re
    if not raw:
        return raw
    m = re.search(r"\((.*?)\)", raw)
    if not m:
        return raw
    inside = m.group(1)
    if "_" in inside:
        inside = inside.split("_", 1)[1]
    return f"Доставка ({inside})"


@router.post("/manager/pdf", response_class=HTMLResponse)
async def manager_generate_pdf(request: Request, data_json: str = Form(...)):
    """
    Принимает data_json (строка), валидирует и генерирует PDF,
    сохраняет файл в локальную папку pdf/ и возвращает страницу со ссылкой на скачивание.
    """
    try:
        data = json.loads(data_json)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

    # Если передана структура items в формате, который ждёт generate_pdf — можно сразу передавать.
    # Формируем CalcRequest для валидации и повторного расчёта (контроль корректности итогов).
    # Здесь ожидаем, что data содержит ключ "items" в том же формате, как в CalcRequest для API.
    # Для простоты — попытаемся сформировать CalcRequest, если это не сработает — проигнорируем и используем переданные total.
    calc_request = None
    try:
        # Ожидаем, что data["items"] — список объектов с полями product_key, width_mm, height_mm, quantity, options
        calc_request = CalcRequest(items=data.get("items_payload", data.get("items_api_format", data.get("items", []))))
        # Если CalcRequest валиден — вызываем calc для проверки
        result = calc(calc_request)
        total = result.total
    except Exception:
        # Если валидация не прошла, используем переданный total
        total = data.get("total", 0)

    # Подготовка items для шаблона PDF:
    # ожидаем, что data['items'] содержит список объектов с keys:
    # product_name, thickness, width, height, quantity, services, item_total
    items_for_pdf = data.get("items", [])

    # Обработка доставок — приводим метки к читабельному виду
    deliveries_raw = data.get("deliveries", [])
    deliveries = []
    for d in deliveries_raw:
        label = d.get("label", "")
        price = d.get("price", 0)
        deliveries.append({
            "label": humanize_delivery_label(label),
            "price": price
        })

    # Формируем уникальное имя файла
    proposal_number = datetime.now().strftime("%d%m%Y%H%M%S")
    filename = f"КП_{proposal_number}.pdf"
    save_path = PDF_DIR / filename

    # Генерация PDF: generate_pdf принимает (items, deliveries, total, filename=...)
    generate_pdf(
        items=items_for_pdf,
        deliveries=deliveries,
        total=total,
        filename=filename,
        proposal_number=proposal_number
    )

    # Возвращаем простую страницу с ссылкой на скачивание
    download_url = f"/manager/pdf/download/{filename}"
    html = f"""
    <html><body>
        <h2>PDF сформирован</h2>
        <p>Файл сохранён: <b>{filename}</b></p>
        <p><a href="{download_url}">Скачать PDF</a></p>
        <p><a href="/manager">Вернуться в панель менеджера</a></p>
    </body></html>
    """
    return HTMLResponse(content=html)


@router.get("/manager/pdf/download/{filename}")
async def download_pdf(filename: str):
    """Скачивание PDF по имени файла из папки pdf/"""
    file_path = PDF_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=file_path, media_type="application/pdf", filename=filename)