"""
SQLAlchemy User stub — kept only so existing PostgreSQL FK columns
(uploaded_by, verified_by, reviewer_id, actor_id etc.) remain valid
as string columns. The actual user data lives in MongoDB.

Do NOT use this for authentication — use app.models.mongo_user.MongoUser.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class Role(Base):
    """Kept in PostgreSQL so validation_rules.created_by FK works."""
    __tablename__ = "roles"
    id          = Column(Integer, primary_key=True)
    name        = Column(String(50), unique=True, nullable=False)
    description = Column(String)


class User(Base):
    """
    Minimal SQLAlchemy stub — real user data is in MongoDB.
    This table is NOT used for login/auth. It is kept so that
    PostgreSQL FK columns (uploaded_by, actor_id, etc.) can
    reference a user ID without breaking integrity.
    """
    __tablename__ = "users"

    id              = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email           = Column(String(255), unique=True, nullable=False, index=True)
    full_name       = Column(String(255), nullable=False)
    hashed_password = Column(String, nullable=False, default="mongo_managed")
    role_id         = Column(Integer, ForeignKey("roles.id"), nullable=True)
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at      = Column(DateTime(timezone=True), default=datetime.utcnow)
