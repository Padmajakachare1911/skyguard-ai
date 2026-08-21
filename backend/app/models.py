from sqlalchemy import Column, Integer, String, Float, DateTime

from app.database import Base


class Violation(Base):
    __tablename__ = "violations"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    image_url = Column(String, nullable=False)