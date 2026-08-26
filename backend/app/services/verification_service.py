"""
Module E — Verified Loan Record Service
Canonical records with SHA-256 hash, field-level lineage, validation summary,
AI recommendation refs, and reviewer decision refs.
"""
import hashlib
import json
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.models.loan import LoanRecord
from app.models.exception import Exception as LoanException
from app.models.verified_loan import VerifiedLoan
from app.models.mongo_user import MongoUser as User
from app.models.upload import Upload


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        return super().default(obj)


def build_canonical_data(loan: LoanRecord) -> Dict[str, Any]:
    def _s(v):
        if isinstance(v, Decimal): return float(v)
        if hasattr(v, "isoformat"): return v.isoformat()
        return v
    return {
        "loan_id":            loan.loan_id,
        "borrower_id":        loan.borrower_id,
        "borrower_name":      loan.borrower_name,
        "co_borrower_name":   loan.co_borrower_name,
        "loan_type":          loan.loan_type,
        "loan_purpose":       loan.loan_purpose,
        "property_state":     loan.property_state,
        "property_zip":       loan.property_zip,
        "servicer_name":      loan.servicer_name,
        "original_principal": _s(loan.original_principal),
        "current_balance":    _s(loan.current_balance),
        "interest_rate":      _s(loan.interest_rate),
        "monthly_payment":    _s(loan.monthly_payment),
        "origination_date":   _s(loan.origination_date),
        "maturity_date":      _s(loan.maturity_date),
        "last_payment_date":  _s(loan.last_payment_date),
        "next_payment_date":  _s(loan.next_payment_date),
        "payment_status":     loan.payment_status,
        "days_past_due":      loan.days_past_due,
        "document_status":    loan.document_status,
        "lien_position":      loan.lien_position,
    }


def compute_record_hash(canonical_data: Dict[str, Any]) -> str:
    """SHA-256 of sort-key-ordered JSON. Deterministic regardless of insertion order."""
    serialized = json.dumps(canonical_data, sort_keys=True, cls=DecimalEncoder)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def build_data_lineage(loan: LoanRecord, upload: Optional[Upload]) -> Dict[str, Any]:
    """Field-level lineage: every canonical field traced to its source file + row."""
    source_file = upload.original_filename if upload else "unknown"
    source_row  = loan.source_row or "unknown"
    canonical   = build_canonical_data(loan)
    return {
        field: {
            "source":      upload.source_type if upload else "LOAN_TAPE",
            "source_file": source_file,
            "source_row":  source_row,
            "value":       value,
            "normalized":  True,
        }
        for field, value in canonical.items()
    }


def verify_loan(
    db: Session,
    loan_record_id: str,
    verifier: User,
    reviewer_note: Optional[str] = None,
) -> VerifiedLoan:
    """
    Create (or update) a verified loan record.
    Populates: canonical_data, record_hash, data_lineage, validation_summary,
               ai_recommendation_ids, reviewer_decision_ids.
    """
    loan = db.query(LoanRecord).filter(LoanRecord.id == str(loan_record_id)).first()
    if not loan:
        raise ValueError(f"LoanRecord {loan_record_id} not found")

    upload    = db.query(Upload).filter(Upload.id == str(loan.upload_id)).first()
    canonical = build_canonical_data(loan)
    rec_hash  = compute_record_hash(canonical)
    lineage   = build_data_lineage(loan, upload)

    # Count all exceptions for this loan
    exception_count = db.query(LoanException).filter(
        LoanException.loan_record_id == str(loan_record_id)
    ).count()

    # Collect AI recommendation IDs
    from app.models.ai import AIRecommendation
    ai_ids = [
        str(r.id)
        for r in db.query(AIRecommendation)
        .filter(AIRecommendation.loan_id == loan.loan_id).all()
    ]

    # Collect reviewer decision IDs
    from app.models.review import ReviewDecision
    exc_ids = [
        str(e.id) for e in db.query(LoanException).filter(
            LoanException.loan_record_id == str(loan_record_id)
        ).all()
    ]
    rd_ids = []
    if exc_ids:
        rd_ids = [
            str(d.id)
            for d in db.query(ReviewDecision)
            .filter(ReviewDecision.exception_id.in_(exc_ids)).all()
        ]

    # Validation summary (quality score)
    val_summary = None
    if upload:
        try:
            from app.services.validation_service import compute_data_quality_score
            val_summary = compute_data_quality_score(db, upload.id)
        except Exception:
            pass

    common = dict(
        canonical_data        = canonical,
        record_hash           = rec_hash,
        is_hash_valid         = True,
        data_lineage          = lineage,
        validation_summary    = val_summary,
        exception_count       = exception_count,
        ai_recommendation_ids = ai_ids,
        reviewer_decision_ids = rd_ids,
        verified_by           = str(verifier.id),
        verified_at           = datetime.utcnow(),
        notes                 = reviewer_note,
        status                = "VERIFIED",
        source_file           = upload.original_filename if upload else None,
        source_row            = loan.source_row,
    )

    existing = db.query(VerifiedLoan).filter(VerifiedLoan.loan_id == loan.loan_id).first()
    if existing:
        for k, v in common.items():
            setattr(existing, k, v)
        db.flush()
        return existing

    vl = VerifiedLoan(
        loan_id        = loan.loan_id,
        loan_record_id = str(loan.id),
        upload_id      = str(loan.upload_id) if loan.upload_id else None,
        hash_algorithm = "SHA-256",
        **common,
    )
    db.add(vl)
    db.flush()
    return vl


def verify_hash(verified_loan: VerifiedLoan) -> bool:
    """Re-compute SHA-256 and compare. Returns False if canonical_data was tampered."""
    recomputed = compute_record_hash(verified_loan.canonical_data)
    return recomputed == verified_loan.record_hash
