# backend/api/dashboard.py
"""Dashboard router – provides a summary endpoint.
The implementation returns simple aggregate counts from the DB.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..models.invoice import Invoice
from ..models.vendor import Vendor
from ..models.purchase_order import PurchaseOrder

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    invoice_count = db.query(Invoice).count()
    vendor_count = db.query(Vendor).count()
    po_count = db.query(PurchaseOrder).count()
    return {
        "invoices": invoice_count,
        "vendors": vendor_count,
        "purchase_orders": po_count,
    }
