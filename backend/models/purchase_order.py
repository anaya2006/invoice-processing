# backend/models/purchase_order.py
"""Purchase order aggregate and its line items.
Only the fields required for imports are defined; relationships are set up
so that SQLAlchemy can resolve them without needing full business logic.
"""
from __future__ import annotations

import datetime
from decimal import Decimal
from typing import List

import sqlalchemy as sa
from sqlalchemy import String, DateTime, Numeric, ForeignKey, UniqueConstraint

from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..db.base import Base
from .vendor import Vendor

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    po_number: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), nullable=False)
    currency: Mapped[str] = mapped_column(String, nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)  # OPEN / CLOSED
    issued_at: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)

    # relationship back to vendor
    vendor: Mapped[Vendor] = relationship("Vendor", backref="purchase_orders")
    lines: Mapped[List["POLine"]] = relationship("POLine", back_populates="po", cascade="all, delete-orphan")

class POLine(Base):
    __tablename__ = "po_lines"
    __table_args__ = (UniqueConstraint("po_id", "line_no", name="uq_po_line"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    po_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"), nullable=False)
    line_no: Mapped[int] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    qty: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric, nullable=False)

    po: Mapped[PurchaseOrder] = relationship("PurchaseOrder", back_populates="lines")
