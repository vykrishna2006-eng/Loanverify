"""After a human decision, leftover issues (e.g. stale) must surface next."""
from datetime import date, timedelta
from uuid import uuid4

from app.models.exception import Exception as LoanException
from app.services.validation_service import revalidate_loan_after_review
from tests.conftest import auth_headers


def _open_exception(loan, rule_id, exception_type, severity, field, actual, message):
    return LoanException(
        id=str(uuid4()),
        loan_record_id=str(loan.id),
        upload_id=str(loan.upload_id),
        loan_id=loan.loan_id,
        rule_id=rule_id,
        exception_type=exception_type,
        severity=severity,
        field_name=field,
        actual_value=actual,
        expected_value="see rule",
        message=message,
        status="OPEN",
    )


def test_revalidate_creates_stale_after_other_rule_resolved(db, sample_loan_record):
    loan = sample_loan_record["loan"]
    loan.borrower_state = "XX"
    loan.last_payment_date = date.today() - timedelta(days=200)
    db.flush()

    state_exc = _open_exception(
        loan, "R012", "INVALID_STATE", "MEDIUM", "borrower_state", "XX", "Invalid state"
    )
    state_exc.status = "RESOLVED"
    db.add(state_exc)
    db.flush()

    remaining = revalidate_loan_after_review(db, loan)
    types = {e.exception_type for e in remaining}
    assert "STALE_RECORD" in types
    assert "INVALID_STATE" not in types


def test_revalidate_does_not_reopen_waived_rule(db, sample_loan_record):
    loan = sample_loan_record["loan"]
    loan.borrower_state = "XX"
    loan.last_payment_date = date.today()
    db.flush()

    state_exc = _open_exception(
        loan, "R012", "INVALID_STATE", "MEDIUM", "borrower_state", "XX", "Invalid state"
    )
    state_exc.status = "RESOLVED"
    db.add(state_exc)
    db.flush()

    remaining = revalidate_loan_after_review(db, loan)
    assert remaining == []


def test_decision_returns_next_issue_then_verifies(client, db, reviewer_token, sample_loan_record):
    loan = sample_loan_record["loan"]
    loan.payment_status = "PENDING"
    loan.last_payment_date = date.today() - timedelta(days=220)
    db.flush()

    payment_exc = _open_exception(
        loan, "R008", "INVALID_PAYMENT_STATUS", "MEDIUM",
        "payment_status", "PENDING", "Invalid payment status",
    )
    db.add(payment_exc)
    db.commit()

    headers = auth_headers(reviewer_token)
    first = client.post(
        f"/api/exceptions/{payment_exc.id}/decision",
        json={"decision": "APPROVED", "reviewer_note": "status confirmed with servicer"},
        headers=headers,
    )
    assert first.status_code == 200, first.text
    body = first.json()
    assert body["verified"] is False
    assert body["next_exception_id"]
    assert body["remaining_count"] >= 1
    assert any(e["exception_type"] == "STALE_RECORD" for e in body["remaining_exceptions"])

    stale_id = body["next_exception_id"]
    second = client.post(
        f"/api/exceptions/{stale_id}/decision",
        json={"decision": "APPROVED", "reviewer_note": "stale record acknowledged"},
        headers=headers,
    )
    assert second.status_code == 200, second.text
    assert second.json()["verified"] is True
    assert second.json()["next_exception_id"] is None

    listed = client.get("/api/verified-loans", headers=headers)
    assert listed.status_code == 200
    ids = [item["loan_id"] for item in listed.json()["items"]]
    assert loan.loan_id in ids
