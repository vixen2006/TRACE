"""
Authorization / permission checks.
Every tool call and API operation must pass through these checks.
The LLM is never trusted to self-authorize; all checks run in deterministic Python.
"""
from uuid import UUID
from fastapi import HTTPException, status


def assert_owns_project(user_id: UUID, project_user_id: UUID) -> None:
    """Raise 403 if the authenticated user does not own the project."""
    if user_id != project_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you do not own this project.",
        )


def assert_owns_contribution(user_id: UUID, contribution_user_id: UUID) -> None:
    if user_id != contribution_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you do not own this contribution.",
        )


def assert_owns_report(user_id: UUID, report_user_id: UUID) -> None:
    if user_id != report_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you do not own this report.",
        )


def assert_owns_agent_run(user_id: UUID, run_user_id: UUID) -> None:
    if user_id != run_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you do not own this agent run.",
        )


def assert_owns_connection(user_id: UUID, connection_user_id: UUID) -> None:
    if user_id != connection_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: you do not own this connection.",
        )
