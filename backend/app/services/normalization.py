"""
Contribution Normalization & Evidence Verification Engine.
Applies deterministic, rule-based checks on engineering activities to produce verified Contribution claims.
Does NOT rely on LLM confidence scores.
"""
from __future__ import annotations

import re
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

NOISY_FILE_PATTERNS = [
    r"package-lock\.json$",
    r"yarn\.lock$",
    r"pnpm-lock\.yaml$",
    r"go\.sum$",
    r"Cargo\.lock$",
    r"poetry\.lock$",
    r"Gemfile\.lock$",
    r"\.min\.js$",
    r"\.min\.css$",
]


class VerificationResult(BaseModel):
    status: str  # verified | pending | insufficient_evidence | conflicting_evidence
    confidence: float
    gaps: list[str] = Field(default_factory=list)
    is_authored: bool
    is_reviewed: bool
    is_noisy_only: bool = False
    is_coauthored: bool = False


def verify_activity_claim(
    activity: dict[str, Any],
    user_github_handle: str,
    claimed_role: str | None = None,
) -> VerificationResult:
    """
    Perform deterministic validation on a single activity item against user identity.
    """
    gaps = []
    author = (activity.get("author_handle") or "").lower()
    user_handle = (user_github_handle or "").lower()
    act_type = activity.get("activity_type")
    act_status = (activity.get("status") or "").lower()
    title = activity.get("title") or ""
    metadata = activity.get("metadata") or {}

    is_authored = False
    is_reviewed = False
    is_noisy = False
    is_coauthored = False

    # 1. Identity & Role Verification
    if act_type == "pull_request" or act_type == "commit" or act_type == "issue":
        if author == user_handle:
            is_authored = True
        else:
            gaps.append(f"Author handle '{author}' does not match user handle '{user_handle}'.")

    elif act_type == "review":
        if author == user_handle:
            is_reviewed = True
            claimed_role = "reviewer"
        else:
            gaps.append(f"Reviewer handle '{author}' does not match user handle '{user_handle}'.")

    # 2. Lockfile & Noisy Diff Check
    changed_files = metadata.get("changed_files") or []
    if changed_files:
        noisy_count = sum(
            1 for f in changed_files if any(re.search(pat, f, re.IGNORECASE) for pat in NOISY_FILE_PATTERNS)
        )
        if noisy_count == len(changed_files):
            is_noisy = True
            gaps.append("Contribution consists exclusively of generated lockfiles or minified assets.")

    # 3. Co-author Check
    body = (activity.get("body_preview") or "").lower()
    if "co-authored-by:" in body:
        is_coauthored = True

    # 4. Status Check & Verification Matrix
    status_state = "pending"
    confidence = 0.5

    if is_authored or is_reviewed:
        if act_status in ("merged", "approved", "committed", "closed"):
            status_state = "verified"
            confidence = 0.95 if not is_noisy else 0.4
        elif act_status in ("reverted", "changes_requested"):
            status_state = "conflicting_evidence"
            confidence = 0.3
            gaps.append(f"Activity status is '{act_status}' — requires investigation.")
        elif act_status in ("open", "draft"):
            status_state = "pending"
            confidence = 0.7
            gaps.append(f"Work is currently {act_status} (in progress).")
        else:
            status_state = "pending"
            confidence = 0.5
    else:
        status_state = "insufficient_evidence"
        confidence = 0.1
        gaps.append("No direct author or reviewer link established.")

    if is_noisy:
        confidence = min(confidence, 0.4)

    return VerificationResult(
        status=status_state,
        confidence=round(confidence, 2),
        gaps=gaps,
        is_authored=is_authored,
        is_reviewed=is_reviewed,
        is_noisy_only=is_noisy,
        is_coauthored=is_coauthored,
    )
