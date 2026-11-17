# backend/api/invoices.py
"""Invoice API router.
Provides CRUD‑style endpoints required by the SPEC.
Implementation is intentionally minimal – it wires the route signatures
to the corresponding service stubs (storage, workflow, validation, etc.).
"""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..models.invoice import Invoice, InvoiceLine
from ..services.storage import save_upload_file
from ..services.workflow import transition
from ..services.validation import validate_invoice

router = APIRouter(prefix="/invoices", tags=["invoices"])

@router.post("/upload", status_code=status.HTTP_200_OK)
async def upload_invoice(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # Store the file and compute its SHA‑256 hash
    file_path, sha256 = await save_upload_file(file)
    # Create a minimal Invoice record (the rest of the fields would be filled by the OCR pipeline)
    invoice = Invoice(
        vendor_id=None,
        po_id=None,
        invoice_number="UNKNOWN",
        invoice_date="1970-01-01",
        currency="USD",
        subtotal=0,
        tax_total=0,
        total=0,
        status="UPLOADED",
        source_file_path=file_path,
        original_filename=file.filename,
        file_sha256=sha256,
        idempotency_key=sha256,
        created_by=1,  # placeholder – would be current user
        extraction_source="upload",
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return {"id": invoice.id, "file_sha256": sha256}

@router.get("", response_model=list[dict])
def list_invoices(db: Session = Depends(get_db)):
    invoices = db.query(Invoice).all()
    return [{"id": inv.id, "status": inv.status, "total": float(inv.total)} for inv in invoices]

@router.get("/{invoice_id}", response_model=dict)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)):
    inv = db.get(Invoice, invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return {
        "id": inv.id,
        "status": inv.status,
        "total": float(inv.total),
        "lines": [
            {"line_no": line.line_no, "description": line.description, "qty": float(line.qty), "unit_price": float(line.unit_price)}
            for line in inv.lines
        ],
    }

@router.post("/{invoice_id}/transitions", status_code=status.HTTP_200_OK)
def invoice_transition(
    invoice_id: int,
    action: str,
    comment: str | None = None,
    expected_version: int | None = None,
    idempotency_key: str | None = None,
    db: Session = Depends(get_db),
    # In a real app we would depend on current_user and its role
):
    # Simplified – assume role derived from auth (omitted here)
    actor_role = "SYSTEM"
    inv = transition(
        db=db,
        invoice_id=invoice_id,
        action=action,
        actor_role=actor_role,
        comment=comment,
        expected_version=expected_version,
        idempotency_key=idempotency_key,
    )
    return {"id": inv.id, "new_status": inv.status, "version": inv.version}
