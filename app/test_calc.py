from app.core.calculator import calc
from app.core.schemas import CalcRequest, CalcItem, CalcOptions


def main():
    # --- Пример данных для теста ---
    item = CalcItem(
        width_mm=1000, 
        height_mm=1200, 
        product_key="mirror_standart_4mm"
    )
    
    options = CalcOptions(
        edge=True,
        film=True,
        drill=True,
        drill_qty=2,
        pack=True,
        delivery_city="center",
        mount=True
    )
    
    request = CalcRequest(item=item, options=options)
    
    # --- Выполнение расчета ---
    try:
        response = calc(request)
        print("Расчёт успешно выполнен!\n")
        for pos in response.positions:
            print(f"{pos.name}: {pos.total} руб.")
        print(f"\nИтого: {response.total} руб.")
    except ValueError as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()