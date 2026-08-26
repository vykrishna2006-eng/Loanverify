"""Exports Router"""
import csv
import io
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.verified_loan import VerifiedLoan
from app.models.exception import Exception as LoanException
from app.models.audit import AuditEvent
from app.models.mongo_user import MongoUser as User
from app.services import audit_service
from app.services.audit_service import AuditEventType

router = APIRouter()


@router.get("/verified-loans/csv", summary="Export verified loans as CSV")
def export_verified_loans_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    loans = db.query(VerifiedLoan).filter(VerifiedLoan.status == "VERIFIED").all()

    output = io.StringIO()
    fieldnames = [
        "loan_id", "borrower_id", "borrower_name", "loan_type",
        "original_principal", "current_balance", "interest_rate",
        "payment_status", "origination_date", "maturity_date",
        "property_state", "verified_at", "record_hash", "exception_count",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for loan in loans:
        cd = loan.canonical_data or {}
        writer.writerow({
            "loan_id": loan.loan_id,
            "borrower_id": cd.get("borrower_id", ""),
            "borrower_name": cd.get("borrower_name", ""),
            "loan_type": cd.get("loan_type", ""),
            "original_principal": cd.get("original_principal", ""),
            "current_balance": cd.get("current_balance", ""),
            "interest_rate": cd.get("interest_rate", ""),
            "payment_status": cd.get("payment_status", ""),
            "origination_date": cd.get("origination_date", ""),
            "maturity_date": cd.get("maturity_date", ""),
            "property_state": cd.get("property_state", ""),
            "verified_at": loan.verified_at.isoformat() if loan.verified_at else "",
            "record_hash": loan.record_hash,
            "exception_count": loan.exception_count,
        })

    audit_service.log_event(
        db=db, event_type=AuditEventType.RECORD_EXPORTED,
        actor=current_user,
        new_value={"type": "verified_loans_csv", "count": len(loans)},
    )
    db.commit()

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=verified_loans.csv"},
    )


@router.get("/audit/csv", summary="Export audit trail as CSV")
def export_audit_csv(
    loan_id: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(AuditEvent)
    if loan_id:
        q = q.filter(AuditEvent.loan_id == loan_id)
    events = q.order_by(AuditEvent.created_at.asc()).all()

    output = io.StringIO()
    fieldnames = ["created_at", "event_type", "actor_email", "loan_id", "reason", "ai_involved"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for e in events:
        writer.writerow({
            "created_at": e.created_at.isoformat() if e.created_at else "",
            "event_type": e.event_type,
            "actor_email": e.actor_email or "",
            "loan_id": e.loan_id or "",
            "reason": e.reason or "",
            "ai_involved": e.ai_involved,
        })

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_trail.csv"},
    )
