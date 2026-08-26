"""Module F — Audit Trail Router"""
import math
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.audit import AuditEvent
from app.models.mongo_user import MongoUser as User
from app.schemas.audit import AuditEventOut, AuditListOut

router = APIRouter()


@router.get("", response_model=AuditListOut, summary="List all audit events")
def list_audit_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    loan_id: Optional[str] = None,
    event_type: Optional[str] = None,
    upload_id: Optional[str] = None,
    actor_email: Optional[str] = None,
    ai_involved: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(AuditEvent)
    if loan_id:
        q = q.filter(AuditEvent.loan_id.ilike(f"%{loan_id}%"))
    if event_type:
        q = q.filter(AuditEvent.event_type == event_type)
    if upload_id:
        q = q.filter(AuditEvent.upload_id == upload_id)
    if actor_email:
        q = q.filter(AuditEvent.actor_email.ilike(f"%{actor_email}%"))
    if ai_involved is not None:
        q = q.filter(AuditEvent.ai_involved == ai_involved)

    total = q.count()
    items = q.order_by(AuditEvent.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return AuditListOut(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/loan/{loan_id}", summary="Get full audit trail for a specific loan")
def get_loan_audit(
    loan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns the complete chronological audit trail for a loan. Required by Module H: GET /audit/:loanId"""
    events = (
        db.query(AuditEvent)
        .filter(AuditEvent.loan_id == loan_id)
        .order_by(AuditEvent.created_at.asc())
        .all()
    )
    return {
        "loan_id": loan_id,
        "event_count": len(events),
        "events": [AuditEventOut.model_validate(e) for e in events],
    }


@router.get("/event-types", summary="Get list of all audit event types")
def get_event_types():
    from app.services.audit_service import AuditEventType
    return {
        "event_types": [v for k, v in vars(AuditEventType).items() if not k.startswith("_")]
    }
