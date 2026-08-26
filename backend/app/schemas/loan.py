from pydantic import BaseModel
from typing import Optional, Any, Dict, List
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal


class LoanRecordOut(BaseModel):
    id: UUID
    upload_id: UUID
    source_row: Optional[int] = None
    loan_id: str
    borrower_id: Optional[str] = None
    borrower_name: Optional[str] = None
    co_borrower_name: Optional[str] = None
    loan_type: Optional[str] = None
    loan_purpose: Optional[str] = None
    property_state: Optional[str] = None
    borrower_state: Optional[str] = None
    property_zip: Optional[str] = None
    servicer_name: Optional[str] = None
    original_principal: Optional[Decimal] = None
    current_balance: Optional[Decimal] = None
    interest_rate: Optional[Decimal] = None
    monthly_payment: Optional[Decimal] = None
    term_months: Optional[int] = None
    origination_date: Optional[date] = None
    maturity_date: Optional[date] = None
    last_payment_date: Optional[date] = None
    next_payment_date: Optional[date] = None
    last_updated_at: Optional[date] = None
    payment_status: Optional[str] = None
    days_past_due: Optional[int] = None
    document_status: Optional[str] = None
    lien_position: Optional[str] = None
    credit_grade: Optional[str] = None
    employment_length: Optional[str] = None
    income_band: Optional[str] = None
    source_system: Optional[str] = None
    parse_errors: Optional[Dict[str, Any]] = None
    is_duplicate: bool
    duplicate_of: Optional[str] = None
    created_at: datetime
    raw_data: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class LoanFieldEdit(BaseModel):
    field_name: str
    new_value: str
    reason: Optional[str] = None


class LoanListOut(BaseModel):
    items: List[LoanRecordOut]
    total: int
    page: int
    page_size: int
    total_pages: int
