# backend/models/exception.py
"""ExceptionLog model for business‑rule violations.
Only the fields needed for import sanity are defined.
"""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Boolean, Integer, ForeignKey, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base

class ExceptionLog(Base):
    __tablename__ = "exceptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), nullable=False)
    rule_code: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)  # INFO / WARN / BLOCKING
    message: Mapped[str] = mapped_column(String, nullable=False)
    evidence: Mapped[dict] = mapped_column(JSON, nullable=False)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    run_id: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    invoice: Mapped["Invoice"] = relationship("Invoice", back_populates="exceptions")
