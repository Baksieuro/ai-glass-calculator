"""
Набор простых функций для работы с таблицами (create/read).
Создание КП логируется.
"""

import json
from datetime import datetime

from sqlalchemy.orm import Session

from app import models
from app.logging_config import get_logger

logger = get_logger(__name__)


def create_proposal(db: Session, proposal_number: str, total: float, pdf_path: str,
                    items: list, deliveries: list = None, manager: str | None = None,
                    status: str = "draft") -> models.Proposal:
    """Создаёт запись о коммерческом предложении."""
    deliveries_json = json.dumps(deliveries, ensure_ascii=False) if deliveries is not None else None
    items_json = json.dumps(items, ensure_ascii=False) if items is not None else None

    obj = models.Proposal(
        proposal_number=proposal_number,
        created_at=datetime.utcnow(),
        total=total,
        pdf_path=str(pdf_path),
        items_json=items_json,
        deliveries_json=deliveries_json,
        manager=manager,
        status=status
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    logger.info(
        "proposal_created | proposal_number=%s | total=%.2f | items_count=%s",
        proposal_number,
        total,
        len(items) if items else 0,
    )
    return obj

def list_proposals(db: Session, limit: int = 50, offset: int = 0):
    """Возвращает список КП, сортированных по дате (новые первыми)."""
    return db.query(models.Proposal).order_by(models.Proposal.created_at.desc()).offset(offset).limit(limit).all()

def get_proposal(db: Session, proposal_id: int):
    """Получить КП по id."""
    return db.query(models.Proposal).filter(models.Proposal.id == proposal_id).first()

def get_proposal_by_number(db: Session, proposal_number: str):
    return db.query(models.Proposal).filter(models.Proposal.proposal_number == proposal_number).first()