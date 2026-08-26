"""
Seed MongoDB with demo users for LoanVerify AI.
Run once after setting up MongoDB Atlas or local MongoDB.

Usage:
    cd backend
    python scripts/seed_mongodb.py

Environment variable needed:
    MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pymongo import MongoClient
import bcrypt
import uuid
from datetime import datetime

from app.config import settings
from app.auth import get_password_hash

def seed():
    print(f"Connecting to MongoDB: {settings.MONGODB_URL[:40]}...")
    client = MongoClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DB_NAME]

    users_col = db["users"]
    roles_col = db["roles"]

    # ── Seed roles ────────────────────────────────────────────────────────────
    roles = [
        {"id": "r1", "name": "DATA_OPERATOR",  "description": "Upload CSV, run validation"},
        {"id": "r2", "name": "REVIEWER",        "description": "Review exceptions, approve loans"},
        {"id": "r3", "name": "DATA_CONSUMER",   "description": "View verified loans, export data"},
    ]
    for role in roles:
        if not roles_col.find_one({"name": role["name"]}):
            roles_col.insert_one(role)
            print(f"  [OK] Role seeded: {role['name']}")
        else:
            print(f"  [-] Role exists: {role['name']}")

    # ── Seed demo users ───────────────────────────────────────────────────────
    demo_users = [
        {
            "id":              str(uuid.uuid4()),
            "email":           "operator@loanverify.ai",
            "full_name":       "Alex Operator",
            "hashed_password": get_password_hash("password123"),
            "role_name":       "DATA_OPERATOR",
            "is_active":       True,
            "created_at":      datetime.utcnow(),
        },
        {
            "id":              str(uuid.uuid4()),
            "email":           "reviewer@loanverify.ai",
            "full_name":       "Riley Reviewer",
            "hashed_password": get_password_hash("password123"),
            "role_name":       "REVIEWER",
            "is_active":       True,
            "created_at":      datetime.utcnow(),
        },
        {
            "id":              str(uuid.uuid4()),
            "email":           "consumer@loanverify.ai",
            "full_name":       "Casey Consumer",
            "hashed_password": get_password_hash("password123"),
            "role_name":       "DATA_CONSUMER",
            "is_active":       True,
            "created_at":      datetime.utcnow(),
        },
    ]

    for user in demo_users:
        if not users_col.find_one({"email": user["email"]}):
            users_col.insert_one(user)
            print(f"  [OK] User seeded: {user['email']} ({user['role_name']})")
        else:
            print(f"  [-] User exists: {user['email']}")

    # Create index on email for fast lookup
    users_col.create_index("email", unique=True)
    users_col.create_index("id",    unique=True)
    print("\n[OK] MongoDB seed complete!")
    print("\nDemo credentials:")
    print("  operator@loanverify.ai  / password123  (DATA_OPERATOR)")
    print("  reviewer@loanverify.ai  / password123  (REVIEWER)")
    print("  consumer@loanverify.ai  / password123  (DATA_CONSUMER)")

    client.close()


if __name__ == "__main__":
    seed()
