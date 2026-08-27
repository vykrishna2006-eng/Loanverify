"""
API Tests — Module H
Tests all required API endpoints.
"""
import pytest
import json
from tests.conftest import auth_headers


class TestAuthAPI:
    def test_login_success(self, client, seed_db):
        res = client.post("/api/auth/token", data={
            "username": "operator@test.com",
            "password": "testpass",
        })
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "operator@test.com"
        assert data["user"]["role"]["name"] == "DATA_OPERATOR"

    def test_login_wrong_password(self, client, seed_db):
        res = client.post("/api/auth/token", data={
            "username": "operator@test.com",
            "password": "wrongpassword",
        })
        assert res.status_code == 401

    def test_login_unknown_user(self, client, seed_db):
        res = client.post("/api/auth/token", data={
            "username": "nobody@test.com",
            "password": "testpass",
        })
        assert res.status_code == 401

    def test_get_me(self, client, operator_token):
        res = client.get("/api/auth/me", headers=auth_headers(operator_token))
        assert res.status_code == 200
        assert res.json()["email"] == "operator@test.com"

    def test_get_me_unauthenticated(self, client):
        res = client.get("/api/auth/me")
        assert res.status_code == 401

    def test_register_new_user(self, client, seed_db):
        res = client.post("/api/auth/register", params={
            "email": "newuser@test.com",
            "full_name": "New User",
            "password": "newpass123",
            "role_name": "DATA_CONSUMER",
        })
        assert res.status_code == 200
        assert res.json()["email"] == "newuser@test.com"


class TestLoansAPI:
    def test_get_loans_empty(self, client, operator_token):
        res = client.get("/api/loans", headers=auth_headers(operator_token))
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

    def test_get_loans_with_records(self, client, operator_token, sample_loan_record):
        res = client.get("/api/loans", headers=auth_headers(operator_token))
        assert res.status_code == 200
        data = res.json()
        assert data["total"] >= 1

    def test_get_loan_by_id(self, client, operator_token, sample_loan_record):
        loan_id = sample_loan_record["loan"].loan_id
        res = client.get(f"/api/loans/{loan_id}", headers=auth_headers(operator_token))
        assert res.status_code == 200
        assert res.json()["loan_id"] == loan_id

    def test_get_loan_not_found(self, client, operator_token):
        res = client.get("/api/loans/NONEXISTENT_LOAN", headers=auth_headers(operator_token))
        assert res.status_code == 404

    def test_get_loans_search(self, client, operator_token, sample_loan_record):
        res = client.get("/api/loans?search=L000001", headers=auth_headers(operator_token))
        assert res.status_code == 200

    def test_get_loans_unauthenticated(self, client):
        res = client.get("/api/loans")
        assert res.status_code == 401

    def test_get_loans_pagination(self, client, operator_token):
        res = client.get("/api/loans?page=1&page_size=5", headers=auth_headers(operator_token))
        assert res.status_code == 200
        data = res.json()
        assert data["page"] == 1
        assert data["page_size"] == 5


class TestExceptionsAPI:
    def test_get_exceptions_empty(self, client, operator_token):
        res = client.get("/api/exceptions", headers=auth_headers(operator_token))
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert "summary" in data

    def test_get_exceptions_with_filters(self, client, operator_token):
        res = client.get(
            "/api/exceptions?severity=HIGH&status=OPEN&page=1&page_size=10",
            headers=auth_headers(operator_token)
        )
        assert res.status_code == 200

    def test_get_exception_not_found(self, client, operator_token):
        from uuid import uuid4
        res = client.get(f"/api/exceptions/{uuid4()}", headers=auth_headers(operator_token))
        assert res.status_code == 404


class TestVerifiedLoansAPI:
    def test_get_verified_loans_empty(self, client, operator_token):
        res = client.get("/api/verified-loans", headers=auth_headers(operator_token))
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert data["total"] >= 0

    def test_get_verified_loan_not_found(self, client, operator_token):
        res = client.get("/api/verified-loans/NONEXISTENT", headers=auth_headers(operator_token))
        assert res.status_code == 404


class TestAuditAPI:
    def test_get_audit_events(self, client, operator_token):
        res = client.get("/api/audit", headers=auth_headers(operator_token))
        assert res.status_code == 200
        data = res.json()
        assert "items" in data
        assert "total" in data

    def test_get_audit_by_loan(self, client, operator_token):
        res = client.get("/api/audit/loan/L000001", headers=auth_headers(operator_token))
        assert res.status_code == 200
        data = res.json()
        assert "loan_id" in data
        assert "events" in data

    def test_get_audit_event_types(self, client, operator_token):
        res = client.get("/api/audit/event-types", headers=auth_headers(operator_token))
        assert res.status_code == 200
        data = res.json()
        assert "event_types" in data
        assert "FILE_UPLOADED" in data["event_types"]


class TestDashboardAPI:
    def test_global_summary(self, client, operator_token):
        res = client.get("/api/dashboard/summary", headers=auth_headers(operator_token))
        assert res.status_code == 200
        data = res.json()
        assert "total_uploads" in data
        assert "total_loan_records" in data
        assert "total_exceptions" in data
        assert "verified_loans" in data
        assert "severity_breakdown" in data
        assert data["silent_ai_changes"] == 0  # AI safety guarantee

    def test_operator_dashboard(self, client, operator_token):
        res = client.get("/api/dashboard/operator", headers=auth_headers(operator_token))
        assert res.status_code == 200
        data = res.json()
        assert data["role"] == "DATA_OPERATOR"
        assert "metrics" in data
        assert "recent_uploads" in data

    def test_reviewer_dashboard(self, client, reviewer_token):
        res = client.get("/api/dashboard/reviewer", headers=auth_headers(reviewer_token))
        assert res.status_code == 200
        data = res.json()
        assert data["role"] == "REVIEWER"
        assert "metrics" in data

    def test_consumer_dashboard(self, client, operator_token):
        res = client.get("/api/dashboard/consumer", headers=auth_headers(operator_token))
        assert res.status_code == 200
        data = res.json()
        assert data["role"] == "DATA_CONSUMER"
        assert "before_after" in data


class TestRulesAPI:
    def test_list_rules(self, client, operator_token):
        res = client.get("/api/rules", headers=auth_headers(operator_token))
        assert res.status_code == 200
        data = res.json()
        assert isinstance(data, list)
        assert len(data) >= 15
        assert data[0]["rule_id"] == "R001"

    def test_health_check(self, client):
        res = client.get("/api/health")
        assert res.status_code == 200
        assert res.json()["status"] == "healthy"
        assert "version" in res.json()


class TestRBACEnforcement:
    def test_operator_cannot_submit_decision(self, client, operator_token):
        """DATA_OPERATOR must not be able to submit review decisions (REVIEWER only)."""
        from uuid import uuid4
        res = client.post(
            f"/api/exceptions/{uuid4()}/decision",
            json={"decision": "APPROVED"},
            headers=auth_headers(operator_token),
        )
        # Should be 403 Forbidden
        assert res.status_code == 403

    def test_unauthenticated_access_blocked(self, client):
        for path in ["/api/loans", "/api/exceptions", "/api/verified-loans", "/api/audit"]:
            res = client.get(path)
            assert res.status_code == 401, f"Expected 401 for {path}"
