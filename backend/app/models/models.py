"""
SQLAlchemy ORM models — the persistent memory of TRACE.
Every contribution claim references evidence; evidence references activities.
Cross-database compatible (PostgreSQL in production, SQLite in tests).
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import (
    JSON,
    UUID,
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


# ──────────────────────────────────────────────
# Users
# ──────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    github_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(200), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(200))
    avatar_url: Mapped[Optional[str]] = mapped_column(String(1000))
    email: Mapped[Optional[str]] = mapped_column(String(320), unique=True)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    github_account: Mapped[Optional["GithubAccount"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    connections: Mapped[list["Connection"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    projects: Mapped[list["Project"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    contributions: Mapped[list["Contribution"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    agent_runs: Mapped[list["AgentRun"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    reports: Mapped[list["Report"]] = relationship(back_populates="user", cascade="all, delete-orphan")


# ──────────────────────────────────────────────
# GitHub Accounts (OAuth encrypted token storage)
# ──────────────────────────────────────────────
class GithubAccount(Base):
    __tablename__ = "github_accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    github_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    encrypted_token: Mapped[str] = mapped_column(Text, nullable=False)
    scopes: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user: Mapped["User"] = relationship(back_populates="github_account")


# ──────────────────────────────────────────────
# Connections (OAuth integrations)
# ──────────────────────────────────────────────
class Connection(Base):
    __tablename__ = "connections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)  # "github"
    external_user_id: Mapped[str] = mapped_column(String(200), nullable=False)
    external_username: Mapped[Optional[str]] = mapped_column(String(200))
    encrypted_token: Mapped[str] = mapped_column(Text, nullable=False)  # Fernet-encrypted
    scopes: Mapped[Optional[str]] = mapped_column(String(500))
    sync_status: Mapped[str] = mapped_column(String(32), default="idle")  # idle | syncing | error
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship(back_populates="connections")

    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_connection_user_provider"),
    )


# ──────────────────────────────────────────────
# Projects
# ──────────────────────────────────────────────
class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    repository_url: Mapped[Optional[str]] = mapped_column(String(500))
    github_repo_full_name: Mapped[Optional[str]] = mapped_column(String(300))  # "owner/repo"
    description: Mapped[Optional[str]] = mapped_column(Text)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship(back_populates="projects")
    activities: Mapped[list["Activity"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    contributions: Mapped[list["Contribution"]] = relationship(back_populates="project")


# ──────────────────────────────────────────────
# Activities (raw source records)
# ──────────────────────────────────────────────
class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[str] = mapped_column(String(64), nullable=False)       # "github"
    external_id: Mapped[str] = mapped_column(String(200), nullable=False)   # PR number, commit SHA, etc.
    activity_type: Mapped[str] = mapped_column(String(64), nullable=False)  # pull_request | commit | review | issue
    title: Mapped[Optional[str]] = mapped_column(String(500))
    body_preview: Mapped[Optional[str]] = mapped_column(Text)               # first 500 chars — not full text
    occurred_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[Optional[str]] = mapped_column(String(64))               # merged | open | closed | reverted
    url: Mapped[Optional[str]] = mapped_column(String(1000))
    author_handle: Mapped[Optional[str]] = mapped_column(String(200))
    metadata_: Mapped[Optional[dict]] = mapped_column("metadata", JSON)
    synced_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    project: Mapped["Project"] = relationship(back_populates="activities")
    evidence: Mapped[list["Evidence"]] = relationship(back_populates="activity", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("project_id", "provider", "external_id", name="uq_activity_identity"),
        Index("ix_activity_project_type", "project_id", "activity_type"),
        Index("ix_activity_occurred_at", "occurred_at"),
    )


# ──────────────────────────────────────────────
# Evidence (traceability records)
# ──────────────────────────────────────────────
class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    activity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("activities.id", ondelete="CASCADE"), nullable=False)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)   # github_pr | github_commit | etc.
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64))         # SHA-256 of key fields
    permission_classification: Mapped[str] = mapped_column(String(64), default="authorized")

    activity: Mapped["Activity"] = relationship(back_populates="evidence")
    contribution_links: Mapped[list["ContributionEvidence"]] = relationship(back_populates="evidence")


# ──────────────────────────────────────────────
# Contributions (verified claims)
# ──────────────────────────────────────────────
class Contribution(Base):
    __tablename__ = "contributions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("projects.id", ondelete="SET NULL"))
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    contribution_role: Mapped[Optional[str]] = mapped_column(String(200))  # author | reviewer | etc.
    outcome: Mapped[Optional[str]] = mapped_column(Text)
    verification_status: Mapped[str] = mapped_column(String(32), default="pending")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship(back_populates="contributions")
    project: Mapped[Optional["Project"]] = relationship(back_populates="contributions")
    evidence_links: Mapped[list["ContributionEvidence"]] = relationship(
        back_populates="contribution", cascade="all, delete-orphan"
    )


# ──────────────────────────────────────────────
# Contribution ↔ Evidence join
# ──────────────────────────────────────────────
class ContributionEvidence(Base):
    __tablename__ = "contribution_evidence"

    contribution_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("contributions.id", ondelete="CASCADE"), primary_key=True
    )
    evidence_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evidence.id", ondelete="CASCADE"), primary_key=True
    )
    relationship_type: Mapped[str] = mapped_column(String(64), default="supports")

    contribution: Mapped["Contribution"] = relationship(back_populates="evidence_links")
    evidence: Mapped["Evidence"] = relationship(back_populates="contribution_links")


# ──────────────────────────────────────────────
# Agent runs
# ──────────────────────────────────────────────
class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    goal: Mapped[str] = mapped_column(Text, nullable=False)
    date_range_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    date_range_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending | running | completed | failed
    tool_call_count: Mapped[int] = mapped_column(default=0)
    state_snapshot: Mapped[Optional[dict]] = mapped_column(JSON)
    tool_call_audit: Mapped[Optional[list]] = mapped_column(JSON)       # redacted audit trail
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship(back_populates="agent_runs")
    report: Mapped[Optional["Report"]] = relationship(back_populates="agent_run", uselist=False)


# ──────────────────────────────────────────────
# Reports
# ──────────────────────────────────────────────
class Report(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    agent_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("agent_runs.id", ondelete="SET NULL"))
    report_type: Mapped[str] = mapped_column(String(64), default="weekly_summary")
    period_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    content: Mapped[Optional[dict]] = mapped_column(JSON)   # structured report payload
    version: Mapped[int] = mapped_column(default=1)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship(back_populates="reports")
    agent_run: Mapped[Optional["AgentRun"]] = relationship(back_populates="report")
