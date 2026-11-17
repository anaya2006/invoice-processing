# backend/api/admin.py
"""Admin API router.
Provides a seed endpoint (POST /admin/seed) for demo data.
Only accessible to ADMIN role and when DEMO_MODE is enabled.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.config import settings
from ..services.auth import require_permission
from ..models.user import User as UserORM

# Import the seed function
from ..scripts.seed_demo import seed_demo

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/seed", response_model=dict)
def seed_demo_endpoint(
    _current_user: UserORM = Depends(require_permission("ADMIN"))
):
    """Seed demo data. Requires ADMIN role and DEMO_MODE true."""
    if not settings.DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="DEMO_MODE is disabled; seeding not allowed.",
        )
    created, existed = seed_demo()
    return {"created": created, "existed": existed}
