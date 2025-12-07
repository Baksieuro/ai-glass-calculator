"""
SQLAlchemy-модели.
Здесь определены простые модели для хранения истории коммерческих предложений (КП).
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Text
from datetime import datetime
from app.db import Base

class Proposal(Base):
    __tablename__ = "proposals"

    id = Column(Integer, primary_key=True, index=True)
    proposal_number = Column(String(64), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    total = Column(Float, default=0.0, nullable=False)
    pdf_path = Column(String(512), nullable=True)         # относительный/абсолютный путь к файлу
    items_json = Column(Text, nullable=True)              # JSON строки: items
    deliveries_json = Column(Text, nullable=True)         # JSON строки: deliveries
    manager = Column(String(128), nullable=True)          # имя менеджера (опционально)
    status = Column(String(32), default="draft")          # draft/confirmed/cancelled