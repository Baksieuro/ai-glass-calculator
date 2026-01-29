"""
Загрузка ассетов для PDF: логотип и фото работ.
Единый модуль для pdf_routes и pdf_generator.
"""

from pathlib import Path

from app.config import settings


def get_logo_file_uri() -> str | None:
    """Возвращает file:/// URI первого изображения в LOGO_DIR или None."""
    if not settings.LOGO_DIR.exists():
        return None
    for f in settings.LOGO_DIR.iterdir():
        if f.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp", ".svg"}:
            return f"file:///{f.resolve()}"
    return None


def get_works_file_uris(limit: int = 8) -> list[str]:
    """Возвращает список file:/// URI изображений из WORKS_DIR (до limit штук)."""
    if not settings.WORKS_DIR.exists():
        return []
    uris = []
    for f in settings.WORKS_DIR.iterdir():
        if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
            uris.append(f"file:///{f.resolve()}")
            if len(uris) >= limit:
                break
    return uris
