# файл: app/models/match.py

from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.declarative import declared_attr

# Import the shared Base
from app.models.base import Base

class Match(Base):
    __tablename__ = "matches"
    
    @declared_attr
    def __table_args__(cls):
        return (
            UniqueConstraint("user_1_id", "user_2_id", name="unique_match"),
            {'schema': 'dating_bot'}
        )

    id = Column(Integer, primary_key=True)
    user_1_id = Column(Integer, ForeignKey("dating_bot.users.id"))
    user_2_id = Column(Integer, ForeignKey("dating_bot.users.id"))
    thread_id = Column(String, unique=True)  # UUID або щось подібне
    created_at = Column(DateTime(timezone=True), server_default=func.now())

