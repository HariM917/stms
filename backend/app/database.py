"""
Async database engine, session factory, and dependency.

Uses SQLAlchemy 2.0 async API with asyncpg (PostgreSQL) or aiosqlite (SQLite).
"""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


# ---------------------------------------------------------------------------
# Engine & Session Factory (created lazily on first use)
# ---------------------------------------------------------------------------

_engine = None
_async_session_factory = None


def _get_engine():
    """Create or return the cached async engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        url = settings.database_url_async

        # Use different pool settings for SQLite vs PostgreSQL
        if "sqlite" in url:
            _engine = create_async_engine(
                url,
                echo=settings.db_echo,
                future=True,
            )
        else:
            _engine = create_async_engine(
                url,
                echo=settings.db_echo,
                future=True,
                pool_size=settings.db_pool_size,
                max_overflow=settings.db_max_overflow,
                pool_recycle=settings.db_pool_recycle,
                pool_pre_ping=True,
            )
    return _engine


def _get_session_factory():
    """Create or return the cached session factory."""
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=_get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _async_session_factory


# ---------------------------------------------------------------------------
# FastAPI Dependency
# ---------------------------------------------------------------------------

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides an async database session.
    Commits on success, rolls back on exception.
    """
    session_factory = _get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ---------------------------------------------------------------------------
# Lifecycle helpers (called from app lifespan)
# ---------------------------------------------------------------------------

async def init_db() -> None:
    """
    Initialize the database.
    In development/testing, creates tables if they don't exist.
    In production, table creation via Base.metadata.create_all is strictly disabled;
    Alembic migrations are required.
    """
    settings = get_settings()
    if settings.is_production:
        engine = _get_engine()
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return

    # Ensure all ORM models are registered in Base.metadata
    import app.models.db.session  # noqa: F401
    import app.models.db.traffic_report  # noqa: F401
    import app.models.db.user  # noqa: F401

    engine = _get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Dispose the engine connection pool."""
    global _engine, _async_session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_factory = None


@asynccontextmanager
async def get_db_context():
    """
    Context manager variant of get_db() for use outside of FastAPI routes
    (e.g., scripts, background tasks).
    """
    session_factory = _get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
