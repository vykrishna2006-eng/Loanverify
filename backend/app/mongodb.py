"""
MongoDB connection — used exclusively for authentication (users + roles).
Loan data, exceptions, audit trail, verified loans all stay in PostgreSQL.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from app.config import settings

# ── Async client (used in FastAPI async route handlers) ──────────────────────
_async_client: AsyncIOMotorClient = None


def get_async_client() -> AsyncIOMotorClient:
    global _async_client
    if _async_client is None:
        _async_client = AsyncIOMotorClient(settings.MONGODB_URL)
    return _async_client


def get_auth_db():
    """Returns the async MongoDB database for authentication."""
    return get_async_client()[settings.MONGODB_DB_NAME]


# ── Sync client (used in seed scripts and startup tasks) ─────────────────────
def get_sync_db():
    """Returns a synchronous MongoDB database — for seeding and one-off scripts."""
    client = MongoClient(settings.MONGODB_URL)
    return client[settings.MONGODB_DB_NAME]


async def connect_mongodb():
    """Call on app startup to verify MongoDB connection."""
    client = get_async_client()
    await client.admin.command("ping")
    print(f"[OK] MongoDB connected: {settings.MONGODB_DB_NAME}")


async def close_mongodb():
    """Call on app shutdown."""
    global _async_client
    if _async_client:
        _async_client.close()
        _async_client = None
