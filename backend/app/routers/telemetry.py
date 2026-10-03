from datetime import datetime, timezone

from fastapi import APIRouter

from app.schemas import Telemetry

router = APIRouter()

latest_telemetry = {
    "latitude": 19.033,
    "longitude": 73.0297,
    "altitude": 0.0,
    "flight_mode": "UNKNOWN",
    "timestamp": datetime.now(timezone.utc)
}


@router.get("/telemetry", response_model=Telemetry)
def get_telemetry():
    return latest_telemetry


@router.post("/telemetry", response_model=Telemetry)
def update_telemetry(telemetry: Telemetry):
    global latest_telemetry

    latest_telemetry = telemetry.model_dump()

    return latest_telemetry