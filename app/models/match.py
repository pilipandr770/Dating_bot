# файл: app/models/matches.py

from sqlalchemy import Column, Integer, ForeignKey, DateTime, String, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (
        UniqueConstraint("user_1_id", "user_2_id", name="unique_match"),
        {'schema': 'dating_bot'}
    )

    id = Column(Integer, primary_key=True)
    user_1_id = Column(Integer, ForeignKey("dating_bot.users.id"))
    user_2_id = Column(Integer, ForeignKey("dating_bot.users.id"))
    thread_id = Column(String, unique=True)  # UUID або щось подібне
    match_time = Column(DateTime(timezone=True), server_default=func.now())

