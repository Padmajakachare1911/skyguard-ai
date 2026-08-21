from pydantic import BaseModel
from datetime import datetime


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
    latitude: float
    longitude: float
    timestamp: datetime
    image_url: str