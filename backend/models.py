"""
models.py -- Multi-tenant database models and engine setup using SQLAlchemy.
"""

import os
import uuid
from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'nexus_ai.db')}")

# For SQLite, enable check_same_thread=False for multi-threading
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def generate_uuid() -> str:
    return str(uuid.uuid4())


def generate_org_code(prefix="NX") -> str:
    """Generates a clean human-readable organization join code, e.g. NX-8429."""
    import random
    return f"{prefix}-{random.randint(1000, 9999)}"


class Tenant(Base):
    """
    Represents an isolated Organization / Clinic / Hospital entity.
    All patient records and screenings belong strictly to a Tenant.
    """
    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(120), nullable=False)
    code = Column(String(20), unique=True, index=True, default=generate_org_code)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    screenings = relationship("ScreeningRecord", back_populates="tenant", cascade="all, delete-orphan")


class User(Base):
    """
    User belonging to a specific Tenant with role authorization (admin, staff).
    """
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    email = Column(String(160), unique=True, index=True, nullable=False)
    name = Column(String(120), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="staff")  # 'admin' or 'staff'
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    screenings = relationship("ScreeningRecord", back_populates="user")


class ScreeningRecord(Base):
    """
    Clinical dengue risk prediction record, strictly isolated to a Tenant.
    """
    __tablename__ = "screening_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)

    patient_name = Column(String(120), default="Not Specified")
    age = Column(Float, nullable=False)
    sex = Column(String(20), nullable=False)
    haemoglobin = Column(Float, nullable=False)
    platelet_count = Column(Float, nullable=False)
    pdw = Column(Float, nullable=False)
    wbc_count = Column(Float, default=0.0)

    risk_level = Column(String(20), nullable=False)  # 'Low', 'Moderate', 'High'
    probability = Column(Float, nullable=False)
    dengue_positive = Column(Boolean, default=False)
    source_filename = Column(String(255), default="Manual Entry")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="screenings")
    user = relationship("User", back_populates="screenings")


def init_db():
    """Initializes all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
