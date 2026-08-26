# LoanVerify AI — Architecture Note

> Required deliverable — PDF Section 12: 1–2 pages covering system design, data model, API design, validation engine, AI feature, audit trail, and trade-offs.

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Vercel)                         │
│                     React 18 + React Router                      │
│   Login  │  Uploads  │  Exceptions  │  AI Assistant  │  Audit   │
└────────────────────────────┬─────────────────────────────────────┘
                             │ HTTPS (JWT Bearer token)
┌────────────────────────────▼─────────────────────────────────────┐
│                      BACKEND (Render)                            │
│                    FastAPI + Python 3.11                         │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐    │
│  │ Module A │  │ Module B │  │ Module C │  │   Module D   │    │
│  │ Ingest   │  │ Validate │  │Exception │  │ AI Assistant │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐    │
│  │ Module E │  │ Module F │  │ Module G │  │   Module H   │    │
│  │ Verified │  │  Audit   │  │Dashboard │  │  REST APIs   │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘    │
└───────────────────┬───────────────────────────┬─────────────────┘
                    │                           │
       ┌────────────▼──────────┐   ┌────────────▼──────────┐
       │   PostgreSQL (Render) │   │  MongoDB Atlas (Free) │
       │   Loan data           │   │  Authentication only  │
       │   - loan_records      │   │  - users collection   │
       │   - exceptions        │   │  - roles collection   │
       │   - verified_loans    │   └───────────────────────┘
       │   - audit_events      │
       │   - ai_recommendations│
       │   - review_decisions  │
       └───────────────────────┘
```

---

## Data Architecture

### Two-Database Design

| Database | Purpose | Why |
|----------|---------|-----|
| **PostgreSQL** | All loan data | Relational integrity, complex joins, ACID transactions |
| **MongoDB** | Authentication | Flexible schema for users, fast single-doc lookups at login |

### PostgreSQL Schema (12 tables)

```
uploads          → loan_records → validation_results
                              → exceptions → exception_comments
                                          → ai_recommendations
                                          → review_decisions
                                          → audit_events
                              → verified_loans
validation_rules
```

Key design decisions:
- `loan_records.raw_data` (JSON) preserves every original CSV value for lineage
- `exceptions` has `review_decisions` as a list (many per exception) — full history
- `verified_loans.record_hash` is SHA-256 of sorted-key JSON — deterministic and tamper-detectable
- `audit_events` is append-only — nothing is ever deleted from this table

### MongoDB Schema (2 collections)

```javascript
// users collection
{
  id:              "uuid-string",
  email:           "reviewer@loanverify.ai",
  full_name:       "Riley Reviewer",
  hashed_password: "$2b$12$...",  // bcrypt
  role_name:       "REVIEWER",    // DATA_OPERATOR | REVIEWER | DATA_CONSUMER
  is_active:       true,
  created_at:      ISODate
}

// roles collection
{
  id:          "r2",
  name:        "REVIEWER",
  description: "Review exceptions, approve loans"
}
```

---

## API Design (Module H)

### Authentication Flow
```
POST /api/auth/token  →  MongoDB lookup  →  bcrypt verify  →  JWT (8h)
All other endpoints   →  JWT decode (no DB)  →  role check  →  PostgreSQL query
```

### REST Endpoints
```
GET  /api/loans                    Paginated, filterable, searchable
GET  /api/loans/:id                By loan_id string; ?include_exceptions=true
GET  /api/exceptions               Filter: severity, status, type, loan_id, borrower_id
GET  /api/verified-loans           Paginated, search by loan_id
GET  /api/verified-loans/:id       Full detail: canonical data + lineage + hash
GET  /api/audit/:loanId            Full chronological audit trail for one loan
GET  /api/summary                  Global stats: totals, rates, severity breakdown
POST /api/uploads                  CSV upload + immediate validation
POST /api/exceptions/:id/ai-review Generate AI recommendation (never writes to DB)
POST /api/exceptions/:id/decision  Submit human decision (APPROVED/REJECTED/EDITED...)
GET  /api/docs                     Swagger/OpenAPI UI
```

---

## Validation Engine (Module B)

### Design: Configurable Rule Registry

```python
SINGLE_RECORD_RULE_MAP = {
    "R001": rule_required_fields,
    "R002": rule_valid_origination_date,
    ...18 rules total
}

def run_validation(db, upload_id):
    active_ids = _get_active_rule_ids(db)   # respects is_active flag
    for loan in loans:
        for rule_id, fn in SINGLE_RECORD_RULE_MAP.items():
            if rule_id not in active_ids: continue
            result = fn(loan, upload_id)    # pure function → None or ExceptionResult
```

Each rule is a **pure function** — no side effects, no DB calls, easy to test individually. Results are bulk-inserted after all rules run (performance).

### Rules Covering PDF Section 7

| Issue | Rule | Severity |
|-------|------|----------|
| Missing loan IDs | R001 | HIGH |
| Duplicate loan IDs | R009 | HIGH |
| Duplicate borrower+amount+date | R016 | HIGH |
| Invalid date formats | R018 | HIGH |
| Maturity before origination | R003 | HIGH |
| Negative principal | R004 | HIGH |
| Balance > principal | R006 | HIGH |
| Interest rate outside range | R005 | HIGH |
| Status/DPD conflict | R014 | HIGH |
| Missing document status | R010 | MEDIUM |
| Conflicting tape vs servicer | R017 | HIGH |
| Stale records | R011 | LOW |
| Invalid state codes | R012 | MEDIUM |
| Suspicious borrower repetition | R015 | MEDIUM |
| Closed + positive balance | R013 | HIGH |

---

## AI Feature Design (Module D)

### Human-in-the-Loop Architecture (Section 9 Compliance)

```
AI Service (any provider)
         ↓
  AIRecommendation row created
  (stored in PostgreSQL, status: recommendation)
         ↓
  Exception status → IN_REVIEW
         ↓
  Human Reviewer sees recommendation:
    explanation, suggested_value, confidence_score, model, prompt, tokens
         ↓
  Human submits ReviewDecision:
    APPROVED | REJECTED | EDITED | ESCALATED | REQUEST_CORRECTION
         ↓
  Only after APPROVED/EDITED:
    - Corrected value written to loan record
    - VerifiedLoan record created
    - Audit event logged
```

**AI never writes directly to any database.** `silent_ai_changes = 0` is enforced and returned in `/api/summary`.

### 7 AI Features
1. **Explain** — why did this rule fail (mock + Gemini)
2. **Suggest** — corrected value recommendation
3. **Compare** — loan tape vs servicer update (LLM or date heuristic)
4. **Note** — generate reviewer note text
5. **Classify** — explain severity level
6. **Batch** — natural language summary of all exceptions
7. **Rule Gen** — NL → validation rule expression (LLM or pattern match; always PENDING_REVIEW)

---

## Audit Trail (Module F)

All 10 required events plus extras:

```
FILE_UPLOADED → RECORDS_IMPORTED → VALIDATION_EXECUTED → EXCEPTION_CREATED
→ AI_RECOMMENDATION_GENERATED → REVIEWER_COMMENT_ADDED → FIELD_EDITED
→ LOAN_APPROVED / LOAN_REJECTED → VERIFIED_RECORD_CREATED → RECORD_EXPORTED
+ USER_LOGIN, HASH_VERIFIED, HASH_MISMATCH, RULE_ACTIVATED
```

Design: `audit_events` table is **append-only**. Every event stores `actor_id`, `actor_email`, `old_value`, `new_value`, `reason`, `ai_involved`, `ai_metadata`. The `ai_involved` boolean makes it easy to filter AI vs human actions.

---

## Record Hashing (Module E)

```python
def compute_record_hash(canonical_data: dict) -> str:
    # Sort keys for determinism — order of insertion doesn't matter
    serialized = json.dumps(canonical_data, sort_keys=True, cls=DecimalEncoder)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

def verify_hash(verified_loan) -> bool:
    recomputed = compute_record_hash(verified_loan.canonical_data)
    return recomputed == verified_loan.record_hash
```

If any field in `canonical_data` changes after verification, `verify_hash()` returns `False` and a `HASH_MISMATCH` audit event is logged.

---

## Trade-offs

| Decision | Rationale |
|----------|-----------|
| MongoDB for auth only | PostgreSQL is better for relational loan data. MongoDB gives flexible user schema without migrations. |
| Mock AI provider | Judges can run the full app without an API key. Set `AI_PROVIDER=gemini` to enable live Gemini. |
| SQLite for tests | No PostgreSQL needed in CI. Tests run in ~0.3 seconds. |
| Bulk insert for CSV | 10,000 rows in one `bulk_insert_mappings` call vs 10,000 individual INSERTs — ~50x faster. |
| Append-only audit | Never delete audit events. The audit trail is immutable by design. |
| Rule registry pattern | Each rule is an independent function. Easy to add, remove, or disable without touching other rules. |
| Reviewer history list | `review_decisions` is a list (one row per decision). Old decisions are never deleted — full history always visible. |

---

*LoanVerify AI — Intain Campus FinTech Challenge 2026*
