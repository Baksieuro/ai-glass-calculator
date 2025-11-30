import json
import math
from pathlib import Path
from app.config import settings
from app.core.schemas import (
    CalcRequest, CalcResponse, CalcPosition, CalcItemFull
)


DATA_DIR = settings.DATA_DIR


# --- Вспомогательные функции ---
def mm2m(v): return v / 1000
def calc_area(w, h): return mm2m(w) * mm2m(h)
def calc_perimeter(w, h): return 2 * (mm2m(w) + mm2m(h))


def round_to_100_up(x: float) -> float:
    """Округление вверх до сотни"""
    return math.ceil(x / 100) * 100


def load_products():
    products = {}
    path = DATA_DIR / "products.txt"
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            name, thickness, key = line.split(";")[:3]
            products[key] = {
                "label": name,
                "thickness": float(thickness)
            }
    return products


def load_json(name):
    with open(DATA_DIR / name, encoding="utf-8") as f:
        return json.load(f)


# ================================================================
#                     ОСНОВНАЯ ФУНКЦИЯ РАСЧЁТА
# ================================================================
def calc(request: CalcRequest) -> CalcResponse:
    products = load_products()
    mat_prices = load_json("prices_materials.json")
    srv_prices = load_json("prices_services.json")

    positions: list[CalcPosition] = []
    grand_total = 0

    # ============================================================
    #                 ОБРАБОТКА КАЖДОГО ИЗДЕЛИЯ
    # ============================================================
    for idx, item in enumerate(request.items):

        # Границы
        if item.height_mm > settings.MAX_HEIGHT_MM:
            raise ValueError(f"Ошибка: Высота превышает {settings.MAX_HEIGHT_MM} мм")

        if item.width_mm > settings.MAX_WIDTH_MM:
            raise ValueError(f"Ошибка: Ширина превышает {settings.MAX_WIDTH_MM} мм")

        product = products.get(item.product_key)
        if product is None:
            raise ValueError(f"Ошибка: неизвестный товар {item.product_key}")

        area = calc_area(item.width_mm, item.height_mm)
        perimeter = calc_perimeter(item.width_mm, item.height_mm)

        # ---- Цена материала ----
        mat_price = mat_prices.get(item.product_key)
        if mat_price is None:
            raise ValueError(f"Ошибка: нет цены для {item.product_key}")

        base_price_single = area * mat_price
        base_price_single = round_to_100_up(base_price_single)

        total_item = base_price_single * item.quantity

        positions.append(CalcPosition(
            name=f"{product['label']} ({product['thickness']} мм) "
                 f"[{item.width_mm}×{item.height_mm} мм]",
            quantity=item.quantity,
            unit="шт",
            unit_price=base_price_single,
            total=total_item,
            item_index=idx
        ))

        # --- Опции изделия ---
        opts = item.options

        # Обработка кромки
        if opts.edge:
            edge_price = perimeter * srv_prices["edge"]
            edge_price = max(edge_price, 100)  # минималка
            edge_total = edge_price * item.quantity

            positions.append(CalcPosition(
                name="Обработка кромки",
                quantity=item.quantity,
                unit="шт",
                unit_price=edge_price,
                total=edge_total,
                item_index=idx
            ))
            total_item += edge_total

        # Пленка
        if opts.film and "mirror" in item.product_key:
            film_price = area * srv_prices["film"]
            film_price = max(film_price, 100)
            film_total = film_price * item.quantity

            positions.append(CalcPosition(
                name="Противоосколочная плёнка",
                quantity=item.quantity,
                unit="шт",
                unit_price=film_price,
                total=film_total,
                item_index=idx
            ))
            total_item += film_total

        # Сверление
        if opts.drill:
            t = str(int(product["thickness"]))
            drill_unit = srv_prices["drill"].get(t)
            if drill_unit is None:
                raise ValueError(f"Ошибка: нет цены сверления для толщины {t} мм")

            drill_total = drill_unit * (opts.drill_qty or 0) * item.quantity

            positions.append(CalcPosition(
                name="Сверление отверстий",
                quantity=(opts.drill_qty or 0) * item.quantity,
                unit="шт",
                unit_price=drill_unit,
                total=drill_total,
                item_index=idx
            ))
            total_item += drill_total

        # Упаковка
        if opts.pack:
            pack_price = area * srv_prices["pack"]
            pack_price = max(pack_price, 100)
            pack_total = pack_price * item.quantity

            positions.append(CalcPosition(
                name="Упаковка в гофрокартон",
                quantity=item.quantity,
                unit="шт",
                unit_price=pack_price,
                total=pack_total,
                item_index=idx
            ))
            total_item += pack_total

        # Монтаж
        if opts.mount:
            m_price = srv_prices["mount"] * area
            m_total = m_price * item.quantity

            positions.append(CalcPosition(
                name="Монтаж (ориентировочно)",
                quantity=item.quantity,
                unit="шт",
                unit_price=m_price,
                total=m_total,
                item_index=idx
            ))
            total_item += m_total

        # Добавляем итог по изделию
        total_item = round_to_100_up(total_item)
        grand_total += total_item

        positions.append(CalcPosition(
            name="Итого по изделию",
            quantity=1,
            unit="шт",
            unit_price=total_item,
            total=total_item,
            item_index=idx
        ))

    # ============================================================
    #                    ДОСТАВКА (общая)
    # ============================================================
    delivery_city = request.items[0].options.delivery_city if request.items else None
    if delivery_city:
        delivery_rates = srv_prices["delivery"]
        d_price = delivery_rates.get(delivery_city, 0)
        grand_total += d_price

        positions.append(CalcPosition(
            name=f"Доставка ({delivery_city})",
            quantity=1,
            unit="шт",
            unit_price=d_price,
            total=d_price,
            item_index=None
        ))

    # Округляем общий итог
    grand_total = round_to_100_up(grand_total)

    return CalcResponse(
        positions=positions,
        total=grand_total
)