# файл: app/models/user_photos.py

from sqlalchemy import Column, Integer, ForeignKey, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class UserPhoto(Base):
    __tablename__ = "user_photos"
    __table_args__ = {'schema': 'dating_bot'}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("dating_bot.users.id"))
    file_id = Column(String, nullable=False)
    file_url = Column(String)
    is_main = Column(Boolean, default=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
