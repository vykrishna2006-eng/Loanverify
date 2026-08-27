"""Module D — AI Assistant Router (all 7 AI features)"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models.mongo_user import MongoUser as User
from app.schemas.ai import GenerateRuleRequest, GeneratedRuleOut, BatchSummaryOut
from app.services import ai_service, audit_service
from app.services.audit_service import AuditEventType

router = APIRouter()


def _resolve_exception(db: Session, identifier: str):
    from app.models.exception import Exception as LoanException
    cleaned = identifier.strip()
    # 1. Try exact match by exception UUID
    exc = db.query(LoanException).filter(LoanException.id == cleaned).first()
    if exc:
        return exc
    # 2. Try match by Loan ID (e.g. L001855)
    exc = db.query(LoanException).filter(LoanException.loan_id.ilike(cleaned)).first()
    return exc


@router.get("/recommendation/{exception_id}", summary="Get AI recommendation for an exception")
def get_recommendation(
    exception_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Feature 1+2: Get or generate AI explanation and suggestion by Exception UUID or Loan ID."""
    from app.models.ai import AIRecommendation
    from app.models.exception import Exception as LoanException

    exc = _resolve_exception(db, exception_id)
    if not exc:
        raise HTTPException(
            status_code=404,
            detail=f"No exception found for '{exception_id}'. Please enter a valid Exception UUID or Loan ID (e.g. L001855)."
        )

    rec = db.query(AIRecommendation).filter(AIRecommendation.exception_id == exc.id).first()
    if not rec:
        # Generate on-the-fly if not generated yet!
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
        ai_result = ai_service.explain_exception(exception_data)
        parsed    = ai_result.get("parsed", {})
        sev_info  = ai_service.classify_severity(exc.exception_type, exc.field_name or "", exc.actual_value)

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
            raw_response      = ai_result.get("raw"),
            prompt_tokens     = ai_result.get("prompt_tokens"),
            completion_tokens = ai_result.get("completion_tokens"),
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)

    return rec


@router.post("/compare-sources/{exception_id}", summary="Feature 3: Compare data sources")
def compare_sources(
    exception_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    **Feature 3 — Source Comparison**

    Compare loan tape vs servicer update values and get AI recommendation
    on which source to prefer.
    """
    from app.models.exception import Exception as LoanException
    from app.models.loan import LoanRecord

    exc = _resolve_exception(db, exception_id)
    if not exc:
        raise HTTPException(
            status_code=404,
            detail=f"No exception found for '{exception_id}'. Please enter a valid Exception UUID or Loan ID."
        )

    loan = db.query(LoanRecord).filter(LoanRecord.id == exc.loan_record_id).first()

    # Build source comparison from available data
    source_a = {
        "name": "Loan Tape",
        "field": exc.field_name,
        "value": exc.actual_value,
        "updated_date": loan.origination_date.isoformat() if loan and loan.origination_date else "unknown",
        "source_file": loan.upload_id if loan else None,
    }
    source_b = {
        "name": "Expected / Rule Criteria",
        "field": exc.field_name,
        "value": exc.expected_value,
        "updated_date": "rule-defined",
        "source_file": "validation_rules",
    }

    comparison = ai_service.compare_sources(
        {"loan_id": exc.loan_id, "exception_type": exc.exception_type},
        source_a,
        source_b,
    )

    return {
        "loan_id": exc.loan_id,
        "field": exc.field_name,
        "comparison": comparison,
        "ai_safety_note": "This is a comparison RECOMMENDATION. Human reviewer must decide.",
    }


@router.post("/generate-note/{exception_id}", summary="Feature 4: Generate reviewer note")
def generate_reviewer_note(
    exception_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    **Feature 4 — Auto-Generate Reviewer Note**

    AI drafts a professional reviewer note for the exception.
    The reviewer can accept, edit, or discard the generated note.
    """
    from app.models.exception import Exception as LoanException
    from app.models.ai import AIRecommendation

    exc = _resolve_exception(db, exception_id)
    if not exc:
        raise HTTPException(
            status_code=404,
            detail=f"No exception found for '{exception_id}'. Please enter a valid Exception UUID or Loan ID."
        )

    ai_rec = db.query(AIRecommendation).filter(AIRecommendation.exception_id == exc.id).first()

    if ai_rec and ai_rec.generated_note:
        note = ai_rec.generated_note
    else:
        note = (
            f"Reviewed {exc.exception_type.replace('_', ' ').lower()} exception on loan {exc.loan_id}. "
            f"Field '{exc.field_name}' had value {exc.actual_value} (expected: {exc.expected_value}). "
            f"Severity: {exc.severity}. Reviewed on behalf of {current_user.full_name}."
        )

    return {
        "generated_note": note,
        "ai_generated": True,
        "disclaimer": "This note was AI-generated. Please review and edit before saving.",
        "loan_id": exc.loan_id,
        "exception_id": exc.id,
    }


@router.post("/classify-severity/{exception_id}", summary="Feature 5: Classify exception severity")
def classify_severity(
    exception_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """**Feature 5 — Severity Classification**"""
    from app.models.exception import Exception as LoanException

    exc = _resolve_exception(db, exception_id)
    if not exc:
        raise HTTPException(
            status_code=404,
            detail=f"No exception found for '{exception_id}'. Please enter a valid Exception UUID or Loan ID."
        )

    result = ai_service.classify_severity(exc.exception_type, exc.field_name or "", exc.actual_value)
    return {
        "loan_id": exc.loan_id,
        "exception_type": exc.exception_type,
        **result,
    }


@router.post("/batch-summary", response_model=BatchSummaryOut, summary="Feature 6: Batch exception summary")
def batch_summary(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    **Feature 6 — Batch Summary**

    Generates a natural-language summary of all exceptions in an upload.
    Includes counts, most common issues, and actionable recommendations.
    """
    from app.models.exception import Exception as LoanException
    import uuid

    exceptions = db.query(LoanException).filter(
        LoanException.upload_id == uuid.UUID(upload_id)
    ).all()

    exc_dicts = [
        {
            "loan_id": e.loan_id,
            "exception_type": e.exception_type,
            "severity": e.severity,
            "field_name": e.field_name,
            "actual_value": e.actual_value,
        }
        for e in exceptions
    ]

    summary = ai_service.generate_batch_summary(exc_dicts)

    audit_service.log_event(
        db=db,
        event_type=AuditEventType.BATCH_SUMMARY_GENERATED,
        actor=current_user,
        upload_id=uuid.UUID(upload_id),
        ai_involved=True,
        ai_metadata={"total_exceptions": summary["total"]},
    )
    db.commit()

    return BatchSummaryOut(
        total_exceptions=summary["total"],
        high_severity=summary["high"],
        medium_severity=summary["medium"],
        low_severity=summary["low"],
        summary_text=summary["summary_text"],
        most_common_issue=summary["most_common_issue"],
        recommendations=summary["recommendations"],
    )


@router.post("/generate-rule", response_model=GeneratedRuleOut, summary="Feature 7: Generate validation rule from NL")
def generate_rule(
    body: GenerateRuleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    **Feature 7 — Natural-Language Rule Generation**

    Convert a plain-English description into a proposed validation rule.

    Example: "Flag loans where the balance is more than 90% of the original principal"

    **The generated rule is NEVER automatically activated.**
    It must be reviewed and explicitly activated by a human reviewer.
    """
    result = ai_service.generate_rule_from_description(body.description)
    return GeneratedRuleOut(
        rule_expression=result["rule_expression"],
        rule_name=result["rule_name"],
        description=result["description"],
        suggested_severity=result["suggested_severity"],
        explanation=result["explanation"],
        ai_generated=True,
    )
