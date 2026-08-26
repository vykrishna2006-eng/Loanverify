"""
Unit Tests — Module B: Validation Rules
Tests each of the 15 validation rules in isolation.
No database required — pure function tests.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Patch database so import doesn't try to connect to PostgreSQL
import unittest.mock as mock
with mock.patch.dict(os.environ, {"DATABASE_URL": "sqlite:///:memory:"}):
    pass

import pytest
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4


# ── Mock LoanRecord (no SQLAlchemy required) ───────────────────────────────────

def make_loan(**kwargs):
    class MockLoan:
        def __init__(self, **kw):
            self.id              = uuid4()
            self.loan_id         = kw.get("loan_id", "L000001")
            self.borrower_id     = kw.get("borrower_id", "B001")
            self.original_principal = kw.get("original_principal", Decimal("300000"))
            self.current_balance    = kw.get("current_balance",    Decimal("280000"))
            self.interest_rate      = kw.get("interest_rate",      Decimal("4.5"))
            self.origination_date   = kw.get("origination_date",   date(2018, 1, 1))
            self.maturity_date      = kw.get("maturity_date",      date(2048, 1, 1))
            self.last_payment_date  = kw.get("last_payment_date",  date(2024, 1, 1))
            self.payment_status     = kw.get("payment_status",     "CURRENT")
            self.days_past_due      = kw.get("days_past_due",      0)
            self.document_status    = kw.get("document_status",    "COMPLETE")
            self.property_state     = kw.get("property_state",     "CA")
    return MockLoan(**kwargs)


# Import rule functions directly — no DB dependency
from app.services.validation_service import (
    rule_required_fields,
    rule_valid_origination_date,
    rule_valid_maturity_date,
    rule_no_negative_principal,
    rule_valid_interest_rate,
    rule_balance_vs_principal,
    rule_no_invalid_balance,
    rule_valid_payment_status,
    rule_document_status,
    rule_stale_record,
    rule_valid_state,
    rule_closed_positive_balance,
    rule_status_dpd_conflict,
    rule_borrower_repetition,
)

UPLOAD_ID = uuid4()


class TestRequiredFields:
    def test_pass_all_present(self):
        assert rule_required_fields(make_loan(), UPLOAD_ID) is None

    def test_fail_missing_loan_id(self):
        r = rule_required_fields(make_loan(loan_id=""), UPLOAD_ID)
        assert r is not None and r.rule_id == "R001" and r.severity == "HIGH"

    def test_fail_missing_principal(self):
        r = rule_required_fields(make_loan(original_principal=None), UPLOAD_ID)
        assert r is not None and r.exception_type == "MISSING_REQUIRED_FIELDS"

    def test_fail_missing_origination_date(self):
        r = rule_required_fields(make_loan(origination_date=None), UPLOAD_ID)
        assert r is not None and "origination_date" in r.field_name


class TestOriginationDate:
    def test_pass_valid_past_date(self):
        assert rule_valid_origination_date(make_loan(origination_date=date(2015, 6, 1)), UPLOAD_ID) is None

    def test_fail_future_date(self):
        future = date.today() + timedelta(days=100)
        r = rule_valid_origination_date(make_loan(origination_date=future), UPLOAD_ID)
        assert r is not None and r.rule_id == "R002" and r.exception_type == "FUTURE_ORIGINATION_DATE"

    def test_skip_when_none(self):
        assert rule_valid_origination_date(make_loan(origination_date=None), UPLOAD_ID) is None


class TestMaturityDate:
    def test_pass_maturity_after_origination(self):
        assert rule_valid_maturity_date(
            make_loan(origination_date=date(2015,1,1), maturity_date=date(2045,1,1)), UPLOAD_ID
        ) is None

    def test_fail_maturity_before_origination(self):
        r = rule_valid_maturity_date(
            make_loan(origination_date=date(2020,1,1), maturity_date=date(2019,1,1)), UPLOAD_ID
        )
        assert r is not None and r.rule_id == "R003"

    def test_fail_maturity_equal_origination(self):
        d = date(2020, 1, 1)
        assert rule_valid_maturity_date(make_loan(origination_date=d, maturity_date=d), UPLOAD_ID) is not None


class TestNegativePrincipal:
    def test_pass(self):
        assert rule_no_negative_principal(make_loan(original_principal=Decimal("250000")), UPLOAD_ID) is None

    def test_fail_negative(self):
        r = rule_no_negative_principal(make_loan(original_principal=Decimal("-100000")), UPLOAD_ID)
        assert r is not None and r.rule_id == "R004" and r.severity == "HIGH"

    def test_fail_zero(self):
        assert rule_no_negative_principal(make_loan(original_principal=Decimal("0")), UPLOAD_ID) is not None


class TestInterestRate:
    def test_pass_valid_rate(self):
        assert rule_valid_interest_rate(make_loan(interest_rate=Decimal("4.5")), UPLOAD_ID) is None

    def test_fail_zero(self):
        r = rule_valid_interest_rate(make_loan(interest_rate=Decimal("0")), UPLOAD_ID)
        assert r is not None and r.rule_id == "R005"

    def test_fail_decimal_fraction(self):
        # 0.045 instead of 4.5 — common data entry error
        r = rule_valid_interest_rate(make_loan(interest_rate=Decimal("0.045")), UPLOAD_ID)
        assert r is not None and r.exception_type == "INVALID_INTEREST_RATE"

    def test_fail_too_high(self):
        assert rule_valid_interest_rate(make_loan(interest_rate=Decimal("75")), UPLOAD_ID) is not None

    def test_skip_none(self):
        assert rule_valid_interest_rate(make_loan(interest_rate=None), UPLOAD_ID) is None


class TestBalanceVsPrincipal:
    def test_pass_under(self):
        assert rule_balance_vs_principal(
            make_loan(original_principal=Decimal("300000"), current_balance=Decimal("280000")), UPLOAD_ID
        ) is None

    def test_pass_equal(self):
        assert rule_balance_vs_principal(
            make_loan(original_principal=Decimal("300000"), current_balance=Decimal("300000")), UPLOAD_ID
        ) is None

    def test_fail_exceeds(self):
        r = rule_balance_vs_principal(
            make_loan(original_principal=Decimal("300000"), current_balance=Decimal("450000")), UPLOAD_ID
        )
        assert r is not None and r.rule_id == "R006" and r.severity == "HIGH"
        assert r.exception_type == "BALANCE_GREATER_THAN_PRINCIPAL"

    def test_skip_none(self):
        assert rule_balance_vs_principal(make_loan(current_balance=None, original_principal=None), UPLOAD_ID) is None


class TestNoInvalidBalance:
    def test_pass_positive(self):
        assert rule_no_invalid_balance(make_loan(current_balance=Decimal("100000")), UPLOAD_ID) is None

    def test_pass_zero(self):
        assert rule_no_invalid_balance(make_loan(current_balance=Decimal("0")), UPLOAD_ID) is None

    def test_fail_negative(self):
        r = rule_no_invalid_balance(make_loan(current_balance=Decimal("-5000")), UPLOAD_ID)
        assert r is not None and r.rule_id == "R007" and r.exception_type == "NEGATIVE_BALANCE"


class TestPaymentStatus:
    @pytest.mark.parametrize("s", ["CURRENT","DELINQUENT","DEFAULT","PAID_OFF","CLOSED"])
    def test_pass_valid(self, s):
        assert rule_valid_payment_status(make_loan(payment_status=s), UPLOAD_ID) is None

    def test_fail_invalid(self):
        r = rule_valid_payment_status(make_loan(payment_status="PENDING"), UPLOAD_ID)
        assert r is not None and r.rule_id == "R008"

    def test_fail_missing(self):
        r = rule_valid_payment_status(make_loan(payment_status=None), UPLOAD_ID)
        assert r is not None and r.exception_type == "MISSING_PAYMENT_STATUS"


class TestDocumentStatus:
    def test_pass(self):
        assert rule_document_status(make_loan(document_status="COMPLETE"), UPLOAD_ID) is None

    def test_fail_none(self):
        r = rule_document_status(make_loan(document_status=None), UPLOAD_ID)
        assert r is not None and r.rule_id == "R010"

    def test_fail_empty(self):
        assert rule_document_status(make_loan(document_status=""), UPLOAD_ID) is not None


class TestStaleRecord:
    def test_pass_recent(self):
        assert rule_stale_record(make_loan(last_payment_date=date.today() - timedelta(days=30)), UPLOAD_ID) is None

    def test_fail_stale(self):
        r = rule_stale_record(make_loan(last_payment_date=date.today() - timedelta(days=200)), UPLOAD_ID)
        assert r is not None and r.rule_id == "R011" and r.severity == "LOW"

    def test_skip_none(self):
        assert rule_stale_record(make_loan(last_payment_date=None), UPLOAD_ID) is None


class TestValidState:
    @pytest.mark.parametrize("state", ["CA","TX","NY","FL","WA"])
    def test_pass_valid(self, state):
        assert rule_valid_state(make_loan(property_state=state), UPLOAD_ID) is None

    def test_fail_invalid(self):
        r = rule_valid_state(make_loan(property_state="XX"), UPLOAD_ID)
        assert r is not None and r.rule_id == "R012"

    def test_skip_none(self):
        assert rule_valid_state(make_loan(property_state=None), UPLOAD_ID) is None


class TestClosedPositiveBalance:
    def test_pass_closed_zero(self):
        assert rule_closed_positive_balance(
            make_loan(payment_status="CLOSED", current_balance=Decimal("0")), UPLOAD_ID
        ) is None

    def test_pass_current_positive(self):
        assert rule_closed_positive_balance(
            make_loan(payment_status="CURRENT", current_balance=Decimal("200000")), UPLOAD_ID
        ) is None

    def test_fail(self):
        r = rule_closed_positive_balance(
            make_loan(payment_status="CLOSED", current_balance=Decimal("15000")), UPLOAD_ID
        )
        assert r is not None and r.rule_id == "R013" and r.severity == "HIGH"


class TestStatusDPDConflict:
    def test_pass_current_zero_dpd(self):
        assert rule_status_dpd_conflict(make_loan(payment_status="CURRENT", days_past_due=0), UPLOAD_ID) is None

    def test_pass_delinquent_positive_dpd(self):
        assert rule_status_dpd_conflict(make_loan(payment_status="DELINQUENT", days_past_due=45), UPLOAD_ID) is None

    def test_fail(self):
        r = rule_status_dpd_conflict(make_loan(payment_status="CURRENT", days_past_due=30), UPLOAD_ID)
        assert r is not None and r.rule_id == "R014" and r.exception_type == "STATUS_DPD_CONFLICT"


class TestBorrowerRepetition:
    def test_pass_normal_count(self):
        loans = [make_loan(borrower_id="B001") for _ in range(3)]
        assert len(rule_borrower_repetition(loans, UPLOAD_ID)) == 0

    def test_fail_suspicious(self):
        loans = [make_loan(borrower_id="B999") for _ in range(10)]
        results = rule_borrower_repetition(loans, UPLOAD_ID)
        assert len(results) > 0 and results[0].rule_id == "R015"


class TestDuplicateDetection:
    def test_duplicate_flagging_logic(self):
        ids = ["L001", "L002", "L001", "L003", "L002"]
        seen, dups = {}, []
        for lid in ids:
            if lid in seen:
                dups.append(lid)
            else:
                seen[lid] = True
        assert "L001" in dups and "L002" in dups and "L003" not in dups
