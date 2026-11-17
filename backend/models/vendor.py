# backend/models/vendor.py
"""Vendor aggregate model."""
from __future__ import annotations

import datetime
from sqlalchemy import String, Boolean, DateTime, Column
from sqlalchemy.orm import Mapped, mapped_column

from ..db.base import Base

class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    tax_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    default_currency: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)  # ACTIVE / INACTIVE
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow
    )
