"""Module E — Verified Loan Records Router"""
import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.auth import get_current_user, require_reviewer_only
from app.models.verified_loan import VerifiedLoan
from app.models.loan import LoanRecord
from app.models.mongo_user import MongoUser as User
from app.services import audit_service, verification_service
from app.services.audit_service import AuditEventType

router = APIRouter()


@router.get("", summary="List verified loan records")
def list_verified_loans(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(VerifiedLoan)
    if search:
        q = q.filter(or_(
            VerifiedLoan.loan_id.ilike(f"%{search}%"),
            VerifiedLoan.source_file.ilike(f"%{search}%"),
        ))
    if status:
        q = q.filter(VerifiedLoan.status == status.upper())

    total = q.count()
    items = q.order_by(VerifiedLoan.verified_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "items": [_to_dict(v, db) for v in items],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": math.ceil(total / page_size) if total > 0 else 0,
    }


@router.get("/{loan_id}", summary="Get verified loan by loan_id")
def get_verified_loan(
    loan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    vl = db.query(VerifiedLoan).filter(VerifiedLoan.loan_id == loan_id).first()
    if not vl:
        raise HTTPException(status_code=404, detail=f"No verified record for loan {loan_id}")
    return _to_dict(vl, db)


@router.post("", summary="Manually verify a loan record")
def verify_loan_manual(
    loan_id: str = Query(..., description="The loan_id string to verify"),
    reviewer_note: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_reviewer_only),
):
    """
    Manually create a verified record for any loan_id.
    Works for both clean loans (no exceptions) and loans with resolved exceptions.
    Does NOT require an exception_id — fixes the gap where clean loans couldn't be verified.
    """
    loan = db.query(LoanRecord).filter(LoanRecord.loan_id == loan_id).first()
    if not loan:
        raise HTTPException(status_code=404, detail=f"Loan {loan_id} not found")

    vl = verification_service.verify_loan(
        db=db,
        loan_record_id=str(loan.id),
        verifier=current_user,
        reviewer_note=reviewer_note,
    )
    audit_service.log_event(
        db=db,
        event_type=AuditEventType.VERIFIED_RECORD_CREATED,
        actor=current_user,
        loan_id=vl.loan_id,
        new_value={"record_hash": vl.record_hash, "hash_algorithm": vl.hash_algorithm},
    )
    db.commit()
    return _to_dict(vl, db)


@router.get("/{loan_id}/verify-hash", summary="Re-compute SHA-256 and check for tampering")
def verify_hash(
    loan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    vl = db.query(VerifiedLoan).filter(VerifiedLoan.loan_id == loan_id).first()
    if not vl:
        raise HTTPException(status_code=404, detail=f"No verified record for loan {loan_id}")

    is_valid     = verification_service.verify_hash(vl)
    vl.is_hash_valid = is_valid

    audit_service.log_event(
        db=db,
        event_type=AuditEventType.HASH_VERIFIED if is_valid else AuditEventType.HASH_MISMATCH,
        actor=current_user,
        loan_id=loan_id,
        new_value={"is_valid": is_valid, "stored_hash": vl.record_hash},
    )
    db.commit()

    return {
        "loan_id":        loan_id,
        "stored_hash":    vl.record_hash,
        "is_valid":       is_valid,
        "hash_algorithm": vl.hash_algorithm,
        "message": (
            "Record integrity verified — data has not been modified since verification."
            if is_valid else
            "⚠️ HASH MISMATCH — verified record may have been tampered with after verification!"
        ),
    }


@router.post("/{loan_id}/export", summary="Export a verified loan record")
def export_verified_loan(
    loan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    vl = db.query(VerifiedLoan).filter(VerifiedLoan.loan_id == loan_id).first()
    if not vl:
        raise HTTPException(status_code=404, detail=f"No verified record for loan {loan_id}")

    from datetime import datetime
    vl.export_count = (vl.export_count or 0) + 1
    vl.exported_at  = datetime.utcnow()

    audit_service.log_event(
        db=db,
        event_type=AuditEventType.RECORD_EXPORTED,
        actor=current_user,
        loan_id=loan_id,
        new_value={"export_count": vl.export_count, "exported_at": vl.exported_at.isoformat()},
    )
    db.commit()

    return {
        "loan_id":        vl.loan_id,
        "canonical_data": vl.canonical_data,
        "data_lineage":   vl.data_lineage,
        "validation_summary": vl.validation_summary,
        "record_hash":    vl.record_hash,
        "hash_algorithm": vl.hash_algorithm,
        "verified_by":    str(vl.verified_by),
        "verified_at":    vl.verified_at.isoformat() if vl.verified_at else None,
        "status":         vl.status,
        "exception_count": vl.exception_count,
        "ai_recommendation_ids":  vl.ai_recommendation_ids,
        "reviewer_decision_ids":  vl.reviewer_decision_ids,
        "exported_at":    vl.exported_at.isoformat(),
    }


# ─── Helper ───────────────────────────────────────────────────────────────────

def _to_dict(vl: VerifiedLoan, db: Session) -> dict:
    """Serialize VerifiedLoan including resolved verified_by user name."""
    verified_by_name = None
    if vl.verified_by:
        user = db.query(__import__("app.models.user", fromlist=["User"]).User).filter_by(
            id=str(vl.verified_by)
        ).first()
        verified_by_name = user.full_name if user else None

    return {
        "id":              vl.id,
        "loan_id":         vl.loan_id,
        "loan_record_id":  vl.loan_record_id,
        "upload_id":       vl.upload_id,
        "canonical_data":  vl.canonical_data,
        "source_file":     vl.source_file,
        "source_row":      vl.source_row,
        "data_lineage":    vl.data_lineage,
        "validation_summary": vl.validation_summary,
        "exception_count": vl.exception_count,
        "ai_recommendation_ids": vl.ai_recommendation_ids or [],
        "reviewer_decision_ids": vl.reviewer_decision_ids or [],
        "verified_by":     str(vl.verified_by) if vl.verified_by else None,
        "verified_by_name": verified_by_name,           # ← resolved name
        "verified_at":     vl.verified_at.isoformat() if vl.verified_at else None,
        "record_hash":     vl.record_hash,
        "hash_algorithm":  vl.hash_algorithm,
        "is_hash_valid":   vl.is_hash_valid,
        "status":          vl.status,
        "notes":           vl.notes,
        "export_count":    vl.export_count,
        "exported_at":     vl.exported_at.isoformat() if vl.exported_at else None,
    }
