# файл: app/models/messages.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Message(Base):
    __tablename__ = "messages"
    __table_args__ = {'schema': 'dating_bot'}

    id = Column(Integer, primary_key=True)
    thread_id = Column(String, ForeignKey("dating_bot.matches.thread_id"))
    sender_id = Column(Integer, ForeignKey("dating_bot.users.id"))
    message_text = Column(String)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
