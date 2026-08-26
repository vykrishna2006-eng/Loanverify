"""Authentication router — uses MongoDB for user storage."""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app.auth import (
    authenticate_user, create_access_token,
    get_current_user, get_password_hash,
)
from app.models.mongo_user import MongoUser
from app.mongodb import get_auth_db
from app.services import audit_service
from app.services.audit_service import AuditEventType
from app.database import SessionLocal

router = APIRouter()


@router.post("/token", summary="Login — returns JWT access token")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": user.id})

    # Log login event in PostgreSQL audit trail
    db = SessionLocal()
    try:
        audit_service.log_event(
            db=db,
            event_type=AuditEventType.USER_LOGIN,
            actor=None,                   # MongoUser — pass fields manually
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            new_value={"role": user.role_name, "email": user.email},
            metadata={"user_id": user.id, "actor_email": user.email},
        )
        db.commit()
    except Exception:
        pass
    finally:
        db.close()

    return {
        "access_token": token,
        "token_type":   "bearer",
        "user": {
            "id":        user.id,
            "email":     user.email,
            "full_name": user.full_name,
            "role":      {"name": user.role_name, "id": None, "description": ""},
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        },
    }


@router.get("/me", summary="Get current authenticated user")
async def get_me(current_user: MongoUser = Depends(get_current_user)):
    return {
        "id":        current_user.id,
        "email":     current_user.email,
        "full_name": current_user.full_name,
        "role":      {"name": current_user.role_name},
        "is_active": current_user.is_active,
    }


from pydantic import BaseModel, EmailStr
from typing import Optional


class RegisterRequest(BaseModel):
    email: str
    full_name: str
    password: str
    role_name: Optional[str] = "DATA_CONSUMER"


@router.post("/register", summary="Register a new user (stores in MongoDB)")
async def register(
    body: Optional[RegisterRequest] = None,
    email: Optional[str] = None,
    full_name: Optional[str] = None,
    password: Optional[str] = None,
    role_name: Optional[str] = None,
):
    final_email = (body.email if body else email or "").strip()
    final_name = (body.full_name if body else full_name or "").strip()
    final_password = body.password if body else password or ""
    final_role = (body.role_name if body and body.role_name else role_name) or "DATA_CONSUMER"
    final_role = final_role.strip().upper()

    if not final_email or not final_name or not final_password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="email, full_name, and password are required",
        )

    db_mongo = get_auth_db()

    # Check duplicate
    existing = await db_mongo["users"].find_one({"email": final_email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    valid_roles = {"DATA_OPERATOR", "REVIEWER", "DATA_CONSUMER"}
    if final_role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {valid_roles}")

    new_user = {
        "id":              str(uuid.uuid4()),
        "email":           final_email,
        "full_name":       final_name,
        "hashed_password": get_password_hash(final_password),
        "role_name":       final_role,
        "is_active":       True,
        "created_at":      datetime.utcnow(),
    }
    await db_mongo["users"].insert_one(new_user)

    return {
        "id":        new_user["id"],
        "email":     new_user["email"],
        "full_name": new_user["full_name"],
        "role":      {"name": final_role},
    }
