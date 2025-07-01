# файл: app/models/__init__.py

# Import all models so they're registered with SQLAlchemy's metadata
from app.models.base import Base
from app.models.user import User
from app.models.user_photos import UserPhoto
from app.models.swipes import Swipe
from app.models.match import Match
from app.models.reports import Report
from app.models.messages import Message

# Add more model imports as needed

__all__ = [
    'Base', 
    'User', 
    'UserPhoto', 
    'Swipe', 
    'Match', 
    'Report',
    'Message'
]
