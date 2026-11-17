from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

class PurchaseOrderBase(BaseModel):
    po_number: str
    vendor_id: int
    currency: str
    total: Decimal
    status: str
    issued_at: datetime

class PurchaseOrderRead(PurchaseOrderBase):
    id: int
    lines: List["POLineRead"] = []

    class Config:
        orm_mode = True

class POLineBase(BaseModel):
    po_id: int
    line_no: int
    description: str
    qty: Decimal
    unit_price: Decimal

class POLineRead(POLineBase):
    id: int

    class Config:
        orm_mode = True
