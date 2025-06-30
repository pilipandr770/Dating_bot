# файл: app/models/places.py

from sqlalchemy import Column, Integer, String, Float, Boolean, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy import DateTime
import enum

Base = declarative_base()

class PlaceType(str, enum.Enum):
    restaurant = "restaurant"
    cinema = "cinema"
    event = "event"

class Place(Base):
    __tablename__ = "places"
    __table_args__ = {'schema': 'dating_bot'}

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    type = Column(Enum(PlaceType))
    address = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    url = Column(String)
    partner_id = Column(Integer, nullable=True)  # майбутня інтеграція
    is_promoted = Column(Boolean, default=False)
    image_url = Column(String)

class Reservation(Base):
    __tablename__ = "reservations"
    __table_args__ = {'schema': 'dating_bot'}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("dating_bot.users.id"))
    place_id = Column(Integer, ForeignKey("dating_bot.places.id"))
    reservation_time = Column(DateTime(timezone=True))
    status = Column(String, default="pending")
    external_reference = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
