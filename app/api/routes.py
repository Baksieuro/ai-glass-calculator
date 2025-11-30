"""
Эндпоинты API: /calculate и /pdf
- /calculate возвращает детализированный CalcResponse (positions + total)
- /pdf формирует коммерческое предложение в фирменном стиле
"""
from fastapi import APIRouter, HTTPException
from app.core.schemas import CalcRequest
from app.core.calculator import calc
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
    """Генерация PDF на основе CalcResponse"""
    try:
        result = calc(request)
        pdf_path = generate_pdf(result)
        return {"status": "ok", "file": str(pdf_path)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))