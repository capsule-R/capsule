"""Pydantic request/response schemas for the REST API."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field


# ── Auth ─────────────────────────────────────────────────────

class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    refresh_token: str


# ── Users ────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None
    avatar_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


# ── Workspaces ───────────────────────────────────────────────

class CreateWorkspaceRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    slug: str = Field(min_length=2, max_length=50, pattern=r"^[a-z0-9-]+$")


class UpdateWorkspaceRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)


class WorkspaceResponse(BaseModel):
    id: str
    name: str
    slug: str
    owner_id: str
    plan_tier: str
    retention_days: int
    storage_used_bytes: int
    storage_quota_bytes: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Workspace members ────────────────────────────────────────

class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: str = Field(default="member", pattern=r"^(admin|member|viewer)$")


class MemberResponse(BaseModel):
    id: str
    user_id: str
    workspace_id: str
    role: str
    accepted_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Sessions ─────────────────────────────────────────────────

class SessionUploadMetadata(BaseModel):
    # Pattern restricts path traversal and header-injection characters
    session_id: str = Field(min_length=1, max_length=128, pattern=r"^[a-zA-Z0-9_\-]+$")
    agent_name: str = Field(min_length=1, max_length=200)
    agent_version: str | None = Field(default=None, max_length=100)
    tags: list[str] = Field(default_factory=list)
    user_metadata: dict[str, Any] = Field(default_factory=dict)
    auto_redact: bool = False


class SessionResponse(BaseModel):
    id: str
    workspace_id: str
    agent_name: str
    agent_version: str | None
    started_at: datetime | None
    ended_at: datetime | None
    duration_ms: int | None
    status: str
    step_count: int
    total_cost_usd: float = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    storage_size_bytes: int
    tags: list[str]
    error_type: str | None
    error_message: str | None
    uploaded_at: datetime
    expires_at: datetime
    view_url: str | None = None

    model_config = {"from_attributes": True}


class SessionListResponse(BaseModel):
    items: list[SessionResponse]
    total: int
    cursor: str | None = None


class DailyCount(BaseModel):
    date: str  # YYYY-MM-DD (UTC)
    count: int


class SessionStatsResponse(BaseModel):
    """Aggregate session metrics for the dashboard overview."""

    total: int                 # all-time, non-deleted
    failed: int                # all-time failed
    total_cost_usd: float      # all-time sum
    total_input_tokens: int
    total_output_tokens: int
    range_days: int
    daily: list[DailyCount]    # captured-per-day over the requested range


# ── Replays ──────────────────────────────────────────────────

class TriggerReplayRequest(BaseModel):
    mode: str = Field(default="cassette", pattern=r"^(cassette|live)$")
    branch_from_step: int | None = None
    modifications: dict[str, Any] = Field(default_factory=dict)


class ReplayResponse(BaseModel):
    id: str
    session_id: str
    status: str
    replay_mode: str
    branch_from_step: int | None
    created_at: datetime


class ReplayStatusResponse(BaseModel):
    """Polled status of a previously-triggered replay job."""

    replay_id: str
    status: str  # queued | running | completed | failed
    result: dict | None = None
    error: str | None = None


# ── Branches ─────────────────────────────────────────────────

class BranchCreateRequest(BaseModel):
    from_step: int = Field(ge=0)
    note: str | None = Field(default=None, max_length=2000)


class BranchCreateResponse(BaseModel):
    branch_id: str


# ── API Keys ─────────────────────────────────────────────────

class CreateApiKeyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    expires_at: datetime | None = None


class ApiKeyResponse(BaseModel):
    id: str
    workspace_id: str
    name: str
    key_prefix: str
    created_at: datetime
    expires_at: datetime | None
    last_used_at: datetime | None
    # full_key only returned on creation
    full_key: str | None = None

    model_config = {"from_attributes": True}


# ── Health ───────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    environment: str


# ── Errors (RFC 7807) ────────────────────────────────────────

class ProblemDetail(BaseModel):
    type: str = "about:blank"
    title: str
    status: int
    detail: str | None = None
    instance: str | None = None
    request_id: str | None = None
