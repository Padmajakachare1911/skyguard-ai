from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.schemas import Violation, ViolationCreate
from app.database import get_db
from app import models
from app.routers.telemetry import find_closest_telemetry


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


@router.get("/violations", response_model=list[Violation])
def get_violations(db: Session = Depends(get_db)):
    return db.query(models.Violation).all()


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


@router.websocket("/ws/violations")
async def violation_websocket(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)