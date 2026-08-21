from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas import Violation, ViolationCreate
from app.database import get_db
from app import models

router = APIRouter()

@router.get("/violations", response_model=list[Violation])
def get_violations(db: Session = Depends(get_db)):
    return db.query(models.Violation).all()

@router.post("/violations", response_model=Violation)
def create_violation(
    violation: ViolationCreate,
    db: Session = Depends(get_db)
):
    db_violation = models.Violation(
        type=violation.type,
        confidence=violation.confidence,
        latitude=violation.latitude,
        longitude=violation.longitude,
        timestamp=violation.timestamp,
        image_url=violation.image_url
    )

    db.add(db_violation)
    db.commit()
    db.refresh(db_violation)

    return db_violation