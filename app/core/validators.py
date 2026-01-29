"""
Валидация входных данных калькулятора: размеры, товар, цены.
Сообщения об ошибках берутся из config.get_texts().
"""

from app.config import settings, get_texts


def validate_dimensions(height_mm: float, width_mm: float) -> None:
    """Проверяет высоту и ширину против MAX_HEIGHT_MM, MAX_WIDTH_MM. Raises ValueError."""
    texts = get_texts()
    err = texts.get("errors", {})
    if height_mm > settings.MAX_HEIGHT_MM:
        raise ValueError(
            err.get("height_max", "Ошибка: Высота превышает {max_mm} мм").format(
                max_mm=settings.MAX_HEIGHT_MM
            )
        )
    if width_mm > settings.MAX_WIDTH_MM:
        raise ValueError(
            err.get("width_max", "Ошибка: Ширина превышает {max_mm} мм").format(
                max_mm=settings.MAX_WIDTH_MM
            )
        )


def validate_product_key(product_key: str, products: dict) -> None:
    """Проверяет, что product_key есть в справочнике products. Raises ValueError."""
    if product_key not in products:
        texts = get_texts()
        msg = texts.get("errors", {}).get(
            "unknown_product", "Ошибка: неизвестный товар {product_key}"
        )
        raise ValueError(msg.format(product_key=product_key))


def validate_material_price(product_key: str, mat_prices: dict) -> None:
    """Проверяет наличие цены материала для product_key. Raises ValueError."""
    if product_key not in mat_prices:
        texts = get_texts()
        msg = texts.get("errors", {}).get(
            "no_material_price", "Ошибка: нет цены для {product_key}"
        )
        raise ValueError(msg.format(product_key=product_key))


def validate_drill_price(thickness_str: str, drill_prices: dict) -> None:
    """Проверяет наличие цены сверления для толщины. Raises ValueError."""
    if thickness_str not in drill_prices:
        texts = get_texts()
        msg = texts.get("errors", {}).get(
            "no_drill_price",
            "Ошибка: нет цены сверления для толщины {thickness} мм",
        )
        raise ValueError(msg.format(thickness=thickness_str))
