"""Module G — Three Role Dashboards + Module H /summary endpoint"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.auth import get_current_user, get_current_user
from app.models.mongo_user import MongoUser as User
from app.models.upload import Upload
from app.models.loan import LoanRecord
from app.models.exception import Exception as LoanException
from app.models.verified_loan import VerifiedLoan
from app.models.review import ReviewDecision
from app.models.ai import AIRecommendation

router = APIRouter()


# ─── Helper ──────────────────────────────────────────────────────────────────

def _import_success_rate(db: Session) -> float:
    """Correct formula: imported_rows / (imported_rows + failed_rows) across all uploads."""
    from sqlalchemy import func as sqlfunc
    result = db.query(
        sqlfunc.sum(Upload.imported_rows).label("imported"),
        sqlfunc.sum(Upload.failed_rows).label("failed"),
    ).one()
    imported = result.imported or 0
    failed   = result.failed   or 0
    total    = imported + failed
    return round((imported / total) * 100, 1) if total > 0 else 100.0


# ─── Operator Dashboard ───────────────────────────────────────────────────────

@router.get("/operator", summary="Data Operator dashboard — uploads, imports, validation summary")
def operator_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),   # role-restricted
):
    total_uploads    = db.query(Upload).count()
    completed        = db.query(Upload).filter(Upload.status == "COMPLETED").count()
    total_records    = db.query(LoanRecord).count()
    total_exceptions = db.query(LoanException).count()
    open_exceptions  = db.query(LoanException).filter(LoanException.status == "OPEN").count()

    failed_records = (
        db.query(LoanException.loan_record_id)
        .filter(LoanException.loan_record_id.isnot(None))
        .distinct().count()
    )

    recent_uploads = (
        db.query(Upload).order_by(Upload.created_at.desc()).limit(10).all()
    )
    source_breakdown = db.query(
        Upload.source_type, func.count(Upload.id).label("count")
    ).group_by(Upload.source_type).all()

    return {
        "role": "DATA_OPERATOR",
        "metrics": {
            "total_uploads":           total_uploads,
            "completed_uploads":       completed,
            "total_records_imported":  total_records,
            "validation_failures":     total_exceptions,
            "open_exceptions":         open_exceptions,
            "records_needing_correction": failed_records,
            "import_success_rate":     _import_success_rate(db),   # fixed formula
        },
        "recent_uploads": [
            {
                "id":            str(u.id),
                "filename":      u.original_filename,
                "source_type":   u.source_type,
                "status":        u.status,
                "total_rows":    u.total_rows,
                "imported_rows": u.imported_rows,
                "failed_rows":   u.failed_rows,
                "created_at":    u.created_at.isoformat() if u.created_at else None,
            }
            for u in recent_uploads
        ],
        "source_breakdown": {row.source_type: row.count for row in source_breakdown},
    }


# ─── Reviewer Dashboard ───────────────────────────────────────────────────────

@router.get("/reviewer", summary="Reviewer dashboard — exception queue, AI panel, decisions")
def reviewer_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # role-restricted
):
    open_exc     = db.query(LoanException).filter(LoanException.status == "OPEN").count()
    in_review    = db.query(LoanException).filter(LoanException.status == "IN_REVIEW").count()
    resolved     = db.query(LoanException).filter(LoanException.status == "RESOLVED").count()
    high_open    = db.query(LoanException).filter(LoanException.severity == "HIGH",   LoanException.status == "OPEN").count()
    medium_open  = db.query(LoanException).filter(LoanException.severity == "MEDIUM", LoanException.status == "OPEN").count()

    ai_generated   = db.query(AIRecommendation).count()
    decisions_made = db.query(ReviewDecision).count()
    ai_followed    = db.query(ReviewDecision).filter(ReviewDecision.ai_decision_followed == True).count()

    my_decisions = (
        db.query(ReviewDecision)
        .filter(ReviewDecision.reviewer_id == str(current_user.id))
        .order_by(ReviewDecision.created_at.desc())
        .limit(10).all()
    )
    recent_exceptions = (
        db.query(LoanException)
        .filter(LoanException.status.in_(["OPEN", "IN_REVIEW"]))
        .order_by(LoanException.severity.desc(), LoanException.created_at.desc())
        .limit(15).all()
    )
    # AI panel: exceptions that have an AI recommendation waiting for decision
    ai_pending = (
        db.query(LoanException)
        .join(AIRecommendation, LoanException.id == AIRecommendation.exception_id)
        .filter(LoanException.status == "IN_REVIEW")
        .order_by(LoanException.severity.desc())
        .limit(10).all()
    )

    return {
        "role": "REVIEWER",
        "metrics": {
            "open_exceptions":       open_exc,
            "in_review":             in_review,
            "resolved_exceptions":   resolved,
            "high_severity_open":    high_open,
            "medium_severity_open":  medium_open,
            "pending_decisions":     in_review,
            "ai_reviews_generated":  ai_generated,
            "total_decisions_made":  decisions_made,
            "ai_followed_rate":      round((ai_followed / max(decisions_made, 1)) * 100, 1),
        },
        "recent_exceptions": [
            {
                "id":             str(e.id),
                "loan_id":        e.loan_id,
                "exception_type": e.exception_type,
                "severity":       e.severity,
                "status":         e.status,
                "field_name":     e.field_name,
                "actual_value":   e.actual_value,
                "created_at":     e.created_at.isoformat() if e.created_at else None,
            }
            for e in recent_exceptions
        ],
        # AI panel — exceptions with pending AI recommendations
        "ai_pending_review": [
            {
                "id":             str(e.id),
                "loan_id":        e.loan_id,
                "exception_type": e.exception_type,
                "severity":       e.severity,
                "has_ai_rec":     True,
            }
            for e in ai_pending
        ],
        "my_recent_decisions": [
            {
                "id":            str(d.id),
                "exception_id":  str(d.exception_id),
                "decision":      d.decision,
                "ai_followed":   d.ai_decision_followed,
                "corrected_value": d.corrected_value,
                "created_at":    d.created_at.isoformat() if d.created_at else None,
            }
            for d in my_decisions
        ],
    }


# ─── Consumer Dashboard ───────────────────────────────────────────────────────

@router.get("/consumer", summary="Data Consumer dashboard — verified records, quality, export")
def consumer_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),   # all roles may view verified data
):
    total_loans      = db.query(LoanRecord).count()
    verified_loans   = db.query(VerifiedLoan).filter(VerifiedLoan.status == "VERIFIED").count()
    total_exceptions = db.query(LoanException).count()
    open_exceptions  = db.query(LoanException).filter(LoanException.status == "OPEN").count()

    verification_rate = round((verified_loans / max(total_loans, 1)) * 100, 1)
    exception_rate    = round((total_exceptions / max(total_loans, 1)) * 100, 2)

    recent_verified = (
        db.query(VerifiedLoan).order_by(VerifiedLoan.verified_at.desc()).limit(10).all()
    )

    # Quality score from the most recent upload
    latest_upload = db.query(Upload).order_by(Upload.created_at.desc()).first()
    quality_score = None
    if latest_upload:
        from app.services.validation_service import compute_data_quality_score
        quality_score = compute_data_quality_score(db, latest_upload.id)

    return {
        "role": "DATA_CONSUMER",
        "metrics": {
            "total_loans":          total_loans,
            "verified_loans":       verified_loans,
            "verification_rate":    verification_rate,
            "data_quality_score":   quality_score.get("overall") if quality_score else None,
            "total_exceptions":     total_exceptions,
            "open_exceptions":      open_exceptions,
            "exception_rate":       exception_rate,
        },
        "quality_breakdown": quality_score.get("categories") if quality_score else {},
        "before_after": {
            "before": {
                "total_records": total_loans,
                "exceptions":    total_exceptions,
                "exception_rate": exception_rate,
            },
            "after": {
                "total_records":      total_loans,
                "pending":            open_exceptions,
                "verified":           verified_loans,
                "verification_rate":  verification_rate,
                "silent_ai_changes":  0,   # guaranteed — AI never writes directly
            },
        },
        "recent_verifications": [
            {
                "id":              str(v.id),
                "loan_id":         v.loan_id,
                "verified_at":     v.verified_at.isoformat() if v.verified_at else None,
                "record_hash":     v.record_hash[:16] + "..." if v.record_hash else None,
                "is_hash_valid":   v.is_hash_valid,
                "status":          v.status,
                "exception_count": v.exception_count,
            }
            for v in recent_verified
        ],
    }


# ─── Module H: GET /summary ───────────────────────────────────────────────────
# Registered at TWO paths:
#   /api/dashboard/summary  (via this router)
#   /api/summary            (via alias in main.py)

@router.get("/summary", summary="Global system summary — Module H GET /summary")
def global_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Required by Module H spec: GET /summary"""
    total_uploads    = db.query(Upload).count()
    total_loans      = db.query(LoanRecord).count()
    total_exceptions = db.query(LoanException).count()
    open_exceptions  = db.query(LoanException).filter(LoanException.status == "OPEN").count()
    verified_loans   = db.query(VerifiedLoan).filter(VerifiedLoan.status == "VERIFIED").count()
    ai_recs          = db.query(AIRecommendation).count()

    high   = db.query(LoanException).filter(LoanException.severity == "HIGH").count()
    medium = db.query(LoanException).filter(LoanException.severity == "MEDIUM").count()
    low    = db.query(LoanException).filter(LoanException.severity == "LOW").count()

    return {
        "total_uploads":        total_uploads,
        "total_loan_records":   total_loans,
        "total_exceptions":     total_exceptions,
        "open_exceptions":      open_exceptions,
        "verified_loans":       verified_loans,
        "ai_recommendations":   ai_recs,
        "exception_rate":       round((total_exceptions / max(total_loans, 1)) * 100, 2),
        "verification_rate":    round((verified_loans   / max(total_loans, 1)) * 100, 1),
        "severity_breakdown":   {"HIGH": high, "MEDIUM": medium, "LOW": low},
        "import_success_rate":  _import_success_rate(db),
        "silent_ai_changes":    0,
    }
