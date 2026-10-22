"""
Dashboard summary endpoint — aggregated stats for the authenticated user.
All queries are scoped by user_id.
"""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.models.models import Activity, Contribution, Project
from app.schemas.schemas import DashboardStats

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DashboardStats:
    """
    Return aggregated dashboard statistics for the current user.
    All counts are scoped to the authenticated user's data.
    """
    # Active projects count
    projects_result = await db.execute(
        select(func.count(Project.id)).where(Project.user_id == current_user.id)
    )
    projects_active = projects_result.scalar() or 0

    # PR counts (by status) — activities in projects owned by the user
    merged_result = await db.execute(
        select(func.count(Activity.id))
        .join(Activity.project)
        .where(
            Project.user_id == current_user.id,
            Activity.activity_type == "pull_request",
            Activity.status == "merged",
        )
    )
    merged_prs = merged_result.scalar() or 0

    open_result = await db.execute(
        select(func.count(Activity.id))
        .join(Activity.project)
        .where(
            Project.user_id == current_user.id,
            Activity.activity_type == "pull_request",
            Activity.status == "open",
        )
    )
    open_prs = open_result.scalar() or 0

    # Total commits
    commits_result = await db.execute(
        select(func.count(Activity.id))
        .join(Activity.project)
        .where(
            Project.user_id == current_user.id,
            Activity.activity_type == "commit",
        )
    )
    total_commits = commits_result.scalar() or 0

    # Contribution verification stats
    total_contribs_result = await db.execute(
        select(func.count(Contribution.id)).where(Contribution.user_id == current_user.id)
    )
    total_contribs = total_contribs_result.scalar() or 0

    verified_result = await db.execute(
        select(func.count(Contribution.id)).where(
            Contribution.user_id == current_user.id,
            Contribution.verification_status == "verified",
        )
    )
    verified_count = verified_result.scalar() or 0

    pending_result = await db.execute(
        select(func.count(Contribution.id)).where(
            Contribution.user_id == current_user.id,
            Contribution.verification_status == "pending",
        )
    )
    needs_verification = pending_result.scalar() or 0

    gap_result = await db.execute(
        select(func.count(Contribution.id)).where(
            Contribution.user_id == current_user.id,
            Contribution.verification_status == "needs_evidence",
        )
    )
    claims_needing_sources = gap_result.scalar() or 0

    evidence_coverage_pct = (
        round((verified_count / total_contribs) * 100, 1) if total_contribs > 0 else 0.0
    )

    return DashboardStats(
        merged_prs=merged_prs,
        open_prs=open_prs,
        total_commits=total_commits,
        projects_active=projects_active,
        evidence_coverage_pct=evidence_coverage_pct,
        claims_needing_sources=claims_needing_sources,
        needs_verification=needs_verification,
    )
