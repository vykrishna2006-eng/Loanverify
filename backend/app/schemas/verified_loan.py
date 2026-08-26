from pydantic import BaseModel
from typing import Optional, Any, Dict, List
from uuid import UUID
from datetime import datetime


class VerifiedLoanOut(BaseModel):
    id: UUID
    loan_id: str
    loan_record_id: UUID
    upload_id: Optional[UUID] = None
    canonical_data: Dict[str, Any]
    source_file: Optional[str] = None
    source_row: Optional[int] = None
    data_lineage: Optional[Dict[str, Any]] = None
    validation_summary: Optional[Dict[str, Any]] = None
    exception_count: int
    verified_by: UUID
    verified_at: datetime
    record_hash: str
    hash_algorithm: str
    is_hash_valid: bool
    status: str
    notes: Optional[str] = None
    export_count: int

    class Config:
        from_attributes = True


class VerifiedLoanListOut(BaseModel):
    items: List[VerifiedLoanOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class VerifyLoanRequest(BaseModel):
    exception_id: UUID
    reviewer_note: Optional[str] = None
