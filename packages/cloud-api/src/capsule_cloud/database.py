"""SQLAlchemy async database setup."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from capsule_cloud.config import get_settings


class Base(DeclarativeBase):
    pass


def get_engine():
    settings = get_settings()
    return create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    )


def get_session_factory():
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


def get_db():
    """FastAPI dependency — yields a DB session."""
    Session = get_session_factory()
    db = Session()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """Create all tables (used in dev / tests)."""
    engine = get_engine()
    Base.metadata.create_all(engine)
