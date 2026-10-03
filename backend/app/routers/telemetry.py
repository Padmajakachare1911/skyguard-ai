from datetime import datetime, timezone

from fastapi import APIRouter

from app.schemas import Telemetry

router = APIRouter()

# Stores the latest telemetry point
latest_telemetry = {
    "latitude": 19.033,
    "longitude": 73.0297,
    "altitude": 0.0,
    "flight_mode": "UNKNOWN",
    "timestamp": datetime.now(timezone.utc)
}

# Stores recent telemetry points for timestamp synchronization
telemetry_history = []

# Maximum number of telemetry points to keep
MAX_TELEMETRY_HISTORY = 100


@router.get("/telemetry", response_model=Telemetry)
def get_telemetry():
    return latest_telemetry


@router.post("/telemetry", response_model=Telemetry)
def update_telemetry(telemetry: Telemetry):
    global latest_telemetry

    telemetry_data = telemetry.model_dump()

    # Update latest telemetry
    latest_telemetry = telemetry_data

    # Add telemetry point to history
    telemetry_history.append(telemetry_data)

    # Keep only the latest 100 points
    if len(telemetry_history) > MAX_TELEMETRY_HISTORY:
        telemetry_history.pop(0)

    return latest_telemetry

def find_closest_telemetry(target_timestamp: datetime):
    if not telemetry_history:
        return None

    closest_point = min(
        telemetry_history,
        key=lambda point: abs(
            point["timestamp"] - target_timestamp
        )
    )

    return closest_point