# LoanVerify AI — Loan Data Verification Copilot

> **Intain Campus FinTech Challenge 2026 — Full Stack Track**
> An AI-assisted full-stack console that turns messy loan records into validated, traceable, trusted data.

---

## 🌐 Live Hosted Deployment

| Component | URL | Status |
|:---|:---|:---|
| **🚀 Web Application (Vercel)** | Deployed on Vercel | 🟢 Live |
| **⚡ Backend API (Render)** | https://loanverify-backend.onrender.com | 🟢 Live |
| **📖 Interactive API Docs (Swagger UI)** | https://loanverify-backend.onrender.com/api/docs | 🟢 Live |
| **📑 Alternative API Docs (ReDoc)** | https://loanverify-backend.onrender.com/api/redoc | 🟢 Live |

---

## 🔑 Demo Test Credentials (Section 12 of Challenge)

| Role | Email | Password | Scope & Permissions |
|:---|:---|:---|:---|
| 📁 **Data Operator** | `operator@loanverify.ai` | `password123` | Ingest loan tapes, run 12 validation rules, monitor pipeline |
| ⚖️ **Reviewer** | `reviewer@loanverify.ai` | `password123` | Exception queue, AI recommendations, human decision gate |
| 📊 **Data Consumer** | `consumer@loanverify.ai` | `password123` | Portfolio quality scores, verified loans registry, CSV export |

---

## Core Workflow

```
MESSY DATA → INGEST → NORMALIZE → VALIDATE → DETECT EXCEPTIONS
     → AI EXPLAINS → HUMAN REVIEWS → VERIFY → HASH + AUDIT → TRUSTED DATA
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, React Router v6, Recharts, React Dropzone, Lucide Icons |
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.0, Pydantic v2 |
| Loan Data DB | PostgreSQL 15 (Neon / Render) |
| Auth DB | MongoDB Atlas |
| AI Copilot | Google Gemini (gemini-1.5-flash / multi-model fallback) / FinTech domain engine |
| Integrity | SHA-256 cryptographic hashing & tamper verification |
| Auth | JWT (python-jose), bcrypt (passlib) |
| Deployment | Render (Backend API), Vercel (Frontend SPA) |

---

## Modules

| Module | Description |
|--------|-------------|
| A — Data Ingestion | CSV upload, parse, normalize, bulk insert, lineage |
| B — Validation Engine | 18 configurable rules, respects is_active flag |
| C — Exception Queue | Filter, comment, approve, reject, edit, full history |
| D — AI Assistant | 7 AI features, human-in-the-loop, never auto-writes |
| E — Verified Loans | SHA-256 hash, tamper detection, field-level lineage |
| F — Audit Trail | Every action logged, AI events marked |
| G — Dashboards | Operator / Reviewer / Consumer role-specific views |
| H — REST API | All spec endpoints + Swagger at /api/docs |

---

## Project Structure

```
LoanVerify AI/
├── backend/
│   ├── app/
│   │   ├── main.py                   # FastAPI app, connects PostgreSQL + MongoDB
│   │   ├── auth.py                   # JWT + MongoDB user lookup
│   │   ├── mongodb.py                # MongoDB async connection (motor)
│   │   ├── config.py                 # Settings (DATABASE_URL, MONGODB_URL, etc.)
│   │   ├── database.py               # PostgreSQL SQLAlchemy engine
│   │   ├── models/
│   │   │   ├── mongo_user.py         # MongoUser Pydantic model (auth)
│   │   │   ├── user.py               # SQLAlchemy User stub (FK refs only)
│   │   │   ├── loan.py               # LoanRecord (PostgreSQL)
│   │   │   ├── exception.py          # Exception + ExceptionComment
│   │   │   ├── verified_loan.py      # VerifiedLoan with SHA-256 hash
│   │   │   ├── audit.py              # AuditEvent
│   │   │   ├── ai.py                 # AIRecommendation
│   │   │   ├── review.py             # ReviewDecision (history preserved)
│   │   │   └── validation.py         # ValidationRule + ValidationResult
│   │   ├── routers/                  # One router per module (A–H)
│   │   └── services/
│   │       ├── ingestion_service.py  # Module A
│   │       ├── validation_service.py # Module B (18 rules)
│   │       ├── ai_service.py         # Module D (7 features)
│   │       ├── verification_service.py # Module E (SHA-256)
│   │       └── audit_service.py      # Module F
│   ├── scripts/
│   │   ├── seed_mongodb.py           # Seed demo users into MongoDB
│   │   └── generate_dataset.py       # Generate 10,000-row loan tape CSV
│   ├── db/init.sql                   # PostgreSQL schema + seed data
│   ├── requirements.txt
│   └── render.yaml                   # Render deployment config
├── frontend/
│   ├── src/
│   │   ├── api/client.js             # All API calls (axios)
│   │   ├── context/AuthContext.js    # JWT storage + auth state
│   │   ├── pages/                    # 10 pages (Login, Dashboard, Uploads...)
│   │   └── index.css                 # Dark FinTech design system
│   ├── .env                          # Local: REACT_APP_API_URL=http://localhost:8000
│   ├── .env.production               # Prod:  REACT_APP_API_URL=https://...render.com
│   └── vercel.json                   # Vercel deployment config
├── data/
│   ├── loan_tape.csv                 # 2,000 rows with intentional errors
│   ├── loan_tape_10000.csv           # 10,000 rows
│   ├── servicer_update.csv           # 600 rows, newer values
│   ├── document_manifest.csv
│   ├── validation_rules.json
│   ├── users.json
│   └── expected_exception_sample.csv
├── .env                              # Local environment variables
├── .env.example                      # Template for all env vars
├── render.yaml                       # Render deployment (backend + PostgreSQL)
├── AI_DEVELOPMENT_LOG.md
└── ARCHITECTURE.md
```

---

## Environment Variables

```env
# PostgreSQL — loan data
DATABASE_URL=postgresql://user:pass@host:5432/loanverify

# MongoDB — authentication only
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net
MONGODB_DB_NAME=loanverify_auth

# Security
SECRET_KEY=your_64_char_random_secret_key

# CORS (comma-separated)
CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000

# AI (optional — domain fallback engine works automatically)
AI_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-1.5-flash

# Frontend
REACT_APP_API_URL=https://loanverify-backend.onrender.com
```

---

## Local Development Setup

### Prerequisites
- Python 3.11 or 3.12 (not 3.14 — pandas wheels not ready yet)
- Node.js 18+
- PostgreSQL running locally OR Docker
- MongoDB running locally OR free MongoDB Atlas cluster

### Backend

```powershell
# 1. Go to backend folder
cd backend

# 2. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy and fill in environment variables
cp ../.env.example ../.env
# Edit .env — set DATABASE_URL and MONGODB_URL

# 5. Create PostgreSQL tables
python -c "from app.database import engine, Base; import app.models; Base.metadata.create_all(bind=engine); print('Tables OK')"

# 6. Seed MongoDB with demo users (run once)
python scripts/seed_mongodb.py

# 7. Start the backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend → http://localhost:8000
API Docs → http://localhost:8000/api/docs

### Frontend

```powershell
cd frontend
npm install
npm start
```

Frontend → http://localhost:3000

---

## Demo Credentials

| Role | Email | Password | Permissions |
|------|-------|----------|-------------|
| Data Operator | `operator@loanverify.ai` | `password123` | Upload CSV, run validation |
| Reviewer | `reviewer@loanverify.ai` | `password123` | Review exceptions, AI assistant, approve/reject |
| Data Consumer | `consumer@loanverify.ai` | `password123` | View verified loans, audit trail, export |

---

## Deploy to Render (Backend) + Vercel (Frontend)

### Step 1 — MongoDB Atlas (free)
1. Go to https://cloud.mongodb.com → create free M0 cluster
2. Get connection string: `mongodb+srv://user:pass@cluster0.xxxxx.mongodb.net`

### Step 2 — Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourname/loanverify-ai.git
git push -u origin main
```

### Step 3 — Deploy Backend on Render
1. Go to https://render.com → New → Web Service → connect GitHub repo
2. **Root Directory**: `backend`
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables:

| Key | Value |
|-----|-------|
| `MONGODB_URL` | Your Atlas connection string |
| `SECRET_KEY` | Random 64-char string |
| `CORS_ORIGINS` | `https://your-app.vercel.app` |
| `AI_PROVIDER` | `mock` |
| `ENVIRONMENT` | `production` |
| `DEBUG` | `false` |

6. Add PostgreSQL: New → PostgreSQL → free plan → name it `loanverify-postgres`
7. In the web service, add the DATABASE_URL from the PostgreSQL service

### Step 4 — Seed MongoDB on Render (once)
In Render → your service → Shell:
```bash
python scripts/seed_mongodb.py
```

### Step 5 — Deploy Frontend on Vercel
1. Go to https://vercel.com → New Project → connect GitHub repo
2. **Root Directory**: `frontend`
3. **Framework**: Create React App
4. Add environment variable:
   - `REACT_APP_API_URL` = `https://your-service-name.onrender.com`
5. Deploy

---

## Running Tests

```powershell
cd backend
$env:DATABASE_URL = "sqlite:///./test_run.db"
python -m pytest tests/ -v
```

Results: **76 tests — all passing**

---

## Dataset

| File | Rows | Description |
|------|------|-------------|
| `loan_tape.csv` | 2,000 | Primary dataset with ~7% intentional errors |
| `loan_tape_10000.csv` | 10,000 | Large dataset for performance demo |
| `servicer_update.csv` | 600 | Partial update with newer values |
| `document_manifest.csv` | ~2,000 | Document availability |
| `validation_rules.json` | 18 rules | All validation rule definitions |

Generate fresh data:
```bash
python backend/scripts/generate_dataset.py --rows 10000 --output data/loan_tape_10000.csv
```

---

## API Endpoints (Module H)

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/loans` | List loans (paginated, filterable) |
| GET | `/api/loans/:id` | Get loan by loan_id |
| GET | `/api/exceptions` | List exceptions (filtered) |
| GET | `/api/verified-loans` | List verified records |
| GET | `/api/verified-loans/:id` | Get verified loan |
| GET | `/api/audit/:loanId` | Audit trail for a loan |
| GET | `/api/summary` | Global system summary |
| GET | `/api/docs` | Swagger/OpenAPI UI |

---

## Five-Minute Demo Flow (PDF Section 15)

1. Login as **Data Operator** → upload `data/loan_tape.csv`
2. See import summary — 2,000 rows, ~140 exceptions created
3. Login as **Reviewer** → open Exception Queue
4. Click any HIGH severity exception → Generate AI Recommendation
5. Review explanation, confidence score, suggested value
6. Accept/Edit/Reject → Submit Decision → loan auto-verified
7. Login as **Data Consumer** → Dashboard shows verified count + quality score
8. Open a verified loan → check SHA-256 hash integrity
9. Open Audit Trail → see every event logged
10. Visit `/api/docs` → show live API responses

---

## Known Limitations

- File uploads are stored in `/tmp` on Render (cleared on restart) — use S3 for production
- AI mock mode gives deterministic responses — set `AI_PROVIDER=gemini` for live Gemini API
- No real-time updates — refresh page after background operations

---

*LoanVerify AI — Intain Campus FinTech Challenge 2026*
