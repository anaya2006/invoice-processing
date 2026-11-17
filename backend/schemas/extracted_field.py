from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

class ExtractedFieldBase(BaseModel):
    invoice_id: int
    field_name: str
    extracted_value: str
    confidence: float
    corrected_value: Optional[str] = None
    corrected_by: Optional[int] = None
    corrected_at: Optional[datetime] = None

class ExtractedFieldRead(ExtractedFieldBase):
    id: int

    class Config:
        orm_mode = True
