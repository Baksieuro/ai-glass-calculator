"""
Расчёт стоимости изделий из стекла/зеркал: загрузка данных, calc(), response_to_pdf_data().
Валидация — core.validators, тексты — config.get_texts(). Расчёты логируются.
"""

import json
import math

from app.config import settings, get_texts
from app.core.schemas import CalcRequest, CalcResponse, CalcPosition
from app.core.validators import (
    validate_dimensions,
    validate_product_key,
    validate_material_price,
    validate_drill_price,
)
from app.logging_config import get_logger

logger = get_logger(__name__)


def _unit() -> str:
    return get_texts().get("units", {}).get("piece", "шт")


def _pos(key: str) -> str:
    return get_texts().get("positions", {}).get(key, key)


def mm2m(v: float) -> float:
    return v / 1000


def calc_area(w: float, h: float) -> float:
    return mm2m(w) * mm2m(h)


def calc_perimeter(w: float, h: float) -> float:
    return 2 * (mm2m(w) + mm2m(h))


def round_to_100_up(x: float) -> float:
    return math.ceil(x / 100) * 100


def load_products() -> dict:
    path = settings.DATA_DIR / "products.txt"
    products = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(";")[:3]
            name, thickness, key = parts[0], float(parts[1]), parts[2]
            products[key] = {"label": name, "thickness": thickness}
    return products


def load_json(name: str) -> dict:
    with open(settings.DATA_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def calc(request: CalcRequest) -> CalcResponse:
    products = load_products()
    mat_prices = load_json("prices_materials.json")
    srv_prices = load_json("prices_services.json")
    unit = _unit()
    min_price = settings.MIN_OPTION_PRICE

    # Лог входных данных расчёта
    items_summary = [
        {"product_key": i.product_key, "width_mm": i.width_mm, "height_mm": i.height_mm, "quantity": i.quantity}
        for i in request.items
    ]
    logger.info("calculation_start | items_count=%s | items=%s", len(request.items), items_summary)

    positions: list[CalcPosition] = []
    grand_total = 0.0

    for idx, item in enumerate(request.items):
        validate_dimensions(item.height_mm, item.width_mm)
        validate_product_key(item.product_key, products)
        product = products[item.product_key]
        validate_material_price(item.product_key, mat_prices)

        area = calc_area(item.width_mm, item.height_mm)
        perimeter = calc_perimeter(item.width_mm, item.height_mm)
        mat_price = mat_prices[item.product_key]
        base_price_single = round_to_100_up(area * mat_price)
        total_item = base_price_single * item.quantity

        positions.append(
            CalcPosition(
                name=f"{product['label']} ({product['thickness']} мм) [{item.width_mm}×{item.height_mm} мм]",
                quantity=item.quantity,
                unit=unit,
                unit_price=base_price_single,
                total=total_item,
                item_index=idx,
            )
        )

        opts = item.options

        if opts.edge:
            edge_price = max(perimeter * srv_prices["edge"], min_price)
            total_item += edge_price * item.quantity
            positions.append(
                CalcPosition(
                    name=_pos("edge"),
                    quantity=item.quantity,
                    unit=unit,
                    unit_price=edge_price,
                    total=edge_price * item.quantity,
                    item_index=idx,
                )
            )

        if opts.film and "mirror" in item.product_key:
            film_price = max(area * srv_prices["film"], min_price)
            total_item += film_price * item.quantity
            positions.append(
                CalcPosition(
                    name=_pos("film"),
                    quantity=item.quantity,
                    unit=unit,
                    unit_price=film_price,
                    total=film_price * item.quantity,
                    item_index=idx,
                )
            )

        if opts.drill:
            t = str(int(product["thickness"]))
            validate_drill_price(t, srv_prices["drill"])
            drill_unit = srv_prices["drill"][t]
            qty = (opts.drill_qty or 0) * item.quantity
            drill_total = drill_unit * qty
            total_item += drill_total
            positions.append(
                CalcPosition(
                    name=_pos("drill"),
                    quantity=qty,
                    unit=unit,
                    unit_price=drill_unit,
                    total=drill_total,
                    item_index=idx,
                )
            )

        if opts.pack:
            pack_price = max(area * srv_prices["pack"], min_price)
            total_item += pack_price * item.quantity
            positions.append(
                CalcPosition(
                    name=_pos("pack"),
                    quantity=item.quantity,
                    unit=unit,
                    unit_price=pack_price,
                    total=pack_price * item.quantity,
                    item_index=idx,
                )
            )

        if opts.mount:
            m_price = srv_prices["mount"] * area
            m_total = m_price * item.quantity
            total_item += m_total
            positions.append(
                CalcPosition(
                    name=_pos("mount"),
                    quantity=item.quantity,
                    unit=unit,
                    unit_price=m_price,
                    total=m_total,
                    item_index=idx,
                )
            )

        total_item = round_to_100_up(total_item)
        grand_total += total_item
        positions.append(
            CalcPosition(
                name=_pos("total_per_item"),
                quantity=1,
                unit=unit,
                unit_price=total_item,
                total=total_item,
                item_index=idx,
            )
        )

    delivery_city = request.items[0].options.delivery_city if request.items else None
    if delivery_city:
        d_price = srv_prices["delivery"].get(delivery_city, 0)
        grand_total += d_price
        positions.append(
            CalcPosition(
                name=_pos("delivery").format(city=delivery_city),
                quantity=1,
                unit=unit,
                unit_price=d_price,
                total=d_price,
                item_index=None,
            )
        )

    grand_total = round_to_100_up(grand_total)
    logger.info("calculation_done | total=%.2f | positions_count=%s", grand_total, len(positions))
    return CalcResponse(positions=positions, total=grand_total)


def response_to_pdf_data(response: CalcResponse) -> dict:
    """
    Преобразует CalcResponse в структуру для PDF/превью: items, deliveries, total.
    """
    texts = get_texts()
    total_label = texts.get("positions", {}).get("total_per_item", "Итого по изделию")

    items_map = {}
    for pos in response.positions:
        idx = getattr(pos, "item_index", None)
        if idx is None:
            continue
        if idx not in items_map:
            items_map[idx] = {
                "product_name": "",
                "thickness": "",
                "width": None,
                "height": None,
                "quantity": 1,
                "services": [],
                "item_total": 0.0,
            }
        if "мм" in str(pos.name) and "[" in pos.name:
            main_part = str(pos.name).split("[")[0].strip()
            dims = str(pos.name).split("[")[1].split("]")[0]
            w_s, h_s = dims.split("×")

            def clean_num(s):
                return float("".join(c for c in str(s) if (c.isdigit() or c == ".")))

            items_map[idx]["product_name"] = main_part.split("(")[0].strip()
            items_map[idx]["thickness"] = main_part.split("(")[1].replace("мм)", "").strip()
            items_map[idx]["width"] = clean_num(w_s)
            items_map[idx]["height"] = clean_num(h_s)
            items_map[idx]["quantity"] = int(pos.quantity)
        elif str(pos.name) == total_label:
            items_map[idx]["item_total"] = pos.total
        else:
            items_map[idx]["services"].append(pos.name)

    items_list = [items_map[k] for k in sorted(items_map.keys())]
    deliveries = [
        {"label": pos.name, "price": pos.total}
        for pos in response.positions
        if getattr(pos, "item_index", None) is None
    ]

    return {"items": items_list, "deliveries": deliveries, "total": response.total}
