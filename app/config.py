"""
Единая конфигурация: пути, лимиты, тексты и реквизиты.
Все пути относительно корня проекта (ai_glass_calculator/).
"""

import json
from pathlib import Path
from typing import ClassVar, Dict, List
from pydantic_settings import BaseSettings


# Корень проекта (родитель папки app/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_APP_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Glass Calculator"

    # Пути (все от корня проекта)
    PROJECT_ROOT: Path = _PROJECT_ROOT
    APP_DIR: Path = _APP_DIR
    DATA_DIR: Path = _PROJECT_ROOT / "data"
    PDF_DIR: Path = _PROJECT_ROOT / "pdf"
    TEMPLATES_DIR: Path = _APP_DIR / "templates"
    STATIC_DIR: Path = _APP_DIR / "static"
    ASSETS_DIR: Path = _APP_DIR / "assets"
    LOGO_DIR: Path = _APP_DIR / "assets" / "logo"
    WORKS_DIR: Path = _APP_DIR / "assets" / "works"

    # Ограничения размеров стекла (мм)
    MAX_HEIGHT_MM: int = 1605
    MAX_WIDTH_MM: int = 2750

    # Минимальная сумма по позиции (руб)
    MIN_OPTION_PRICE: int = 100

    class Config:
        env_file = ".env"


settings = Settings()


def get_texts() -> dict:
    """Загружает тексты из data/texts.json (ошибки, подписи позиций)."""
    path = settings.DATA_DIR / "texts.json"
    if not path.exists():
        return _default_texts()
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return _default_texts()


def _default_texts() -> dict:
    return {
        "errors": {
            "height_max": "Ошибка: Высота превышает {max_mm} мм",
            "width_max": "Ошибка: Ширина превышает {max_mm} мм",
            "unknown_product": "Ошибка: неизвестный товар {product_key}",
            "no_material_price": "Ошибка: нет цены для {product_key}",
            "no_drill_price": "Ошибка: нет цены сверления для толщины {thickness} мм",
        },
        "positions": {
            "edge": "Обработка кромки",
            "film": "Противоосколочная плёнка",
            "drill": "Сверление отверстий",
            "pack": "Упаковка в гофрокартон",
            "mount": "Монтаж (ориентировочно)",
            "total_per_item": "Итого по изделию",
            "delivery": "Доставка ({city})",
        },
        "units": {"piece": "шт"},
    }


def get_company_info() -> Dict[str, str]:
    """Реквизиты компании: из data/company_info.json или дефолт из кода."""
    path = settings.DATA_DIR / "company_info.json"
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "name": "ИП Брюховецкий Аркадий Александрович",
        "address": "614014, Пермский край, г. Пермь, мр-н. Архиерейка, 49",
        "inn": "590618398032",
        "ks": "30101810745374525104",
        "rs": "40802810901500265084",
        "bank": "ООО «Банк Точка»",
        "bik": "044525104",
    }


# Условия для PDF (списки строк)
DELIVERY_TERMS: ClassVar[List[str]] = [
    "— Доставка по городу Пермь.",
    "— Доставка до подъезда.",
    "— Подъём оплачивается отдельно.",
]
PAYMENT_TERMS: ClassVar[List[str]] = [
    "— Предоплата 50%.",
    "— Возможна безналичная оплата с НДС.",
]
ADDITIONAL_TERMS: ClassVar[List[str]] = [
    "— Гарантия на монтаж — 12 месяцев.",
    "— Изготовление от 3 до 7 рабочих дней.",
]
FINAL_TERMS: ClassVar[List[str]] = [
    "Спасибо за обращение! Мы ценим ваше доверие.",
]
