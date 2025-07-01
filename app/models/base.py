# файл: app/models/base.py

from sqlalchemy.orm import declarative_base

# Create a single shared Base for all models
Base = declarative_base()
