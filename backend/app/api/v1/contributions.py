"""
Contributions API endpoints — verified claims backed by evidence.
Strict tenant isolation: all queries filtered by current_user.id.
"""
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.models.models import Contribution, ContributionEvidence, Evidence
from app.schemas.schemas import ContributionOut

router = APIRouter()


@router.get("", response_model=list[ContributionOut])
async def list_contributions(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    project_id: Optional[UUID] = Query(None),
    verification_status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> list[Contribution]:
    """Return all contribution claims owned by the current user."""
    query = select(Contribution).where(Contribution.user_id == current_user.id)

    if project_id:
        query = query.where(Contribution.project_id == project_id)
    if verification_status:
        query = query.where(Contribution.verification_status == verification_status)

    query = query.order_by(Contribution.created_at.desc()).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/{contribution_id}")
async def get_contribution_details(
    contribution_id: UUID,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Return details of a contribution claim including supporting evidence sources."""
    query = select(Contribution).where(
        Contribution.id == contribution_id,
        Contribution.user_id == current_user.id,
    )
    result = await db.execute(query)
    contrib = result.scalar_one_or_none()
    if not contrib:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contribution claim not found.")

    # Fetch evidence links
    links_query = (
        select(Evidence)
        .join(ContributionEvidence, ContributionEvidence.evidence_id == Evidence.id)
        .where(ContributionEvidence.contribution_id == contribution_id)
    )
    evidence_res = await db.execute(links_query)
    evidence_items = list(evidence_res.scalars().all())

    return {
        "id": str(contrib.id),
        "summary": contrib.summary,
        "contribution_role": contrib.contribution_role,
        "outcome": contrib.outcome,
        "verification_status": contrib.verification_status,
        "confidence": contrib.confidence,
        "created_at": contrib.created_at.isoformat(),
        "evidence": [
            {
                "id": str(e.id),
                "source_type": e.source_type,
                "source_url": e.source_url,
                "observed_at": e.observed_at.isoformat(),
            }
            for e in evidence_items
        ],
    }
