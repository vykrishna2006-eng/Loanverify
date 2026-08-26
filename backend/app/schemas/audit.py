from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List
from datetime import datetime


class AuditEventOut(BaseModel):
    id: str
    event_type: str
    actor_id: Optional[str] = None
    actor_email: Optional[str] = None
    loan_id: Optional[str] = None
    upload_id: Optional[str] = None
    exception_id: Optional[str] = None
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None
    ai_involved: bool = False
    ai_metadata: Optional[Dict[str, Any]] = None
    extra_metadata: Optional[Dict[str, Any]] = Field(None, alias="extra_metadata")
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class AuditListOut(BaseModel):
    items: List[AuditEventOut]
    total: int
    page: int
    page_size: int
    total_pages: int
