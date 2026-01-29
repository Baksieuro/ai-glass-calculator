"""
Эндпоинты API: /calculate и /pdf
- /calculate возвращает детализированный CalcResponse (positions + total)
- /pdf формирует коммерческое предложение в фирменном стиле
"""
from fastapi import APIRouter, HTTPException

from app.core.schemas import CalcRequest
from app.core.calculator import calc, response_to_pdf_data
from app.core.pdf_generator import generate_pdf

router = APIRouter(tags=["Calculator"])


@router.post("/calculate")
async def api_calculate(request: CalcRequest):
    """Возвращает JSON расчёта без PDF"""
    try:
        result = calc(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/pdf")
async def api_pdf(request: CalcRequest):
    """Генерация PDF: расчёт + преобразование в items/deliveries и вызов generate_pdf."""
    try:
        result = calc(request)
        data = response_to_pdf_data(result)
        pdf_path = generate_pdf(
            items=data["items"],
            deliveries=data["deliveries"],
            total=data["total"],
        )
        return {"status": "ok", "file": str(pdf_path)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))