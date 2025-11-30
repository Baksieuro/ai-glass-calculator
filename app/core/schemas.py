from pydantic import BaseModel, Field
from typing import Optional, List


class CalcOptions(BaseModel):
    """Опции расчёта для одного изделия"""
    edge: bool = False                         # Обработка кромки
    film: bool = False                         # Плёнка
    drill: bool = False                        # Сверление отверстий
    drill_qty: Optional[int] = 0               # Кол-во отверстий
    pack: bool = False                         # Упаковка в картон
    delivery_city: Optional[str] = None        # Доставка (только один раз)
    mount: bool = False                        # Монтаж


class CalcItemFull(BaseModel):
    """Описание одного изделия"""
    product_key: str = Field(..., description="Ключ товара из products.txt")
    width_mm: float
    height_mm: float
    quantity: int = 1
    options: CalcOptions = CalcOptions()


class CalcRequest(BaseModel):
    """Основной вход API — список изделий"""
    items: List[CalcItemFull]


class CalcPosition(BaseModel):
    """Позиция результата (может быть материал или услуга)"""
    name: str
    quantity: float
    unit: str
    unit_price: float
    total: float
    item_index: Optional[int] = None  # Привязка к изделию


class CalcResponse(BaseModel):
    """Ответ калькулятора — список позиций и итог"""
    positions: List[CalcPosition]
    total: float