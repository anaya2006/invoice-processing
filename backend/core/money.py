# backend/core/money.py
"""Custom SQLAlchemy type for precise monetary values.
Stores a Decimal as TEXT with a fixed number of fractional places.
The `DecimalString` decorator is used for money, quantity, unit_price, etc.
"""
from __future__ import annotations

import decimal
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.types import TypeDecorator, VARCHAR

# Helper to quantize a Decimal to a given number of places
def _quantize(value: Decimal, places: int) -> Decimal:
    quant = Decimal((0, (1,), -places))  # e.g. places=2 -> Decimal('0.01')
    return value.quantize(quant, rounding=ROUND_HALF_UP)

class DecimalString(TypeDecorator):
    """Store a Decimal as a string (TEXT) with fixed precision.

    Parameters
    ----------
    places: int
        Number of fractional decimal places (e.g. 2 for money, 3 for quantity).
    """

    impl = VARCHAR
    cache_ok = True

    def __init__(self, places: int = 2, **kwargs):
        super().__init__(**kwargs)
        self.places = places

    def process_bind_param(self, value: Decimal | None, dialect) -> str | None:
        if value is None:
            return None
        if not isinstance(value, Decimal):
            raise TypeError(f"DecimalString expects Decimal, got {type(value)}")
        q = _quantize(value, self.places)
        # Store as plain string without exponent
        return format(q, "f")

    def process_result_value(self, value: str | None, dialect) -> Decimal | None:
        if value is None:
            return None
        return Decimal(value)
