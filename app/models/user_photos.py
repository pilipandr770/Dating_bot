# файл: app/models/user_photos.py

from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.declarative import declared_attr

# Import the shared Base
from app.models.base import Base

class UserPhoto(Base):
    __tablename__ = "user_photos"
    
    @declared_attr
    def __table_args__(cls):
        return {'schema': 'dating_bot'}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("dating_bot.users.id"))
    file_id = Column(String, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
