"""
FastAPI dependencies for authentication and authorization.
get_current_user is the single choke-point for all authenticated endpoints.
Every endpoint that requires a user must declare it as a dependency.
"""
from typing import Annotated
from uuid import UUID

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_token
from app.models.models import User

bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    trace_session: Annotated[str | None, Cookie(alias="trace_session")] = None,
    session: Annotated[str | None, Cookie(alias="session")] = None,
) -> User:
    """
    Extract the authenticated user from either:
    - Authorization: Bearer <token> header (for API clients / tests)
    - trace_session or session cookie (for browser sessions via GitHub OAuth)

    Raises 401 if no valid credential is present.
    The returned User object is used for all subsequent authorization checks.
    """
    token: str | None = None

    if credentials and credentials.credentials:
        token = credentials.credentials
    elif trace_session:
        token = trace_session
    elif session:
        token = session

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = verify_token(token)
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload.")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found.",
        )

    return user


# Convenience type alias used in route signatures
CurrentUser = Annotated[User, Depends(get_current_user)]
