"""FastAPI application entry point for Capsule Cloud API."""

from __future__ import annotations

import time
import uuid
from collections.abc import Sequence
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import structlog
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from capsule_cloud.config import get_settings
from capsule_cloud.database import create_tables
from capsule_cloud.rate_limit import limiter
from capsule_cloud.routers import api_keys, auth, branches, replays, sessions, workspaces
from capsule_cloud.schemas import HealthResponse, ProblemDetail

logger = structlog.get_logger(__name__)

__version__ = "0.1.0"


def _sanitize_pydantic_errors(errors: Sequence[Any]) -> list[dict[str, Any]]:
    """Strip "input" and "ctx" from Pydantic's error dicts before they ever
    reach a response body or a log that captures response bodies. Both can
    embed the raw submitted value — e.g. a too-short-password error's
    "input" field IS the password itself."""
    return [{k: v for k, v in err.items() if k not in ("input", "ctx")} for err in errors]


# ── Lifespan ──────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logger.info("capsule_cloud.startup", environment=settings.environment, version=__version__)
    # Surface Modal replay config at boot (never log the secret values themselves)
    # so it's obvious in Railway logs whether cloud replay is wired up.
    logger.info(
        "capsule_cloud.modal_config",
        modal_token_configured=bool(settings.modal_token_id and settings.modal_token_secret),
        writeback_db_direct_set=bool(settings.database_url_direct),
    )
    await create_tables()
    yield
    logger.info("capsule_cloud.shutdown")


# ── App factory ───────────────────────────────────────────────

def create_app() -> FastAPI:
    settings = get_settings()

    _in_dev = settings.environment == "development"
    app = FastAPI(
        title="Capsule Cloud API",
        version=__version__,
        description=(
            "REST API for the Capsule deterministic replay & time-travel debugger. "
            "Upload, browse, and replay AI agent sessions from any provider."
        ),
        # Disable interactive docs in non-development environments to avoid
        # exposing the full API schema to unauthenticated users in production.
        docs_url="/api/v1/docs" if _in_dev else None,
        redoc_url="/api/v1/redoc" if _in_dev else None,
        openapi_url="/api/v1/openapi.json" if _in_dev else None,
        lifespan=lifespan,
    )

    # ── Rate limiting ────────────────────────────────────────
    app.state.limiter = limiter
    # slowapi's handler is typed for RateLimitExceeded specifically, which is
    # narrower than Starlette's declared Callable[[Request, Exception], ...].
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

    # ── CORS ──────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        **settings.get_cors_config(),
    )

    # ── Security response headers ─────────────────────────────
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):  # type: ignore[no-untyped-def]
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("X-XSS-Protection", "1; mode=block")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        return response

    # ── Request-ID + latency logging middleware ───────────────
    @app.middleware("http")
    async def request_logging(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        t0 = time.perf_counter()
        response = await call_next(request)
        latency_ms = (time.perf_counter() - t0) * 1000
        logger.info(
            "http.request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            latency_ms=round(latency_ms, 2),
            request_id=request_id,
        )
        response.headers["X-Request-ID"] = request_id
        return response

    # ── Global exception handlers ─────────────────────────────

    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):  # type: ignore[no-untyped-def]
        return JSONResponse(
            status_code=404,
            content=ProblemDetail(
                title="Not Found",
                status=404,
                detail=str(exc.detail) if hasattr(exc, "detail") else "Resource not found",
                instance=str(request.url),
                request_id=getattr(request.state, "request_id", None),
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(  # type: ignore[no-untyped-def]
        request: Request, exc: RequestValidationError
    ):
        # This is what FastAPI actually raises for request body/query/path
        # validation failures — NOT a plain HTTPException(422), so it must be
        # registered against the exception class itself. A handler keyed on
        # the bare status code 422 (see below) never intercepts these; that
        # was silently dead code.
        return JSONResponse(
            status_code=422,
            content=ProblemDetail(
                title="Validation Error",
                status=422,
                detail=str(_sanitize_pydantic_errors(exc.errors())),
                instance=str(request.url),
                request_id=getattr(request.state, "request_id", None),
            ).model_dump(),
        )

    @app.exception_handler(422)
    async def validation_error_handler(request: Request, exc):  # type: ignore[no-untyped-def]
        # Covers any *other* code path that raises HTTPException(422)
        # directly (e.g. sessions.py's invalid-metadata-JSON check).
        detail = str(exc)
        if hasattr(exc, "errors"):
            detail = str(_sanitize_pydantic_errors(exc.errors()))
        return JSONResponse(
            status_code=422,
            content=ProblemDetail(
                title="Validation Error",
                status=422,
                detail=detail,
                instance=str(request.url),
                request_id=getattr(request.state, "request_id", None),
            ).model_dump(),
        )

    @app.exception_handler(500)
    async def internal_error_handler(request: Request, exc):  # type: ignore[no-untyped-def]
        try:
            logger.error("unhandled_exception", error=str(exc))
        except Exception:
            pass  # Don't let logging failure cascade
        return JSONResponse(
            status_code=500,
            content=ProblemDetail(
                title="Internal Server Error",
                status=500,
                detail="An unexpected error occurred",
                instance=str(request.url),
                request_id=getattr(request.state, "request_id", None),
            ).model_dump(),
        )

    # ── Health ────────────────────────────────────────────────
    @app.get(
        "/api/v1/health",
        response_model=HealthResponse,
        tags=["health"],
        summary="Health check",
    )
    def health() -> HealthResponse:
        return HealthResponse(version=__version__, environment=settings.environment)

    # ── Routers ───────────────────────────────────────────────
    prefix = "/api/v1"
    app.include_router(auth.router, prefix=prefix)
    app.include_router(workspaces.router, prefix=prefix)
    app.include_router(sessions.router, prefix=prefix)
    app.include_router(api_keys.router, prefix=prefix)
    app.include_router(branches.router, prefix=prefix)
    app.include_router(replays.router, prefix=prefix)

    return app


app = create_app()
