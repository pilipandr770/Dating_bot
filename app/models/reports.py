# файл: app/models/reports.py

from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.declarative import declared_attr

# Import the shared Base
from app.models.base import Base

class Report(Base):
    __tablename__ = "reports"
    
    @declared_attr
    def __table_args__(cls):
        return {'schema': 'dating_bot'}

    id = Column(Integer, primary_key=True)
    reporter_id = Column(Integer, ForeignKey("dating_bot.users.id"), nullable=True)  # Can be NULL for system-generated reports
    reported_id = Column(Integer, ForeignKey("dating_bot.users.id"))
    reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
