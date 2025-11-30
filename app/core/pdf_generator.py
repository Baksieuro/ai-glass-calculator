"""
Генерация фирменного PDF-коммерческого предложения с поддержкой:
- списка изделий (items),
- отдельного блока доставки (deliveries),
- логотипа и фотографий работ из папки assets,
- передачей дополнительных условий и реквизитов.
"""

from pathlib import Path
from datetime import datetime
import json
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from app.config import settings
from app.core.calculator import calc
from app.core.schemas import CalcResponse, CalcPosition


BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"

# Загружаем реквизиты компании
with open(settings.DATA_DIR / "company_info.json", "r", encoding="utf-8") as f:
    company_info = json.load(f)


def _load_logo():
    """Ищет логотип в app/assets/logo и возвращает file:// путь"""
    logo_dir = ASSETS_DIR / "logo"
    if not logo_dir.exists():
        return None

    for f in logo_dir.iterdir():
        if f.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
            return f"file:///{f.resolve()}"

    return None


def _load_works():
    """
    Возвращает список file:// к изображениям работ (максимум 3 случайных).
    """
    works_dir = ASSETS_DIR / "works"
    if not works_dir.exists():
        return []

    imgs = []
    for f in works_dir.iterdir():
        if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
            imgs.append(f"file:///{f.resolve()}")

    # Берём максимум 3 случайных
    import random
    random.shuffle(imgs)
    return imgs[:3]

def clean_number(s: str) -> float:
    return float(''.join(ch for ch in s if (ch.isdigit() or ch == '.')))

def humanize_delivery_label(raw: str) -> str:
    """
    Приводит доставку к формату (центр), (пригород), (край), без английских префиксов.
    Пример: "Доставка (center_центр)" → "Доставка (центр)"
    """
    import re
    m = re.search(r"\((.*?)\)", raw)
    if not m:
        return raw
    inside = m.group(1)  # center_центр
    if "_" in inside:
        inside = inside.split("_", 1)[1]  # берём русскую часть
    return f"Доставка ({inside})"


# -------------------------------------------------------------------------
#                          ГЕНЕРАЦИЯ PDF
# -------------------------------------------------------------------------
def generate_pdf(result: CalcResponse):
    """
    Генерация PDF коммерческого предложения.
    Формирование структуры:
        items[]      — товары
        deliveries[] — доставка
    """
    # Готовим структуру для шаблона
    items_map = {}
    deliveries = []

    for pos in result.positions:

        # --- Доставка ---
        if pos.item_index is None:
            deliveries.append({
                "label": humanize_delivery_label(pos.name),
                "price": pos.total
            })
            continue

        # --- Товары и услуги ---
        if pos.item_index not in items_map:
            items_map[pos.item_index] = {
                "product_name": "",
                "thickness": "",
                "width": 0,
                "height": 0,
                "quantity": 1,
                "services": [],
                "item_total": 0
            }

        # --- Материал ---
        if "мм)" in pos.name and "[" in pos.name:
            main_part = pos.name.split("[")[0].strip()
            dims = pos.name.split("[")[1].split("]")[0]
            width_str, height_str = dims.split("×")

            items_map[pos.item_index]["product_name"] = main_part.split("(")[0].strip()
            items_map[pos.item_index]["thickness"] = main_part.split("(")[1].replace("мм)", "").strip()
            items_map[pos.item_index]["width"] = clean_number(width_str)
            items_map[pos.item_index]["height"] = clean_number(height_str)
            items_map[pos.item_index]["quantity"] = int(pos.quantity)

        # --- Услуги ---
        else:
            if "Итого" not in pos.name:
                items_map[pos.item_index]["services"].append(pos.name)

        # --- Итог по изделию ---
        if pos.name.startswith("Итого"):
            items_map[pos.item_index]["item_total"] = pos.total

    # Переводим карту в список по порядку
    items = [items_map[k] for k in sorted(items_map.keys())]

    # Подключение шаблона
    env = Environment(loader=FileSystemLoader(BASE_DIR / "templates"))
    template = env.get_template("commercial_blue.html")

    html_out = template.render(
        items=items,
        deliveries=deliveries,
        total=result.total,
        proposal_number=datetime.now().strftime("%H%M%S"),
        date=datetime.now().strftime("%d.%m.%Y"),
        company_info=company_info,
        logo=_load_logo(),
        works=_load_works(),
        delivery_terms="до 14 рабочих дней",
        payment_terms="Предоплата 100% на р/с Поставщика",
        additional_terms=(
            "Стоимость является ориентировочной. "
            "Окончательная цена рассчитывается после профессионального замера."
        ),
        final_terms=[
            "Настоящее предложение действует 14 дней.",
            "Предложение является безотзывной офертой."
        ]
    )

    # Генерация файла
    filename = f"Коммерческое предложение {datetime.now().strftime('%d-%m-%Y %H-%M-%S')}.pdf"
    pdf_path = settings.BASE_DIR / filename
    HTML(string=html_out).write_pdf(str(pdf_path))

    return pdf_path