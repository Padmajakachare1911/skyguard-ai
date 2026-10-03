from pydantic import BaseModel
from datetime import datetime
from typing import Literal


ViolationType = Literal[
    "no-helmet",
    "no-vest",
    "restricted-zone",
    "machinery-proximity",
    "person-down"
]


class Violation(BaseModel):
    id: int
    type: ViolationType
    confidence: float
    latitude: float
    longitude: float
    timestamp: datetime
    image_url: str


class ViolationCreate(BaseModel):
    type: ViolationType
    confidence: float
    latitude: float
    longitude: float
    timestamp: datetime
    image_url: str

class Telemetry(BaseModel):
    latitude: float
    longitude: float
    altitude: float
    flight_mode: str
    timestamp: datetime