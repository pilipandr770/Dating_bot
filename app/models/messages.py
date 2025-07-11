# файл: app/models/messages.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.declarative import declared_attr

# Import the shared Base
from app.models.base import Base

class Message(Base):
    __tablename__ = "messages"
    
    @declared_attr
    def __table_args__(cls):
        return {'schema': 'dating_bot'}

    id = Column(Integer, primary_key=True)
    thread_id = Column(String, ForeignKey("dating_bot.matches.thread_id"))
    sender_id = Column(Integer, ForeignKey("dating_bot.users.id"))
    message_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
