from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# SQLite for testing, PostgreSQL for production
_db_url = settings.DATABASE_URL
_connect_args = {}
_pool_kwargs = {}

if _db_url.startswith("sqlite"):
    _connect_args = {"check_same_thread": False}
else:
    # psycopg3 uses "postgresql+psycopg://..." — auto-convert legacy URL format
    if _db_url.startswith("postgresql://") and "+psycopg" not in _db_url:
        _db_url = _db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    _pool_kwargs = {"pool_pre_ping": True, "pool_size": 10, "max_overflow": 20}

engine = create_engine(
    _db_url,
    connect_args=_connect_args,
    echo=settings.DEBUG,
    **_pool_kwargs,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema():
    """Add columns introduced after the original schema without dropping data."""
    from sqlalchemy import text, inspect

    inspector = inspect(engine)
    if "loan_records" not in inspector.get_table_names():
        return

    existing = {c["name"] for c in inspector.get_columns("loan_records")}
    dialect = engine.dialect.name
    json_type = "JSONB" if dialect == "postgresql" else "JSON"
    additions = {
        "borrower_state": "VARCHAR(10)",
        "term_months": "INTEGER",
        "last_updated_at": "DATE",
        "credit_grade": "VARCHAR(20)",
        "employment_length": "VARCHAR(50)",
        "income_band": "VARCHAR(50)",
        "source_system": "VARCHAR(100)",
        "parse_errors": json_type,
    }
    with engine.begin() as conn:
        for name, col_type in additions.items():
            if name not in existing:
                conn.execute(text(f"ALTER TABLE loan_records ADD COLUMN {name} {col_type}"))
        if dialect == "postgresql":
            conn.execute(text("ALTER TABLE ai_recommendations ADD COLUMN IF NOT EXISTS prompt_text TEXT"))
        else:
            ai_cols = {c["name"] for c in inspector.get_columns("ai_recommendations")} if "ai_recommendations" in inspector.get_table_names() else set()
            if "prompt_text" not in ai_cols and "ai_recommendations" in inspector.get_table_names():
                conn.execute(text("ALTER TABLE ai_recommendations ADD COLUMN prompt_text TEXT"))
