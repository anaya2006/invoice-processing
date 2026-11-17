# backend/services/workflow.py
"""Workflow service – state‑machine transition helper.
Implements the single entry point ``transition`` that validates guards,
checks permissions, increments the invoice version atomically, and writes an audit event.
The full business rules are in the SPEC; here we provide a minimal stub that satisfies imports
and can be expanded later.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from ..models.invoice import Invoice
from ..models.audit_event import AuditEvent
from ..core.errors import ConflictError, ForbiddenError, ValidationError

def _check_guards(invoice: Invoice, action: str, actor_role: str) -> None:
    """Placeholder guard checks.
    Raise appropriate ServiceError subclasses if a guard fails.
    """
    # Example: only FINANCE_REVIEWER can approve
    if action == "approve" and actor_role != "FINANCE_REVIEWER":
        raise ForbiddenError("Only finance reviewers can approve")
    # Add more guard logic as needed.

def _apply_transition(invoice: Invoice, action: str) -> str:
    """Map an action to the next state string.
    Returns the new ``to_state``.
    """
    mapping = {
        "extraction_succeeded": "EXTRACTED",
        "extraction_failed": "FAILED_EXTRACTION",
        "submit_for_approval": "PENDING_APPROVAL",
        "approve": "APPROVED",
        "reject": "REJECTED",
        # ... other mappings per SPEC
    }
    if action not in mapping:
        raise ValidationError(f"Invalid transition action: {action}")
    return mapping[action]

def transition(
    db: Session,
    invoice_id: int,
    action: str,
    actor_role: str,
    comment: str | None = None,
    expected_version: int | None = None,
    idempotency_key: str | None = None,
) -> Invoice:
    """Perform a state transition on ``invoice_id``.
    The function runs in a single transaction:
    1. Load the invoice.
    2. Verify ``expected_version`` matches (optimistic locking).
    3. Run guard checks.
    4. Compute the new state.
    5. Increment ``version``.
    6. Write an ``AuditEvent``.
    Returns the refreshed ``Invoice`` instance.
    """
    invoice: Invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise ConflictError("Invoice not found")
    if expected_version is not None and invoice.version != expected_version:
        raise ConflictError("Version conflict")

    # Guard checks
    _check_guards(invoice, action, actor_role)

    # Determine new state
    to_state = _apply_transition(invoice, action)

    # Update invoice
    invoice.status = to_state
    invoice.version = (invoice.version or 0) + 1
    db.add(invoice)

    # Write audit event
    audit = AuditEvent(
        invoice_id=invoice.id,
        actor_id=None,
        actor_role=actor_role,
        action=action,
        from_state=invoice.status,
        to_state=to_state,
        comment=comment,
        payload={},
        idempotency_key=idempotency_key,
    )
    db.add(audit)
    db.flush()
    return invoice
