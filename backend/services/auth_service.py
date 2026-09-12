"""
auth_service.py -- Authentication, password hashing, JWT token handling,
and multi-tenant dependency injection for FastAPI.
"""

import os
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from models import get_db, User, Tenant

# Configurable secrets from environment variables
SECRET_KEY = os.environ.get("JWT_SECRET", "nexus_ai_super_secret_healthcare_key_2026_change_in_prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours

security_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hashes a plaintext password securely using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generates a signed JWT access token containing user and tenant IDs."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a signed JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication session. Please sign in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db),
) -> User:
    """
    Mandatory authentication dependency.
    Validates token and returns the current User, ensuring tenant membership.
    """
    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(auth.credentials)
    user_id: str = payload.get("sub")
    tenant_id: str = payload.get("tenant_id")

    if not user_id or not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload is missing user or tenant credentials.",
        )

    user = db.query(User).filter(User.id == user_id, User.tenant_id == tenant_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User or organization could not be verified.",
        )

    return user


def get_current_tenant(current_user: User = Depends(get_current_user)) -> Tenant:
    """
    Returns the isolated Tenant entity for the authenticated user.
    Guarantees that tenant context is strictly resolved from backend session.
    """
    if not current_user.tenant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No valid organization associated with this account.",
        )
    return current_user.tenant


def get_optional_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Optional authentication dependency.
    Returns User if a valid token is provided, or None if unauthenticated.
    """
    if not auth or not auth.credentials:
        return None
    try:
        payload = decode_access_token(auth.credentials)
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")
        if user_id and tenant_id:
            return db.query(User).filter(User.id == user_id, User.tenant_id == tenant_id).first()
    except Exception:
        pass
    return None
