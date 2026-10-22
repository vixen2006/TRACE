"""
Activities API endpoints — filtered, paginated raw activity records.
Strict tenant isolation: queries require project ownership.
"""
from datetime import datetime
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.models.models import Activity, Project
from app.schemas.schemas import ActivityOut

router = APIRouter()


@router.get("", response_model=list[ActivityOut])
async def list_activities(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    project_id: Optional[UUID] = Query(None),
    activity_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[Activity]:
    """
    List raw activity records (PRs, commits, reviews, issues).
    Only returns activities belonging to projects owned by the current user.
    """
    query = (
        select(Activity)
        .join(Activity.project)
        .where(Project.user_id == current_user.id)
    )

    if project_id:
        query = query.where(Activity.project_id == project_id)
    if activity_type:
        query = query.where(Activity.activity_type == activity_type)
    if status_filter:
        query = query.where(Activity.status == status_filter)

    query = query.order_by(Activity.occurred_at.desc().nullslast()).offset(offset).limit(limit)

    result = await db.execute(query)
    return list(result.scalars().all())
