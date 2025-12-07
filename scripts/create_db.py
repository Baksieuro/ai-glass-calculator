import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from app.db import engine, Base
from app import models

def create():
    Base.metadata.create_all(bind=engine)
    print("DB created")

if __name__ == "__main__":
    create()