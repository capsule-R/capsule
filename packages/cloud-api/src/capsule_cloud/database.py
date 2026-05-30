"""SQLAlchemy async database setup."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from capsule_cloud.config import get_settings


class Base(DeclarativeBase):
    pass


# Module-level singletons — created once, reused for the process lifetime.
_engine = None
_session_factory = None


def _build_connect_args(url: str) -> dict:
    """Translate libpq-style SSL hints into asyncpg's connect kwargs.

    asyncpg does NOT understand the ``sslmode=`` query param that libpq/psycopg
    use — it expects an ``ssl`` argument instead. Railway's *public* Postgres
    endpoint (``*.proxy.rlwy.net``) terminates TLS and will RESET a plaintext
    connection (→ ``ConnectionReset: [Errno 104]``). The *internal* endpoint
    (``*.railway.internal``) is on the private network and needs no SSL.
    """
    from urllib.parse import urlparse

    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    query = parsed.query.lower()

    # Internal/local hosts: no SSL needed.
    if host.endswith(".railway.internal") or host in ("localhost", "127.0.0.1", ""):
        return {}

    # Anything else (public proxy, external managed PG): require SSL.
    if "sslmode=disable" in query:
        return {}
    return {"ssl": True}


def _strip_ssl_query(url: str) -> str:
    """Remove libpq ``sslmode``/``ssl`` query params asyncpg can't parse."""
    from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl

    parsed = urlparse(url)
    if not parsed.query:
        return url
    kept = [(k, v) for k, v in parse_qsl(parsed.query) if k.lower() not in ("sslmode", "ssl")]
    return urlunparse(parsed._replace(query=urlencode(kept)))


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        url = settings.database_url
        connect_args = _build_connect_args(url)
        url = _strip_ssl_query(url)
        try:
            _engine = create_async_engine(
                url,
                echo=settings.debug,
                pool_pre_ping=True,
                connect_args=connect_args,
            )
        except Exception as exc:
            # Show the URL scheme (never credentials) to help debug
            scheme = url.split("://")[0] if "://" in url else repr(url[:40])
            raise RuntimeError(
                f"Failed to create database engine (URL scheme: {scheme!r}). "
                "Check DATABASE_URL in your environment. "
                f"Original error: {exc}"
            ) from exc
    return _engine


def get_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _session_factory


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
