# app/booking/models_simplified.py

import enum
from sqlalchemy import Column, Integer, String, Enum, JSON, Boolean, ForeignKey, DateTime, Float, Text
from sqlalchemy.sql import func
from app.models.base import Base

# Определение типов мест
class PlaceType(str, enum.Enum):
    restaurant = "restaurant"
    cafe = "cafe"
    bar = "bar"
    park = "park"
    cinema = "cinema"
    event = "event"
    other = "other"

# Модель места (точно соответствует схеме БД)
class Place(Base):
    __tablename__ = "places"
    __table_args__ = {"schema": "dating_bot"}
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    city = Column(String, nullable=True)
    type = Column(String, nullable=True)  # Не Enum, а String, т.к. в БД тип TEXT
    link = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_partner = Column(Boolean, default=False)
    
    # Эти поля отсутствуют в БД, но могут понадобиться для логики приложения
    # Не будут использоваться при взаимодействии с БД
    description = Column(String, nullable=True)
    photo_url = Column(String, nullable=True)

# Модель бронирования (упрощенная)
class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = {"schema": "dating_bot"}
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("dating_bot.users.id"))
    place_id = Column(Integer, ForeignKey("dating_bot.places.id"))
    match_id = Column(Integer)
    status = Column(String, default="pending")  # pending, confirmed, cancelled
    external_reference = Column(String)  # Номер бронирования во внешней системе
    reservation_time = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
