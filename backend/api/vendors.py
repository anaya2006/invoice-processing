# backend/api/vendors.py
"""Vendor API router – minimal CRUD endpoints required by the SPEC.
Only list and retrieve are implemented for now; create/update can be added later.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db.session import get_db
from ..models.vendor import Vendor

router = APIRouter(prefix="/vendors", tags=["vendors"])

@router.get("", response_model=list[dict])
def list_vendors(db: Session = Depends(get_db)):
    vendors = db.query(Vendor).all()
    return [{"id": v.id, "name": v.name, "tax_id": v.tax_id, "status": v.status} for v in vendors]

@router.get("/{vendor_id}", response_model=dict)
def get_vendor(vendor_id: int, db: Session = Depends(get_db)):
    vendor = db.get(Vendor, vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return {"id": vendor.id, "name": vendor.name, "tax_id": vendor.tax_id, "status": vendor.status}
