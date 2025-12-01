from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.config import settings
from pathlib import Path
from app.core.calculator import calc, load_products
from app.core.schemas import CalcRequest, CalcItem, CalcOptions

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@router.get("/manager", response_class=HTMLResponse)
async def manager_form(request: Request):
    """Страница формы расчёта"""
    products = load_products()
    return templates.TemplateResponse(
        "manager_form.html",
        {"request": request, "products": products}
    )


@router.post("/manager/preview", response_class=HTMLResponse)
async def manager_preview(
    request: Request,
    product_key: str = Form(...),
    width_mm: float = Form(...),
    height_mm: float = Form(...),
    quantity: int = Form(...),

    edge: bool = Form(False),
    film: bool = Form(False),
    drill: bool = Form(False),
    drill_qty: int = Form(0),
    pack: bool = Form(False),
    delivery_city: str = Form(""),
    mount: bool = Form(False),
):
    """Просмотр результата перед формированием PDF"""
    
    item = CalcItem(
        width_mm=width_mm,
        height_mm=height_mm,
        product_key=product_key
    )

    options = CalcOptions(
        edge=edge,
        film=film,
        drill=drill,
        drill_qty=drill_qty,
        pack=pack,
        delivery_city=delivery_city,
        mount=mount
    )

    req = CalcRequest(item=item, options=options)
    result = calc(req)

    return templates.TemplateResponse(
        "manager_preview.html",
        {
            "request": request,
            "product_key": product_key,
            "item": item,
            "quantity": quantity,
            "options": options,
            "result": result
        }
    )