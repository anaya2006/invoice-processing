# backend/main.py
"""FastAPI application entry point.
All routers are imported and included here.
"""
from fastapi import FastAPI

app = FastAPI(title="Finance and Invoice Processing Automation Platform",version="0.0.1")

# Include routers
from backend.api.health import router as health_router
from backend.api.auth import router as auth_router
from backend.api.invoices import router as invoices_router
from backend.api.vendors import router as vendors_router
from backend.api.purchase_orders import router as po_router
from backend.api.dashboard import router as dashboard_router
from backend.api.admin import router as admin_router

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(invoices_router)
app.include_router(vendors_router)
app.include_router(po_router)
app.include_router(dashboard_router)
app.include_router(admin_router)

@app.get("/")
def home():
    return {"message": "Invoice Processing API"}
