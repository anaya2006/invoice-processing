# backend/models/invoice.py
"""Invoice aggregate and line items.
Only the columns required for import sanity are defined.
Complex business logic (state machine, validation, etc.) will be added later.
"""
from __future__ import annotations

import datetime
from decimal import Decimal
from typing import List

import sqlalchemy as sa
from sqlalchemy import String, DateTime, Numeric, Boolean, ForeignKey, JSON, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base
from .user import User
from .vendor import Vendor
from .purchase_order import PurchaseOrder

class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("vendor_id", "invoice_number", name="uq_vendor_invoice"),
        Index("ix_invoices_status", "status"),
        Index("ix_invoices_vendor_number", "vendor_id", "invoice_number"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    vendor_id: Mapped[int | None] = mapped_column(ForeignKey("vendors.id"))
    po_id: Mapped[int | None] = mapped_column(ForeignKey("purchase_orders.id"))
    invoice_number: Mapped[str] = mapped_column(String, nullable=False)
    invoice_date: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False)
    subtotal: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    tax_total: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    source_file_path: Mapped[str] = mapped_column(String, nullable=False)
    original_filename: Mapped[str] = mapped_column(String, nullable=False)
    file_sha256: Mapped[str] = mapped_column(String, index=True, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String, nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    version: Mapped[int] = mapped_column(sa.Integer, default=1, nullable=False)
    duplicate_of_invoice_id: Mapped[int | None] = mapped_column(ForeignKey("invoices.id"))
    duplicate_released: Mapped[bool] = mapped_column(Boolean, default=False)
    anomaly_score: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    risk_priority: Mapped[int | None] = mapped_column(sa.Integer, nullable=True)
    ocr_report: Mapped[dict] = mapped_column(JSON, nullable=True)
    extraction_source: Mapped[str] = mapped_column(String, nullable=False)

    # Relationships
    creator: Mapped[User] = relationship("User", backref="invoices_created")
    vendor: Mapped[Vendor] = relationship("Vendor", backref="invoices")
    po: Mapped[PurchaseOrder] = relationship("PurchaseOrder", backref="invoices")
    lines: Mapped[List["InvoiceLine"]] = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    extracted_fields: Mapped[List["ExtractedField"]] = relationship("ExtractedField", back_populates="invoice", cascade="all, delete-orphan")
    exceptions: Mapped[List["ExceptionLog"]] = relationship("ExceptionLog", back_populates="invoice", cascade="all, delete-orphan")
    audit_events: Mapped[List["AuditEvent"]] = relationship("AuditEvent", back_populates="invoice", cascade="all, delete-orphan")

class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), nullable=False)
    line_no: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    qty: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric, nullable=False)

    invoice: Mapped[Invoice] = relationship("Invoice", back_populates="lines")
