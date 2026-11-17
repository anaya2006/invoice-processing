# backend/models/audit_event.py
"""Immutable audit trail model.
Only the columns needed for import validation are defined.
The table is created by SQLAlchemy when metadata.create_all() is called.
"""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Integer, Boolean, ForeignKey, JSON, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base

class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        UniqueConstraint("invoice_id", "idempotency_key", name="uq_audit_invoice_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), nullable=False)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))  # null = SYSTEM
    actor_role: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    from_state: Mapped[str | None] = mapped_column(String, nullable=True)
    to_state: Mapped[str] = mapped_column(String, nullable=False)
    comment: Mapped[str | None] = mapped_column(String, nullable=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    invoice = relationship("Invoice", back_populates="audit_events")
