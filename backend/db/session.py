# backend/db/session.py
"""Database session utilities.
Creates the engine from SETTINGS.DATABASE_URL and provides a FastAPI
dependency `get_db` yielding a Session with foreign‑keys enforced.
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker

from ..core.config import settings
from .base import Base

# Create engine; echo disabled for production
engine = sa.create_engine(settings.DATABASE_URL, echo=False, future=True)

# Enable foreign‑key constraints for SQLite
if "sqlite" in settings.DATABASE_URL:
    @sa.event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):  # pragma: no cover
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Session factory
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

def get_db():
    """FastAPI dependency that yields a DB session and ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
