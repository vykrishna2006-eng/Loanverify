"""Module C — Exception Queue Router"""
import math
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.database import get_db
from app.auth import get_current_user
from app.models.exception import Exception as LoanException, ExceptionComment
from app.models.loan import LoanRecord
from app.models.mongo_user import MongoUser as User
from app.schemas.exception import ExceptionOut, ExceptionListOut, CommentCreate, DecisionCreate
from app.services import audit_service, ai_service
from app.services.audit_service import AuditEventType

router = APIRouter()


# ─── Editable loan fields allowed by reviewers ───────────────────────────────
EDITABLE_FIELDS = {
    "current_balance", "payment_status", "days_past_due",
    "interest_rate", "original_principal", "document_status",
    "servicer_name", "origination_date", "maturity_date",
    "last_payment_date", "borrower_state", "property_state",
}


@router.get("", response_model=ExceptionListOut, summary="List exceptions with filters")
def list_exceptions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    severity: Optional[str] = None,
    status: Optional[str] = None,
    exception_type: Optional[str] = None,
    upload_id: Optional[str] = None,
    loan_id: Optional[str] = None,
    borrower_id: Optional[str] = None,
    assigned_to: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Exception queue with server-side filtering and pagination.
    Supports filter by severity, status, exception_type, loan_id, borrower_id.
    Includes severity summary counts.
    """
    q = db.query(LoanException)

    if severity:
        q = q.filter(LoanException.severity == severity.upper())
    if status:
        q = q.filter(LoanException.status == status.upper())
    if exception_type:
        q = q.filter(LoanException.exception_type == exception_type)
    if upload_id:
        q = q.filter(LoanException.upload_id == upload_id)
    if loan_id:
        q = q.filter(LoanException.loan_id.ilike(f"%{loan_id}%"))
    if assigned_to:
        q = q.filter(LoanException.assigned_to == assigned_to)
    if borrower_id:
        # join to LoanRecord to filter by borrower_id
        matching = [
            r.loan_id for r in db.query(LoanRecord.loan_id)
            .filter(LoanRecord.borrower_id.ilike(f"%{borrower_id}%"))
            .distinct().all()
        ]
        if matching:
            q = q.filter(LoanException.loan_id.in_(matching))
        else:
            q = q.filter(False)
    if search:
        matching_loan_ids = [
            r.loan_id for r in db.query(LoanRecord.loan_id).filter(
                or_(
                    LoanRecord.loan_id.ilike(f"%{search}%"),
                    LoanRecord.borrower_id.ilike(f"%{search}%"),
                    LoanRecord.borrower_name.ilike(f"%{search}%"),
                )
            ).distinct().all()
        ]
        q = q.filter(or_(
            LoanException.loan_id.ilike(f"%{search}%"),
            LoanException.message.ilike(f"%{search}%"),
            LoanException.exception_type.ilike(f"%{search}%"),
            LoanException.loan_id.in_(matching_loan_ids) if matching_loan_ids else False,
        ))

    total = q.count()
    items = q.order_by(
        LoanException.severity.desc(),
        LoanException.created_at.desc()
    ).offset((page - 1) * page_size).limit(page_size).all()

    # Global summary counts (not filtered — shows full queue state)
    summary_rows = db.query(
        LoanException.severity,
        func.count(LoanException.id).label("count")
    ).group_by(LoanException.severity).all()
    summary = {row.severity: row.count for row in summary_rows}
    summary["total"] = sum(summary.values())

    return ExceptionListOut(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
        summary=summary,
    )


@router.get("/types", summary="List all distinct exception types in the system")
def list_exception_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns distinct exception_type values — used to populate the filter dropdown."""
    rows = db.query(LoanException.exception_type).distinct().order_by(LoanException.exception_type).all()
    return [r.exception_type for r in rows if r.exception_type]


@router.get("/{exception_id}", summary="Get full exception detail")
def get_exception(
    exception_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exc = db.query(LoanException).filter(LoanException.id == exception_id).first()
    if not exc:
        raise HTTPException(status_code=404, detail="Exception not found")

    from app.models.ai import AIRecommendation
    from app.models.review import ReviewDecision

    ai_rec   = db.query(AIRecommendation).filter(AIRecommendation.exception_id == exception_id).first()
    # Return ALL review decisions (full history), ordered oldest-first
    decisions = (
        db.query(ReviewDecision)
        .filter(ReviewDecision.exception_id == exception_id)
        .order_by(ReviewDecision.created_at.asc())
        .all()
    )
    comments = (
        db.query(ExceptionComment)
        .filter(ExceptionComment.exception_id == exception_id)
        .order_by(ExceptionComment.created_at.asc())
        .all()
    )
    # Loan record for field-edit context
    loan = db.query(LoanRecord).filter(LoanRecord.id == exc.loan_record_id).first()

    return {
        "exception": ExceptionOut.model_validate(exc),
        "loan": {
            "id": str(loan.id) if loan else None,
            "loan_id": loan.loan_id if loan else None,
            "borrower_id": loan.borrower_id if loan else None,
            "borrower_name": loan.borrower_name if loan else None,
            "current_balance": float(loan.current_balance) if loan and loan.current_balance else None,
            "payment_status": loan.payment_status if loan else None,
        } if loan else None,
        "ai_recommendation": {
            "id": str(ai_rec.id),
            "explanation": ai_rec.explanation,
            "suggested_value": ai_rec.suggested_value,
            "suggested_action": ai_rec.suggested_action,
            "confidence_score": float(ai_rec.confidence_score) if ai_rec.confidence_score else None,
            "severity_reason": ai_rec.severity_reason,
            "generated_note": ai_rec.generated_note,
            "model_used": ai_rec.model_used,
            "prompt_text": ai_rec.prompt_text,
            "created_at": ai_rec.created_at.isoformat() if ai_rec.created_at else None,
        } if ai_rec else None,
        # Full history, not just latest
        "review_history": [
            {
                "id": str(d.id),
                "decision": d.decision,
                "reviewer_id": str(d.reviewer_id),
                "reviewer_name": d.reviewer.full_name if d.reviewer else None,
                "original_value": d.original_value,
                "corrected_value": d.corrected_value,
                "reviewer_note": d.reviewer_note,
                "ai_decision_followed": d.ai_decision_followed,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in decisions
        ],
        "review_decision": {         # most-recent decision for convenience
            "id": str(decisions[-1].id),
            "decision": decisions[-1].decision,
            "corrected_value": decisions[-1].corrected_value,
            "reviewer_note": decisions[-1].reviewer_note,
            "ai_decision_followed": decisions[-1].ai_decision_followed,
            "created_at": decisions[-1].created_at.isoformat() if decisions[-1].created_at else None,
        } if decisions else None,
        "comments": [
            {
                "id": str(c.id),
                "comment": c.comment,
                "author_id": str(c.author_id),
                "author_name": c.author.full_name if c.author else None,
                "created_at": c.created_at.isoformat(),
            }
            for c in comments
        ],
    }


@router.post("/{exception_id}/comment", summary="Add a comment to an exception")
def add_comment(
    exception_id: str,
    body: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exc = db.query(LoanException).filter(LoanException.id == exception_id).first()
    if not exc:
        raise HTTPException(status_code=404, detail="Exception not found")

    comment = ExceptionComment(
        exception_id=exc.id,
        author_id=current_user.id,
        comment=body.comment,
    )
    db.add(comment)

    audit_service.log_event(
        db=db,
        event_type=AuditEventType.REVIEWER_COMMENT_ADDED,
        actor=current_user,
        loan_id=exc.loan_id,
        exception_id=exc.id,
        new_value={"comment": body.comment},
    )
    db.commit()
    db.refresh(comment)
    return {
        "id": str(comment.id),
        "exception_id": exception_id,
        "comment": comment.comment,
        "author_id": str(current_user.id),
        "author_name": current_user.full_name,
        "created_at": comment.created_at.isoformat(),
    }


@router.post("/{exception_id}/ai-review", summary="Generate AI recommendation for an exception")
def generate_ai_review(
    exception_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Module D Feature 1+2+5: Generates explanation, suggested correction, severity reason.
    AI output is stored as a RECOMMENDATION ONLY — never applied directly to DB.
    Human reviewer must accept/edit/reject.
    """
    from app.models.ai import AIRecommendation

    exc = db.query(LoanException).filter(LoanException.id == exception_id).first()
    if not exc:
        raise HTTPException(status_code=404, detail="Exception not found")

    # Delete previous recommendation if regenerating
    existing = db.query(AIRecommendation).filter(AIRecommendation.exception_id == exception_id).first()
    if existing:
        db.delete(existing)
        db.flush()

    exception_data = {
        "loan_id":        exc.loan_id,
        "exception_type": exc.exception_type,
        "field_name":     exc.field_name,
        "actual_value":   exc.actual_value,
        "expected_value": exc.expected_value,
        "message":        exc.message,
        "severity":       exc.severity,
        "rule_id":        exc.rule_id,
    }

    ai_result  = ai_service.explain_exception(exception_data)
    parsed     = ai_result.get("parsed", {})
    sev_info   = ai_service.classify_severity(exc.exception_type, exc.field_name or "", exc.actual_value)

    rec = AIRecommendation(
        exception_id      = exc.id,
        loan_id           = exc.loan_id,
        explanation       = parsed.get("explanation"),
        suggested_value   = parsed.get("suggested_value"),
        suggested_action  = parsed.get("suggested_action", "FLAG_FOR_REVIEW"),
        confidence_score  = parsed.get("confidence_score", 70.0),
        severity_reason   = parsed.get("severity_reason") or sev_info.get("reason"),
        generated_note    = parsed.get("generated_note"),
        model_used        = ai_result.get("model"),
        prompt_text       = ai_result.get("prompt"),
        prompt_tokens     = ai_result.get("prompt_tokens"),
        completion_tokens = ai_result.get("completion_tokens"),
        latency_ms        = ai_result.get("latency_ms"),
    )
    db.add(rec)
    exc.status = "IN_REVIEW"

    audit_service.log_event(
        db=db,
        event_type=AuditEventType.AI_RECOMMENDATION_GENERATED,
        actor=current_user,
        loan_id=exc.loan_id,
        exception_id=exc.id,
        ai_involved=True,
        ai_metadata={
            "model":            ai_result.get("model"),
            "confidence":       parsed.get("confidence_score"),
            "suggested_action": parsed.get("suggested_action"),
            "prompt_tokens":    ai_result.get("prompt_tokens"),
        },
    )
    db.commit()
    db.refresh(rec)

    return {
        "recommendation_id": str(rec.id),
        "loan_id":           rec.loan_id,
        "explanation":       rec.explanation,
        "suggested_value":   rec.suggested_value,
        "suggested_action":  rec.suggested_action,
        "confidence_score":  float(rec.confidence_score) if rec.confidence_score else None,
        "severity_reason":   rec.severity_reason,
        "generated_note":    rec.generated_note,
        "model_used":        rec.model_used,
        "prompt_text":       rec.prompt_text,
        "created_at":        rec.created_at.isoformat() if rec.created_at else None,
        # Explicit safety notice — required by Section 9 of PDF
        "ai_safety_note": (
            "AI RECOMMENDATION ONLY — no data has been changed. "
            "A human reviewer must Accept, Edit, or Reject before any changes are applied."
        ),
    }


@router.post("/{exception_id}/decision", summary="Submit a human review decision")
def submit_decision(
    exception_id: str,
    body: DecisionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Human-in-the-Loop decision gate (Section 9 of PDF).

    Decisions:
    - APPROVED          — exception is resolved; loan is correct
    - REJECTED          — exception is invalid; no change needed
    - EDITED            — reviewer applies a corrected value to the loan field
    - ESCALATED         — needs senior review
    - REQUEST_CORRECTION — data needs to come from source

    When EDITED: corrected_value is written to the loan record and logged in the audit trail.
    AI is NEVER allowed to call this endpoint.
    """
    from app.models.review import ReviewDecision
    from app.models.ai import AIRecommendation
    from decimal import Decimal

    exc = db.query(LoanException).filter(LoanException.id == exception_id).first()
    if not exc:
        raise HTTPException(status_code=404, detail="Exception not found")

    decision_upper = body.decision.upper()
    valid = {"APPROVED", "REJECTED", "EDITED", "ESCALATED", "REQUEST_CORRECTION"}
    if decision_upper not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid decision. Must be one of: {valid}")

    if decision_upper == "EDITED" and not body.corrected_value:
        raise HTTPException(status_code=400, detail="corrected_value is required when decision is EDITED")

    ai_rec = db.query(AIRecommendation).filter(AIRecommendation.exception_id == exception_id).first()

    # ── Task 3: PRESERVE HISTORY — never delete old decisions ────────────────
    # Each call appends a new ReviewDecision row. Full history is queryable.
    old_value_snapshot = exc.actual_value

    decision_row = ReviewDecision(
        exception_id         = exc.id,
        ai_recommendation_id = str(ai_rec.id) if ai_rec else None,
        reviewer_id          = current_user.id,
        decision             = decision_upper,
        ai_decision_followed = body.ai_decision_followed,
        original_value       = old_value_snapshot,
        corrected_value      = body.corrected_value,
        reviewer_note        = body.reviewer_note,
    )
    db.add(decision_row)

    # ── Task 2: EDITED — write corrected_value back to the loan record ───────
    field_written = None
    if decision_upper == "EDITED" and exc.field_name and body.corrected_value:
        loan = db.query(LoanRecord).filter(LoanRecord.id == exc.loan_record_id).first()
        if loan and exc.field_name in EDITABLE_FIELDS:
            field_written = exc.field_name
            new_val = body.corrected_value
            # Type-cast based on field
            try:
                if exc.field_name in {"current_balance", "original_principal", "interest_rate"}:
                    new_val = Decimal(str(body.corrected_value).replace(",", "").replace("$", ""))
                elif exc.field_name in {"days_past_due"}:
                    new_val = int(body.corrected_value)
                elif exc.field_name in {"origination_date", "maturity_date", "last_payment_date"}:
                    from datetime import date
                    new_val = date.fromisoformat(str(body.corrected_value)[:10])
                elif exc.field_name in {"payment_status", "document_status", "borrower_state", "property_state"}:
                    new_val = str(body.corrected_value).strip().upper()
            except (ValueError, TypeError):
                new_val = body.corrected_value  # store as string if cast fails

            setattr(loan, exc.field_name, new_val)

            # Also update actual_value on the exception to reflect the correction
            exc.actual_value = str(new_val)

            audit_service.log_event(
                db=db,
                event_type=AuditEventType.FIELD_EDITED,
                actor=current_user,
                loan_id=exc.loan_id,
                exception_id=exc.id,
                old_value={exc.field_name: old_value_snapshot},
                new_value={exc.field_name: str(new_val)},
                reason=body.reviewer_note or "Corrected via exception review",
            )

    # ── Update exception status ───────────────────────────────────────────────
    if decision_upper in ("APPROVED", "REJECTED", "EDITED"):
        exc.status      = "RESOLVED"
        exc.resolved_at = datetime.utcnow()
    elif decision_upper == "ESCALATED":
        exc.status = "IN_REVIEW"
    elif decision_upper == "REQUEST_CORRECTION":
        exc.status = "OPEN"

    # ── Map decision to audit event type ─────────────────────────────────────
    event_map = {
        "APPROVED":           AuditEventType.LOAN_APPROVED,
        "REJECTED":           AuditEventType.LOAN_REJECTED,
        "EDITED":             AuditEventType.LOAN_APPROVED,      # edit+approve in one step
        "ESCALATED":          AuditEventType.LOAN_ESCALATED,
        "REQUEST_CORRECTION": AuditEventType.CORRECTION_REQUESTED,
    }

    audit_service.log_event(
        db=db,
        event_type=event_map.get(decision_upper, AuditEventType.LOAN_APPROVED),
        actor=current_user,
        loan_id=exc.loan_id,
        exception_id=exc.id,
        old_value={"status": "IN_REVIEW", "value": old_value_snapshot},
        new_value={"decision": decision_upper, "corrected_value": body.corrected_value, "field": field_written},
        reason=body.reviewer_note,
        ai_involved=ai_rec is not None,
        ai_metadata={"ai_followed": body.ai_decision_followed} if ai_rec else None,
    )

    # ── Auto-verify when all exceptions for this loan are resolved ────────────
    if decision_upper in ("APPROVED", "EDITED"):
        _try_auto_verify(db, exc.loan_record_id, current_user, body.reviewer_note)

    db.commit()

    return {
        "decision":         decision_upper,
        "exception_id":     exception_id,
        "loan_id":          exc.loan_id,
        "reviewer":         current_user.full_name,
        "field_updated":    field_written,
        "corrected_value":  body.corrected_value,
        "message":          f"Decision '{decision_upper}' recorded successfully.",
        "verified":         decision_upper in ("APPROVED", "EDITED"),
    }


def _try_auto_verify(db, loan_record_id, verifier: User, note: str = None):
    """Auto-create verified record when ALL exceptions for this loan are resolved."""
    try:
        from app.services.verification_service import verify_loan

        open_count = db.query(LoanException).filter(
            LoanException.loan_record_id == str(loan_record_id),
            LoanException.status.in_(["OPEN", "IN_REVIEW"]),
        ).count()

        if open_count == 0:
            vl = verify_loan(db, str(loan_record_id), verifier, note)
            audit_service.log_event(
                db=db,
                event_type=AuditEventType.VERIFIED_RECORD_CREATED,
                actor=verifier,
                loan_id=vl.loan_id,
                new_value={
                    "record_hash": vl.record_hash,
                    "verified_at": vl.verified_at.isoformat() if vl.verified_at else None,
                },
            )
    except Exception as e:
        print(f"Auto-verify warning: {e}")


@router.post("/{exception_id}/assign", summary="Assign exception to a reviewer")
def assign_exception(
    exception_id: str,
    assignee_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exc = db.query(LoanException).filter(LoanException.id == exception_id).first()
    if not exc:
        raise HTTPException(status_code=404, detail="Exception not found")

    exc.assigned_to = assignee_id
    audit_service.log_event(
        db=db,
        event_type=AuditEventType.EXCEPTION_ASSIGNED,
        actor=current_user,
        loan_id=exc.loan_id,
        exception_id=exc.id,
        new_value={"assigned_to": assignee_id},
    )
    db.commit()
    return {"message": "Assigned successfully", "exception_id": exception_id, "assigned_to": assignee_id}
