# backend/db/base.py
"""SQLAlchemy declarative base used by all ORM models."""
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
