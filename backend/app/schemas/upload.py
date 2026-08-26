from pydantic import BaseModel
from typing import Optional, Any, Dict
from uuid import UUID
from datetime import datetime


class UploadOut(BaseModel):
    id: UUID
    filename: str
    original_filename: str
    file_size: Optional[int] = None
    source_type: str
    total_rows: int
    imported_rows: int
    failed_rows: int
    status: str
    error_summary: Optional[Dict[str, Any]] = None
    uploaded_by: Optional[UUID] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UploadSummary(BaseModel):
    upload_id: UUID
    filename: str
    total_rows: int
    imported_rows: int
    failed_rows: int
    validation_errors: int
    exceptions_created: int
    status: str
    failed_row_details: Optional[list] = []
