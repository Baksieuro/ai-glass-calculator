"""
Генерация PDF для API (POST /api/pdf): items/deliveries/total → HTML → PDF.
Пути и ассеты — из config и core.assets. Генерация логируется.
"""

from datetime import datetime
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from app.config import settings, get_company_info, DELIVERY_TERMS, PAYMENT_TERMS, ADDITIONAL_TERMS, FINAL_TERMS
from app.core.assets import get_logo_file_uri, get_works_file_uris
from app.logging_config import get_logger

logger = get_logger(__name__)
env = Environment(loader=FileSystemLoader(str(settings.TEMPLATES_DIR)))


def generate_pdf(
    items: list,
    deliveries: list,
    total: float,
    filename: str | None = None,
    proposal_number: str | None = None,
    delivery_terms: list | None = None,
    payment_terms: list | None = None,
    additional_terms: list | None = None,
    final_terms: list | None = None,
) -> Path:
    """
    Генерирует PDF из items/deliveries/total.
    Сохраняет в settings.PDF_DIR (или settings.APP_DIR для обратной совместимости).
    Возвращает Path к файлу.
    """
    delivery_terms = delivery_terms or DELIVERY_TERMS
    payment_terms = payment_terms or PAYMENT_TERMS
    additional_terms = additional_terms or ADDITIONAL_TERMS
    final_terms = final_terms or FINAL_TERMS

    if filename is None:
        filename = f"Коммерческое предложение {datetime.now().strftime('%d-%m-%Y %H-%M-%S')}.pdf"
    if proposal_number is None:
        proposal_number = datetime.now().strftime("%d%m%Y%H%M%S")

    html_out = env.get_template("commercial_blue.html").render(
        items=items or [],
        deliveries=deliveries or [],
        total=total or 0,
        proposal_number=proposal_number,
        date=datetime.now().strftime("%d.%m.%Y"),
        company_info=get_company_info(),
        delivery_terms=delivery_terms,
        payment_terms=payment_terms,
        additional_terms=additional_terms,
        final_terms=final_terms,
        logo=get_logo_file_uri(),
        works=get_works_file_uris(limit=8),
    )

    out_dir = settings.PDF_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / filename
    HTML(string=html_out, base_url=str(settings.APP_DIR)).write_pdf(str(pdf_path))
    logger.info("pdf_generated | proposal_number=%s | total=%.2f | file=%s", proposal_number, total, str(pdf_path))
    return pdf_path
