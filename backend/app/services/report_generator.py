"""
Report Generation & Export Service.
Assembles evidence-backed reports (Weekly Summaries, 1-on-1 Notes, Performance Reviews, Interview Stories)
and generates CSV exports.
"""
from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import Activity, Contribution, Report


async def generate_structured_report(
    db: AsyncSession,
    user_id: UUID,
    report_type: str,
    period_start: datetime | None = None,
    period_end: datetime | None = None,
    agent_run_id: UUID | None = None,
) -> Report:
    """
    Generate a report based on stored activities and verified contributions.
    """
    # Fetch user's activities
    query = select(Activity).join(Activity.project).where(Activity.project.has(user_id=user_id))
    if period_start:
        query = query.where(Activity.occurred_at >= period_start)
    if period_end:
        query = query.where(Activity.occurred_at <= period_end)

    result = await db.execute(query.order_by(Activity.occurred_at.desc()))
    activities = list(result.scalars().all())

    shipped = []
    in_progress = []
    reviews = []
    issues = []
    evidence_gaps = []

    for act in activities:
        item = {
            "id": str(act.id),
            "type": act.activity_type,
            "title": act.title,
            "status": act.status,
            "url": act.url,
            "occurred_at": act.occurred_at.isoformat() if act.occurred_at else None,
            "author": act.author_handle,
        }
        if act.status in ("merged", "committed", "closed"):
            shipped.append(item)
        elif act.status in ("open", "draft"):
            in_progress.append(item)
        elif act.activity_type == "review":
            reviews.append(item)

        if not act.url:
            evidence_gaps.append(f"Activity '{act.title}' is missing source URL evidence.")

    content = {
        "title": f"{report_type.replace('_', ' ').title()} ({len(shipped)} shipped, {len(in_progress)} in progress)",
        "summary": f"Total {len(activities)} activities recorded. {len(shipped)} completed, {len(in_progress)} active.",
        "shipped_work": shipped,
        "work_in_progress": in_progress,
        "code_reviews": reviews,
        "evidence_gaps": evidence_gaps,
        "one_on_one_talking_points": [
            f"Discussed progress on {len(shipped)} merged items.",
            f"Review status on {len(in_progress)} active PRs/issues.",
            f"Reviewed code feedback on {len(reviews)} pull requests.",
        ],
        "interview_stories": [
            {
                "situation": "Feature implementation and system improvement.",
                "task": f"Deliver work items across {len(shipped)} merged PRs.",
                "action": "Investigated requirements, wrote code, handled review feedback.",
                "result": f"Successfully shipped {len(shipped)} changes with traceable evidence.",
                "evidence_urls": [s["url"] for s in shipped if s.get("url")][:5],
            }
        ] if shipped else [],
    }

    report = Report(
        user_id=user_id,
        agent_run_id=agent_run_id,
        report_type=report_type,
        period_start=period_start,
        period_end=period_end,
        content=content,
        version=1,
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)
    return report


def generate_contributions_csv(contributions_data: list[dict[str, Any]]) -> str:
    """Generate RFC 4180 compliant CSV content for export."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Contribution ID",
        "Summary",
        "Role",
        "Outcome",
        "Verification Status",
        "Confidence",
        "Created At",
    ])

    for row in contributions_data:
        writer.writerow([
            row.get("id", ""),
            row.get("summary", ""),
            row.get("contribution_role", ""),
            row.get("outcome", ""),
            row.get("verification_status", ""),
            row.get("confidence", 0.0),
            row.get("created_at", ""),
        ])

    return output.getvalue()
