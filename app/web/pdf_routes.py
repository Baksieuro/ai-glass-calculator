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
from html import unescape
from typing import Any

from app.core.calculator import calc
from app.core.schemas import CalcRequest
from app.core.pdf_generator import generate_pdf
from app.config import settings

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
PDF_DIR = BASE_DIR / ".." / "pdf"
PDF_DIR.mkdir(parents=True, exist_ok=True)


def _safe_load_json(s: str) -> Any:
    """
    Попытки безопасно превратить входную строку в Python-объект.
    Возможные входы:
      - корректный JSON (строка) -> dict/list
      - JSON с HTML-экранированием (&quot;) -> надо unescape
      - строка, обрамлённая кавычками: "\"{...}\"" -> нужно удалить внешние кавычки и распарсить
    Возвращает Python-объект (dict/list) или поднимает ValueError.
    """
    if not isinstance(s, str):
        raise ValueError("Ожидалась строка JSON")

    # 1) прямая попытка
    try:
        obj = json.loads(s)
        # Если json.loads вернул строку (случай двойной сериализации) — пробуем далее
        if not isinstance(obj, (dict, list)):
            # obj может быть строкой, тогда продолжим обработку ниже
            pass
        else:
            return obj
    except Exception:
        obj = None

    # 2) убираем html-энкодинг (&quot; и т.п.)
    try:
        s2 = unescape(s)
    except Exception:
        s2 = s

    # 3) если строка обрамлена кавычками, убираем их
    if (s2.startswith('"') and s2.endswith('"')) or (s2.startswith("'") and s2.endswith("'")):
        s2 = s2[1:-1]

    # 4) ещё одна попытка загрузки
    try:
        obj2 = json.loads(s2)
        if isinstance(obj2, (dict, list)):
            return obj2
        # если получили строку — попробуем ещё раз (вдруг была двойная сериализация)
        if isinstance(obj2, str):
            s3 = obj2
            try:
                obj3 = json.loads(s3)
                if isinstance(obj3, (dict, list)):
                    return obj3
            except Exception:
                pass
    except Exception:
        pass

    # 5) последний шанс: попробовать удалить escaped quotes и повторить
    s3 = s2.replace('\\"', '"').replace('&quot;', '"')
    try:
        obj4 = json.loads(s3)
        if isinstance(obj4, (dict, list)):
            return obj4
    except Exception:
        pass

    raise ValueError("Не удалось распарсить data_json — некорректный формат JSON")


@router.post("/manager/pdf", response_class=HTMLResponse)
async def manager_generate_pdf(request: Request, data_json: str = Form(...)):
    """
    Принимает data_json (строка), безопасно парсит и генерирует PDF,
    сохраняет в папку pdf/ и возвращает страницу со ссылкой на скачивание.
    """
    try:
        data = _safe_load_json(data_json)
    except ValueError as e:
        # Возвращаем понятную ошибку (400) вместо 500
        raise HTTPException(status_code=400, detail=f"Invalid data_json: {e}")

    # Ожидаем, что data — dict и содержит items, total
    if not isinstance(data, dict):
        raise HTTPException(status_code=400, detail="data_json должен быть JSON-объектом (словарём)")

    items = data.get("items")
    if items is None:
        raise HTTPException(status_code=400, detail="data_json не содержит ключ 'items'")

    deliveries = data.get("deliveries", [])
    total = data.get("total", 0)

    # Номер КП
    proposal_number = datetime.now().strftime("%d%m%Y%H%M%S")
    filename = f"КП_{proposal_number}.pdf"
    save_path = PDF_DIR / filename

    # Генерация PDF
    generate_pdf(
        items=items,
        deliveries=deliveries,
        total=total,
        proposal_number=proposal_number,
        filename=save_path.name
    )

    html = f"""
    <html><body>
        <h2>PDF сформирован</h2>
        <p>Файл сохранён: <b>{filename}</b></p>
        <p><a href="/manager/pdf/download/{filename}">Скачать PDF</a></p>
        <p><a href="/manager">◀ Вернуться в панель менеджера</a></p>
    </body></html>
    """
    return HTMLResponse(content=html)


@router.get("/manager/pdf/download/{filename}")
async def download_pdf(filename: str):
    file_path = PDF_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path=file_path, media_type="application/pdf", filename=filename)