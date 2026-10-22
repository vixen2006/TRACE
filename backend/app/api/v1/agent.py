"""
Agent run endpoints with SSE streaming and DB persistence.
Strict tenant isolation: agent runs are created by and scoped to authenticated user.
"""
import json
from datetime import datetime, timezone
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.orchestrator import AgentOrchestrator
from app.agent.state import AgentRunState
from app.core.database import get_db
from app.core.deps import CurrentUser
from app.core.security import decrypt_token
from app.models.models import AgentRun, Connection
from app.schemas.schemas import AgentRunOut, StartRunRequest

router = APIRouter()


@router.post("/runs", response_model=AgentRunOut, status_code=status.HTTP_201_CREATED)
async def start_agent_run(
    payload: StartRunRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AgentRun:
    """
    Initialize an agent investigation task and persist AgentRun record.
    """
    run = AgentRun(
        user_id=current_user.id,
        goal=payload.goal,
        date_range_start=payload.date_start,
        date_range_end=payload.date_end,
        status="pending",
        started_at=datetime.now(timezone.utc),
    )
    db.add(run)
    await db.flush()
    await db.refresh(run)
    return run


@router.get("/runs/{run_id}", response_model=AgentRunOut)
async def get_agent_run_status(
    run_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> AgentRun:
    """Get AgentRun status and tool call count."""
    result = await db.execute(
        select(AgentRun).where(
            AgentRun.id == run_id,
            AgentRun.user_id == current_user.id,
        )
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent run not found.")
    return run


@router.get("/runs/{run_id}/events")
async def stream_run_events(
    run_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Stream agent execution events via Server-Sent Events (SSE).
    """
    # 1. Fetch AgentRun record
    run_res = await db.execute(
        select(AgentRun).where(
            AgentRun.id == run_id,
            AgentRun.user_id == current_user.id,
        )
    )
    run = run_res.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent run not found.")

    # 2. Get user's active GitHub connection
    conn_res = await db.execute(
        select(Connection).where(
            Connection.user_id == current_user.id,
            Connection.provider == "github",
        )
    )
    conn = conn_res.scalar_one_or_none()

    encrypted_token = conn.encrypted_token if conn else ""
    github_handle = (conn.external_username if conn else "") or current_user.display_name

    state = AgentRunState(
        run_id=str(run.id),
        user_id=str(current_user.id),
        goal=run.goal,
        date_range={
            "start": run.date_range_start.isoformat() if run.date_range_start else None,
            "end": run.date_range_end.isoformat() if run.date_range_end else None,
        },
    )

    orchestrator = AgentOrchestrator(encrypted_token=encrypted_token, github_handle=github_handle)

    async def event_generator():
        async for event in orchestrator.run(state):
            yield f"data: {json.dumps(event)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
