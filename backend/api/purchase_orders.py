# backend/api/purchase_orders.py
"""Purchase order API router – provides list and detail endpoints.
Only basic read‑only operations are needed for the initial scaffold.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..models.purchase_order import PurchaseOrder, POLine

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders"])

@router.get("", response_model=list[dict])
def list_pos(db: Session = Depends(get_db)):
    pos = db.query(PurchaseOrder).all()
    return [{"id": po.id, "po_number": po.po_number, "status": po.status} for po in pos]

@router.get("/{po_id}", response_model=dict)
def get_po(po_id: int, db: Session = Depends(get_db)):
    po = db.get(PurchaseOrder, po_id)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    return {
        "id": po.id,
        "po_number": po.po_number,
        "vendor_id": po.vendor_id,
        "currency": po.currency,
        "total": float(po.total),
        "status": po.status,
        "lines": [
            {"line_no": line.line_no, "description": line.description, "qty": float(line.qty), "unit_price": float(line.unit_price)}
            for line in po.lines
        ],
    }
