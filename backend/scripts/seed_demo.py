"""Demo data seeding script.

Run as ``python -m scripts.seed_demo`` from the backend directory.
It aborts with a clear error if ``settings.DEMO_MODE`` is not true.
The function is idempotent – it inserts missing records based on natural keys
(email, tax_id, po_number, (po_id, line_no), invoice_number) and prints what
was created versus what already existed.

The script also creates the database tables and audit triggers if they are
missing, mirroring the startup behaviour of the application.
"""

from __future__ import annotations

import sys, os
# Ensure the project root (parent of backend) is on the path so that
# absolute imports like ``backend.core`` work when this script is executed
# as ``python -m scripts.seed_demo`` from the ``backend`` directory.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from decimal import Decimal
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple

from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.db.base import Base
from backend.db.session import SessionLocal, engine
from backend.db.triggers import create_audit_triggers
from backend.models.user import User
from backend.models.vendor import Vendor
from backend.models.purchase_order import PurchaseOrder, POLine
from backend.models.invoice import Invoice
from backend.models.audit_event import AuditEvent
from backend.services.auth import hash_password

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _ensure_schema() -> None:
    """Create tables and audit triggers if they do not exist."""
    Base.metadata.create_all(bind=engine)
    create_audit_triggers()


def _get_or_create_user(session: Session, email: str, name: str, role: str, password: str) -> Tuple[User, bool]:
    user = session.query(User).filter(User.email == email).first()
    if user:
        return user, False
    pwd_hash = hash_password(password)
    user = User(email=email, name=name, password_hash=pwd_hash, role=role, is_active=True)
    session.add(user)
    session.flush()
    return user, True


def _get_or_create_vendor(session: Session, tax_id: str, name: str, default_currency: str, status: str) -> Tuple[Vendor, bool]:
    vendor = session.query(Vendor).filter(Vendor.tax_id == tax_id).first()
    if vendor:
        return vendor, False
    vendor = Vendor(name=name, tax_id=tax_id, default_currency=default_currency, status=status)
    session.add(vendor)
    session.flush()  # assign primary key so PO can reference it
    return vendor, True


def _get_or_create_po(
    session: Session,
    po_number: str,
    vendor: Vendor,
    currency: str,
    total: Decimal,
    status: str,
    issued_at: datetime,
) -> Tuple[PurchaseOrder, bool]:
    po = session.query(PurchaseOrder).filter(PurchaseOrder.po_number == po_number).first()
    if po:
        return po, False
    po = PurchaseOrder(
        po_number=po_number,
        vendor_id=vendor.id,
        currency=currency,
        total=total,
        status=status,
        issued_at=issued_at,
    )
    session.add(po)
    session.flush()  # assign PK for line insertion
    return po, True


def _get_or_create_po_line(
    session: Session,
    po: PurchaseOrder,
    line_no: int,
    description: str,
    qty: Decimal,
    unit_price: Decimal,
) -> Tuple[POLine, bool]:
    line = (
        session.query(POLine)
        .filter(POLine.po_id == po.id, POLine.line_no == line_no)
        .first()
    )
    if line:
        return line, False
    line = POLine(
        po_id=po.id,
        line_no=line_no,
        description=description,
        qty=qty,
        unit_price=unit_price,
    )
    session.add(line)
    return line, True


def _get_or_create_invoice(
    session: Session,
    invoice_number: str,
    vendor: Vendor,
    created_by: User,
    total: Decimal,
    status: str,
) -> Tuple[Invoice, bool]:
    inv = session.query(Invoice).filter(Invoice.invoice_number == invoice_number).first()
    if inv:
        return inv, False
    inv = Invoice(
        vendor_id=vendor.id,
        po_id=None,
        invoice_number=invoice_number,
        invoice_date=datetime(1970, 1, 1),
        currency=vendor.default_currency,
        subtotal=total,
        tax_total=Decimal("0"),
        total=total,
        status=status,
        source_file_path="seeded.pdf",
        original_filename="seeded.pdf",
        file_sha256=f"seed-{invoice_number}",
        idempotency_key=f"seed-{invoice_number}",
        created_by=created_by.id,
        created_at=datetime.utcnow(),
        version=1,
        extraction_source="seed",
    )
    session.add(inv)
    session.flush()
    return inv, True


def _create_audit_for_invoice(session: Session, invoice: Invoice) -> None:
    audit = AuditEvent(
        invoice_id=invoice.id,
        actor_id=None,
        actor_role="SYSTEM",
        action="APPROVED",
        from_state="UPLOADED",
        to_state="APPROVED",
        comment="Seed demo data",
        payload={},
        idempotency_key=f"seed-{invoice.invoice_number}",
    )
    session.add(audit)

# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

def seed_demo() -> Tuple[Dict[str, int], Dict[str, int]]:
    """Insert demo data.
    Returns two dictionaries – counts of rows created and rows already existing.
    """
    if not getattr(settings, "DEMO_MODE", False):
        print("DEMO_MODE is disabled – aborting seed.")
        sys.exit(1)

    _ensure_schema()
    created: Dict[str, int] = {}
    existed: Dict[str, int] = {}
    session = SessionLocal()
    try:
        # ------------------- Users -------------------
        demo_password = "DemoPass123!"
        users_info = [
            ("operator@demo.com", "Demo Operator", "AP_OPERATOR"),
            ("reviewer@demo.com", "Demo Reviewer", "FINANCE_REVIEWER"),
            ("reviewer2@demo.com", "Demo Reviewer 2", "FINANCE_REVIEWER"),
            ("admin@demo.com", "Demo Admin", "ADMIN"),
            ("auditor@demo.com", "Demo Auditor", "AUDITOR"),
        ]
        for email, name, role in users_info:
            user, was_created = _get_or_create_user(session, email, name, role, demo_password)
            key = f"user:{email}"
            if was_created:
                created[key] = created.get(key, 0) + 1
            else:
                existed[key] = existed.get(key, 0) + 1

        # ------------------- Vendors -------------------
        vendors_info = [
            ("Company S", "TAX123456", "INR", "ACTIVE"),
            ("Acme Corp", "TAX654321", "USD", "ACTIVE"),
            ("Beta Ltd", "TAX111222", "EUR", "ACTIVE"),
            ("Gamma LLC", "TAX333444", "INR", "INACTIVE"),
            ("Delta Inc", "TAX555666", "GBP", "ACTIVE"),
        ]
        vendor_by_tax: Dict[str, Vendor] = {}
        for name, tax_id, currency, status in vendors_info:
            vendor, was_created = _get_or_create_vendor(session, tax_id, name, currency, status)
            vendor_by_tax[tax_id] = vendor
            key = f"vendor:{tax_id}"
            if was_created:
                created[key] = created.get(key, 0) + 1
            else:
                existed[key] = existed.get(key, 0) + 1

        # ------------------- Purchase Orders -------------------
        po_infos = [
            (
                "PO-DEMO-001",
                vendor_by_tax["TAX123456"],
                "INR",
                Decimal("100000"),
                "OPEN",
                datetime(2023, 1, 1),
                [
                    (1, "Laptop", Decimal("10"), Decimal("5000")),
                    (2, "CPU", Decimal("5"), Decimal("10000")),
                ],
            ),
            ("PO-USD-001", vendor_by_tax["TAX654321"], "USD", Decimal("20000"), "OPEN", datetime(2023, 2, 15), []),
            ("PO-EUR-001", vendor_by_tax["TAX111222"], "EUR", Decimal("15000"), "OPEN", datetime(2023, 3, 10), []),
            ("PO-INR-002", vendor_by_tax["TAX123456"], "INR", Decimal("50000"), "CLOSED", datetime(2022, 12, 5), []),
            ("PO-SPLIT-001", vendor_by_tax["TAX123456"], "INR", Decimal("30000"), "OPEN", datetime(2023, 4, 20), [(1, "Monitor", Decimal("2"), Decimal("15000"))]),
            ("PO-USD-002", vendor_by_tax["TAX654321"], "USD", Decimal("12000"), "OPEN", datetime(2023, 5, 1), []),
            ("PO-EUR-002", vendor_by_tax["TAX111222"], "EUR", Decimal("8000"), "OPEN", datetime(2023, 5, 15), []),
            ("PO-INR-003", vendor_by_tax["TAX123456"], "INR", Decimal("40000"), "OPEN", datetime(2023, 6, 5), []),
            ("PO-USD-003", vendor_by_tax["TAX654321"], "USD", Decimal("25000"), "OPEN", datetime(2023, 7, 10), []),
        ]
        for po_number, vendor, currency, total, status, issued_at, lines in po_infos:
            po, po_created = _get_or_create_po(session, po_number, vendor, currency, total, status, issued_at)
            key = f"po:{po_number}"
            if po_created:
                created[key] = created.get(key, 0) + 1
            else:
                existed[key] = existed.get(key, 0) + 1
            for line_no, desc, qty, unit_price in lines:
                line, line_created = _get_or_create_po_line(session, po, line_no, desc, qty, unit_price)
                line_key = f"poline:{po_number}:{line_no}"
                if line_created:
                    created[line_key] = created.get(line_key, 0) + 1
                else:
                    existed[line_key] = existed.get(line_key, 0) + 1

        # ------------------- Historical APPROVED Invoices -------------------
        operator_user = session.query(User).filter(User.email == "operator@demo.com").first()
        company_s = vendor_by_tax["TAX123456"]
        for i in range(1, 21):
            inv_number = f"HIST-{i:04d}"
            total = Decimal("80000") + (i * Decimal("5000"))
            inv, inv_created = _get_or_create_invoice(session, inv_number, company_s, operator_user, total, "APPROVED")
            key = f"invoice:{inv_number}"
            if inv_created:
                created[key] = created.get(key, 0) + 1
                _create_audit_for_invoice(session, inv)
            else:
                existed[key] = existed.get(key, 0) + 1

        session.commit()
    finally:
        session.close()

    # Summary output
    print("--- Seed summary ---")
    for entity, cnt in created.items():
        print(f"Created {entity}: {cnt}")
    for entity, cnt in existed.items():
        print(f"Already existed {entity}: {cnt}")
    return created, existed


if __name__ == "__main__":
    seed_demo()
