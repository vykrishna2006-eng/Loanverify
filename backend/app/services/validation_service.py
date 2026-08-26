"""
Module B — Validation Engine
Configurable rule engine. Each rule is a pure function returning None (pass) or ExceptionResult (fail).
Rules respect the is_active flag from the validation_rules table.
"""
from datetime import date, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Set
from collections import Counter
from sqlalchemy.orm import Session

from app.models.loan import LoanRecord
from app.models.validation import ValidationRule, ValidationResult
from app.models.exception import Exception as LoanException


# ─── Structured exception result ─────────────────────────────────────────────

class ExceptionResult:
    def __init__(self, loan_record_id, upload_id, loan_id, rule_id,
                 exception_type, severity, field_name, actual_value, expected_value, message):
        self.loan_record_id = loan_record_id
        self.upload_id      = upload_id
        self.loan_id        = loan_id
        self.rule_id        = rule_id
        self.exception_type = exception_type
        self.severity       = severity
        self.field_name     = field_name
        self.actual_value   = str(actual_value) if actual_value is not None else None
        self.expected_value = str(expected_value) if expected_value is not None else None
        self.message        = message


VALID_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
    "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
    "VA","WA","WV","WI","WY","DC","PR","GU","VI","AS","MP",
}
VALID_PAYMENT_STATUSES = {"CURRENT","DELINQUENT","DEFAULT","PAID_OFF","CLOSED","FORECLOSURE"}
STALE_THRESHOLD_DAYS   = 180
BORROWER_REPEAT_LIMIT  = 5


# ─── Rule functions (each tagged with its rule_id) ────────────────────────────

def rule_required_fields(loan: LoanRecord, upload_id) -> Optional[ExceptionResult]:
    """R001"""
    missing = []
    if not loan.loan_id:                  missing.append("loan_id")
    if loan.original_principal is None:   missing.append("original_principal")
    if loan.origination_date is None:     missing.append("origination_date")
    if not missing:
        return None
    return ExceptionResult(
        loan.id, upload_id, loan.loan_id or "UNKNOWN",
        "R001", "MISSING_REQUIRED_FIELDS", "HIGH",
        ",".join(missing), "NULL", "NOT NULL",
        f"Required field(s) missing: {', '.join(missing)}",
    )


def rule_valid_origination_date(loan: LoanRecord, upload_id) -> Optional[ExceptionResult]:
    """R002"""
    if loan.origination_date is None:
        return None
    if loan.origination_date > date.today():
        return ExceptionResult(
            loan.id, upload_id, loan.loan_id,
            "R002", "FUTURE_ORIGINATION_DATE", "HIGH",
            "origination_date", loan.origination_date, f"<= {date.today()}",
            f"Origination date {loan.origination_date} is in the future",
        )
    return None


def rule_valid_maturity_date(loan: LoanRecord, upload_id) -> Optional[ExceptionResult]:
    """R003"""
    if not loan.maturity_date or not loan.origination_date:
        return None
    if loan.maturity_date <= loan.origination_date:
        return ExceptionResult(
            loan.id, upload_id, loan.loan_id,
            "R003", "MATURITY_BEFORE_ORIGINATION", "HIGH",
            "maturity_date", loan.maturity_date, f"> {loan.origination_date}",
            f"Maturity {loan.maturity_date} must be after origination {loan.origination_date}",
        )
    return None


def rule_no_negative_principal(loan: LoanRecord, upload_id) -> Optional[ExceptionResult]:
    """R004"""
    if loan.original_principal is None:
        return None
    if loan.original_principal <= Decimal("0"):
        return ExceptionResult(
            loan.id, upload_id, loan.loan_id,
            "R004", "INVALID_PRINCIPAL", "HIGH",
            "original_principal", loan.original_principal, "> 0",
            f"Original principal {loan.original_principal} must be > 0",
        )
    return None


def rule_valid_interest_rate(loan: LoanRecord, upload_id) -> Optional[ExceptionResult]:
    """R005 — also catches decimal-fraction entry errors (0.065 instead of 6.5%)"""
    if loan.interest_rate is None:
        return None
    if loan.interest_rate <= Decimal("0") or loan.interest_rate > Decimal("50") or loan.interest_rate < Decimal("0.5"):
        return ExceptionResult(
            loan.id, upload_id, loan.loan_id,
            "R005", "INVALID_INTEREST_RATE", "HIGH",
            "interest_rate", loan.interest_rate, "0.5 <= rate <= 50 (%)",
            f"Interest rate {loan.interest_rate}% outside valid range (may be decimal fraction: e.g. 0.065 vs 6.5%)",
        )
    return None


def rule_balance_vs_principal(loan: LoanRecord, upload_id) -> Optional[ExceptionResult]:
    """R006"""
    if loan.current_balance is None or loan.original_principal is None:
        return None
    if loan.current_balance > loan.original_principal:
        return ExceptionResult(
            loan.id, upload_id, loan.loan_id,
            "R006", "BALANCE_GREATER_THAN_PRINCIPAL", "HIGH",
            "current_balance", loan.current_balance, f"<= {loan.original_principal}",
            f"Balance {loan.current_balance} exceeds original principal {loan.original_principal}",
        )
    return None


def rule_no_invalid_balance(loan: LoanRecord, upload_id) -> Optional[ExceptionResult]:
    """R007"""
    if loan.current_balance is None:
        return None
    if loan.current_balance < Decimal("0"):
        return ExceptionResult(
            loan.id, upload_id, loan.loan_id,
            "R007", "NEGATIVE_BALANCE", "HIGH",
            "current_balance", loan.current_balance, ">= 0",
            f"Current balance {loan.current_balance} cannot be negative",
        )
    return None


def rule_valid_payment_status(loan: LoanRecord, upload_id) -> Optional[ExceptionResult]:
    """R008"""
    if loan.payment_status is None:
        return ExceptionResult(
            loan.id, upload_id, loan.loan_id,
            "R008", "MISSING_PAYMENT_STATUS", "MEDIUM",
            "payment_status", None, str(VALID_PAYMENT_STATUSES),
            "Payment status is missing",
        )
    if loan.payment_status not in VALID_PAYMENT_STATUSES:
        return ExceptionResult(
            loan.id, upload_id, loan.loan_id,
            "R008", "INVALID_PAYMENT_STATUS", "MEDIUM",
            "payment_status", loan.payment_status, str(VALID_PAYMENT_STATUSES),
            f"Payment status '{loan.payment_status}' is not recognised",
        )
    return None


def rule_document_status(loan: LoanRecord, upload_id) -> Optional[ExceptionResult]:
    """R010"""
    if not loan.document_status:
        return ExceptionResult(
            loan.id, upload_id, loan.loan_id,
            "R010", "MISSING_DOCUMENT_STATUS", "MEDIUM",
            "document_status", None, "COMPLETE|INCOMPLETE|MISSING",
            "Document status is missing",
        )
    return None


def rule_stale_record(loan: LoanRecord, upload_id) -> Optional[ExceptionResult]:
    """R011 — checks last_updated_at first, falls back to last_payment_date"""
    stamp = getattr(loan, "last_updated_at", None) or loan.last_payment_date
    field = "last_updated_at" if getattr(loan, "last_updated_at", None) else "last_payment_date"
    if stamp is None:
        return None
    cutoff = date.today() - timedelta(days=STALE_THRESHOLD_DAYS)
    if stamp < cutoff:
        return ExceptionResult(
            loan.id, upload_id, loan.loan_id,
            "R011", "STALE_RECORD", "LOW",
            field, stamp, f">= {cutoff} ({STALE_THRESHOLD_DAYS}d)",
            f"Record is stale — {field} was {stamp}, over {STALE_THRESHOLD_DAYS} days ago",
        )
    return None


def rule_valid_state(loan: LoanRecord, upload_id) -> Optional[ExceptionResult]:
    """R012 — checks borrower_state then property_state"""
    state = getattr(loan, "borrower_state", None) or loan.property_state
    field = "borrower_state" if getattr(loan, "borrower_state", None) else "property_state"
    if not state:
        return None
    if state not in VALID_STATES:
        return ExceptionResult(
            loan.id, upload_id, loan.loan_id,
            "R012", "INVALID_STATE", "MEDIUM",
            field, state, "Valid 2-letter US state code",
            f"State '{state}' is not a valid US state code",
        )
    return None


def rule_closed_positive_balance(loan: LoanRecord, upload_id) -> Optional[ExceptionResult]:
    """R013"""
    if loan.payment_status == "CLOSED" and loan.current_balance and loan.current_balance > Decimal("0"):
        return ExceptionResult(
            loan.id, upload_id, loan.loan_id,
            "R013", "CLOSED_WITH_POSITIVE_BALANCE", "HIGH",
            "current_balance", loan.current_balance, "0 (loan is CLOSED)",
            f"Loan is CLOSED but has positive balance {loan.current_balance}",
        )
    return None


def rule_status_dpd_conflict(loan: LoanRecord, upload_id) -> Optional[ExceptionResult]:
    """R014"""
    if loan.payment_status == "CURRENT" and loan.days_past_due and loan.days_past_due > 0:
        return ExceptionResult(
            loan.id, upload_id, loan.loan_id,
            "R014", "STATUS_DPD_CONFLICT", "HIGH",
            "days_past_due", f"status=CURRENT, DPD={loan.days_past_due}", "DPD=0 for CURRENT",
            f"Payment status is CURRENT but DPD is {loan.days_past_due}",
        )
    return None


def rule_invalid_date_format(loan: LoanRecord, upload_id) -> Optional[ExceptionResult]:
    """R018"""
    errors = getattr(loan, "parse_errors", None) or {}
    if not errors:
        return None
    fields = ", ".join(errors.keys())
    return ExceptionResult(
        loan.id, upload_id, loan.loan_id or "UNKNOWN",
        "R018", "INVALID_DATE_FORMAT", "HIGH",
        fields, str(errors), "ISO YYYY-MM-DD or US MM/DD/YYYY",
        f"Invalid date format on field(s): {fields}",
    )


# ─── Batch rules (need the full loan list) ────────────────────────────────────

def rule_duplicate_detection(loans: List[LoanRecord], upload_id) -> List[ExceptionResult]:
    """R009 — duplicate loan_id within upload"""
    results, counts, seen = [], Counter(l.loan_id for l in loans if l.loan_id), set()
    for loan in loans:
        if loan.loan_id in counts and counts[loan.loan_id] > 1 and loan.loan_id not in seen:
            seen.add(loan.loan_id)
            results.append(ExceptionResult(
                loan.id, upload_id, loan.loan_id,
                "R009", "DUPLICATE_LOAN_ID", "HIGH",
                "loan_id", f"{loan.loan_id} × {counts[loan.loan_id]}", "unique",
                f"Loan ID {loan.loan_id} appears {counts[loan.loan_id]} times",
            ))
    return results


def rule_borrower_repetition(loans: List[LoanRecord], upload_id) -> List[ExceptionResult]:
    """R015 — same borrower_id on > BORROWER_REPEAT_LIMIT loans"""
    results, counts, seen = [], Counter(l.borrower_id for l in loans if l.borrower_id), set()
    for loan in loans:
        if loan.borrower_id and counts[loan.borrower_id] > BORROWER_REPEAT_LIMIT and loan.borrower_id not in seen:
            seen.add(loan.borrower_id)
            results.append(ExceptionResult(
                loan.id, upload_id, loan.loan_id,
                "R015", "SUSPICIOUS_BORROWER_REPETITION", "MEDIUM",
                "borrower_id", f"{loan.borrower_id} × {counts[loan.borrower_id]}", f"<= {BORROWER_REPEAT_LIMIT}",
                f"Borrower {loan.borrower_id} appears {counts[loan.borrower_id]} times",
            ))
    return results


def rule_duplicate_borrower_combo(loans: List[LoanRecord], upload_id) -> List[ExceptionResult]:
    """R016 — duplicate borrower + principal + origination_date combination"""
    results, key_counts, seen = [], Counter(), set()
    for l in loans:
        k = (l.borrower_id, str(l.original_principal), str(l.origination_date))
        if l.borrower_id:
            key_counts[k] += 1
    for loan in loans:
        k = (loan.borrower_id, str(loan.original_principal), str(loan.origination_date))
        if k in key_counts and key_counts[k] > 1 and k not in seen:
            seen.add(k)
            results.append(ExceptionResult(
                loan.id, upload_id, loan.loan_id,
                "R016", "DUPLICATE_BORROWER_COMBO", "HIGH",
                "borrower_id,original_principal,origination_date",
                f"{k} × {key_counts[k]}", "unique combination",
                f"Borrower {loan.borrower_id} with principal {loan.original_principal} "
                f"and origination {loan.origination_date} repeated {key_counts[k]} times",
            ))
    return results


def rule_cross_source_conflict(db: Session, loans: List[LoanRecord], upload_id) -> List[ExceptionResult]:
    """R017 — conflicting values between loan_tape and servicer_update for same loan_id"""
    from app.models.upload import Upload
    results = []
    compare_fields = ["current_balance","payment_status","days_past_due",
                      "last_payment_date","document_status","servicer_name"]
    upload = db.query(Upload).filter(Upload.id == str(upload_id)).first()
    if not upload:
        return results
    source = (upload.source_type or "LOAN_TAPE").upper()
    other_type = "LOAN_TAPE" if source == "SERVICER_UPDATE" else "SERVICER_UPDATE"
    other_uploads = db.query(Upload).filter(Upload.source_type == other_type).all()
    if not other_uploads:
        return results
    other_ids = [u.id for u in other_uploads]
    others = {r.loan_id: r for r in db.query(LoanRecord).filter(LoanRecord.upload_id.in_(other_ids)).all()}
    for loan in loans:
        other = others.get(loan.loan_id)
        if not other:
            continue
        conflicts = [
            f"{f}: {getattr(loan,f)} vs {getattr(other,f)}"
            for f in compare_fields
            if getattr(loan, f) is not None and getattr(other, f) is not None
            and str(getattr(loan, f)) != str(getattr(other, f))
        ]
        if conflicts:
            results.append(ExceptionResult(
                loan.id, upload_id, loan.loan_id,
                "R017", "CROSS_SOURCE_CONFLICT", "HIGH",
                "cross_source", "; ".join(conflicts), f"{other_type} agrees",
                f"Conflicting values vs {other_type}: " + "; ".join(conflicts),
            ))
    return results


# ─── Rule registry — maps rule_id → function for is_active checking ───────────

SINGLE_RECORD_RULE_MAP: Dict[str, Any] = {
    "R001": rule_required_fields,
    "R002": rule_valid_origination_date,
    "R003": rule_valid_maturity_date,
    "R004": rule_no_negative_principal,
    "R005": rule_valid_interest_rate,
    "R006": rule_balance_vs_principal,
    "R007": rule_no_invalid_balance,
    "R008": rule_valid_payment_status,
    "R010": rule_document_status,
    "R011": rule_stale_record,
    "R012": rule_valid_state,
    "R013": rule_closed_positive_balance,
    "R014": rule_status_dpd_conflict,
    "R018": rule_invalid_date_format,
}

BATCH_RULE_MAP: Dict[str, Any] = {
    "R009": rule_duplicate_detection,
    "R015": rule_borrower_repetition,
    "R016": rule_duplicate_borrower_combo,
    "R017": rule_cross_source_conflict,
}


def _get_active_rule_ids(db: Session) -> Set[str]:
    """Query DB for rules where is_active=True. Falls back to ALL rules if table is empty."""
    rows = db.query(ValidationRule.rule_id).filter(ValidationRule.is_active == True).all()
    if not rows:
        # Fallback: if no rules seeded yet, run everything
        return set(list(SINGLE_RECORD_RULE_MAP.keys()) + list(BATCH_RULE_MAP.keys()))
    return {r.rule_id for r in rows}


# ─── Main validation runner ───────────────────────────────────────────────────

def run_validation(db: Session, upload_id, active_rule_ids=None) -> Dict[str, Any]:
    """
    Run all ACTIVE validation rules against every LoanRecord in the upload.
    Respects the is_active flag in validation_rules table.
    Bulk-inserts ValidationResults and LoanExceptions.
    """
    loans: List[LoanRecord] = (
        db.query(LoanRecord)
        .filter(LoanRecord.upload_id == str(upload_id))
        .all()
    )
    if not loans:
        return {"total": 0, "passed": 0, "failed": 0, "exceptions": 0}

    # ── Determine which rules are active ─────────────────────────────────────
    active_ids: Set[str] = active_rule_ids or _get_active_rule_ids(db)

    all_exceptions: List[ExceptionResult] = []
    validation_results: List[Dict] = []

    # ── Per-record rules ──────────────────────────────────────────────────────
    for loan in loans:
        for rule_id, rule_fn in SINGLE_RECORD_RULE_MAP.items():
            if rule_id not in active_ids:
                continue                          # respect is_active flag
            exc = rule_fn(loan, upload_id)
            passed = exc is None
            validation_results.append({
                "loan_record_id": str(loan.id),
                "upload_id":      str(upload_id),
                "rule_id":        rule_id,
                "passed":         passed,
            })
            if exc:
                all_exceptions.append(exc)

    # ── Batch rules ───────────────────────────────────────────────────────────
    for rule_id, rule_fn in BATCH_RULE_MAP.items():
        if rule_id not in active_ids:
            continue
        if rule_id == "R017":
            batch = rule_fn(db, loans, upload_id)
        else:
            batch = rule_fn(loans, upload_id)
        all_exceptions.extend(batch)

    # ── Bulk insert ValidationResults ─────────────────────────────────────────
    if validation_results:
        db.bulk_insert_mappings(ValidationResult, validation_results)

    # ── Bulk insert Exceptions ────────────────────────────────────────────────
    if all_exceptions:
        db.bulk_insert_mappings(LoanException, [
            {
                "loan_record_id": str(e.loan_record_id),
                "upload_id":      str(e.upload_id),
                "loan_id":        e.loan_id,
                "rule_id":        e.rule_id,
                "exception_type": e.exception_type,
                "severity":       e.severity,
                "field_name":     e.field_name,
                "actual_value":   e.actual_value,
                "expected_value": e.expected_value,
                "message":        e.message,
                "status":         "OPEN",
            }
            for e in all_exceptions
        ])

    total              = len(loans)
    exception_count    = len(all_exceptions)
    loans_with_excs    = len({e.loan_id for e in all_exceptions})

    return {
        "total":    total,
        "passed":   total - loans_with_excs,
        "failed":   loans_with_excs,
        "exceptions": exception_count,
        "severity_breakdown": {
            "HIGH":   sum(1 for e in all_exceptions if e.severity == "HIGH"),
            "MEDIUM": sum(1 for e in all_exceptions if e.severity == "MEDIUM"),
            "LOW":    sum(1 for e in all_exceptions if e.severity == "LOW"),
        },
        "rule_breakdown": dict(Counter(e.rule_id for e in all_exceptions)),
    }


def compute_data_quality_score(db: Session, upload_id) -> Dict[str, Any]:
    """Transparent Data Quality Score from validation results."""
    total = db.query(ValidationResult).filter(ValidationResult.upload_id == str(upload_id)).count()
    if total == 0:
        return {"overall": 0.0, "categories": {}}

    passed = db.query(ValidationResult).filter(
        ValidationResult.upload_id == str(upload_id),
        ValidationResult.passed == True,
    ).count()

    categories = {
        "Required Fields":       ["R001"],
        "Date Quality":          ["R002", "R003", "R011", "R018"],
        "Financial Integrity":   ["R004", "R005", "R006", "R007"],
        "Status Consistency":    ["R008", "R013", "R014"],
        "Document Completeness": ["R010"],
        "Duplicate Detection":   ["R009", "R015", "R016"],
        "Geographic Validity":   ["R012"],
        "Cross-Source":          ["R017"],
    }
    cat_scores = {}
    for name, rule_ids in categories.items():
        ct = db.query(ValidationResult).filter(
            ValidationResult.upload_id == str(upload_id),
            ValidationResult.rule_id.in_(rule_ids),
        ).count()
        if ct > 0:
            cp = db.query(ValidationResult).filter(
                ValidationResult.upload_id == str(upload_id),
                ValidationResult.rule_id.in_(rule_ids),
                ValidationResult.passed == True,
            ).count()
            cat_scores[name] = round((cp / ct) * 100, 1)

    return {"overall": round((passed / total) * 100, 1), "categories": cat_scores}
