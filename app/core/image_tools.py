import random
from pathlib import Path
from PIL import Image
import io
from app.config import settings


def load_logo() -> str | None:
    """Возвращает путь к логотипу или None"""
    logo_dir = settings.LOGO_DIR
    if not logo_dir.exists():
        return None

    for file in logo_dir.iterdir():
        if file.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
            return file.as_uri()  # file:///...

    return None


def load_work_images(limit: int = 3) -> list[str]:
    """Берёт несколько изображений работ и подготавливает их для PDF"""
    works_dir = settings.WORKS_DIR
    if not works_dir.exists():
        return []

    files = [
        f for f in works_dir.iterdir()
        if f.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")
    ]

    if not files:
        return []

    selected = random.sample(files, min(limit, len(files)))

    processed_paths = []
    for img_path in selected:
        processed_paths.append(img_path.as_uri())

    return processed_paths