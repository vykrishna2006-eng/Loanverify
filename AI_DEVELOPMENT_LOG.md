# AI Development Log
## LoanVerify AI — Intain Campus FinTech Challenge 2026

> This document is a required deliverable per Section 10 of the challenge problem statement.
> It demonstrates how AI/agentic coding tools were used during development.

---

## 1. Tools Used

| Tool | Purpose |
|------|---------|
| **Kiro (Claude-based agentic IDE)** | Primary development tool — architecture, code generation, refactoring, debugging, documentation |
| **OpenAI GPT-4o** | AI provider for in-app AI features (exception explanation, rule generation) |
| **GitHub Copilot** | Inline autocomplete for repetitive patterns (schema fields, test cases) |

---

## 2. AI Use Cases During Development

| Use Case | Description |
|----------|-------------|
| Architecture design | Designed the 14-table PostgreSQL schema, service layer separation, and module boundaries |
| API design | Designed all REST endpoints matching Module H specification |
| Schema design | Created all SQLAlchemy models with correct relationships and migration-ready SQL |
| Validation rule engine | Generated the configurable rule engine with 15 independent rule functions |
| UI generation | Generated all React pages with professional FinTech dark theme |
| Test generation | Generated 76 unit and integration tests covering all validation rules |
| Debugging | Identified and fixed `metadata` reserved-word conflict in SQLAlchemy, SQLite/PostgreSQL type compatibility |
| Code review | Reviewed routers for missing auth dependencies and RBAC enforcement |
| Documentation | Generated README, Architecture Note, and this AI Development Log |
| Demo script | Prepared the five-minute demo flow walkthrough |

---

## 3. Representative Prompts (5–10 examples)

### Prompt 1 — Database Schema Design
```
Design a PostgreSQL schema for a loan data verification platform with these entities:
- Users with roles (DATA_OPERATOR, REVIEWER, DATA_CONSUMER)
- Uploads (CSV file tracking with lineage)
- LoanRecords (normalized loan data with raw_data preservation)
- ValidationResults and Exceptions (structured exception objects with rule_id, severity)
- AIRecommendations (separate from human decisions, never auto-applied)
- ReviewDecisions (human-only, explicitly linked to AI recs)
- VerifiedLoans (canonical records with SHA-256 hash)
- AuditEvents (immutable log of every action)

Requirements: full traceability from raw CSV row to verified record.
```

**AI Output:** Full 14-table schema with indexes, foreign keys, and seed data.

**Human Review:** Modified the `Exception` model — AI used `metadata` as a column name which is a reserved word in SQLAlchemy. Renamed to `extra_data`. Also changed all UUID columns to `String(36)` for SQLite test compatibility.

**Why changed:** AI missed the SQLAlchemy reserved-word constraint. Engineering judgment caught it during test runs.

---

### Prompt 2 — Validation Rule Engine Architecture
```
Build a configurable validation rule engine for loan data. Each rule should be a pure function
that takes a LoanRecord and returns either None (pass) or an ExceptionResult (fail).
Rules needed:
R001 required fields, R002 valid origination date, R003 maturity after origination,
R004 no negative principal, R005 valid interest rate, R006 balance <= principal,
R007 no negative balance, R008 valid payment status, R009 duplicate detection,
R010 document status, R011 stale records, R012 valid US state,
R013 closed+positive balance, R014 status/DPD conflict, R015 borrower repetition.

Use bulk insert for performance on 10,000 records.
```

**AI Output:** All 15 rule functions plus bulk validation runner.

**Human Review:** Accepted largely as-is. Added the `0.045 vs 4.5%` interest rate decimal-fraction detection (AI only checked `> 50` and `<= 0`, missing the common data entry error where rates are entered as decimals).

---

### Prompt 3 — AI Human-in-the-Loop Safety Architecture
```
Design the AI review workflow ensuring:
1. AI recommendations are NEVER applied directly to the database
2. Every AI output is stored as a suggestion, separate from the final human decision
3. The reviewer must explicitly Accept / Edit / Reject before any data changes
4. All AI interactions are logged in the audit trail with model metadata
5. The UI must visually distinguish AI recommendations from human decisions
```

**AI Output:** Full service + router + UI implementation with the `AI → Recommendation → Human Reviewer → Database` flow.

**Human Review:** Accepted. Added explicit `ai_safety_note` field in API responses and `"silent_ai_changes": 0` in the summary endpoint — both serve as demo-time proof points for judges.

---

### Prompt 4 — SHA-256 Record Hashing
```
Implement SHA-256 record hashing for verified loan records. Requirements:
- Hash must be computed from canonicalized (sorted-key) JSON of canonical_data
- Hash must be deterministic regardless of field insertion order
- A verify_hash() function must detect if canonical_data was modified after verification
- Show a clear "tampered" vs "intact" result in the UI
```

**AI Output:** `compute_record_hash()` and `verify_hash()` functions plus the UI hash-check button.

**Human Review:** Added `DecimalEncoder` to handle `Decimal` types in JSON serialization — AI missed that SQLAlchemy returns `Decimal` objects which `json.dumps` cannot serialize by default.

---

### Prompt 5 — React FinTech Dashboard
```
Build a professional React dashboard with dark FinTech theme. Requirements:
- Sidebar navigation with role-based visible items
- Role-aware dashboard (different content for OPERATOR / REVIEWER / CONSUMER)
- Exception queue table with severity badges (RED/YELLOW/GREEN)
- Modal detail view with AI recommendation box and human decision form
- Before vs After verification summary visual
- Data quality score with progress bars per category
- Audit timeline view (table + timeline toggle)
No Tailwind, pure CSS custom properties.
```

**AI Output:** Full CSS design system (300+ lines) plus all 10 React page components.

**Human Review:** Adjusted color palette for WCAG contrast ratios. Moved `Toaster` outside the router in `App.js` to prevent re-mounting on navigation. Fixed `useEffect` dependency arrays in dashboard data-fetch hooks.

---

### Prompt 6 — CSV Dataset Generator with Intentional Errors
```
Generate a realistic 10,000-row loan tape CSV with intentional data quality issues
matching the challenge specification:
- ~7% exception rate
- Missing loan IDs, duplicate loan IDs
- Negative principal, balance > principal
- Invalid interest rates (decimal fraction entry error)
- Future origination dates, maturity before origination
- Invalid payment statuses, CURRENT with DPD > 0
- CLOSED loans with positive balance
- Stale records (> 180 days)
- Invalid state codes
- Suspicious borrower repetition
Also generate: servicer_update.csv (600 rows, newer values), document_manifest.csv, validation_rules.json, users.json, expected_exception_sample.csv
```

**AI Output:** Complete generator script and all data files.

**Human Review:** Fixed a `ValueError: day 29 must be in range 1..28 for month 2` error — AI did not handle Feb 29 when adding years to origination dates. Added `try/except` with fallback to day 28.

---

### Prompt 7 — Integration Tests with AI Safety Assertions
```
Write an integration test that specifically verifies the AI safety guarantee:
After calling /exceptions/{id}/ai-review, the loan's current_balance in the database
must be unchanged. The test should fail with a clear message if AI modified data directly.
```

**AI Output:** `test_ai_recommendation_not_applied_directly()` test.

**Human Review:** Accepted as-is. This test is the most important safety assertion in the entire test suite.

---

### Prompt 8 — Natural Language Rule Generation
```
Build Feature 7: a natural language → validation rule generator.
User types: "Flag loans where the balance is more than 90% of the original principal"
System generates: rule_expression, rule_name, severity suggestion, explanation.
Critical requirement: generated rule must NEVER auto-activate.
Status must always be "PENDING_REVIEW" requiring explicit human activation.
```

**AI Output:** `generate_rule_from_description()` with pattern matching and mock/LLM modes.

**Human Review:** Added explicit `assert result["status"] != "ACTIVE"` test cases for multiple rule descriptions — AI's initial implementation returned `"PENDING_REVIEW"` correctly but didn't have the test coverage to prove it.

---

### Prompt 9 — OpenAPI Documentation
```
Configure FastAPI to produce rich OpenAPI docs at /api/docs with:
- Full module descriptions in the app description
- Role requirements in endpoint summaries
- Demo credential table
- Correct tags grouping by module letter (A, B, C...)
```

**AI Output:** Main app description, tag configuration, and router prefixes.

**Human Review:** Accepted. Added the demo credentials table and module workflow description in the FastAPI `description` field.

---

### Prompt 10 — Audit Event Constants
```
Create a strongly-typed audit event type system covering every action in the system:
FILE_UPLOADED, RECORDS_IMPORTED, VALIDATION_EXECUTED, EXCEPTION_CREATED,
AI_RECOMMENDATION_GENERATED, REVIEWER_COMMENT_ADDED, FIELD_EDITED,
LOAN_APPROVED, LOAN_REJECTED, VERIFIED_RECORD_CREATED, RECORD_EXPORTED,
HASH_VERIFIED, HASH_MISMATCH, RULE_CREATED, RULE_ACTIVATED...
Every service call must log an audit event. No action may escape the audit trail.
```

**AI Output:** `AuditEventType` class with all constants plus `log_event()` helper.

**Human Review:** Added `HASH_MISMATCH` event type — AI missed the tamper-detection audit event. Also enforced that `log_event` uses `db.flush()` rather than `db.commit()` so callers control transaction boundaries.

---

## 4. Human Review Process

Every piece of AI-generated code went through this process:

1. **Read before accepting** — no AI output was accepted without reading it line by line
2. **Run tests** — all code was run against the test suite before committing
3. **Check edge cases** — AI often missed null handling, type conversion edge cases, and reserved words
4. **Verify security** — auth dependencies were manually verified on every router endpoint
5. **Validate logic** — financial rules (balance vs principal, rate ranges) were manually verified against the problem statement

---

## 5. Rejected AI Outputs

### Rejection 1 — Auto-Activating AI Rules
**AI Output:** In the first version of `generate_rule_from_description()`, the AI returned:
```python
return {"rule_expression": "...", "status": "ACTIVE", "is_active": True}
```

**Why Rejected:** This directly violated the critical AI safety requirement from Section 9 of the problem statement: *"AI output must not silently change data."* Automatically activating a rule would silently change system behavior without human review.

**What was done instead:** Changed `status` to always be `"PENDING_REVIEW"`. Added three separate test assertions and the `[Review Rule] [Activate] [Reject]` UI flow.

---

### Rejection 2 — Direct AI-to-Database Writes
**AI Output:** An early version of the AI review endpoint attempted to directly update `loan.current_balance` with the AI's `suggested_value`:
```python
# AI's first attempt — REJECTED
if ai_rec.suggested_value and ai_rec.confidence_score > 80:
    loan.current_balance = Decimal(ai_rec.suggested_value)
    db.commit()
```

**Why Rejected:** This is the core safety violation — "AI output must not silently change data" (Section 9). No matter how high the confidence score, the database must only be changed by an explicit human decision.

**What was done instead:** AI output is stored in `ai_recommendations` table only. The `review_decisions` table records the human's choice. Only after `decision = "APPROVED"` does the system create a `VerifiedLoan` record.

---

### Rejection 3 — Bulk Loading All Records into Browser
**AI Output:** An early frontend table component fetched all loan records on mount:
```javascript
useEffect(() => {
  fetch('/api/loans?page_size=10000').then(...)
}, [])
```

**Why Rejected:** For 10,000+ records this would crash the browser tab and flood the network. The challenge explicitly requires demonstrating performance with realistic datasets.

**What was done instead:** Server-side pagination with `page`, `page_size` params on every list endpoint. Tables load 20–50 records per page with prev/next controls.

---

## 6. Estimated AI-Generated Code Percentage

| Layer | AI-Generated | Human-Modified | Human-Written |
|-------|-------------|----------------|---------------|
| Database schema (SQL) | 85% | 15% | 0% |
| SQLAlchemy models | 80% | 20% | 0% |
| FastAPI routers | 75% | 25% | 0% |
| Service layer | 70% | 30% | 0% |
| Validation rules | 80% | 20% | 0% |
| AI service | 75% | 25% | 0% |
| React components | 80% | 20% | 0% |
| CSS design system | 85% | 15% | 0% |
| Unit tests | 70% | 30% | 0% |
| Integration tests | 65% | 35% | 0% |
| Documentation | 60% | 40% | 0% |
| **Overall estimate** | **~76%** | **~24%** | **~0%** | |

---

## 7. Lessons Learned

### Where AI Helped Most

1. **Boilerplate elimination** — SQLAlchemy models, Pydantic schemas, and FastAPI router stubs would have taken 2-3x longer manually
2. **Comprehensive test coverage** — AI generated 76 test cases covering all 15 rules and all API endpoints in minutes
3. **CSS design system** — generating a consistent, professional dark-theme design system from scratch would have taken a full day manually
4. **Data generation** — the loan tape generator with intentional errors matching the exact spec requirements was written in one prompt

### Where Human Engineering Judgment Was Critical

1. **AI safety architecture** — the human-in-the-loop flow (AI → Recommendation → Human → Database) required deliberate architectural decisions that AI alone would not prioritize
2. **Cross-database compatibility** — making models work for both SQLite (tests) and PostgreSQL (production) required understanding SQLAlchemy internals beyond what AI suggested
3. **Reserved word conflicts** — `metadata` in SQLAlchemy, `Exception` as both a Python built-in and model name — AI missed these consistently
4. **Transaction boundaries** — deciding where `db.flush()` vs `db.commit()` belongs required understanding the audit trail's consistency requirements
5. **Security review** — manually verifying that every router endpoint has the correct auth dependency and role check — AI occasionally generated endpoints without `Depends(get_current_user)`

---

*This log covers the full development cycle of LoanVerify AI for the Intain Campus FinTech Challenge 2026.*
