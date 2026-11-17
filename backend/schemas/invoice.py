from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field

class InvoiceBase(BaseModel):
    vendor_id: Optional[int] = None
    po_id: Optional[int] = None
    invoice_number: str
    invoice_date: datetime
    currency: str
    subtotal: Decimal
    tax_total: Decimal
    total: Decimal
    status: str
    source_file_path: str
    original_filename: str
    file_sha256: str
    idempotency_key: str
    created_by: int
    created_at: datetime
    version: int = 1
    duplicate_of_invoice_id: Optional[int] = None
    duplicate_released: bool = False
    anomaly_score: Optional[float] = None
    risk_priority: Optional[int] = None
    extraction_source: str
    ocr_report: Optional[dict] = None

class InvoiceRead(InvoiceBase):
    id: int
    lines: List["InvoiceLineRead"] = []
    extracted_fields: List["ExtractedFieldRead"] = []
    exceptions: List["ExceptionLogRead"] = []
    audit_events: List["AuditEventRead"] = []

    class Config:
        orm_mode = True

class InvoiceLineBase(BaseModel):
    invoice_id: int
    line_no: int
    description: str
    qty: Decimal
    unit_price: Decimal
    amount: Decimal

class InvoiceLineRead(InvoiceLineBase):
    id: int

    class Config:
        orm_mode = True
