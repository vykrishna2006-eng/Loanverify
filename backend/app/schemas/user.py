from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class RoleOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str
    role: RoleOut
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: str
    full_name: str
    password: str
    role_id: int


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
