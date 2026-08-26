from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class ExceptionOut(BaseModel):
    id: UUID
    loan_id: str
    loan_record_id: UUID
    upload_id: Optional[UUID] = None
    rule_id: str
    exception_type: str
    severity: str
    field_name: Optional[str] = None
    actual_value: Optional[str] = None
    expected_value: Optional[str] = None
    message: str
    status: str
    assigned_to: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ExceptionListOut(BaseModel):
    items: List[ExceptionOut]
    total: int
    page: int
    page_size: int
    total_pages: int
    summary: dict


class CommentCreate(BaseModel):
    comment: str


class CommentOut(BaseModel):
    id: UUID
    exception_id: UUID
    author_id: UUID
    comment: str
    created_at: datetime
    author_name: Optional[str] = None

    class Config:
        from_attributes = True


class DecisionCreate(BaseModel):
    decision: str                          # APPROVED | REJECTED | EDITED | ESCALATED | REQUEST_CORRECTION
    corrected_value: Optional[str] = None
    reviewer_note: Optional[str] = None
    ai_decision_followed: Optional[bool] = None
