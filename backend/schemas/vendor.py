from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

class VendorBase(BaseModel):
    name: str
    tax_id: str
    default_currency: str
    status: str

class VendorRead(VendorBase):
    id: int
    updated_at: datetime

    class Config:
        orm_mode = True
