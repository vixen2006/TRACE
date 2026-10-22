"""
Export endpoints — CSV download of verified engineering memory data.
Enforces strict tenant isolation.
"""
from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.models.models import Contribution
from app.services.report_generator import generate_contributions_csv

router = APIRouter()


@router.get("/csv")
async def export_contributions_csv(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    project_id: Optional[UUID] = Query(None),
) -> Response:
    """
    Export the user's verified contribution records as an RFC-4180 compliant CSV.
    Strict tenant isolation: only exports current user's records.
    """
    query = select(Contribution).where(Contribution.user_id == current_user.id)
    if project_id:
        query = query.where(Contribution.project_id == project_id)

    query = query.order_by(Contribution.created_at.desc())
    result = await db.execute(query)
    contributions = list(result.scalars().all())

    data = [
        {
            "id": str(c.id),
            "summary": c.summary,
            "contribution_role": c.contribution_role or "",
            "outcome": c.outcome or "",
            "verification_status": c.verification_status,
            "confidence": c.confidence,
            "created_at": c.created_at.isoformat() if c.created_at else "",
        }
        for c in contributions
    ]

    csv_content = generate_contributions_csv(data)
    filename = f"trace_contributions_{current_user.display_name.lower().replace(' ', '_')}.csv"

    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
