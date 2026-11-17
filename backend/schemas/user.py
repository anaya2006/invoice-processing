from __future__ import annotations

import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field

class UserBase(BaseModel):
    email: str
    name: str
    role: str
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    created_at: datetime.datetime

class UserUpdate(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

    class Config:
        orm_mode = True
