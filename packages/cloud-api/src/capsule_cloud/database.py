"""SQLAlchemy async database setup."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from capsule_cloud.config import get_settings


class Base(DeclarativeBase):
    pass


def get_engine():
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=settings.debug,
    )


def get_session_factory():
    return async_sessionmaker(get_engine(), class_=AsyncSession, expire_on_commit=False)


async def get_db():
    """FastAPI dependency — yields an async DB session."""
    async_session = get_session_factory()
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all tables (used in dev / tests)."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
