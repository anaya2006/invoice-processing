# backend/api/auth.py
"""Authentication API routes.
Provides ``POST /auth/login`` to obtain a JWT and ``GET /auth/me`` to retrieve
the current user's profile. Uses the ``backend.services.auth`` helpers.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..services.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from ..schemas.user import UserRead
from ..models.user import User as UserORM
from ..db.session import get_db
from sqlalchemy.orm import Session

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/auth/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user: UserORM | None = db.query(UserORM).filter(UserORM.email == req.email).first()
    if not user or not verify_password(user.password_hash, req.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(user.id, user.role)
    return TokenResponse(access_token=token)

@router.get("/auth/me", response_model=UserRead)
def me(current_user: UserORM = Depends(get_current_user)) -> UserRead:
    return UserRead.from_orm(current_user)
