"""
Module F — Audit Trail Service
Works with both SQLAlchemy User (legacy) and MongoUser (new auth system).
Actor can be any object with .id and .email attributes.
"""
from typing import Optional, Any, Dict
from sqlalchemy.orm import Session
from app.models.audit import AuditEvent


class AuditEventType:
    FILE_UPLOADED               = "FILE_UPLOADED"
    RECORDS_IMPORTED            = "RECORDS_IMPORTED"
    VALIDATION_EXECUTED         = "VALIDATION_EXECUTED"
    EXCEPTION_CREATED           = "EXCEPTION_CREATED"
    EXCEPTION_UPDATED           = "EXCEPTION_UPDATED"
    AI_RECOMMENDATION_GENERATED = "AI_RECOMMENDATION_GENERATED"
    BATCH_SUMMARY_GENERATED     = "BATCH_SUMMARY_GENERATED"
    REVIEWER_COMMENT_ADDED      = "REVIEWER_COMMENT_ADDED"
    FIELD_EDITED                = "FIELD_EDITED"
    LOAN_APPROVED               = "LOAN_APPROVED"
    LOAN_REJECTED               = "LOAN_REJECTED"
    LOAN_ESCALATED              = "LOAN_ESCALATED"
    CORRECTION_REQUESTED        = "CORRECTION_REQUESTED"
    EXCEPTION_ASSIGNED          = "EXCEPTION_ASSIGNED"
    VERIFIED_RECORD_CREATED     = "VERIFIED_RECORD_CREATED"
    RECORD_EXPORTED             = "RECORD_EXPORTED"
    HASH_VERIFIED               = "HASH_VERIFIED"
    HASH_MISMATCH               = "HASH_MISMATCH"
    USER_LOGIN                  = "USER_LOGIN"
    RULE_CREATED                = "RULE_CREATED"
    RULE_ACTIVATED              = "RULE_ACTIVATED"
    RULE_DEACTIVATED            = "RULE_DEACTIVATED"


def _extract_actor(actor) -> tuple:
    """
    Extract (actor_id, actor_email) from either:
    - MongoUser  (has .id and .email)
    - SQLAlchemy User (has .id and .email)
    - None
    """
    if actor is None:
        return None, None
    actor_id    = str(getattr(actor, "id",    None) or "")
    actor_email = str(getattr(actor, "email", None) or "")
    return actor_id or None, actor_email or None


def log_event(
    db: Session,
    event_type: str,
    actor=None,                               # MongoUser OR SQLAlchemy User OR None
    loan_id: Optional[str] = None,
    upload_id=None,
    exception_id=None,
    old_value: Optional[Dict[str, Any]] = None,
    new_value: Optional[Dict[str, Any]] = None,
    reason: Optional[str] = None,
    ai_involved: bool = False,
    ai_metadata: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> AuditEvent:
    """Create and persist an audit event. Caller must commit the session."""
    actor_id, actor_email = _extract_actor(actor)

    event = AuditEvent(
        event_type     = event_type,
        actor_id       = actor_id,
        actor_email    = actor_email,
        loan_id        = loan_id,
        upload_id      = str(upload_id)    if upload_id    else None,
        exception_id   = str(exception_id) if exception_id else None,
        old_value      = old_value,
        new_value      = new_value,
        reason         = reason,
        ai_involved    = ai_involved,
        ai_metadata    = ai_metadata,
        extra_metadata = metadata,
        ip_address     = ip_address,
        user_agent     = user_agent,
    )
    db.add(event)
    db.flush()
    return event
