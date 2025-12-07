"""
Инициализация SQLite + SQLAlchemy.
База будет лежать в data/app.db (папка data создаётся автоматически).
"""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Корень проекта: ai_glass_calculator/
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# создаём папку data (если нет)
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "app.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()