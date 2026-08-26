-- LoanVerify AI — Initial Database Schema
-- PostgreSQL 15

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─────────────────────────────────────────────
-- USERS & ROLES
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS roles (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(50) UNIQUE NOT NULL,  -- DATA_OPERATOR | REVIEWER | DATA_CONSUMER
    description TEXT
);

INSERT INTO roles (name, description) VALUES
    ('DATA_OPERATOR',  'Can upload CSV files, manage imports, view validation results'),
    ('REVIEWER',       'Can review exceptions, accept/reject AI recommendations, approve loans'),
    ('DATA_CONSUMER',  'Can view verified loans, audit trail, and export data')
ON CONFLICT (name) DO NOTHING;

CREATE TABLE IF NOT EXISTS users (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email         VARCHAR(255) UNIQUE NOT NULL,
    full_name     VARCHAR(255) NOT NULL,
    hashed_password TEXT NOT NULL,
    role_id       INTEGER NOT NULL REFERENCES roles(id),
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- Demo users (passwords are bcrypt of 'password123')
INSERT INTO users (id, email, full_name, hashed_password, role_id) VALUES
    ('a0000001-0000-0000-0000-000000000001', 'operator@loanverify.ai',  'Alex Operator',  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMVfpL0SU5S7L2OVLzS8q3dK5i', 1),
    ('a0000002-0000-0000-0000-000000000002', 'reviewer@loanverify.ai',  'Riley Reviewer',  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMVfpL0SU5S7L2OVLzS8q3dK5i', 2),
    ('a0000003-0000-0000-0000-000000000003', 'consumer@loanverify.ai',  'Casey Consumer',  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMVfpL0SU5S7L2OVLzS8q3dK5i', 3)
ON CONFLICT (email) DO NOTHING;

-- ─────────────────────────────────────────────
-- UPLOADS
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS uploads (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename         VARCHAR(500) NOT NULL,
    original_filename VARCHAR(500) NOT NULL,
    file_size        BIGINT,
    file_path        TEXT,
    source_type      VARCHAR(50) DEFAULT 'LOAN_TAPE',  -- LOAN_TAPE | SERVICER_UPDATE | COLLATERAL
    total_rows       INTEGER DEFAULT 0,
    imported_rows    INTEGER DEFAULT 0,
    failed_rows      INTEGER DEFAULT 0,
    status           VARCHAR(50) DEFAULT 'PROCESSING',  -- PROCESSING | COMPLETED | FAILED
    error_summary    JSONB,
    uploaded_by      UUID REFERENCES users(id),
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    completed_at     TIMESTAMPTZ
);

CREATE INDEX idx_uploads_uploaded_by ON uploads(uploaded_by);
CREATE INDEX idx_uploads_status ON uploads(status);
CREATE INDEX idx_uploads_created_at ON uploads(created_at DESC);

-- ─────────────────────────────────────────────
-- LOAN RECORDS
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS loan_records (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    upload_id           UUID NOT NULL REFERENCES uploads(id) ON DELETE CASCADE,
    source_row          INTEGER,                        -- Row number in original CSV

    -- Core identifiers
    loan_id             VARCHAR(100) NOT NULL,
    borrower_id         VARCHAR(100),
    borrower_name       VARCHAR(500),
    co_borrower_name    VARCHAR(500),

    -- Loan details
    loan_type           VARCHAR(100),
    loan_purpose        VARCHAR(100),
    property_state      VARCHAR(10),
    borrower_state      VARCHAR(10),
    property_zip        VARCHAR(20),
    servicer_name       VARCHAR(255),

    -- Financial fields
    original_principal  NUMERIC(15, 2),
    current_balance     NUMERIC(15, 2),
    interest_rate       NUMERIC(8, 4),
    monthly_payment     NUMERIC(15, 2),
    term_months         INTEGER,

    -- Dates
    origination_date    DATE,
    maturity_date       DATE,
    last_payment_date   DATE,
    next_payment_date   DATE,
    last_updated_at     DATE,

    -- Status fields
    payment_status      VARCHAR(50),   -- CURRENT | DELINQUENT | DEFAULT | PAID_OFF | CLOSED
    days_past_due       INTEGER DEFAULT 0,
    document_status     VARCHAR(50),   -- COMPLETE | INCOMPLETE | MISSING
    lien_position       VARCHAR(20),
    credit_grade        VARCHAR(20),
    employment_length   VARCHAR(50),
    income_band         VARCHAR(50),
    source_system       VARCHAR(100),

    -- Raw storage (original CSV row as JSON)
    raw_data            JSONB,
    parse_errors        JSONB,

    -- Normalization metadata
    normalized_at       TIMESTAMPTZ DEFAULT NOW(),
    is_duplicate        BOOLEAN DEFAULT FALSE,
    duplicate_of        VARCHAR(100),

    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_loan_records_loan_id   ON loan_records(loan_id);
CREATE INDEX idx_loan_records_upload_id ON loan_records(upload_id);
CREATE INDEX idx_loan_records_borrower  ON loan_records(borrower_id);
CREATE INDEX idx_loan_records_status    ON loan_records(payment_status);
CREATE INDEX idx_loan_records_state     ON loan_records(property_state);

-- ─────────────────────────────────────────────
-- VALIDATION RULES
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS validation_rules (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_id         VARCHAR(20) UNIQUE NOT NULL,  -- R001, R002 ...
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    category        VARCHAR(100),  -- REQUIRED_FIELD | DATE | FINANCIAL | STATUS | DUPLICATE | DOCUMENT | CROSS_SOURCE
    severity        VARCHAR(20) DEFAULT 'MEDIUM',  -- HIGH | MEDIUM | LOW
    is_active       BOOLEAN DEFAULT TRUE,
    rule_expression TEXT,          -- human-readable formula
    rule_fn_name    VARCHAR(100),  -- Python function name
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    created_by      UUID REFERENCES users(id),
    source          VARCHAR(50) DEFAULT 'SYSTEM'  -- SYSTEM | AI_GENERATED | USER_DEFINED
);

-- ─────────────────────────────────────────────
-- VALIDATION RESULTS
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS validation_results (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    loan_record_id  UUID NOT NULL REFERENCES loan_records(id) ON DELETE CASCADE,
    upload_id       UUID NOT NULL REFERENCES uploads(id) ON DELETE CASCADE,
    rule_id         VARCHAR(20) NOT NULL,
    passed          BOOLEAN NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_validation_results_loan  ON validation_results(loan_record_id);
CREATE INDEX idx_validation_results_rule  ON validation_results(rule_id);
CREATE INDEX idx_validation_results_pass  ON validation_results(passed);

-- ─────────────────────────────────────────────
-- EXCEPTIONS
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS exceptions (
    id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    loan_record_id   UUID NOT NULL REFERENCES loan_records(id) ON DELETE CASCADE,
    upload_id        UUID REFERENCES uploads(id),
    loan_id          VARCHAR(100) NOT NULL,
    rule_id          VARCHAR(20) NOT NULL,
    exception_type   VARCHAR(100) NOT NULL,
    severity         VARCHAR(20) NOT NULL,   -- HIGH | MEDIUM | LOW
    field_name       VARCHAR(100),
    actual_value     TEXT,
    expected_value   TEXT,
    message          TEXT NOT NULL,
    status           VARCHAR(50) DEFAULT 'OPEN',  -- OPEN | IN_REVIEW | RESOLVED | DISMISSED
    assigned_to      UUID REFERENCES users(id),
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    updated_at       TIMESTAMPTZ DEFAULT NOW(),
    resolved_at      TIMESTAMPTZ
);

CREATE INDEX idx_exceptions_loan_id    ON exceptions(loan_id);
CREATE INDEX idx_exceptions_status     ON exceptions(status);
CREATE INDEX idx_exceptions_severity   ON exceptions(severity);
CREATE INDEX idx_exceptions_upload_id  ON exceptions(upload_id);
CREATE INDEX idx_exceptions_assigned   ON exceptions(assigned_to);

-- ─────────────────────────────────────────────
-- EXCEPTION COMMENTS
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS exception_comments (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    exception_id UUID NOT NULL REFERENCES exceptions(id) ON DELETE CASCADE,
    author_id    UUID NOT NULL REFERENCES users(id),
    comment      TEXT NOT NULL,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_exception_comments_exception ON exception_comments(exception_id);

-- ─────────────────────────────────────────────
-- AI RECOMMENDATIONS
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ai_recommendations (
    id                UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    exception_id      UUID NOT NULL REFERENCES exceptions(id) ON DELETE CASCADE,
    loan_id           VARCHAR(100) NOT NULL,

    -- AI outputs
    explanation       TEXT,            -- Why did this fail?
    suggested_value   TEXT,            -- Suggested corrected value
    suggested_action  VARCHAR(100),    -- ACCEPT_SERVICER | ACCEPT_TAPE | FLAG_FOR_REVIEW | DISMISS
    confidence_score  NUMERIC(5, 2),   -- 0.00 - 100.00
    severity_reason   TEXT,
    source_comparison JSONB,           -- {loan_tape: {...}, servicer: {...}, recommendation: "..."}
    generated_note    TEXT,            -- Auto-generated reviewer note
    batch_summary     TEXT,

    -- Metadata
    model_used        VARCHAR(100),
    prompt_text       TEXT,
    prompt_tokens     INTEGER,
    completion_tokens INTEGER,
    latency_ms        INTEGER,
    created_at        TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ai_recommendations_exception ON ai_recommendations(exception_id);
CREATE INDEX idx_ai_recommendations_loan      ON ai_recommendations(loan_id);

-- ─────────────────────────────────────────────
-- REVIEW DECISIONS (human-in-the-loop)
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS review_decisions (
    id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    exception_id         UUID NOT NULL REFERENCES exceptions(id) ON DELETE CASCADE,
    ai_recommendation_id UUID REFERENCES ai_recommendations(id),
    reviewer_id          UUID NOT NULL REFERENCES users(id),
    decision             VARCHAR(50) NOT NULL,  -- APPROVED | REJECTED | EDITED | ESCALATED | REQUEST_CORRECTION
    ai_decision_followed BOOLEAN,               -- Did reviewer follow AI recommendation?
    original_value       TEXT,
    corrected_value      TEXT,
    reviewer_note        TEXT,
    created_at           TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_review_decisions_exception ON review_decisions(exception_id);
CREATE INDEX idx_review_decisions_reviewer  ON review_decisions(reviewer_id);

-- ─────────────────────────────────────────────
-- VERIFIED LOANS
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS verified_loans (
    id                   UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    loan_id              VARCHAR(100) UNIQUE NOT NULL,
    loan_record_id       UUID NOT NULL REFERENCES loan_records(id),
    upload_id            UUID REFERENCES uploads(id),

    -- Canonical (verified) data snapshot
    canonical_data       JSONB NOT NULL,

    -- Lineage
    source_file          VARCHAR(500),
    source_row           INTEGER,
    data_lineage         JSONB,   -- field-level lineage: {field: {source, row, value, ...}}

    -- Verification metadata
    validation_summary   JSONB,
    exception_count      INTEGER DEFAULT 0,
    exception_ids        UUID[],
    ai_recommendations   UUID[],
    human_decisions      UUID[],

    -- Verification stamp
    verified_by          UUID NOT NULL REFERENCES users(id),
    verified_at          TIMESTAMPTZ DEFAULT NOW(),
    record_hash          VARCHAR(64) NOT NULL,  -- SHA-256 of canonical_data
    hash_algorithm       VARCHAR(20) DEFAULT 'SHA-256',
    is_hash_valid        BOOLEAN DEFAULT TRUE,

    -- Status
    status               VARCHAR(50) DEFAULT 'VERIFIED',  -- VERIFIED | SUPERSEDED | REVOKED
    notes                TEXT,
    exported_at          TIMESTAMPTZ,
    export_count         INTEGER DEFAULT 0
);

CREATE INDEX idx_verified_loans_loan_id     ON verified_loans(loan_id);
CREATE INDEX idx_verified_loans_verified_by ON verified_loans(verified_by);
CREATE INDEX idx_verified_loans_verified_at ON verified_loans(verified_at DESC);
CREATE INDEX idx_verified_loans_status      ON verified_loans(status);

-- ─────────────────────────────────────────────
-- AUDIT EVENTS
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS audit_events (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type   VARCHAR(100) NOT NULL,  -- FILE_UPLOADED | RECORDS_IMPORTED | VALIDATION_EXECUTED | ...
    actor_id     UUID REFERENCES users(id),
    actor_email  VARCHAR(255),           -- Denormalized for query convenience
    loan_id      VARCHAR(100),
    upload_id    UUID REFERENCES uploads(id),
    exception_id UUID REFERENCES exceptions(id),

    -- Change tracking
    old_value    JSONB,
    new_value    JSONB,
    reason       TEXT,

    -- AI metadata
    ai_involved  BOOLEAN DEFAULT FALSE,
    ai_metadata  JSONB,

    -- Request metadata
    ip_address   VARCHAR(45),
    user_agent   TEXT,
    metadata     JSONB,

    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_events_loan_id     ON audit_events(loan_id);
CREATE INDEX idx_audit_events_event_type  ON audit_events(event_type);
CREATE INDEX idx_audit_events_actor_id    ON audit_events(actor_id);
CREATE INDEX idx_audit_events_created_at  ON audit_events(created_at DESC);
CREATE INDEX idx_audit_events_upload_id   ON audit_events(upload_id);
CREATE INDEX idx_audit_events_exception   ON audit_events(exception_id);

-- ─────────────────────────────────────────────
-- EXPORTS
-- ─────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS exports (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    export_type   VARCHAR(50) NOT NULL,  -- VERIFIED_LOANS | AUDIT_TRAIL | EXCEPTIONS
    file_path     TEXT,
    record_count  INTEGER,
    exported_by   UUID REFERENCES users(id),
    filters_used  JSONB,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────────
-- SEED VALIDATION RULES
-- ─────────────────────────────────────────────

INSERT INTO validation_rules (rule_id, name, description, category, severity, rule_expression, rule_fn_name, source) VALUES
    ('R001', 'Required Fields',              'Loan ID, borrower ID, principal, and dates must be present',              'REQUIRED_FIELD', 'HIGH',   'loan_id IS NOT NULL AND original_principal IS NOT NULL', 'rule_required_fields',           'SYSTEM'),
    ('R002', 'Valid Origination Date',       'Origination date must be a valid past date',                              'DATE',           'HIGH',   'origination_date <= TODAY()',                            'rule_valid_origination_date',     'SYSTEM'),
    ('R003', 'Valid Maturity Date',          'Maturity date must be after origination date',                            'DATE',           'HIGH',   'maturity_date > origination_date',                      'rule_valid_maturity_date',        'SYSTEM'),
    ('R004', 'No Negative Principal',        'Original principal must be greater than zero',                            'FINANCIAL',      'HIGH',   'original_principal > 0',                                'rule_no_negative_principal',      'SYSTEM'),
    ('R005', 'Valid Interest Rate',          'Interest rate must be between 0 and 50 percent',                          'FINANCIAL',      'HIGH',   '0 < interest_rate <= 50',                               'rule_valid_interest_rate',        'SYSTEM'),
    ('R006', 'Balance Does Not Exceed Principal', 'Current balance must not exceed original principal',                 'FINANCIAL',      'HIGH',   'current_balance <= original_principal',                 'rule_balance_vs_principal',       'SYSTEM'),
    ('R007', 'No Invalid Balance',           'Current balance must be >= 0',                                            'FINANCIAL',      'HIGH',   'current_balance >= 0',                                  'rule_no_invalid_balance',         'SYSTEM'),
    ('R008', 'Valid Payment Status',         'Payment status must be one of: CURRENT, DELINQUENT, DEFAULT, PAID_OFF, CLOSED', 'STATUS', 'MEDIUM', 'payment_status IN (CURRENT,DELINQUENT,DEFAULT,PAID_OFF,CLOSED)', 'rule_valid_payment_status', 'SYSTEM'),
    ('R009', 'Duplicate Loan Detection',     'Loan ID must be unique within the upload',                                'DUPLICATE',      'HIGH',   'COUNT(loan_id) = 1',                                    'rule_duplicate_detection',        'SYSTEM'),
    ('R010', 'Document Status Present',      'Document status must not be missing',                                     'DOCUMENT',       'MEDIUM', 'document_status IS NOT NULL',                           'rule_document_status',            'SYSTEM'),
    ('R011', 'Stale Record Detection',       'Records not updated in over 180 days are flagged as stale',               'DATE',           'LOW',    'last_payment_date >= TODAY() - 180 days',               'rule_stale_record',               'SYSTEM'),
    ('R012', 'Valid US State',               'Property state must be a valid 2-letter US state code',                   'GEOGRAPHIC',     'MEDIUM', 'property_state IN (valid_states)',                      'rule_valid_state',                'SYSTEM'),
    ('R013', 'Closed Account Positive Balance', 'Closed loans must have zero balance',                                  'STATUS',         'HIGH',   'NOT (payment_status=CLOSED AND current_balance > 0)',   'rule_closed_positive_balance',    'SYSTEM'),
    ('R014', 'Payment Status vs DPD Conflict', 'CURRENT status loans must have 0 days past due',                       'STATUS',         'HIGH',   'NOT (payment_status=CURRENT AND days_past_due > 0)',     'rule_status_dpd_conflict',        'SYSTEM'),
    ('R015', 'Suspicious Borrower Repetition', 'Same borrower ID on more than 5 loans in same upload',                 'DUPLICATE',      'MEDIUM', 'COUNT(borrower_id) <= 5',                               'rule_borrower_repetition',        'SYSTEM'),
    ('R016', 'Duplicate Borrower Combination', 'Same borrower + original principal + origination date must be unique', 'DUPLICATE',      'HIGH',   'COUNT(borrower_id, original_principal, origination_date) = 1', 'rule_duplicate_borrower_combo', 'SYSTEM'),
    ('R017', 'Cross-Source Conflict',          'Values must not conflict between loan_tape and servicer_update',       'CROSS_SOURCE',   'HIGH',   'loan_tape.field = servicer_update.field',              'rule_cross_source_conflict',      'SYSTEM'),
    ('R018', 'Invalid Date Format',            'Origination, maturity, and last-updated dates must be parseable',      'DATE',           'HIGH',   'dates are valid ISO or US formats',                    'rule_invalid_date_format',        'SYSTEM')
ON CONFLICT (rule_id) DO NOTHING;
