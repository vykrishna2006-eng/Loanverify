"""
MongoDB User & Role models for authentication.
These are plain Python dataclasses — NOT SQLAlchemy models.
PostgreSQL models (loan data) are in models/user.py (kept for FK references).
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid


class MongoRole(BaseModel):
    """Role document stored in MongoDB roles collection."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str                    # DATA_OPERATOR | REVIEWER | DATA_CONSUMER
    description: str = ""


class MongoUser(BaseModel):
    """User document stored in MongoDB users collection."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    full_name: str
    hashed_password: str
    role_name: str               # stored directly — no FK needed in Mongo
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Convenience property — matches the interface the rest of the app expects
    @property
    def role(self):
        """Returns a role-like object so existing code using user.role.name still works."""
        return type("Role", (), {"name": self.role_name, "id": None, "description": ""})()


class MongoUserInDB(MongoUser):
    """Used internally — includes raw MongoDB _id."""
    mongo_id: Optional[str] = None


# ── Converters ────────────────────────────────────────────────────────────────

def doc_to_user(doc: dict) -> Optional[MongoUser]:
    """Convert a MongoDB document dict → MongoUser."""
    if not doc:
        return None
    return MongoUser(
        id            = doc.get("id", str(doc.get("_id", ""))),
        email         = doc["email"],
        full_name     = doc["full_name"],
        hashed_password = doc["hashed_password"],
        role_name     = doc["role_name"],
        is_active     = doc.get("is_active", True),
        created_at    = doc.get("created_at", datetime.utcnow()),
    )
