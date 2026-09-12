"""
auth.py -- Router for multi-tenant registration, login, profile, and tenant-isolated data access.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from models import get_db, User, Tenant, ScreeningRecord
from services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    get_current_tenant,
)

router = APIRouter(prefix="/api", tags=["Multi-Tenant Authentication"])


# ── Schemas ───────────────────────────────────────────────────────────────────
class SignUpRequest(BaseModel):
    name: str = Field(..., min_length=2, example="Dr. Priya Sharma")
    email: str = Field(..., example="priya@apexhospital.org")
    password: str = Field(..., min_length=6, example="SecurePass123!")
    tenant_action: str = Field(..., example="create", description="'create' or 'join'")
    organization_name: Optional[str] = Field(None, example="Apex Health Clinic")
    join_code: Optional[str] = Field(None, example="NX-4821")


class SignInRequest(BaseModel):
    email: str = Field(..., example="priya@apexhospital.org")
    password: str = Field(..., example="SecurePass123!")


class UserProfile(BaseModel):
    id: str
    name: str
    email: str
    role: str
    tenant_id: str


class TenantProfile(BaseModel):
    id: str
    name: str
    code: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile
    tenant: TenantProfile


# ── Routes ────────────────────────────────────────────────────────────────────
@router.post("/auth/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignUpRequest, db: Session = Depends(get_db)):
    """
    Registers a user in a multi-tenant structure:
    - If tenant_action == 'create': initializes a new Tenant and assigns 'admin' role.
    - If tenant_action == 'join': resolves Tenant by join_code and assigns 'staff' role.
    """
    clean_email = payload.email.strip().lower()

    # Check for existing user
    existing_user = db.query(User).filter(User.email == clean_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists. Please sign in instead.",
        )

    # Resolve or create Tenant
    if payload.tenant_action == "create":
        org_name = (payload.organization_name or "").strip()
        if not org_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please specify an organization or clinic name.",
            )
        tenant = Tenant(name=org_name)
        db.add(tenant)
        db.flush()  # populate tenant.id and tenant.code
        user_role = "admin"
    elif payload.tenant_action == "join":
        code = (payload.join_code or "").strip().upper()
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please provide an organization join code.",
            )
        tenant = db.query(Tenant).filter(Tenant.code == code).first()
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Organization with join code '{code}' could not be found. Please check with your clinic administrator.",
            )
        user_role = "staff"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid tenant action. Choose 'create' or 'join'.",
        )

    # Hash password and persist user
    pw_hash = hash_password(payload.password)
    user = User(
        tenant_id=tenant.id,
        email=clean_email,
        name=payload.name.strip(),
        password_hash=pw_hash,
        role=user_role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate JWT
    token_data = {
        "sub": user.id,
        "email": user.email,
        "name": user.name,
        "tenant_id": tenant.id,
        "tenant_name": tenant.name,
        "role": user.role,
    }
    token = create_access_token(token_data)

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserProfile(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            tenant_id=tenant.id,
        ),
        tenant=TenantProfile(
            id=tenant.id,
            name=tenant.name,
            code=tenant.code,
        ),
    )


@router.post("/auth/signin", response_model=AuthResponse)
def signin(payload: SignInRequest, db: Session = Depends(get_db)):
    """
    Authenticates user, resolves tenant membership, and returns JWT session token.
    """
    clean_email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == clean_email).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    tenant = user.tenant
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not linked to an active organization.",
        )

    token_data = {
        "sub": user.id,
        "email": user.email,
        "name": user.name,
        "tenant_id": tenant.id,
        "tenant_name": tenant.name,
        "role": user.role,
    }
    token = create_access_token(token_data)

    return AuthResponse(
        access_token=token,
        token_type="bearer",
        user=UserProfile(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            tenant_id=tenant.id,
        ),
        tenant=TenantProfile(
            id=tenant.id,
            name=tenant.name,
            code=tenant.code,
        ),
    )


@router.get("/auth/me")
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Validates token and returns user and tenant context.
    """
    return {
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role,
            "tenant_id": current_user.tenant_id,
        },
        "tenant": {
            "id": current_user.tenant.id,
            "name": current_user.tenant.name,
            "code": current_user.tenant.code,
        },
    }


@router.get("/tenant/screenings")
def get_tenant_screenings(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns screening history strictly isolated to the authenticated user's tenant.
    Cross-tenant data access is impossible at query level.
    """
    records = (
        db.query(ScreeningRecord)
        .filter(ScreeningRecord.tenant_id == current_user.tenant_id)
        .order_by(ScreeningRecord.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": r.id,
            "patient_name": r.patient_name,
            "age": r.age,
            "sex": r.sex,
            "haemoglobin": r.haemoglobin,
            "platelet_count": r.platelet_count,
            "pdw": r.pdw,
            "wbc_count": r.wbc_count,
            "risk_level": r.risk_level,
            "probability": r.probability,
            "dengue_positive": r.dengue_positive,
            "source_filename": r.source_filename,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else None,
        }
        for r in records
    ]


@router.get("/tenant/info")
def get_tenant_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns organization overview, member count, and join code for admins.
    """
    tenant = current_user.tenant
    member_count = db.query(User).filter(User.tenant_id == tenant.id).count()
    screening_count = db.query(ScreeningRecord).filter(ScreeningRecord.tenant_id == tenant.id).count()

    return {
        "id": tenant.id,
        "name": tenant.name,
        "code": tenant.code,
        "created_at": tenant.created_at.strftime("%Y-%m-%d") if tenant.created_at else None,
        "member_count": member_count,
        "screening_count": screening_count,
        "current_user_role": current_user.role,
    }
