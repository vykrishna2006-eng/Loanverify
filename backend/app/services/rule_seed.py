"""Seed built-in validation rules when the table is empty (create_all does not run init.sql)."""
from sqlalchemy.orm import Session

from app.models.validation import ValidationRule

SYSTEM_RULES = [
    {
        "rule_id": "R001",
        "name": "Required Fields",
        "description": "Loan ID, borrower ID, principal, and dates must be present",
        "category": "REQUIRED_FIELD",
        "severity": "HIGH",
        "rule_expression": "loan_id IS NOT NULL AND original_principal IS NOT NULL",
        "rule_fn_name": "rule_required_fields",
    },
    {
        "rule_id": "R002",
        "name": "Valid Origination Date",
        "description": "Origination date must be a valid past date",
        "category": "DATE",
        "severity": "HIGH",
        "rule_expression": "origination_date <= TODAY()",
        "rule_fn_name": "rule_valid_origination_date",
    },
    {
        "rule_id": "R003",
        "name": "Valid Maturity Date",
        "description": "Maturity date must be after origination date",
        "category": "DATE",
        "severity": "HIGH",
        "rule_expression": "maturity_date > origination_date",
        "rule_fn_name": "rule_valid_maturity_date",
    },
    {
        "rule_id": "R004",
        "name": "No Negative Principal",
        "description": "Original principal must be greater than zero",
        "category": "FINANCIAL",
        "severity": "HIGH",
        "rule_expression": "original_principal > 0",
        "rule_fn_name": "rule_no_negative_principal",
    },
    {
        "rule_id": "R005",
        "name": "Valid Interest Rate",
        "description": "Interest rate must be between 0 and 50 percent",
        "category": "FINANCIAL",
        "severity": "HIGH",
        "rule_expression": "0 < interest_rate <= 50",
        "rule_fn_name": "rule_valid_interest_rate",
    },
    {
        "rule_id": "R006",
        "name": "Balance Does Not Exceed Principal",
        "description": "Current balance must not exceed original principal",
        "category": "FINANCIAL",
        "severity": "HIGH",
        "rule_expression": "current_balance <= original_principal",
        "rule_fn_name": "rule_balance_vs_principal",
    },
    {
        "rule_id": "R007",
        "name": "No Invalid Balance",
        "description": "Current balance must be >= 0",
        "category": "FINANCIAL",
        "severity": "HIGH",
        "rule_expression": "current_balance >= 0",
        "rule_fn_name": "rule_no_invalid_balance",
    },
    {
        "rule_id": "R008",
        "name": "Valid Payment Status",
        "description": "Payment status must be one of: CURRENT, DELINQUENT, DEFAULT, PAID_OFF, CLOSED",
        "category": "STATUS",
        "severity": "MEDIUM",
        "rule_expression": "payment_status IN (CURRENT,DELINQUENT,DEFAULT,PAID_OFF,CLOSED)",
        "rule_fn_name": "rule_valid_payment_status",
    },
    {
        "rule_id": "R009",
        "name": "Duplicate Loan Detection",
        "description": "Loan ID must be unique within the upload",
        "category": "DUPLICATE",
        "severity": "HIGH",
        "rule_expression": "COUNT(loan_id) = 1",
        "rule_fn_name": "rule_duplicate_detection",
    },
    {
        "rule_id": "R010",
        "name": "Document Status Present",
        "description": "Document status must not be missing",
        "category": "DOCUMENT",
        "severity": "MEDIUM",
        "rule_expression": "document_status IS NOT NULL",
        "rule_fn_name": "rule_document_status",
    },
    {
        "rule_id": "R011",
        "name": "Stale Record Detection",
        "description": "Records not updated in over 180 days are flagged as stale",
        "category": "DATE",
        "severity": "LOW",
        "rule_expression": "last_payment_date >= TODAY() - 180 days",
        "rule_fn_name": "rule_stale_record",
    },
    {
        "rule_id": "R012",
        "name": "Valid US State",
        "description": "Property state must be a valid 2-letter US state code",
        "category": "GEOGRAPHIC",
        "severity": "MEDIUM",
        "rule_expression": "property_state IN (valid_states)",
        "rule_fn_name": "rule_valid_state",
    },
    {
        "rule_id": "R013",
        "name": "Closed Account Positive Balance",
        "description": "Closed loans must have zero balance",
        "category": "STATUS",
        "severity": "HIGH",
        "rule_expression": "NOT (payment_status=CLOSED AND current_balance > 0)",
        "rule_fn_name": "rule_closed_positive_balance",
    },
    {
        "rule_id": "R014",
        "name": "Payment Status vs DPD Conflict",
        "description": "CURRENT status loans must have 0 days past due",
        "category": "STATUS",
        "severity": "HIGH",
        "rule_expression": "NOT (payment_status=CURRENT AND days_past_due > 0)",
        "rule_fn_name": "rule_status_dpd_conflict",
    },
    {
        "rule_id": "R015",
        "name": "Suspicious Borrower Repetition",
        "description": "Same borrower ID on more than 5 loans in same upload",
        "category": "DUPLICATE",
        "severity": "MEDIUM",
        "rule_expression": "COUNT(borrower_id) <= 5",
        "rule_fn_name": "rule_borrower_repetition",
    },
    {
        "rule_id": "R016",
        "name": "Duplicate Borrower Combination",
        "description": "Same borrower + original principal + origination date must be unique",
        "category": "DUPLICATE",
        "severity": "HIGH",
        "rule_expression": "COUNT(borrower_id, original_principal, origination_date) = 1",
        "rule_fn_name": "rule_duplicate_borrower_combo",
    },
    {
        "rule_id": "R017",
        "name": "Cross-Source Conflict",
        "description": "Values must not conflict between loan_tape and servicer_update",
        "category": "CROSS_SOURCE",
        "severity": "HIGH",
        "rule_expression": "loan_tape.field = servicer_update.field",
        "rule_fn_name": "rule_cross_source_conflict",
    },
    {
        "rule_id": "R018",
        "name": "Invalid Date Format",
        "description": "Origination, maturity, and last-updated dates must be parseable",
        "category": "DATE",
        "severity": "HIGH",
        "rule_expression": "dates are valid ISO or US formats",
        "rule_fn_name": "rule_invalid_date_format",
    },
]


def seed_system_rules(db: Session) -> int:
    """Insert any missing SYSTEM rules. Does not overwrite user/AI rules or is_active."""
    existing = {r.rule_id for r in db.query(ValidationRule.rule_id).all()}
    added = 0
    for spec in SYSTEM_RULES:
        if spec["rule_id"] in existing:
            continue
        db.add(ValidationRule(
            **spec,
            is_active=True,
            source="SYSTEM",
        ))
        added += 1
    if added:
        db.commit()
    return added
