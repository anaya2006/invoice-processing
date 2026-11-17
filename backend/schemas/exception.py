from __future__ import annotations

from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field

class ExceptionLogBase(BaseModel):
    invoice_id: int
    rule_code: str
    severity: str  # INFO / WARN / BLOCKING
    message: str
    evidence: Dict[str, Any]
    resolved: bool = False
    run_id: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ExceptionLogRead(ExceptionLogBase):
    id: int

    class Config:
        orm_mode = True
