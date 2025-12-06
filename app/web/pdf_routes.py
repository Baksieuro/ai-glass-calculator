# app/web/pdf_routes.py
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path
import json
from datetime import datetime
from html import unescape
import shutil

from app.core.pdf_generator import generate_pdf

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
PDF_DIR = BASE_DIR.parent / "pdf"
PDF_DIR.mkdir(parents=True, exist_ok=True)


def humanize_delivery_label(raw: str) -> str:
    """
    Приводит метку доставки к читабельному виду.
    Пример: "Доставка (center_центр)" -> "Доставка (центр)"
    """
    if not raw:
        return raw
    try:
        inside = raw.split("(", 1)[1].split(")", 1)[0]
    except Exception:
        return raw
    if "_" in inside:
        inside = inside.split("_", 1)[1]
    return f"Доставка ({inside})"


def _safe_load_json(s: str):
    """
    Надёжно парсим JSON-параметр, учитывая экранирование HTML.
    """
    try:
        return json.loads(s)
    except Exception:
        try:
            s2 = unescape(s)
            if (s2.startswith('"') and s2.endswith('"')) or (s2.startswith("'") and s2.endswith("'")):
                s2 = s2[1:-1]
            return json.loads(s2)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Невалидный JSON: {e}")


@router.post("/manager/pdf", response_class=HTMLResponse)
async def manager_generate_pdf(request: Request, data_json: str = Form(...)):
    """
    Принимает данные preview (data_json), генерирует PDF, сохраняет в папку pdf/
    и возвращает страницу со ссылкой на скачивание.
    """
    data = _safe_load_json(data_json)

    # Ожидаем структуру
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="data_json должен быть JSON-объектом")

    items = data.get("items", [])
    deliveries_raw = data.get("deliveries", [])
    total = data.get("total", 0)

    # Обработка доставок: humanize label
    deliveries = []
    for d in deliveries_raw:
        lbl = d.get("label", "")
        price = d.get("price", 0)
        deliveries.append({
            "label": humanize_delivery_label(lbl),
            "price": price
        })

    # Уникальное имя файла
    proposal_number = datetime.now().strftime("%d%m%Y%H%M%S")
    filename = f"КП_{proposal_number}.pdf"

    # Генерация PDF — вернёт Path к сгенерированному файлу
    pdf_path = generate_pdf(
        items=items,
        deliveries=deliveries,
        total=total,
        proposal_number=proposal_number,
        filename=filename
    )

    # Если generate_pdf сохранил файл не в папке PDF_DIR — переместим его
    try:
        pdf_path = Path(pdf_path)
    except Exception:
        # Если generate_pdf вернул None или строку, попробуем сформировать путь по filename
        pdf_path = PDF_DIR / filename

    if not pdf_path.exists():
        # Если файл лежит в другом каталоге (например в settings.BASE_DIR), попробуем найти и переместить
        # Попробуем путь относительно проекта root
        potential = Path.cwd() / filename
        if potential.exists():
            shutil.move(str(potential), str(PDF_DIR / filename))
            pdf_path = PDF_DIR / filename
        else:
            # Файл не найден
            raise HTTPException(status_code=500, detail="PDF был сгенерирован, но файл не найден для перемещения")

    # Если файл находится не в PDF_DIR — переместим
    if pdf_path.parent != PDF_DIR:
        target = PDF_DIR / pdf_path.name
        shutil.move(str(pdf_path), str(target))
        pdf_path = target

    download_url = f"/manager/pdf/download/{pdf_path.name}"
    html = f"""
    <html><body>
        <h2>PDF сформирован</h2>
        <p>Файл сохранён: <b>{pdf_path.name}</b></p>
        <p><a href="{download_url}">Скачать PDF</a></p>
        <p><a href="/manager">◀ Вернуться в панель менеджера</a></p>
    </body></html>
    """
    return HTMLResponse(content=html)


@router.get("/manager/pdf/download/{filename}")
async def download_pdf(filename: str):
    """Скачивание PDF"""
    file_path = PDF_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=file_path, media_type="application/pdf", filename=filename)