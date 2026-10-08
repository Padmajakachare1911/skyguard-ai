from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.schemas import Violation, ViolationCreate
from app.database import get_db
from app import models
from app.routers.telemetry import find_closest_telemetry
from app.services.report_service import (
    generate_person_report,
    generate_overall_report,
)

router = APIRouter()


# Manages all connected WebSocket clients
class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, data):
        for connection in self.active_connections:
            await connection.send_json(data)


manager = ConnectionManager()


# ============================================================
# GET ALL VIOLATIONS
# ============================================================

@router.get("/violations", response_model=list[Violation])
def get_violations(db: Session = Depends(get_db)):
    return db.query(models.Violation).all()


# ============================================================
# GET VIOLATIONS FOR ONE PERSON
# ============================================================

@router.get(
    "/violations/person/{person_id}",
    response_model=list[Violation]
)
def get_person_violations(
    person_id: str,
    db: Session = Depends(get_db)
):
    return (
        db.query(models.Violation)
        .filter(models.Violation.person_id == person_id)
        .order_by(models.Violation.timestamp.desc())
        .all()
    )


# ============================================================
# GENERATE INDIVIDUAL WORKER REPORT
# ============================================================

@router.get("/persons/{person_id}/report")
def generate_person_safety_report(
    person_id: str,
    db: Session = Depends(get_db)
):
    violations = (
        db.query(models.Violation)
        .filter(models.Violation.person_id == person_id)
        .order_by(models.Violation.timestamp.desc())
        .all()
    )

    if not violations:
        return {
            "message": f"No violations found for {person_id}"
        }

    report_filename = f"{person_id}_Safety_Report.pdf"
    report_path = f"reports/{report_filename}"

    generate_person_report(
        person_id,
        violations,
        report_path
    )

    return FileResponse(
        path=report_path,
        media_type="application/pdf",
        filename=report_filename
    )


# ============================================================
# GENERATE OVERALL SITE SAFETY REPORT
# ============================================================

@router.get("/reports/overall")
def generate_overall_safety_report(
    db: Session = Depends(get_db)
):
    violations = (
        db.query(models.Violation)
        .order_by(models.Violation.timestamp.desc())
        .all()
    )

    report_filename = "SkyGuard_Overall_Safety_Report.pdf"
    report_path = f"reports/{report_filename}"

    generate_overall_report(
        violations,
        report_path
    )

    return FileResponse(
        path=report_path,
        media_type="application/pdf",
        filename=report_filename
    )


# ============================================================
# CREATE VIOLATION
# ============================================================

@router.post("/violations", response_model=Violation)
async def create_violation(
    violation: ViolationCreate,
    db: Session = Depends(get_db)
):

    # Find the telemetry point closest to the violation timestamp
    matched_telemetry = find_closest_telemetry(
        violation.timestamp
    )

    # Use synchronized telemetry coordinates if available
    if matched_telemetry:
        latitude = matched_telemetry["latitude"]
        longitude = matched_telemetry["longitude"]
    else:
        # Fall back to coordinates sent with the violation
        latitude = violation.latitude
        longitude = violation.longitude

    db_violation = models.Violation(
        person_id=violation.person_id,
        type=violation.type,
        confidence=violation.confidence,
        latitude=latitude,
        longitude=longitude,
        timestamp=violation.timestamp,
        image_url=violation.image_url
    )

    # Save violation to database
    db.add(db_violation)
    db.commit()
    db.refresh(db_violation)

    # Send the new violation to connected WebSocket clients
    violation_data = jsonable_encoder(db_violation)
    await manager.broadcast(violation_data)

    return db_violation


# ============================================================
# LIVE VIOLATION WEBSOCKET
# ============================================================

@router.websocket("/ws/violations")
async def violation_websocket(websocket: WebSocket):

    await manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)