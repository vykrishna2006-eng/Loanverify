"""
Integration Tests — Verification Service + AI Service
No database connection required — pure service function tests.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest


class TestVerificationService:
    """SHA-256 hashing and tamper detection."""

    def test_hash_is_deterministic(self):
        from app.services.verification_service import compute_record_hash
        data = {"loan_id": "L001", "balance": 280000.0, "status": "CURRENT"}
        assert compute_record_hash(data) == compute_record_hash(data)

    def test_hash_changes_when_data_changes(self):
        from app.services.verification_service import compute_record_hash
        h1 = compute_record_hash({"loan_id": "L001", "balance": 280000.0})
        h2 = compute_record_hash({"loan_id": "L001", "balance": 290000.0})
        assert h1 != h2

    def test_hash_is_64_char_hex(self):
        from app.services.verification_service import compute_record_hash
        h = compute_record_hash({"loan_id": "L001"})
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    def test_verify_hash_unchanged(self):
        from app.services.verification_service import compute_record_hash, verify_hash
        data = {"loan_id": "L001", "balance": 280000.0}

        class MockVL:
            canonical_data = data
            record_hash = compute_record_hash(data)

        assert verify_hash(MockVL()) is True

    def test_verify_hash_tampered(self):
        from app.services.verification_service import compute_record_hash, verify_hash
        original = {"loan_id": "L001", "balance": 280000.0}
        tampered = {"loan_id": "L001", "balance": 999999.0}

        class MockVL:
            canonical_data = tampered
            record_hash = compute_record_hash(original)

        assert verify_hash(MockVL()) is False

    def test_hash_key_order_independent(self):
        from app.services.verification_service import compute_record_hash
        a = {"loan_id": "L001", "balance": 100.0, "status": "CURRENT"}
        b = {"status": "CURRENT", "balance": 100.0, "loan_id": "L001"}
        assert compute_record_hash(a) == compute_record_hash(b)


class TestAIService:
    """AI recommendation generation (mock provider)."""

    def test_explain_balance_exception(self):
        from app.services.ai_service import explain_exception
        result = explain_exception({
            "loan_id": "L000123",
            "exception_type": "BALANCE_GREATER_THAN_PRINCIPAL",
            "field_name": "current_balance",
            "actual_value": "450000",
            "expected_value": "<= 400000",
            "message": "Balance exceeds principal",
            "severity": "HIGH",
        })
        parsed = result["parsed"]
        assert "explanation" in parsed
        assert len(parsed["explanation"]) > 20
        assert "confidence_score" in parsed
        assert float(parsed["confidence_score"]) > 0

    def test_explain_missing_fields_requests_correction(self):
        from app.services.ai_service import explain_exception
        result = explain_exception({
            "loan_id": "L000456",
            "exception_type": "MISSING_REQUIRED_FIELDS",
            "field_name": "loan_id",
            "actual_value": "NULL",
            "expected_value": "NOT NULL",
            "message": "loan_id missing",
            "severity": "HIGH",
        })
        assert result["parsed"]["suggested_action"] == "REQUEST_CORRECTION"

    def test_classify_high_severity(self):
        from app.services.ai_service import classify_severity
        r = classify_severity("BALANCE_GREATER_THAN_PRINCIPAL", "current_balance", "450000")
        assert r["severity"] == "HIGH"

    def test_classify_medium_severity(self):
        from app.services.ai_service import classify_severity
        r = classify_severity("MISSING_DOCUMENT_STATUS", "document_status", None)
        assert r["severity"] == "MEDIUM"

    def test_classify_low_severity(self):
        from app.services.ai_service import classify_severity
        r = classify_severity("STALE_RECORD", "last_payment_date", "2022-01-01")
        assert r["severity"] == "LOW"

    def test_batch_summary_empty(self):
        from app.services.ai_service import generate_batch_summary
        r = generate_batch_summary([])
        assert r["total"] == 0
        assert "no exceptions" in r["summary_text"].lower()

    def test_batch_summary_counts(self):
        from app.services.ai_service import generate_batch_summary
        excs = [
            {"exception_type": "BALANCE_GREATER_THAN_PRINCIPAL", "severity": "HIGH"},
            {"exception_type": "BALANCE_GREATER_THAN_PRINCIPAL", "severity": "HIGH"},
            {"exception_type": "MISSING_DOCUMENT_STATUS",        "severity": "MEDIUM"},
            {"exception_type": "STALE_RECORD",                   "severity": "LOW"},
        ]
        r = generate_batch_summary(excs)
        assert r["total"] == 4
        assert r["high"] == 2 and r["medium"] == 1 and r["low"] == 1
        assert r["most_common_issue"] == "BALANCE_GREATER_THAN_PRINCIPAL"

    def test_generate_rule_pending_review(self):
        from app.services.ai_service import generate_rule_from_description
        r = generate_rule_from_description(
            "Flag loans where the balance is more than 90% of the original principal"
        )
        assert r["ai_generated"] is True
        # Critical: must NEVER be auto-activated
        assert r["status"] == "PENDING_REVIEW"
        assert r["status"] not in ("ACTIVE", "ACTIVATED")

    def test_ai_rule_never_auto_activated(self):
        from app.services.ai_service import generate_rule_from_description
        for desc in [
            "Flag loans with interest rate above 20%",
            "Any loan with DPD > 90 should be marked default",
            "Balance cannot exceed original principal",
        ]:
            r = generate_rule_from_description(desc)
            assert r.get("status") == "PENDING_REVIEW", (
                f"AI SAFETY VIOLATION: Rule auto-activated for '{desc}'"
            )

    def test_compare_sources_newer_preferred(self):
        from app.services.ai_service import compare_sources
        result = compare_sources(
            {"loan_id": "L001"},
            {"name": "Loan Tape",       "value": "450000", "updated_date": "2024-08-10"},
            {"name": "Servicer Update", "value": "382500", "updated_date": "2024-08-21"},
        )
        assert "recommendation" in result
        assert result["preferred_source"] == "SERVICER"


class TestIngestionNormalization:
    """Unit tests for CSV column normalization."""

    def test_normalize_column_name(self):
        from app.services.ingestion_service import normalize_column_name
        assert normalize_column_name("Loan ID") == "loan_id"
        assert normalize_column_name("ORIGINAL_PRINCIPAL") == "original_principal"
        assert normalize_column_name("Days-Past-Due") == "days_past_due"

    def test_parse_decimal_valid(self):
        from app.services.ingestion_service import parse_decimal
        from decimal import Decimal
        assert parse_decimal("300000.00") == Decimal("300000.00")
        assert parse_decimal("$280,500.50") == Decimal("280500.50")
        assert parse_decimal("₹450000") == Decimal("450000")

    def test_parse_decimal_invalid(self):
        from app.services.ingestion_service import parse_decimal
        assert parse_decimal("N/A") is None
        assert parse_decimal("") is None
        assert parse_decimal(None) is None

    def test_parse_date_valid(self):
        from app.services.ingestion_service import parse_date
        from datetime import date
        assert parse_date("2018-06-15") == (date(2018, 6, 15), None)
        assert parse_date("06/15/2018") == (date(2018, 6, 15), None)

    def test_parse_date_invalid(self):
        from app.services.ingestion_service import parse_date
        assert parse_date("not-a-date") == (None, "not-a-date")
        assert parse_date("") == (None, None)
        assert parse_date(None) == (None, None)

    def test_normalize_payment_status(self):
        from app.services.ingestion_service import normalize_payment_status
        assert normalize_payment_status("current") == "CURRENT"
        assert normalize_payment_status("DELINQUENT") == "DELINQUENT"
        assert normalize_payment_status("paid off") == "PAID_OFF"
        assert normalize_payment_status("Closed") == "CLOSED"
