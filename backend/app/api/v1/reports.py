"""
Reports API endpoints — generation and retrieval of evidence-backed reports.
Strict tenant isolation on all queries.
"""
from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.models.models import Report
from app.schemas.schemas import ReportOut
from app.services.report_generator import generate_structured_report

router = APIRouter()


class GenerateReportPayload(BaseModel):
    report_type: str = "weekly_summary"  # weekly_summary | one_to_one | perf_review | interview_story
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


@router.get("", response_model=list[ReportOut])
async def list_reports(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(20, ge=1, le=100),
) -> list[Report]:
    """List generated reports for current user."""
    query = (
        select(Report)
        .where(Report.user_id == current_user.id)
        .order_by(Report.generated_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
async def generate_report(
    payload: GenerateReportPayload,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Report:
    """Generate a new structured engineering report from stored evidence."""
    report = await generate_structured_report(
        db=db,
        user_id=current_user.id,
        report_type=payload.report_type,
        period_start=payload.period_start,
        period_end=payload.period_end,
    )
    return report


@router.get("/{report_id}", response_model=ReportOut)
async def get_report(
    report_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Report:
    """Get report by ID with ownership verification."""
    result = await db.execute(
        select(Report).where(
            Report.id == report_id,
            Report.user_id == current_user.id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found.")
    return report
