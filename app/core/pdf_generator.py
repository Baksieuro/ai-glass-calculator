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
TEMPLATES_DIR = BASE_DIR / "templates"
ASSETS_DIR = BASE_DIR / "assets"
DATA_DIR = BASE_DIR / "data"

env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))

# Загружаем реквизиты компании (если файл есть)
company_info = {}
company_info_path = DATA_DIR / "company_info.json"
if company_info_path.exists():
    with open(company_info_path, "r", encoding="utf-8") as f:
        try:
            company_info = json.load(f)
        except Exception:
            company_info = {}

def _load_logo():
    """Возвращает file:/// путь к логотипу или None"""
    logo_dir = ASSETS_DIR / "logo"
    if not logo_dir.exists():
        return None
    for f in logo_dir.iterdir():
        if f.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp", ".svg"]:
            return f"file:///{f.resolve()}"
    return None

def _load_work_photos():
    """Возвращает список file:/// путей к фото работ (максимум 3)"""
    works_dir = ASSETS_DIR / "works"
    if not works_dir.exists():
        return []
    imgs = []
    for f in works_dir.iterdir():
        if f.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
            imgs.append(f"file:///{f.resolve()}")
    # вернём максимум 3
    return imgs[:3]

def generate_pdf(
    items: list,
    deliveries: list,
    total: float,
    filename: str = None,
    proposal_number: str = None,
    delivery_terms: str = "до 14 рабочих дней",
    payment_terms: str = "Предоплата 100% на р/с Поставщика",
    additional_terms: str = "Стоимость, рассчитанная в данном коммерческом предложении, является ориентировочной. Окончательная цена рассчитывается после профессионального замера",
    final_terms: list = None
) -> Path:
    """
    Генерирует PDF из переданных items/deliveries/total.
    Возвращает Path к сгенерированному PDF-файлу (в settings.BASE_DIR).
    """
    if final_terms is None:
        final_terms = [
            "Настоящее предложение действует 14 дней.",
            "Настоящее предложение является безотзывной офертой."
        ]

    # Подготовка данных для шаблона
    logo = _load_logo()
    works = _load_work_photos()

    # Если filename не передан — формируем
    if filename is None:
        now = datetime.now().strftime("%d-%m-%Y %H-%M-%S")
        filename = f"Коммерческое предложение {now}.pdf"

    # Если proposal_number не задан — делаем по времени
    if proposal_number is None:
        proposal_number = datetime.now().strftime("%d%m%Y%H%M%S")

    template = env.get_template("commercial_blue.html")
    html_out = template.render(
        items=items or [],
        deliveries=deliveries or [],
        total=total or 0,
        proposal_number=proposal_number,
        date=datetime.now().strftime("%d.%m.%Y"),
        company_info=company_info,
        delivery_terms=delivery_terms,
        payment_terms=payment_terms,
        additional_terms=additional_terms,
        final_terms=final_terms,
        logo=logo,
        works=works
    )

    # Сохраняем PDF в каталог settings.BASE_DIR (как раньше)
    try:
        from app.config import settings
        out_dir = settings.BASE_DIR
    except Exception:
        out_dir = BASE_DIR

    pdf_path = Path(out_dir) / filename
    HTML(string=html_out, base_url=str(BASE_DIR)).write_pdf(str(pdf_path))
    return pdf_path