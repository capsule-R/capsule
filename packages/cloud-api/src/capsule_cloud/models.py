"""SQLAlchemy ORM models — maps to the PostgreSQL schema from TRD Section 9."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from capsule_cloud.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    email_verified_at = Column(DateTime(timezone=True))
    full_name = Column(String)
    avatar_url = Column(String)
    hashed_password = Column(String)          # null for OAuth users
    auth_provider = Column(String, nullable=False, default="email")
    auth_provider_id = Column(String)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)
    deleted_at = Column(DateTime(timezone=True))

    workspaces_owned = relationship("Workspace", back_populates="owner", foreign_keys="[Workspace.owner_id]")
    memberships = relationship("WorkspaceMember", back_populates="user")


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False, index=True)
    owner_id = Column(String, ForeignKey("users.id"), nullable=False)
    plan_tier = Column(String, nullable=False, default="free")
    stripe_customer_id = Column(String)
    stripe_subscription_id = Column(String)
    retention_days = Column(Integer, nullable=False, default=30)
    storage_quota_bytes = Column(BigInteger, nullable=False, default=1 * 1024 * 1024 * 1024)
    storage_used_bytes = Column(BigInteger, nullable=False, default=0)
    settings_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=_now, onupdate=_now)
    deleted_at = Column(DateTime(timezone=True))

    owner = relationship("User", back_populates="workspaces_owned", foreign_keys=[owner_id])
    members = relationship("WorkspaceMember", back_populates="workspace")
    sessions = relationship("Session", back_populates="workspace")
    api_keys = relationship("ApiKey", back_populates="workspace")


class WorkspaceMember(Base):
    __tablename__ = "workspace_members"
    __table_args__ = (UniqueConstraint("workspace_id", "user_id"),)

    id = Column(String, primary_key=True)
    workspace_id = Column(String, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String, nullable=False, default="member")  # owner|admin|member|viewer
    invited_at = Column(DateTime(timezone=True))
    accepted_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    workspace = relationship("Workspace", back_populates="members")
    user = relationship("User", back_populates="memberships")


class Session(Base):
    __tablename__ = "cloud_sessions"

    id = Column(String, primary_key=True)       # SDK-provided session ID
    workspace_id = Column(String, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    agent_name = Column(String, nullable=False)
    agent_version = Column(String)
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True))
    duration_ms = Column(Integer)
    status = Column(String, nullable=False, default="in_progress")
    step_count = Column(Integer, nullable=False, default=0)
    total_input_tokens = Column(Integer, nullable=False, default=0)
    total_output_tokens = Column(Integer, nullable=False, default=0)
    total_cost_usd = Column(Numeric(10, 6), nullable=False, default=0)
    error_type = Column(String)
    error_message = Column(Text)
    tags_json = Column(Text, nullable=False, default="[]")
    user_metadata_json = Column(Text, nullable=False, default="{}")
    storage_path = Column(String, nullable=False)
    storage_size_bytes = Column(BigInteger, nullable=False)
    integrity_hash = Column(String, nullable=False)
    capsule_format_version = Column(String, nullable=False, default="1.0")
    uploaded_by_id = Column(String, ForeignKey("users.id"))
    uploaded_at = Column(DateTime(timezone=True), nullable=False, default=_now)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    deleted_at = Column(DateTime(timezone=True))

    workspace = relationship("Workspace", back_populates="sessions")


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True)
    workspace_id = Column(String, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    key_prefix = Column(String, nullable=False)   # first 8 chars for display
    key_hash = Column(String, nullable=False)     # argon2 hash
    created_by_id = Column(String, ForeignKey("users.id"), nullable=False)
    last_used_at = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    revoked_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)

    workspace = relationship("Workspace", back_populates="api_keys")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True)
    workspace_id = Column(String, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    actor_user_id = Column(String, ForeignKey("users.id"))
    actor_api_key_id = Column(String, ForeignKey("api_keys.id"))
    actor_ip_address = Column(String)
    action = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)
    resource_id = Column(String, nullable=False)
    metadata_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=_now)
