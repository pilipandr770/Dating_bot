# cinema/models.py

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database import Base

class FilmPurchase(Base):
    __tablename__ = "cinema_purchases"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    film_id = Column(String, nullable=False)
    film_title = Column(String, nullable=False)
    room_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
