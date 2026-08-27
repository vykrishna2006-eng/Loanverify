"""Loans Router — GET /loans, GET /loans/:id, PATCH /loans/:id (Module H + Module C edit)"""
import math
from decimal import Decimal
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.auth import get_current_user
from app.models.loan import LoanRecord
from app.models.mongo_user import MongoUser as User
from app.schemas.loan import LoanRecordOut, LoanListOut

router = APIRouter()

EDITABLE_FIELDS = {
    "current_balance", "original_principal", "interest_rate", "monthly_payment",
    "payment_status", "days_past_due", "document_status",
    "origination_date", "maturity_date", "last_payment_date", "next_payment_date",
    "borrower_state", "property_state", "servicer_name", "loan_type", "loan_purpose",
    "lien_position", "borrower_name", "co_borrower_name",
}


@router.get("", response_model=LoanListOut, summary="List all loan records (Module H: GET /loans)")
def list_loans(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    upload_id: Optional[str] = None,
    search: Optional[str] = None,
    payment_status: Optional[str] = None,
    property_state: Optional[str] = None,
    is_duplicate: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(LoanRecord)
    if upload_id:
        q = q.filter(LoanRecord.upload_id == upload_id)
    if search:
        q = q.filter(or_(
            LoanRecord.loan_id.ilike(f"%{search}%"),
            LoanRecord.borrower_id.ilike(f"%{search}%"),
            LoanRecord.borrower_name.ilike(f"%{search}%"),
            LoanRecord.servicer_name.ilike(f"%{search}%"),
        ))
    if payment_status:
        q = q.filter(LoanRecord.payment_status == payment_status.upper())
    if property_state:
        q = q.filter(LoanRecord.property_state == property_state.upper())
    if is_duplicate is not None:
        q = q.filter(LoanRecord.is_duplicate == is_duplicate)

    total = q.count()
    items = q.order_by(LoanRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return LoanListOut(
        items=items, total=total, page=page, page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/{loan_id}", summary="Get a loan record by loan_id (Module H: GET /loans/:id)")
def get_loan(
    loan_id: str,
    include_exceptions: bool = Query(False, description="Include the exception list for this loan"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the loan record. Set include_exceptions=true to also get the exception list
    for this loan — enabling navigation from Loans page → Exception Queue.
    """
    loan = db.query(LoanRecord).filter(LoanRecord.loan_id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail=f"Loan {loan_id} not found")

    result = LoanRecordOut.model_validate(loan).model_dump()

    if include_exceptions:
        from app.models.exception import Exception as LoanException
        exceptions = (
            db.query(LoanException)
            .filter(LoanException.loan_record_id == str(loan.id))
            .order_by(LoanException.severity.desc(), LoanException.created_at.desc())
            .all()
        )
        result["exceptions"] = [
            {
                "id":             str(e.id),
                "rule_id":        e.rule_id,
                "exception_type": e.exception_type,
                "severity":       e.severity,
                "status":         e.status,
                "field_name":     e.field_name,
                "actual_value":   e.actual_value,
                "message":        e.message,
            }
            for e in exceptions
        ]
        result["exception_count"] = len(exceptions)

    return result


@router.patch("/{loan_id}", summary="Edit an allowed loan field — REVIEWER only (Module C)")
def edit_loan_field(
    loan_id: str,
    field_name: str = Query(..., description="Field to edit"),
    new_value: str = Query(..., description="New value (will be type-cast)"),
    reason: Optional[str] = Query(None, description="Reason for edit (logged in audit trail)"),
    db: Session = Depends(get_db),
    # Role-restricted: only REVIEWERs may edit loan fields directly
    current_user: User = Depends(get_current_user),
):
    """
    Edit an allowed field on a loan record.
    Role-restricted to REVIEWER only.
    Every edit is logged in the audit trail with old value, new value, and reason.
    """
    from app.services import audit_service
    from app.services.audit_service import AuditEventType

    loan = db.query(LoanRecord).filter(LoanRecord.loan_id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail=f"Loan {loan_id} not found")
    if field_name not in EDITABLE_FIELDS:
        raise HTTPException(status_code=400, detail=f"Field '{field_name}' is not editable. Allowed: {sorted(EDITABLE_FIELDS)}")

    old = getattr(loan, field_name, None)
    typed = new_value
    try:
        if field_name in {"current_balance", "original_principal", "interest_rate", "monthly_payment"}:
            typed = Decimal(new_value.replace(",", "").replace("$", ""))
        elif field_name in {"days_past_due"}:
            typed = int(new_value)
        elif field_name in {"origination_date", "maturity_date", "last_payment_date", "next_payment_date"}:
            typed = date.fromisoformat(new_value[:10])
        elif field_name in {"payment_status", "document_status", "borrower_state", "property_state"}:
            typed = new_value.strip().upper()
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=400, detail=f"Cannot convert '{new_value}' for field '{field_name}': {e}")

    setattr(loan, field_name, typed)

    audit_service.log_event(
        db=db,
        event_type=AuditEventType.FIELD_EDITED,
        actor=current_user,
        loan_id=loan.loan_id,
        upload_id=loan.upload_id,
        old_value={field_name: str(old)},
        new_value={field_name: str(typed)},
        reason=reason or "Direct field edit by reviewer",
    )
    db.commit()
    db.refresh(loan)
    return {"loan_id": loan_id, "field_name": field_name, "old_value": str(old), "new_value": str(typed)}
