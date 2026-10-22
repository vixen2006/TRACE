"""FastAPI application entry point."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1 import router as v1_router
from app.api.v1.auth import router as auth_router
from app.core.deps import CurrentUser
from app.schemas.schemas import MeResponse


from app.core.database import engine
from app.models.models import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-create tables on startup if they don't exist
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:
        print(f"[TRACE] Database init note: {exc}")
    yield
    # Shutdown cleanup


app = FastAPI(
    title="TRACE API",
    description="Engineering Memory — verified contribution records powered by a bounded AI agent.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Direct /auth routes for OAuth and session management
app.include_router(auth_router, prefix="/auth", tags=["auth"])

# API V1 routes
app.include_router(v1_router, prefix="/api/v1")


@app.get("/api/me", response_model=MeResponse, tags=["auth"])
@app.get("/api/v1/me", response_model=MeResponse, tags=["auth"])
async def api_me(current_user: CurrentUser) -> MeResponse:
    """Return the current user's profile: username, name, avatar_url, etc."""
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


@app.get("/health")
async def health():
    return {"status": "ok", "service": "trace-api"}
