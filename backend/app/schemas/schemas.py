"""
Pydantic schemas for auth, users, projects, activities, contributions,
agent runs, and reports. Separates API contracts from ORM models.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# Auth / Users
# ──────────────────────────────────────────────
class UserOut(BaseModel):
    id: UUID
    username: str
    name: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    email: Optional[str] = None
    timezone: str = "UTC"
    created_at: datetime

    model_config = {"from_attributes": True}


class MeResponse(BaseModel):
    id: UUID
    username: str
    name: Optional[str] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    email: Optional[str] = None
    timezone: str = "UTC"
    created_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────
# Connections
# ──────────────────────────────────────────────
class ConnectionOut(BaseModel):
    id: UUID
    provider: str
    external_username: Optional[str]
    sync_status: str
    last_synced_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────
# Projects
# ──────────────────────────────────────────────
class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    repository_url: Optional[str] = None
    github_repo_full_name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class ProjectOut(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    repository_url: Optional[str]
    github_repo_full_name: Optional[str]
    description: Optional[str]
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────
# Activities
# ──────────────────────────────────────────────
class ActivityOut(BaseModel):
    id: UUID
    project_id: UUID
    provider: str
    external_id: str
    activity_type: str
    title: Optional[str]
    occurred_at: Optional[datetime]
    status: Optional[str]
    url: Optional[str]
    author_handle: Optional[str]
    synced_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────
# Contributions
# ──────────────────────────────────────────────
class ContributionOut(BaseModel):
    id: UUID
    user_id: UUID
    project_id: Optional[UUID]
    summary: str
    contribution_role: Optional[str]
    outcome: Optional[str]
    verification_status: str
    confidence: float
    created_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────
# Agent runs
# ──────────────────────────────────────────────
class StartRunRequest(BaseModel):
    goal: str = Field(min_length=5, max_length=2000)
    date_start: Optional[datetime] = None
    date_end: Optional[datetime] = None
    project_ids: list[UUID] = []


class AgentRunOut(BaseModel):
    id: UUID
    user_id: UUID
    goal: str
    status: str
    tool_call_count: int
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────
# Reports
# ──────────────────────────────────────────────
class ReportOut(BaseModel):
    id: UUID
    user_id: UUID
    report_type: str
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    content: Optional[dict]
    version: int
    generated_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────
# Sync
# ──────────────────────────────────────────────
class SyncRequest(BaseModel):
    connection_id: UUID
    repo_full_names: list[str] = []
    since: Optional[datetime] = None


# ──────────────────────────────────────────────
# Dashboard summary
# ──────────────────────────────────────────────
class DashboardStats(BaseModel):
    merged_prs: int = 0
    open_prs: int = 0
    total_commits: int = 0
    projects_active: int = 0
    evidence_coverage_pct: float = 0.0
    claims_needing_sources: int = 0
    needs_verification: int = 0
