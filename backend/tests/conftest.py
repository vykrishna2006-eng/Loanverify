"""
Test configuration and shared fixtures.
Uses an in-memory SQLite database for isolation.
Auth (MongoDB) is mocked so tests run without a real MongoDB connection.
"""
import os
# Must be set BEFORE any app imports so database.py uses SQLite
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

import pytest
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.auth import get_password_hash, verify_password, create_access_token, get_current_user
from app.models.mongo_user import MongoUser

# ── In-memory SQLite for tests ────────────────────────────────────────────────
SQLALCHEMY_TEST_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# In-process user registry keyed by email — populated by seed_db
_TEST_USERS: dict = {}       # email -> MongoUser
_TEST_USERS_BY_ID: dict = {} # id    -> MongoUser


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db):
    def override_get_db():
        yield db
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Role->name mapping ────────────────────────────────────────────────────────
_ROLE_NAMES = {1: "DATA_OPERATOR", 2: "REVIEWER", 3: "DATA_CONSUMER"}


@pytest.fixture()
def seed_db(db):
    """Seed minimal roles and users. Also registers MongoUser objects in the
    in-process registry so patched auth works without MongoDB."""
    from app.models.user import Role, User

    # Roles
    r1 = Role(id=1, name="DATA_OPERATOR",  description="Operator")
    r2 = Role(id=2, name="REVIEWER",       description="Reviewer")
    r3 = Role(id=3, name="DATA_CONSUMER",  description="Consumer")
    db.add_all([r1, r2, r3])

    _TEST_USERS.clear()
    _TEST_USERS_BY_ID.clear()

    entries = [
        ("operator@test.com", "Test Operator", "testpass", 1),
        ("reviewer@test.com",  "Test Reviewer", "testpass", 2),
        ("consumer@test.com",  "Test Consumer", "testpass", 3),
    ]
    sql_users = []
    for email, full_name, password, role_id in entries:
        uid = str(uuid4())
        hashed = get_password_hash(password)
        sql_user = User(id=uid, email=email, full_name=full_name,
                        hashed_password=hashed, role_id=role_id)
        db.add(sql_user)
        mongo_user = MongoUser(
            id=uid, email=email, full_name=full_name,
            hashed_password=hashed,
            role_name=_ROLE_NAMES[role_id],
            is_active=True,
            created_at=datetime.utcnow(),
        )
        _TEST_USERS[email] = mongo_user
        _TEST_USERS_BY_ID[uid] = mongo_user
        sql_users.append(sql_user)

    db.commit()
    return {
        "operator": sql_users[0],
        "reviewer": sql_users[1],
        "consumer": sql_users[2],
    }


# ── Patch MongoDB-backed auth helpers ─────────────────────────────────────────

import app.auth as _auth_module


@pytest.fixture(autouse=True)
def patch_auth(monkeypatch):
    """Replace all MongoDB-backed auth helpers with in-process lookups.

    IMPORTANT: routers/auth.py does `from app.auth import authenticate_user`,
    so we patch it in app.routers.auth (where it was imported INTO).
    _get_user_by_id is called inside app.auth, so we patch it there.
    get_auth_db is patched everywhere via app.mongodb + the router's import.
    """
    import app.routers.auth as _router_auth_module
    import app.mongodb as _mongodb_module

    # ── In-memory async MongoDB collection mock ───────────────────────────────
    _in_memory_users: list = []  # list of dicts, like a MongoDB collection

    class _AsyncCursor:
        def __init__(self, docs): self._docs = docs
        def __aiter__(self): return self
        async def __anext__(self):
            if not self._docs:
                raise StopAsyncIteration
            return self._docs.pop(0)

    class _FakeCollection:
        def __init__(self, store): self._store = store
        async def find_one(self, query):
            for doc in self._store:
                if all(doc.get(k) == v for k, v in query.items()):
                    return doc
            return None
        async def insert_one(self, doc):
            self._store.append(doc)
            return type("InsertResult", (), {"inserted_id": doc.get("id")})()
        def find(self, query=None):
            results = [d for d in self._store
                       if not query or all(d.get(k) == v for k, v in query.items())]
            return _AsyncCursor(results)

    class _FakeDB:
        def __getitem__(self, name):
            if name == "users":
                return _FakeCollection(_in_memory_users)
            return _FakeCollection([])

    _fake_db = _FakeDB()

    def mock_get_auth_db():
        return _fake_db

    # Patch get_auth_db in all places it's imported
    monkeypatch.setattr(_mongodb_module, "get_auth_db", mock_get_auth_db)
    monkeypatch.setattr(_router_auth_module, "get_auth_db", mock_get_auth_db)

    # ── auth function mocks ───────────────────────────────────────────────────

    async def mock_authenticate(email: str, password: str):
        user = _TEST_USERS.get(email)
        if user and verify_password(password, user.hashed_password):
            return user
        return None

    async def mock_get_user_by_id(user_id: str):
        return _TEST_USERS_BY_ID.get(user_id)

    # Patch where the name is USED (router), not where it was defined
    monkeypatch.setattr(_router_auth_module, "authenticate_user", mock_authenticate)
    # Patch in app.auth so get_current_user's internal call works too
    monkeypatch.setattr(_auth_module, "_get_user_by_id", mock_get_user_by_id)

    # ── FastAPI dependency override ───────────────────────────────────────────
    from jose import jwt, JWTError
    from fastapi import HTTPException, status
    from fastapi.security import OAuth2PasswordBearer

    async def mock_get_current_user(token: str = __import__("fastapi").Depends(
            OAuth2PasswordBearer(tokenUrl="/api/auth/token"))):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, _auth_module.settings.SECRET_KEY,
                                 algorithms=[_auth_module.settings.ALGORITHM])
            user_id: str = payload.get("sub")
            if not user_id:
                raise credentials_exception
        except JWTError:
            raise credentials_exception
        user = _TEST_USERS_BY_ID.get(user_id)
        if not user or not user.is_active:
            raise credentials_exception
        return user

    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    app.dependency_overrides.pop(get_current_user, None)


# ── Token fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture()
def operator_token(client, seed_db):
    res = client.post("/api/auth/token", data={"username": "operator@test.com", "password": "testpass"})
    return res.json()["access_token"]


@pytest.fixture()
def reviewer_token(client, seed_db):
    res = client.post("/api/auth/token", data={"username": "reviewer@test.com", "password": "testpass"})
    return res.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# ── Sample loan record ─────────────────────────────────────────────────────────

@pytest.fixture()
def sample_loan_record(db, seed_db):
    """Create a minimal valid LoanRecord for tests."""
    from app.models.upload import Upload
    from app.models.loan import LoanRecord

    upload = Upload(
        id=str(uuid4()),
        filename="test.csv",
        original_filename="test.csv",
        source_type="LOAN_TAPE",
        total_rows=1,
        imported_rows=1,
        failed_rows=0,
        status="COMPLETED",
        uploaded_by=seed_db["operator"].id,
    )
    db.add(upload)

    loan = LoanRecord(
        id=str(uuid4()),
        upload_id=upload.id,
        source_row=1,
        loan_id="L000001",
        borrower_id="B001",
        borrower_name="Test Borrower",
        original_principal=Decimal("300000.00"),
        current_balance=Decimal("280000.00"),
        interest_rate=Decimal("4.500"),
        origination_date=date(2018, 6, 15),
        maturity_date=date(2048, 6, 15),
        last_payment_date=date(2024, 1, 15),
        payment_status="CURRENT",
        days_past_due=0,
        document_status="COMPLETE",
        property_state="CA",
    )
    db.add(loan)
    db.commit()
    return {"upload": upload, "loan": loan}

