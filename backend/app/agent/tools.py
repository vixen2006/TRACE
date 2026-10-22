"""
Agent tool definitions — callable functions exposed to the LLM.
Every tool validates authorization before executing.
The LLM supplies arguments; Python decides whether the call is permitted.
"""
from __future__ import annotations

import hashlib
import time
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.agent.state import AgentRunState, ToolCallRecord
from app.agent.validators import run_all_validations
from app.core.security import decrypt_token


# ──────────────────────────────────────────────
# GitHub HTTP helpers
# ──────────────────────────────────────────────

GITHUB_API = "https://api.github.com"
GITHUB_HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _github_get(token: str, path: str, params: dict | None = None) -> Any:
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(
            f"{GITHUB_API}{path}",
            headers={**GITHUB_HEADERS, "Authorization": f"Bearer {token}"},
            params=params or {},
        )
        resp.raise_for_status()
        return resp.json()


def _record_tool_call(
    state: AgentRunState,
    tool_name: str,
    arguments: dict,
    result_summary: str,
    source_ids: list[str],
    duration_ms: int,
) -> None:
    state.tool_call_count += 1
    state.tool_call_audit.append(
        ToolCallRecord(
            tool_name=tool_name,
            arguments={k: "[redacted]" if "token" in k else v for k, v in arguments.items()},
            result_summary=result_summary,
            source_ids=source_ids,
            duration_ms=duration_ms,
            timestamp=datetime.utcnow(),
        )
    )


# ──────────────────────────────────────────────
# Tool implementations
# ──────────────────────────────────────────────


async def list_repositories(state: AgentRunState, encrypted_token: str) -> dict:
    """List repositories the authenticated user can access."""
    t0 = time.monotonic()
    token = decrypt_token(encrypted_token)
    data = await _github_get(token, "/user/repos", {"per_page": 100, "type": "all", "sort": "pushed"})
    repos = [{"full_name": r["full_name"], "private": r["private"], "pushed_at": r["pushed_at"]} for r in data]
    _record_tool_call(state, "list_repositories", {}, f"Found {len(repos)} repos", [], int((time.monotonic() - t0) * 1000))
    return {"repositories": repos}


async def fetch_pull_requests(
    state: AgentRunState,
    encrypted_token: str,
    repo_full_name: str,
    since: Optional[str] = None,
    until: Optional[str] = None,
    state_filter: str = "all",
) -> dict:
    """Retrieve PR metadata, status, dates, authors, and links."""
    t0 = time.monotonic()
    token = decrypt_token(encrypted_token)
    params = {"state": state_filter, "per_page": 100, "sort": "updated", "direction": "desc"}
    data = await _github_get(token, f"/repos/{repo_full_name}/pulls", params)

    prs = []
    for pr in data:
        merged_at = pr.get("merged_at")
        prs.append({
            "number": pr["number"],
            "title": pr["title"],
            "state": pr["state"],
            "merged": merged_at is not None,
            "merged_at": merged_at,
            "created_at": pr["created_at"],
            "updated_at": pr["updated_at"],
            "author": pr["user"]["login"],
            "url": pr["html_url"],
            "draft": pr.get("draft", False),
        })

    source_ids = [f"{repo_full_name}#pr:{p['number']}" for p in prs]
    _record_tool_call(
        state, "fetch_pull_requests",
        {"repo": repo_full_name, "since": since, "until": until},
        f"Retrieved {len(prs)} PRs from {repo_full_name}",
        source_ids,
        int((time.monotonic() - t0) * 1000),
    )
    return {"pull_requests": prs, "repo": repo_full_name}


async def get_pr_details(
    state: AgentRunState,
    encrypted_token: str,
    repo_full_name: str,
    pr_number: int,
) -> dict:
    """Inspect a specific PR including files changed and timeline."""
    t0 = time.monotonic()
    token = decrypt_token(encrypted_token)
    pr = await _github_get(token, f"/repos/{repo_full_name}/pulls/{pr_number}")
    files_data = await _github_get(token, f"/repos/{repo_full_name}/pulls/{pr_number}/files", {"per_page": 100})
    changed_files = [f["filename"] for f in files_data]

    result = {
        "number": pr["number"],
        "title": pr["title"],
        "state": pr["state"],
        "merged": pr.get("merged_at") is not None,
        "merged_at": pr.get("merged_at"),
        "author": pr["user"]["login"],
        "url": pr["html_url"],
        "changed_files": changed_files,
        "additions": pr.get("additions", 0),
        "deletions": pr.get("deletions", 0),
        "body_preview": (pr.get("body") or "")[:500],
    }

    _record_tool_call(
        state, "get_pr_details",
        {"repo": repo_full_name, "pr_number": pr_number},
        f"PR #{pr_number}: {pr['title'][:60]} | merged={result['merged']}",
        [f"{repo_full_name}#pr:{pr_number}"],
        int((time.monotonic() - t0) * 1000),
    )
    return result


async def fetch_commits(
    state: AgentRunState,
    encrypted_token: str,
    repo_full_name: str,
    author: str,
    since: Optional[str] = None,
    until: Optional[str] = None,
) -> dict:
    """Fetch commit metadata and attribution for a given author."""
    t0 = time.monotonic()
    token = decrypt_token(encrypted_token)
    params = {"author": author, "per_page": 100}
    if since:
        params["since"] = since
    if until:
        params["until"] = until
    data = await _github_get(token, f"/repos/{repo_full_name}/commits", params)

    commits = [
        {
            "sha": c["sha"][:12],
            "message_preview": (c["commit"]["message"] or "")[:120],
            "date": c["commit"]["committer"]["date"],
            "url": c["html_url"],
            "author": c.get("author", {}).get("login", author) if c.get("author") else author,
        }
        for c in data
    ]

    source_ids = [f"{repo_full_name}@{c['sha']}" for c in commits]
    _record_tool_call(
        state, "fetch_commits",
        {"repo": repo_full_name, "author": author},
        f"Found {len(commits)} commits by {author}",
        source_ids,
        int((time.monotonic() - t0) * 1000),
    )
    return {"commits": commits, "repo": repo_full_name}


async def fetch_reviews(
    state: AgentRunState,
    encrypted_token: str,
    repo_full_name: str,
    pr_number: int,
) -> dict:
    """Retrieve review activity and outcomes for a PR."""
    t0 = time.monotonic()
    token = decrypt_token(encrypted_token)
    data = await _github_get(token, f"/repos/{repo_full_name}/pulls/{pr_number}/reviews")

    reviews = [
        {
            "reviewer": r["user"]["login"],
            "state": r["state"],   # APPROVED | CHANGES_REQUESTED | COMMENTED | DISMISSED
            "submitted_at": r["submitted_at"],
            "url": r["html_url"],
        }
        for r in data
    ]

    _record_tool_call(
        state, "fetch_reviews",
        {"repo": repo_full_name, "pr_number": pr_number},
        f"{len(reviews)} reviews on PR #{pr_number}",
        [f"{repo_full_name}#pr:{pr_number}#reviews"],
        int((time.monotonic() - t0) * 1000),
    )
    return {"reviews": reviews}


async def fetch_issues(
    state: AgentRunState,
    encrypted_token: str,
    repo_full_name: str,
    assignee: Optional[str] = None,
    since: Optional[str] = None,
) -> dict:
    """Retrieve related tickets and their status."""
    t0 = time.monotonic()
    token = decrypt_token(encrypted_token)
    params: dict = {"per_page": 100, "state": "all"}
    if assignee:
        params["assignee"] = assignee
    if since:
        params["since"] = since
    data = await _github_get(token, f"/repos/{repo_full_name}/issues", params)
    # GitHub issues API also returns PRs — filter them
    issues = [
        {
            "number": i["number"],
            "title": i["title"],
            "state": i["state"],
            "url": i["html_url"],
            "created_at": i["created_at"],
            "closed_at": i.get("closed_at"),
            "assignees": [a["login"] for a in i.get("assignees", [])],
        }
        for i in data
        if "pull_request" not in i
    ]

    _record_tool_call(
        state, "fetch_issues",
        {"repo": repo_full_name, "assignee": assignee},
        f"Found {len(issues)} issues",
        [f"{repo_full_name}#issue:{i['number']}" for i in issues],
        int((time.monotonic() - t0) * 1000),
    )
    return {"issues": issues}


async def search_evidence(
    state: AgentRunState,
    query: str,
    project_id: Optional[str] = None,
    activity_type: Optional[str] = None,
) -> dict:
    """
    Find stored activity records by keyword, project, or type.
    Searches the TRACE database — not external APIs.
    (Full DB integration wired in orchestrator.)
    """
    _record_tool_call(
        state, "search_evidence",
        {"query": query, "project_id": project_id, "activity_type": activity_type},
        f"Searched local evidence store for: {query[:60]}",
        [],
        0,
    )
    # Stub — real DB query wired in orchestrator
    return {"results": [], "note": "search_evidence connected to DB in orchestrator"}


async def validate_contribution(
    state: AgentRunState,
    claim_dict: dict,
    github_handle: str,
    activity_metadata: dict,
) -> dict:
    """Apply deterministic attribution and status rules to a claim."""
    from app.agent.state import ContributionClaim
    t0 = time.monotonic()
    claim = ContributionClaim(**claim_dict)
    gaps = run_all_validations(claim, github_handle, activity_metadata)
    _record_tool_call(
        state, "validate_contribution",
        {"claim_summary": claim.summary[:60]},
        f"Validation complete. Gaps found: {len(gaps)}",
        claim.evidence_ids,
        int((time.monotonic() - t0) * 1000),
    )
    return {"claim": claim.model_dump(), "gaps": [g.model_dump() for g in gaps], "valid": len(gaps) == 0}


# ──────────────────────────────────────────────
# Tool registry — maps names to callables
# ──────────────────────────────────────────────

TOOL_REGISTRY: dict[str, Any] = {
    "list_repositories": list_repositories,
    "fetch_pull_requests": fetch_pull_requests,
    "get_pr_details": get_pr_details,
    "fetch_commits": fetch_commits,
    "fetch_reviews": fetch_reviews,
    "fetch_issues": fetch_issues,
    "search_evidence": search_evidence,
    "validate_contribution": validate_contribution,
}

# OpenAI-compatible tool schemas
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "list_repositories",
            "description": "List GitHub repositories accessible to the authenticated user.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_pull_requests",
            "description": "Retrieve PR metadata for a repository. Returns status, author, dates, and merge state.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_full_name": {"type": "string", "description": "owner/repo"},
                    "since": {"type": "string", "description": "ISO 8601 start date"},
                    "until": {"type": "string", "description": "ISO 8601 end date"},
                    "state_filter": {"type": "string", "enum": ["open", "closed", "all"], "default": "all"},
                },
                "required": ["repo_full_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_pr_details",
            "description": "Get full details of a specific PR including files changed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_full_name": {"type": "string"},
                    "pr_number": {"type": "integer"},
                },
                "required": ["repo_full_name", "pr_number"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_commits",
            "description": "Fetch commits by a specific author in a repository, within a date range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_full_name": {"type": "string"},
                    "author": {"type": "string", "description": "GitHub username"},
                    "since": {"type": "string"},
                    "until": {"type": "string"},
                },
                "required": ["repo_full_name", "author"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_reviews",
            "description": "Get code reviews submitted on a PR, including reviewer and outcome.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_full_name": {"type": "string"},
                    "pr_number": {"type": "integer"},
                },
                "required": ["repo_full_name", "pr_number"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_issues",
            "description": "Retrieve issues from a repository, optionally filtered by assignee.",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_full_name": {"type": "string"},
                    "assignee": {"type": "string"},
                    "since": {"type": "string"},
                },
                "required": ["repo_full_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_evidence",
            "description": "Search previously stored TRACE evidence records.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "project_id": {"type": "string"},
                    "activity_type": {"type": "string"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "validate_contribution",
            "description": "Apply deterministic validation rules to a contribution claim before including it in a report.",
            "parameters": {
                "type": "object",
                "properties": {
                    "claim_dict": {"type": "object"},
                    "github_handle": {"type": "string"},
                    "activity_metadata": {"type": "object"},
                },
                "required": ["claim_dict", "github_handle", "activity_metadata"],
            },
        },
    },
]
