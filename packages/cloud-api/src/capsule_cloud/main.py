"""FastAPI application entry point for Capsule Cloud API."""

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from capsule_cloud.config import get_settings
from capsule_cloud.database import create_tables
from capsule_cloud.routers import api_keys, auth, sessions, workspaces
from capsule_cloud.schemas import HealthResponse, ProblemDetail

logger = structlog.get_logger(__name__)

__version__ = "0.1.0"


# ── Lifespan ──────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logger.info("capsule_cloud.startup", environment=settings.environment, version=__version__)
    await create_tables()
    yield
    logger.info("capsule_cloud.shutdown")


# ── App factory ───────────────────────────────────────────────

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Capsule Cloud API",
        version=__version__,
        description=(
            "REST API for the Capsule deterministic replay & time-travel debugger. "
            "Upload, browse, and replay AI agent sessions from any provider."
        ),
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
        openapi_url="/api/v1/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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

    @app.exception_handler(422)
    async def validation_error_handler(request: Request, exc):  # type: ignore[no-untyped-def]
        from fastapi.exceptions import RequestValidationError
        detail = str(exc)
        if hasattr(exc, "errors"):
            detail = str(exc.errors())
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

    return app


app = create_app()
