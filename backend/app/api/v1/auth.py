"""
GitHub OAuth authentication endpoints.
GitHub is the sole sign-in method. The flow:
  1. GET /auth/github/login  → redirect to GitHub with random state
  2. GET /auth/github/callback → verify state, exchange code, upsert user + github_account
  3. Set httpOnly session cookie (JWT containing only user ID)
  4. Redirect to frontend dashboard

Tokens are encrypted at rest using TOKEN_ENCRYPTION_KEY.
The GitHub access token never appears in cookies, frontend responses, or LLM context.
"""
import secrets
from typing import Annotated
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import CurrentUser
from app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    encrypt_token,
)
from app.models.models import Connection, GithubAccount, User
from app.schemas.schemas import MeResponse, UserOut

router = APIRouter()

COOKIE_NAME = settings.session_cookie_name or "trace_session"
COOKIE_MAX_AGE = ACCESS_TOKEN_EXPIRE_MINUTES * 60  # seconds

# In-memory state store — use Redis in production
_oauth_states: set[str] = set()


def _set_session_cookie(response: Response, token: str) -> None:
    """Set signed, httpOnly, secure, SameSite=Lax session cookie containing only the user ID."""
    secure = (
        settings.session_cookie_secure
        if settings.session_cookie_secure is not None
        else (settings.environment != "development")
    )
    for name in {COOKIE_NAME, "trace_session", "session"}:
        response.set_cookie(
            key=name,
            value=token,
            max_age=COOKIE_MAX_AGE,
            httponly=True,
            samesite="lax",
            secure=secure,
            path="/",
        )


def _clear_session_cookie(response: Response) -> None:
    """Clear session cookies across all aliases."""
    for name in {COOKIE_NAME, "trace_session", "session"}:
        response.delete_cookie(key=name, path="/")


@router.get("/github/login")
async def github_login() -> RedirectResponse:
    """
    Redirect the user to GitHub's OAuth authorization page.
    A random state value prevents CSRF attacks.
    Scope: read:user and public repo access (minimal needed). Private repo access requires explicit consent.
    """
    state = secrets.token_urlsafe(32)
    _oauth_states.add(state)

    params = {
        "client_id": settings.github_client_id,
        "redirect_uri": settings.github_redirect_uri,
        "scope": "read:user public_repo",
        "state": state,
    }
    auth_url = "https://github.com/login/oauth/authorize?" + urlencode(params)
    return RedirectResponse(url=auth_url, status_code=302)


@router.get("/github/callback")
async def github_callback(
    code: str,
    state: str,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> RedirectResponse:
    """
    Handle GitHub OAuth callback.
    Validates state, exchanges code for access token, fetches GitHub profile,
    upserts User + GithubAccount (encrypted at rest), sets session cookie, redirects to dashboard.
    The raw GitHub token is encrypted before storage and never returned to the client or placed in cookie.
    """
    # Validate state (CSRF protection)
    if state not in _oauth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OAuth state.",
        )
    _oauth_states.discard(state)

    # Exchange code for access token
    async with httpx.AsyncClient(timeout=15) as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
                "redirect_uri": settings.github_redirect_uri,
            },
            headers={"Accept": "application/json"},
        )
        token_data = token_resp.json()

    if "error" in token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"GitHub OAuth error: {token_data.get('error_description', token_data['error'])}",
        )

    raw_token = token_data.get("access_token")
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No access token returned from GitHub.",
        )
    scopes = token_data.get("scope", "")

    # Fetch GitHub user profile
    async with httpx.AsyncClient(timeout=15) as client:
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {raw_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        if user_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch profile from GitHub.",
            )
        github_user = user_resp.json()

    github_id = github_user["id"]
    github_username = github_user["login"]
    avatar_url = github_user.get("avatar_url", "")
    display_name = github_user.get("name") or github_username
    email = github_user.get("email")

    # Upsert user (find by github_id)
    result = await db.execute(select(User).where(User.github_id == github_id))
    user = result.scalar_one_or_none()

    if user:
        # Update profile on later logins
        user.username = github_username
        user.display_name = display_name
        user.avatar_url = avatar_url
        if email:
            user.email = email
    else:
        # First-time login — create user row
        user = User(
            github_id=github_id,
            username=github_username,
            display_name=display_name,
            avatar_url=avatar_url,
            email=email,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)

    # Encrypt the token using TOKEN_ENCRYPTION_KEY
    encrypted = encrypt_token(raw_token)

    # Upsert into github_accounts table
    ga_result = await db.execute(
        select(GithubAccount).where(GithubAccount.user_id == user.id)
    )
    github_account = ga_result.scalar_one_or_none()

    if github_account:
        github_account.github_id = github_id
        github_account.encrypted_token = encrypted
        github_account.scopes = scopes
    else:
        github_account = GithubAccount(
            user_id=user.id,
            github_id=github_id,
            encrypted_token=encrypted,
            scopes=scopes,
        )
        db.add(github_account)

    # Also sync Connection table record for backward compatibility
    conn_result = await db.execute(
        select(Connection).where(
            Connection.user_id == user.id,
            Connection.provider == "github",
        )
    )
    conn = conn_result.scalar_one_or_none()

    if conn:
        conn.encrypted_token = encrypted
        conn.external_user_id = str(github_id)
        conn.external_username = github_username
        conn.scopes = scopes
        conn.sync_status = "idle"
    else:
        conn = Connection(
            user_id=user.id,
            provider="github",
            external_user_id=str(github_id),
            external_username=github_username,
            encrypted_token=encrypted,
            scopes=scopes,
            sync_status="idle",
        )
        db.add(conn)

    await db.flush()

    # Issue session cookie (signed JWT containing ONLY the user ID) and redirect to dashboard
    session_token = create_access_token(str(user.id))
    redirect = RedirectResponse(url=f"{settings.frontend_url}/dashboard", status_code=302)
    _set_session_cookie(redirect, session_token)
    return redirect


@router.post("/logout")
async def logout_post(response: Response) -> dict:
    """Clear the session cookie."""
    _clear_session_cookie(response)
    return {"detail": "Logged out."}


@router.get("/logout")
async def logout_get(response: Response) -> RedirectResponse:
    """Clear session cookie and redirect to login."""
    redirect = RedirectResponse(url=f"{settings.frontend_url}/login", status_code=302)
    _clear_session_cookie(redirect)
    return redirect


@router.get("/me", response_model=MeResponse)
async def get_me(current_user: CurrentUser) -> MeResponse:
    """Return the currently authenticated user's profile."""
    return MeResponse(
        id=current_user.id,
        username=current_user.username,
        name=current_user.display_name or current_user.username,
        display_name=current_user.display_name,
        avatar_url=current_user.avatar_url,
        email=current_user.email,
        timezone=current_user.timezone,
        created_at=current_user.created_at,
    )


@router.delete("/me/data", status_code=status.HTTP_200_OK)
async def delete_user_data(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    response: Response,
) -> dict:
    """
    Request complete data deletion for the authenticated user.
    Deletes connections, github_accounts, projects, activities, contributions, agent runs, reports, and user profile.
    """
    user_id = current_user.id
    await db.delete(current_user)
    await db.flush()
    _clear_session_cookie(response)
    return {"status": "success", "message": f"All engineering memory data for user {user_id} has been permanently deleted."}
