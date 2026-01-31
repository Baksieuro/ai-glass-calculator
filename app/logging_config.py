"""
Централизованная настройка логирования для продакшена.
- errors.log: ошибки и некорректные данные (ERROR, WARNING)
- app.log: расчёты и действия менеджеров (INFO)
Ротация файлов для ограничения размера.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.config import settings


LOGS_DIR = settings.LOGS_DIR
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Максимальный размер одного лог-файла (5 MB), хранить 5 архивов
MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 5
ENCODING = "utf-8"

_FORMAT_DETAIL = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_FORMAT_SIMPLE = "%(asctime)s | %(levelname)-8s | %(message)s"
_DATE_FMT = "%Y-%m-%d %H:%M:%S"


def _make_handler(
    filename: str,
    level: int = logging.DEBUG,
    fmt: str = _FORMAT_DETAIL,
) -> RotatingFileHandler:
    path = LOGS_DIR / filename
    h = RotatingFileHandler(
        path,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding=ENCODING,
    )
    h.setLevel(level)
    h.setFormatter(logging.Formatter(fmt, datefmt=_DATE_FMT))
    return h


def get_logger(name: str) -> logging.Logger:
    """Возвращает логгер с именем name (например __name__), пишет в app.log и errors.log."""
    root = logging.getLogger("app")
    if not root.handlers:
        root.setLevel(logging.DEBUG)
        root.propagate = False
        root.addHandler(_make_handler("app.log", logging.INFO))
        root.addHandler(_make_handler("errors.log", logging.WARNING))
        if sys.stderr:
            ch = logging.StreamHandler(sys.stderr)
            ch.setLevel(logging.WARNING)
            ch.setFormatter(logging.Formatter(_FORMAT_SIMPLE, datefmt=_DATE_FMT))
            root.addHandler(ch)
    return logging.getLogger(name)
