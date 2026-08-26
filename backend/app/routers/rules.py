"""Validation Rules Router"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user, require_operator
from app.models.validation import ValidationRule
from app.models.mongo_user import MongoUser as User
from app.services import audit_service
from app.services.audit_service import AuditEventType

router = APIRouter()


@router.get("", summary="List all validation rules")
def list_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    rules = db.query(ValidationRule).order_by(ValidationRule.rule_id).all()
    return [
        {
            "id": str(r.id),
            "rule_id": r.rule_id,
            "name": r.name,
            "description": r.description,
            "category": r.category,
            "severity": r.severity,
            "is_active": r.is_active,
            "rule_expression": r.rule_expression,
            "source": r.source,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rules
    ]


@router.post("/{rule_id}/activate", summary="Activate a validation rule")
def activate_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator),
):
    rule = db.query(ValidationRule).filter(ValidationRule.rule_id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule.is_active = True
    audit_service.log_event(
        db=db, event_type=AuditEventType.RULE_ACTIVATED,
        actor=current_user, new_value={"rule_id": rule_id},
    )
    db.commit()
    return {"message": f"Rule {rule_id} activated", "rule_id": rule_id}


@router.post("/{rule_id}/deactivate", summary="Deactivate a validation rule")
def deactivate_rule(
    rule_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator),
):
    rule = db.query(ValidationRule).filter(ValidationRule.rule_id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule.is_active = False
    audit_service.log_event(
        db=db, event_type=AuditEventType.RULE_DEACTIVATED,
        actor=current_user, new_value={"rule_id": rule_id},
    )
    db.commit()
    return {"message": f"Rule {rule_id} deactivated", "rule_id": rule_id}


@router.post("/activate-ai-rule", summary="Activate an AI-generated rule (after human review)")
def activate_ai_rule(
    name: str,
    description: str,
    rule_expression: str,
    severity: str = "MEDIUM",
    db: Session = Depends(get_db),
    current_user: User = Depends(require_operator),
):
    """
    Human explicitly activates an AI-generated rule after reviewing it.
    AI-generated rules are NEVER auto-activated.
    """
    import uuid
    # Generate next rule ID
    count = db.query(ValidationRule).count()
    rule_id = f"R{count + 1:03d}"

    rule = ValidationRule(
        rule_id=rule_id,
        name=name,
        description=description,
        category="USER_DEFINED",
        severity=severity.upper(),
        is_active=True,
        rule_expression=rule_expression,
        source="AI_GENERATED",
        created_by=current_user.id,
    )
    db.add(rule)
    audit_service.log_event(
        db=db, event_type=AuditEventType.RULE_CREATED,
        actor=current_user,
        new_value={"rule_id": rule_id, "name": name, "source": "AI_GENERATED"},
    )
    db.commit()
    return {"message": "AI-generated rule activated after human review", "rule_id": rule_id}
