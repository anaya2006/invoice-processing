from __future__ import annotations

import logging
from typing import Any, Dict

# Placeholder validation service. In a full implementation this would run the
# extracted OCR data through a series of business‑rule checks and raise
# HTTPException on failures. For now we provide a no‑op function so the API
# can be imported and the server started.

def validate_invoice(data: Dict[str, Any] | None = None) -> bool:
    """Validate an invoice payload.

    Args:
        data: Optional dictionary representing invoice data.
    Returns:
        ``True`` – validation passes.
    """
    logging.getLogger(__name__).debug("validate_invoice called with %s", data)
    # No real validation performed in this stub.
    return True
