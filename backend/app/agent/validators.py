"""
Deterministic contribution-validation rules.
These run in Python — never delegated to the LLM.
Rules enforce attribution, status accuracy, and evidence requirements.
"""
from __future__ import annotations

from typing import Any

from app.agent.state import ContributionClaim, EvidenceGap


class ValidationError(Exception):
    pass


def validate_claim_has_evidence(claim: ContributionClaim) -> None:
    """Every contribution claim must reference at least one evidence record."""
    if not claim.evidence_ids:
        raise ValidationError(
            f"Claim '{claim.summary[:80]}' has no evidence references. "
            "Unsupported claims must not be included in reports."
        )


def validate_status_accuracy(claim: ContributionClaim, activity_metadata: dict[str, Any]) -> list[EvidenceGap]:
    """
    Check that status claims match source facts.
    - merged ≠ deployed: merging a PR does not prove production deployment.
    - reverted PRs must not be listed as shipped.
    - Open PRs must not be described as completed.
    Returns a list of evidence gaps if issues are found.
    """
    gaps: list[EvidenceGap] = []

    pr_state = activity_metadata.get("pr_state")
    is_merged = activity_metadata.get("merged", False)
    is_reverted = activity_metadata.get("reverted", False)

    if claim.status == "shipped" and not is_merged:
        gaps.append(EvidenceGap(
            claim_summary=claim.summary,
            gap_description="Claim describes work as shipped but the PR was not merged.",
            suggested_investigation="Confirm merge status before marking as shipped.",
        ))

    if claim.status == "shipped" and is_reverted:
        gaps.append(EvidenceGap(
            claim_summary=claim.summary,
            gap_description="PR was subsequently reverted; cannot be listed as shipped.",
            suggested_investigation="Check revert commit or PR. Remove or update status.",
        ))

    if claim.outcome and "deployed" in claim.outcome.lower() and not activity_metadata.get("deployment_evidence"):
        gaps.append(EvidenceGap(
            claim_summary=claim.summary,
            gap_description="Claim mentions deployment but no deployment evidence was found. "
                            "A merged PR alone does not establish deployment.",
            suggested_investigation="Look for deployment logs, release tags, or CI/CD records.",
        ))

    return gaps


def validate_attribution(claim: ContributionClaim, github_handle: str, activity_metadata: dict[str, Any]) -> list[EvidenceGap]:
    """
    Ensure the authenticated user is attributed — not just that the activity
    exists on a repository they can see.
    """
    gaps: list[EvidenceGap] = []
    author = activity_metadata.get("author_handle", "")
    reviewers = activity_metadata.get("reviewer_handles", [])

    if claim.contribution_role == "author" and author and author.lower() != github_handle.lower():
        gaps.append(EvidenceGap(
            claim_summary=claim.summary,
            gap_description=f"Claim role is 'author' but the PR/commit author is '{author}', not '{github_handle}'.",
            suggested_investigation="Verify authorship. This may be a team activity rather than a personal contribution.",
        ))

    if claim.contribution_role == "reviewer" and github_handle.lower() not in [r.lower() for r in reviewers]:
        gaps.append(EvidenceGap(
            claim_summary=claim.summary,
            gap_description=f"Claim role is 'reviewer' but '{github_handle}' does not appear in the reviewer list.",
            suggested_investigation="Check review records for this PR.",
        ))

    return gaps


def validate_no_bot_attribution(activity_metadata: dict[str, Any]) -> bool:
    """Return True if the activity appears to be authored by a bot account."""
    author = activity_metadata.get("author_handle", "")
    return author.endswith("[bot]") or "dependabot" in author.lower() or "renovate" in author.lower()


def validate_not_lockfile_only(activity_metadata: dict[str, Any]) -> bool:
    """
    Return True if the PR/commit only touches lock files.
    Lock-file-only changes should not generate contribution claims.
    """
    changed_files = activity_metadata.get("changed_files", [])
    lockfiles = {"package-lock.json", "yarn.lock", "poetry.lock", "Pipfile.lock", "go.sum", "Cargo.lock"}
    if not changed_files:
        return False
    return all(f.split("/")[-1] in lockfiles for f in changed_files)


def validate_confidence(claim: ContributionClaim) -> None:
    if claim.confidence < 0.0 or claim.confidence > 1.0:
        raise ValidationError(f"Confidence must be between 0.0 and 1.0, got {claim.confidence}.")


def run_all_validations(
    claim: ContributionClaim,
    github_handle: str,
    activity_metadata: dict[str, Any],
) -> list[EvidenceGap]:
    """
    Run all deterministic validation rules against a claim.
    Returns accumulated evidence gaps; raises ValidationError for hard failures.
    """
    validate_claim_has_evidence(claim)
    validate_confidence(claim)

    gaps: list[EvidenceGap] = []
    gaps.extend(validate_status_accuracy(claim, activity_metadata))
    gaps.extend(validate_attribution(claim, github_handle, activity_metadata))

    return gaps
