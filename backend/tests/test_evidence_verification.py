"""
Tests for evidence verification engine and rule normalization.
"""
import pytest

from app.services.normalization import verify_activity_claim


def test_merged_authored_pr_verification():
    activity = {
        "activity_type": "pull_request",
        "title": "Add secure authentication middleware",
        "author_handle": "alice_dev",
        "status": "merged",
        "body_preview": "Implemented JWT cookies and tenant security filters.",
        "metadata": {"changed_files": ["app/core/deps.py", "app/api/auth.py"]},
    }

    res = verify_activity_claim(activity, user_github_handle="alice_dev")
    assert res.status == "verified"
    assert res.confidence >= 0.9
    assert res.is_authored is True
    assert len(res.gaps) == 0


def test_noisy_lockfile_diff_filter():
    activity = {
        "activity_type": "pull_request",
        "title": "Update dependencies",
        "author_handle": "alice_dev",
        "status": "merged",
        "metadata": {"changed_files": ["package-lock.json", "yarn.lock"]},
    }

    res = verify_activity_claim(activity, user_github_handle="alice_dev")
    assert res.is_noisy_only is True
    assert res.confidence <= 0.4
    assert any("generated lockfiles" in gap for gap in res.gaps)


def test_reverted_pr_conflicting_evidence():
    activity = {
        "activity_type": "pull_request",
        "title": "Experimental database migration",
        "author_handle": "alice_dev",
        "status": "reverted",
        "metadata": {"changed_files": ["alembic/versions/001.py"]},
    }

    res = verify_activity_claim(activity, user_github_handle="alice_dev")
    assert res.status == "conflicting_evidence"
    assert res.confidence <= 0.3
    assert any("reverted" in gap for gap in res.gaps)
