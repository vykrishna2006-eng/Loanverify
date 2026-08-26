"""
Authentication — JWT tokens + bcrypt passwords.
User storage: MongoDB (users collection in loanverify_auth database).
Loan data remains in PostgreSQL.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.config import settings
from app.models.mongo_user import MongoUser, doc_to_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


# ── Password helpers ──────────────────────────────────────────────────────────

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


# ── JWT helpers ───────────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ── MongoDB user lookup ───────────────────────────────────────────────────────

async def _get_user_by_email(email: str) -> Optional[MongoUser]:
    """Look up a user in MongoDB by email."""
    from app.mongodb import get_auth_db
    db   = get_auth_db()
    doc  = await db["users"].find_one({"email": email})
    return doc_to_user(doc)


async def _get_user_by_id(user_id: str) -> Optional[MongoUser]:
    """Look up a user in MongoDB by their UUID id field."""
    from app.mongodb import get_auth_db
    db  = get_auth_db()
    doc = await db["users"].find_one({"id": user_id})
    return doc_to_user(doc)


async def authenticate_user(email: str, password: str) -> Optional[MongoUser]:
    """Verify email + password against MongoDB. Returns user or None."""
    user = await _get_user_by_email(email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


# ── FastAPI dependencies ──────────────────────────────────────────────────────

async def get_current_user(token: str = Depends(oauth2_scheme)) -> MongoUser:
    """Decode JWT and fetch user from MongoDB."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if not user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = await _get_user_by_id(user_id)
    if not user or not user.is_active:
        raise credentials_exception
    return user


def require_role(*roles: str):
    """Factory — returns a FastAPI dependency that enforces role membership."""
    async def _check(current_user: MongoUser = Depends(get_current_user)) -> MongoUser:
        if current_user.role_name not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {', '.join(roles)}",
            )
        return current_user
    return _check


# ── Convenience role dependencies ─────────────────────────────────────────────
require_operator      = require_role("DATA_OPERATOR")
require_reviewer_only = require_role("REVIEWER")
require_reviewer      = require_role("REVIEWER", "DATA_OPERATOR")
require_any_role      = require_role("DATA_OPERATOR", "REVIEWER", "DATA_CONSUMER")
