"""
Shared test fixtures for the STMS test suite.

Uses an in-memory SQLite database and httpx AsyncClient for fast, isolated tests.
"""
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Force test settings before importing app modules
os.environ["ENVIRONMENT"] = "test"
os.environ["DB_DRIVER"] = "sqlite"
os.environ["JWT_SECRET"] = "test-secret-key-do-not-use-in-production"
os.environ["LOG_LEVEL"] = "WARNING"

from app.database import Base, get_db
from app.main import create_app


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def db_engine():
    """Create an async in-memory SQLite engine for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Provide a test database session that rolls back after each test."""
    session_factory = async_sessionmaker(
        bind=db_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with session_factory() as session:
        yield session


# ---------------------------------------------------------------------------
# App / Client fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def app(db_engine):
    """Create a test FastAPI app with the test database."""
    # Initialize mock detectors (they don't need real ML models)
    from app.services import detector_service
    detector_service.initialize_all()

    test_app = create_app()

    # Override the database dependency to use our test engine
    test_session_factory = async_sessionmaker(
        bind=db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def _override_get_db():
        async with test_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    test_app.dependency_overrides[get_db] = _override_get_db
    return test_app


@pytest_asyncio.fixture
async def client(app):
    """Provide an async HTTP test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# Auth helper fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def registered_user(client):
    """Register a test user and return their data + token."""
    response = await client.post("/api/v1/auth/register", json={
        "name": "Test User",
        "email": "test@example.com",
        "password": "testpass123",
    })
    data = response.json()
    return {
        "response": data,
        "token": data.get("token"),
        "user": data.get("user"),
        "headers": {"Authorization": f"Bearer {data.get('token')}"},
    }


@pytest_asyncio.fixture
async def auth_headers(registered_user):
    """Provide just the auth headers for convenience."""
    return registered_user["headers"]


@pytest_asyncio.fixture
async def admin_user(client, db_engine):
    """Create an admin user and return their token and headers."""
    # Register user
    email = "admin@example.com"
    response = await client.post("/api/v1/auth/register", json={
        "name": "Admin User",
        "email": email,
        "password": "adminpassword123",
    })
    data = response.json()
    token = data.get("token")

    # Elevate role in DB
    from sqlalchemy import update
    from app.models.db.user import User
    session_factory = async_sessionmaker(bind=db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await session.execute(update(User).where(User.email == email).values(role="admin"))
        await session.commit()

    return {
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }


@pytest_asyncio.fixture
async def operator_user(client, db_engine):
    """Create an operator user and return their token and headers."""
    email = "operator@example.com"
    response = await client.post("/api/v1/auth/register", json={
        "name": "Operator User",
        "email": email,
        "password": "operatorpassword123",
    })
    data = response.json()
    token = data.get("token")

    # Elevate role in DB
    from sqlalchemy import update
    from app.models.db.user import User
    session_factory = async_sessionmaker(bind=db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        await session.execute(update(User).where(User.email == email).values(role="operator"))
        await session.commit()

    return {
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"},
    }

