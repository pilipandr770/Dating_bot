# app/booking/models.py

import enum
from sqlalchemy import Column, Integer, String, Enum, JSON, Boolean, ForeignKey, DateTime, Float
from sqlalchemy.sql import func
from app.models.base import Base

class PlaceType(enum.Enum):
    restaurant = "restaurant"
    cafe = "cafe"
    bar = "bar"
    park = "park"
    cinema = "cinema"
    event = "event"
    other = "other"

class Place(Base):
    __tablename__ = "places"
    __table_args__ = {"schema": "dating_bot"}

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    city = Column(String)
    type = Column(String)  # Используем String вместо Enum для совместимости с существующей схемой
    link = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    is_partner = Column(Boolean, default=False)
    
    # Новые поля для интеграции с внешними API
    partner_name = Column(String)
    external_id = Column(String, unique=True)
    place_metadata = Column(JSON)  # Переименовано из metadata, т.к. это зарезервированное слово в SQLAlchemy
    is_promoted = Column(Boolean, default=False)
    image_url = Column(String)

class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = {"schema": "dating_bot"}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("dating_bot.users.id"), nullable=False)
    place_id = Column(Integer, ForeignKey("dating_bot.places.id"), nullable=False)
    reservation_time = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Новые поля для интеграции с внешними API
    match_id = Column(Integer, ForeignKey("dating_bot.matches.id"), nullable=True)
    status = Column(String, default="pending")
    details = Column(JSON)
    external_reference = Column(String)
