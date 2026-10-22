"""
Pytest configuration and async test fixtures for TRACE backend.
Uses SQLite in-memory database with aiosqlite for fast isolated test runs.
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.models import Base, User

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def prepare_database():
    """Create all tables before each test and drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session():
    """Yield a clean test database session."""
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession):
    """FastAPI AsyncClient configured with test DB dependency override."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def user_a(db_session: AsyncSession) -> User:
    """Create test User A."""
    u = User(
        github_id=10001,
        username="alice",
        email="usera@trace.dev",
        display_name="Alice Developer",
        avatar_url="https://github.com/alice.png",
        timezone="UTC",
    )
    db_session.add(u)
    await db_session.flush()
    await db_session.refresh(u)
    return u


@pytest_asyncio.fixture
async def user_b(db_session: AsyncSession) -> User:
    """Create test User B."""
    u = User(
        github_id=10002,
        username="bob",
        email="userb@trace.dev",
        display_name="Bob Engineer",
        avatar_url="https://github.com/bob.png",
        timezone="UTC",
    )
    db_session.add(u)
    await db_session.flush()
    await db_session.refresh(u)
    return u


@pytest_asyncio.fixture
def auth_headers_user_a(user_a: User) -> dict:
    token = create_access_token(str(user_a.id))
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
def auth_headers_user_b(user_b: User) -> dict:
    token = create_access_token(str(user_b.id))
    return {"Authorization": f"Bearer {token}"}
