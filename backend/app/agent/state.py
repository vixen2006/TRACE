"""
Agent run state — the explicit in-memory state held during one bounded execution.
Also contains the Pydantic schemas for agent output validation.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class RunStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    stopped = "stopped"


class ToolCallRecord(BaseModel):
    tool_name: str
    arguments: dict[str, Any]
    result_summary: str          # redacted summary — never raw API responses
    source_ids: list[str] = []
    duration_ms: int
    timestamp: datetime


class EvidenceGap(BaseModel):
    claim_summary: str
    gap_description: str
    suggested_investigation: Optional[str] = None


class ContributionClaim(BaseModel):
    summary: str
    contribution_role: str                # author | reviewer | co-author | reporter
    outcome: Optional[str] = None
    status: str                           # shipped | in_progress | reverted | open
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_ids: list[str]               # must be non-empty
    project_id: Optional[str] = None
    occurred_at: Optional[datetime] = None
    notes: Optional[str] = None


class AgentRunState(BaseModel):
    """Explicit state object maintained throughout one bounded execution loop."""
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    goal: str
    date_range: dict[str, Optional[str]]   # {"start": "ISO", "end": "ISO"}
    project_ids: list[str] = []
    evidence_ids: list[str] = []           # IDs of stored evidence records found so far
    claims: list[ContributionClaim] = []
    unresolved_gaps: list[EvidenceGap] = []
    tool_call_count: int = 0
    tool_call_audit: list[ToolCallRecord] = []
    status: RunStatus = RunStatus.pending
    error: Optional[str] = None


class AgentReport(BaseModel):
    """Validated structured result returned by the agent at the end of a run."""
    run_id: str
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    report_type: str
    shipped: list[ContributionClaim] = []
    in_progress: list[ContributionClaim] = []
    decisions: list[ContributionClaim] = []
    blockers: list[str] = []
    problems_solved: list[ContributionClaim] = []
    evidence_gaps: list[EvidenceGap] = []
    summary_text: str
    confidence_overall: float = Field(ge=0.0, le=1.0)
    generated_at: datetime
