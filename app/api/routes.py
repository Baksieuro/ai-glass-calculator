"""
Эндпоинты API: /calculate и /pdf
- /calculate возвращает детализированный CalcResponse (positions + total)
- /pdf формирует коммерческое предложение в фирменном стиле
Ошибки и успешные расчёты логируются.
"""
from fastapi import APIRouter, HTTPException

from app.core.schemas import CalcRequest
from app.core.calculator import calc, response_to_pdf_data
from app.core.pdf_generator import generate_pdf
from app.logging_config import get_logger

router = APIRouter(tags=["Calculator"])
logger = get_logger(__name__)


@router.post("/calculate")
async def api_calculate(request: CalcRequest):
    """Возвращает JSON расчёта без PDF"""
    try:
        result = calc(request)
        logger.info("api_calculate | success | total=%.2f | items_count=%s", result.total, len(request.items))
        return result
    except Exception as e:
        logger.error("api_calculate | error | %s", str(e), exc_info=True)
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
        logger.info("api_pdf | success | total=%.2f | file=%s", result.total, str(pdf_path))
        return {"status": "ok", "file": str(pdf_path)}
    except Exception as e:
        logger.error("api_pdf | error | %s", str(e), exc_info=True)
        raise HTTPException(status_code=400, detail=str(e))