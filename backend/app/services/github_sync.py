"""
GitHub Sync Service — ingests engineering activity for authorized repositories.
Stores normalized Activity records and Evidence traceability links.
Enforces multi-user security: only consumes decrypted token of the owning user.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_token
from app.models.models import Activity, Connection, Evidence, Project

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"


async def _github_request(token: str, path: str, params: dict | None = None) -> Any:
    """Execute authenticated GitHub REST request with timeout handling."""
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "TRACE-Engineering-Memory/1.0",
    }
    async with httpx.AsyncClient(timeout=25.0) as client:
        resp = await client.get(f"{GITHUB_API}{path}", headers=headers, params=params or {})
        resp.raise_for_status()
        return resp.json()


def _compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


async def sync_github_repository(
    db: AsyncSession,
    user_id: UUID,
    connection_id: UUID,
    repo_full_name: str,
    since: Optional[datetime] = None,
) -> dict:
    """
    Ingest PRs, Commits, Reviews, and Issues for a given repository.
    Strict tenant scope: user_id must match Connection ownership.
    """
    # 1. Fetch connection & decrypt token
    conn_result = await db.execute(
        select(Connection).where(
            Connection.id == connection_id,
            Connection.user_id == user_id,
        )
    )
    conn = conn_result.scalar_one_or_none()
    if not conn:
        raise ValueError("Connection not found or unauthorized.")

    token = decrypt_token(conn.encrypted_token)

    # 2. Get or create Project record for this user
    proj_result = await db.execute(
        select(Project).where(
            Project.user_id == user_id,
            Project.github_repo_full_name == repo_full_name,
        )
    )
    project = proj_result.scalar_one_or_none()
    if not project:
        project = Project(
            user_id=user_id,
            name=repo_full_name.split("/")[-1] if "/" in repo_full_name else repo_full_name,
            github_repo_full_name=repo_full_name,
            repository_url=f"https://github.com/{repo_full_name}",
            description=f"GitHub repository {repo_full_name}",
        )
        db.add(project)
        await db.flush()

    synced_counts = {"pull_requests": 0, "commits": 0, "reviews": 0, "issues": 0}

    # 3. Ingest Pull Requests
    try:
        pr_params = {"state": "all", "per_page": 100, "sort": "updated", "direction": "desc"}
        prs_data = await _github_request(token, f"/repos/{repo_full_name}/pulls", pr_params)
        for pr in prs_data:
            ext_id = str(pr["number"])
            merged_at = pr.get("merged_at")
            state = "merged" if merged_at else pr["state"]
            created_dt = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))

            existing = await db.execute(
                select(Activity).where(
                    Activity.project_id == project.id,
                    Activity.provider == "github",
                    Activity.external_id == ext_id,
                    Activity.activity_type == "pull_request",
                )
            )
            act = existing.scalar_one_or_none()

            meta = {
                "number": pr["number"],
                "draft": pr.get("draft", False),
                "merged": merged_at is not None,
                "merged_at": merged_at,
                "head_branch": pr.get("head", {}).get("ref"),
                "base_branch": pr.get("base", {}).get("ref"),
            }

            if not act:
                act = Activity(
                    project_id=project.id,
                    provider="github",
                    external_id=ext_id,
                    activity_type="pull_request",
                    title=pr["title"],
                    body_preview=(pr.get("body") or "")[:500],
                    occurred_at=created_dt,
                    status=state,
                    url=pr["html_url"],
                    author_handle=pr["user"]["login"] if pr.get("user") else None,
                    metadata_=meta,
                )
                db.add(act)
                await db.flush()

                # Add evidence
                ev = Evidence(
                    activity_id=act.id,
                    source_type="github_pr",
                    source_url=pr["html_url"],
                    content_hash=_compute_hash(f"{pr['title']}:{state}:{act.author_handle}"),
                    permission_classification="authorized",
                )
                db.add(ev)
            else:
                act.title = pr["title"]
                act.status = state
                act.metadata_ = meta

            synced_counts["pull_requests"] += 1

            # Ingest PR reviews
            try:
                reviews_data = await _github_request(token, f"/repos/{repo_full_name}/pulls/{pr['number']}/reviews")
                for r in reviews_data:
                    rev_ext_id = f"pr_{pr['number']}_rev_{r['id']}"
                    rev_existing = await db.execute(
                        select(Activity).where(
                            Activity.project_id == project.id,
                            Activity.provider == "github",
                            Activity.external_id == rev_ext_id,
                            Activity.activity_type == "review",
                        )
                    )
                    if not rev_existing.scalar_one_or_none():
                        rev_dt = datetime.fromisoformat(r["submitted_at"].replace("Z", "+00:00")) if r.get("submitted_at") else created_dt
                        rev_act = Activity(
                            project_id=project.id,
                            provider="github",
                            external_id=rev_ext_id,
                            activity_type="review",
                            title=f"Review on PR #{pr['number']}: {r['state']}",
                            body_preview=(r.get("body") or "")[:500],
                            occurred_at=rev_dt,
                            status=r["state"].lower(),
                            url=r["html_url"],
                            author_handle=r["user"]["login"] if r.get("user") else None,
                            metadata_={"pr_number": pr["number"], "review_state": r["state"]},
                        )
                        db.add(rev_act)
                        await db.flush()

                        db.add(Evidence(
                            activity_id=rev_act.id,
                            source_type="github_review",
                            source_url=r["html_url"],
                            content_hash=_compute_hash(f"rev:{pr['number']}:{r['state']}:{rev_act.author_handle}"),
                        ))
                        synced_counts["reviews"] += 1
            except Exception as rev_err:
                logger.warning(f"Failed to sync reviews for PR #{pr['number']}: {rev_err}")

    except Exception as err:
        logger.error(f"Error syncing PRs for {repo_full_name}: {err}")

    # 4. Ingest Commits
    try:
        commit_params = {"per_page": 100}
        commits_data = await _github_request(token, f"/repos/{repo_full_name}/commits", commit_params)
        for c in commits_data:
            sha = c["sha"]
            c_date_str = c["commit"]["committer"]["date"]
            c_dt = datetime.fromisoformat(c_date_str.replace("Z", "+00:00"))
            author = c.get("author", {}).get("login") if c.get("author") else c["commit"]["author"]["name"]

            c_existing = await db.execute(
                select(Activity).where(
                    Activity.project_id == project.id,
                    Activity.provider == "github",
                    Activity.external_id == sha,
                    Activity.activity_type == "commit",
                )
            )
            if not c_existing.scalar_one_or_none():
                commit_act = Activity(
                    project_id=project.id,
                    provider="github",
                    external_id=sha,
                    activity_type="commit",
                    title=(c["commit"]["message"] or "").split("\n")[0][:200],
                    body_preview=(c["commit"]["message"] or "")[:500],
                    occurred_at=c_dt,
                    status="committed",
                    url=c["html_url"],
                    author_handle=author,
                    metadata_={"sha": sha, "tree": c["commit"]["tree"]["sha"]},
                )
                db.add(commit_act)
                await db.flush()

                db.add(Evidence(
                    activity_id=commit_act.id,
                    source_type="github_commit",
                    source_url=c["html_url"],
                    content_hash=_compute_hash(f"{sha}:{author}"),
                ))
                synced_counts["commits"] += 1
    except Exception as err:
        logger.error(f"Error syncing commits for {repo_full_name}: {err}")

    # 5. Ingest Issues
    try:
        issue_params = {"state": "all", "per_page": 100}
        issues_data = await _github_request(token, f"/repos/{repo_full_name}/issues", issue_params)
        for issue in issues_data:
            if "pull_request" in issue:
                continue  # skip PRs returned in issues endpoint

            iss_ext_id = str(issue["number"])
            iss_dt = datetime.fromisoformat(issue["created_at"].replace("Z", "+00:00"))

            iss_existing = await db.execute(
                select(Activity).where(
                    Activity.project_id == project.id,
                    Activity.provider == "github",
                    Activity.external_id == iss_ext_id,
                    Activity.activity_type == "issue",
                )
            )
            if not iss_existing.scalar_one_or_none():
                iss_act = Activity(
                    project_id=project.id,
                    provider="github",
                    external_id=iss_ext_id,
                    activity_type="issue",
                    title=issue["title"],
                    body_preview=(issue.get("body") or "")[:500],
                    occurred_at=iss_dt,
                    status=issue["state"],
                    url=issue["html_url"],
                    author_handle=issue["user"]["login"] if issue.get("user") else None,
                    metadata_={
                        "number": issue["number"],
                        "closed_at": issue.get("closed_at"),
                        "assignees": [a["login"] for a in issue.get("assignees", [])],
                    },
                )
                db.add(iss_act)
                await db.flush()

                db.add(Evidence(
                    activity_id=iss_act.id,
                    source_type="github_issue",
                    source_url=issue["html_url"],
                    content_hash=_compute_hash(f"issue:{issue['number']}:{issue['state']}"),
                ))
                synced_counts["issues"] += 1
    except Exception as err:
        logger.error(f"Error syncing issues for {repo_full_name}: {err}")

    # Update connection status
    conn.sync_status = "idle"
    conn.last_synced_at = datetime.now(timezone.utc)
    await db.flush()

    return {
        "status": "success",
        "repo": repo_full_name,
        "synced": synced_counts,
        "last_synced_at": conn.last_synced_at.isoformat(),
    }
