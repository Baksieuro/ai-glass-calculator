from pathlib import Path
from typing import ClassVar, Dict, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Glass Calculator"

    BASE_DIR: Path = Path(__file__).resolve().parent
    DATA_DIR: Path = BASE_DIR / "data"

    # Модель для ИИ
    MODEL: str = "qwen"  # options: qwen, chatgpt, gigachat

    # Директории ассетов
    ASSETS_DIR: Path = BASE_DIR / "assets"
    LOGO_DIR: Path = ASSETS_DIR / "logo"
    WORKS_DIR: Path = ASSETS_DIR / "works"

    # Ограничения размеров стекла
    MAX_HEIGHT_MM: int = 1605
    MAX_WIDTH_MM: int = 2750

    # -----------------------------
    #     НЕПОЛЯ МОДЕЛИ (ClassVar)
    # -----------------------------
    COMPANY_INFO: ClassVar[Dict[str, str]] = {
        "name": "ИП Брюховецкий Аркадий Александрович",
        "address": "614014, Пермский край, г. Пермь, мр-н. Архиерейка, 49",
        "inn": "590618398032",
        "ks": "30101810745374525104",
        "rs": "40802810901500265084",
        "bank": "ООО «Банк Точка»",
        "bik": "044525104"
    }

    DELIVERY_TERMS: ClassVar[List[str]] = [
        "— Доставка по городу Пермь.",
        "— Доставка до подъезда.",
        "— Подъём оплачивается отдельно."
    ]

    PAYMENT_TERMS: ClassVar[List[str]] = [
        "— Предоплата 50%.",
        "— Возможна безналичная оплата с НДС."
    ]

    ADDITIONAL_TERMS: ClassVar[List[str]] = [
        "— Гарантия на монтаж — 12 месяцев.",
        "— Изготовление от 3 до 7 рабочих дней."
    ]

    FINAL_TERMS: ClassVar[List[str]] = [
        "Спасибо за обращение! Мы ценим ваше доверие."
    ]

    class Config:
        env_file = ".env"


settings = Settings()