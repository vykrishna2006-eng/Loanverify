import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.database import engine, Base
from app.mongodb import connect_mongodb, close_mongodb

# Import all SQLAlchemy models so PostgreSQL tables are created
import app.models  # noqa: F401

from app.routers import (
    auth,
    uploads,
    loans,
    exceptions,
    ai_assistant,
    verified_loans,
    audit,
    dashboard,
    rules,
    exports,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    # 1. Create PostgreSQL tables (loan data)
    Base.metadata.create_all(bind=engine)

    # 2. Connect to MongoDB (authentication)
    try:
        await connect_mongodb()
    except Exception as e:
        print(f"[WARN] MongoDB connection warning: {e}")

    # 3. Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    await close_mongodb()


app = FastAPI(
    title="LoanVerify AI",
    description="""
## LoanVerify AI — Loan Data Verification Copilot

An AI-assisted loan data verification and exception-resolution platform that converts
messy loan data into validated, traceable, trusted records.

### Architecture
- **PostgreSQL** — loan records, exceptions, audit trail, verified loans
- **MongoDB** — user accounts and authentication

### Workflow
`MESSY DATA → INGEST → NORMALIZE → VALIDATE → DETECT EXCEPTIONS → AI EXPLAINS → HUMAN REVIEWS → VERIFY → HASH + AUDIT → TRUSTED DATA`

### Demo Credentials
| Role | Email | Password |
|------|-------|----------|
| Data Operator | operator@loanverify.ai | password123 |
| Reviewer | reviewer@loanverify.ai | password123 |
| Data Consumer | consumer@loanverify.ai | password123 |
    """,
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router,           prefix="/api/auth",           tags=["Authentication"])
app.include_router(uploads.router,        prefix="/api/uploads",        tags=["Module A — Ingestion"])
app.include_router(loans.router,          prefix="/api/loans",          tags=["Module H — Loans"])
app.include_router(exceptions.router,     prefix="/api/exceptions",     tags=["Module C — Exceptions"])
app.include_router(ai_assistant.router,   prefix="/api/ai",             tags=["Module D — AI Assistant"])
app.include_router(verified_loans.router, prefix="/api/verified-loans", tags=["Module E — Verified Loans"])
app.include_router(audit.router,          prefix="/api/audit",          tags=["Module F — Audit Trail"])
app.include_router(dashboard.router,      prefix="/api/dashboard",      tags=["Module G — Dashboards"])
app.include_router(rules.router,          prefix="/api/rules",          tags=["Validation Rules"])
app.include_router(exports.router,        prefix="/api/exports",        tags=["Exports"])


# ── Module H spec-exact aliases ───────────────────────────────────────────────
from app.auth import get_current_user
from app.models.mongo_user import MongoUser


@app.get("/api/summary", tags=["Module H — Summary"])
async def summary_alias(current_user: MongoUser = Depends(get_current_user)):
    """GET /summary — Module H spec endpoint alias."""
    from app.database import SessionLocal
    from app.routers.dashboard import global_summary
    db = SessionLocal()
    try:
        return global_summary(db=db, current_user=current_user)
    finally:
        db.close()


@app.get("/api/audit/{loan_id}", tags=["Module H — Audit"])
async def audit_by_loan_alias(
    loan_id: str,
    current_user: MongoUser = Depends(get_current_user),
):
    """GET /audit/:loanId — Module H spec endpoint alias."""
    from app.database import SessionLocal
    from app.routers.audit import get_loan_audit
    db = SessionLocal()
    try:
        return get_loan_audit(loan_id=loan_id, db=db, current_user=current_user)
    finally:
        db.close()


@app.get("/api/health", tags=["System"])
def health_check():
    return {
        "status":  "healthy",
        "version": settings.APP_VERSION,
        "app":     settings.APP_NAME,
        "auth_db": "mongodb",
        "data_db": "postgresql",
    }
