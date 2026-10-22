"""
Synchronization API endpoints — triggers background activity ingestion for selected repos.
Enforces OAuth connection ownership.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.models.models import Connection
from app.schemas.schemas import SyncRequest
from app.services.github_sync import sync_github_repository

router = APIRouter()


@router.post("")
async def trigger_sync(
    payload: SyncRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """
    Trigger activity ingestion for specified repositories using user's GitHub connection.
    """
    conn_res = await db.execute(
        select(Connection).where(
            Connection.id == payload.connection_id,
            Connection.user_id == current_user.id,
        )
    )
    conn = conn_res.scalar_one_or_none()
    if not conn:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="GitHub connection not found.")

    conn.sync_status = "syncing"
    await db.flush()

    results = []
    for repo in payload.repo_full_names:
        try:
            res = await sync_github_repository(
                db=db,
                user_id=current_user.id,
                connection_id=conn.id,
                repo_full_name=repo,
                since=payload.since,
            )
            results.append(res)
        except Exception as exc:
            results.append({"repo": repo, "status": "error", "error": str(exc)})

    return {"status": "completed", "results": results}
