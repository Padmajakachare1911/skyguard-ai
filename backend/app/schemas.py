from pydantic import BaseModel
from datetime import datetime
from typing import Literal


ViolationType = Literal[
    "no-helmet",
    "no-vest",
    "restricted-zone",
    "restricted-zone-entry",
    "machinery-proximity",
    "person-down"
]


class Violation(BaseModel):
    id: int
    type: str
    confidence: float
    latitude: float
    longitude: float
    timestamp: datetime
    image_url: str


class ViolationCreate(BaseModel):
    type: str
    confidence: float
    latitude: float = 19.0330
    longitude: float = 73.0297
    timestamp: datetime
    image_url: str = "default_snapshot.jpg"
    person_id: str | None = None

class Telemetry(BaseModel):
    latitude: float
    longitude: float
    altitude: float
    flight_mode: str
    timestamp: datetime