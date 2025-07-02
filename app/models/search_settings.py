# файл: app/models/search_settings.py

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import Base

class SearchSettings(Base):
    __tablename__ = "search_settings"
    __table_args__ = ({'schema': 'dating_bot'})

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("dating_bot.users.id", ondelete="CASCADE"), unique=True, nullable=False)
    min_age = Column(Integer, default=18)
    max_age = Column(Integer, default=99)
    preferred_gender = Column(String)  # "чоловік", "жінка", "будь-яка"
    max_distance = Column(Integer, default=100)  # в кілометрах
    city_filter = Column(Boolean, default=False)  # чи шукати тільки в своєму місті
    
    # Зв'язок з користувачем
    user = relationship("User", backref="search_settings")
