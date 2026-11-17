# backend/models/extracted_field.py
"""Extracted field definition for OCR extraction results.
Only the minimal columns needed for imports and basic relationship mapping are defined.
"""
from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base

class ExtractedField(Base):
    __tablename__ = "extracted_fields"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), nullable=False)
    field_name: Mapped[str] = mapped_column(String, nullable=False)
    extracted_value: Mapped[str] = mapped_column(String, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    corrected_value: Mapped[str | None] = mapped_column(String, nullable=True)
    corrected_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    corrected_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    invoice = relationship("Invoice", back_populates="extracted_fields")
