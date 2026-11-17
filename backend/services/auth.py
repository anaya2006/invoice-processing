# backend/services/auth.py
"""Authentication utilities.
Provides password hashing/verification (argon2), JWT creation and verification,
and FastAPI dependencies for the current user and role‑based permission checking.
"""
from __future__ import annotations

import datetime
from typing import Annotated

import jwt
from argon2 import PasswordHasher
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from ..core.config import settings
from ..models.user import User
from ..db.session import get_db
from sqlalchemy.orm import Session

# Argon2 password hasher (default parameters are secure)
ph = PasswordHasher()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def hash_password(password: str) -> str:
    """Hash a plain password using Argon2."""
    return ph.hash(password)

def verify_password(hashed: str, password: str) -> bool:
    """Verify a password against its Argon2 hash.
    Returns True if the password matches, otherwise raises an exception.
    """
    try:
        ph.verify(hashed, password)
        return True
    except Exception:
        return False

def create_access_token(user_id: int, role: str) -> str:
    """Create a JWT access token.
    The token contains ``sub`` (user id) and ``role`` claims and expires
    according to ``settings.JWT_EXPIRE_HOURS``.
    """
    expire = datetime.datetime.utcnow() + datetime.timedelta(hours=settings.JWT_EXPIRE_HOURS)
    payload = {
        "sub": str(user_id),
        "role": role,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

def decode_token(token: str) -> dict:
    """Decode a JWT token and return the payload.
    Raises ``HTTPException`` with 401 if the token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency that returns the authenticated ``User`` instance.
    Checks ``is_active`` and raises ``401`` or ``403`` as appropriate.
    """
    payload = decode_token(token)
    user_id = int(payload.get("sub"))
    role = payload.get("role")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")
    # Attach role to the user object for convenience
    user.role = role
    return user

def require_permission(required_role: str):
    """Return a FastAPI dependency that ensures the caller has ``required_role``.
    ``ADMIN`` can do everything; ``SYSTEM`` is internal and never used from the API.
    """
    def _dependency(current_user: User = Depends(get_current_user)):
        if current_user.role == "ADMIN":
            return current_user
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role {required_role}",
            )
        return current_user
    return _dependency
