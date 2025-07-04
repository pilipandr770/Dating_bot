# app/booking/models.py
import enum
from sqlalchemy import Column, Integer, String, Enum, Boolean, ForeignKey, DateTime, Float, JSON
from sqlalchemy.dialects.postgresql import JSONB
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

class AdminMessage(Base):
    __tablename__ = "admin_messages"
    __table_args__ = {"schema": "dating_bot"}
    
    id = Column(Integer, primary_key=True)
    city = Column(String, nullable=False)
    place_type = Column(String, nullable=False)
    message = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<AdminMessage(id={self.id}, city='{self.city}', type='{self.place_type}')>"

class Place(Base):
    __tablename__ = "places"
    __table_args__ = {"schema": "dating_bot"}

    # Точное соответствие реальной структуре БД
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    city = Column(String)
    type = Column(String)  # Используем String вместо Enum для совместимости с существующей схемой
    link = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    is_partner = Column(Boolean, default=False)
    
    # Дополнительные поля, обнаруженные в БД
    partner_name = Column(String)
    external_id = Column(String)
    # 'metadata' is a reserved name in SQLAlchemy, rename to place_metadata
    place_metadata = Column("metadata", JSONB)  # Map to 'metadata' column in DB
    is_promoted = Column(Boolean, default=False)
    image_url = Column(String)

class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = {"schema": "dating_bot"}

    # Точное соответствие схеме БД из schema.sql
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("dating_bot.users.id"), nullable=True)
    place_id = Column(Integer, ForeignKey("dating_bot.places.id"), nullable=True)
    reservation_time = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
