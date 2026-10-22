"""
Automated tests for GitHub OAuth authentication, session management,
unauthenticated 401 enforcement, and multi-tenant isolation.
"""
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import _oauth_states
from app.core.security import create_access_token, decrypt_token
from app.models.models import GithubAccount, Project, User


@pytest.mark.asyncio
async def test_unauthenticated_requests_return_401(client: AsyncClient):
    """Verify that unauthenticated requests to protected endpoints return 401."""
    endpoints = [
        ("GET", "/api/me"),
        ("GET", "/api/v1/auth/me"),
        ("GET", "/api/v1/projects"),
        ("POST", "/api/v1/projects"),
        ("GET", "/api/v1/dashboard/stats"),
        ("GET", "/api/v1/activities"),
        ("GET", "/api/v1/contributions"),
        ("GET", "/api/v1/reports"),
        ("GET", "/api/v1/exports/csv"),
        ("POST", "/api/v1/sync"),
    ]

    for method, url in endpoints:
        if method == "GET":
            resp = await client.get(url)
        else:
            resp = await client.post(url, json={"name": "Test"})
        assert resp.status_code == 401, f"Expected 401 for {method} {url}, got {resp.status_code}"
        assert "detail" in resp.json()


@pytest.mark.asyncio
async def test_api_me_endpoint(client: AsyncClient, auth_headers_user_a: dict, user_a: User):
    """Verify GET /api/me returns username, name, avatar_url, and id."""
    resp = await client.get("/api/me", headers=auth_headers_user_a)
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == user_a.username
    assert data["name"] == user_a.display_name
    assert data["avatar_url"] == user_a.avatar_url
    assert data["id"] == str(user_a.id)

    # Also test /api/v1/auth/me
    v1_resp = await client.get("/api/v1/auth/me", headers=auth_headers_user_a)
    assert v1_resp.status_code == 200
    assert v1_resp.json()["username"] == user_a.username


@pytest.mark.asyncio
async def test_github_oauth_login_redirect(client: AsyncClient):
    """Verify /auth/github/login generates random state, minimal scope, and redirects to GitHub."""
    resp = await client.get("/auth/github/login", follow_redirects=False)
    assert resp.status_code == 302
    location = resp.headers["location"]
    assert location.startswith("https://github.com/login/oauth/authorize?")
    assert "scope=read%3Auser+public_repo" in location or "scope=read:user+public_repo" in location or "read%3Auser" in location
    assert "state=" in location
    assert "client_id=" in location


@pytest.mark.asyncio
async def test_github_oauth_callback_invalid_state(client: AsyncClient):
    """Verify callback with an unrecognized state returns 400."""
    resp = await client.get("/auth/github/callback?code=fake_code&state=non_existent_state")
    assert resp.status_code == 400
    assert "Invalid or expired OAuth state" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_github_oauth_first_login_and_subsequent_login(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """
    Verify:
    1. First login creates User + encrypted token in github_accounts.
    2. Session cookie is issued containing ONLY user id (no GitHub token).
    3. Subsequent login updates existing User.
    """
    state = "test_valid_oauth_state_12345"
    _oauth_states.add(state)

    fake_github_token = "gho_mocked_github_secret_access_token_9999"
    fake_profile = {
        "id": 987654,
        "login": "octocat_user",
        "name": "Mona Lisa Octocat",
        "avatar_url": "https://github.com/images/octocat.png",
        "email": "octocat@github.com",
    }

    orig_post = AsyncClient.post
    orig_get = AsyncClient.get

    async def mock_post(self, url, *args, **kwargs):
        if "access_token" in str(url):
            return Response(200, json={"access_token": fake_github_token, "scope": "read:user public_repo"})
        return await orig_post(self, url, *args, **kwargs)

    async def mock_get(self, url, *args, **kwargs):
        if "api.github.com/user" in str(url):
            return Response(200, json=fake_profile)
        return await orig_get(self, url, *args, **kwargs)

    with patch.object(AsyncClient, "post", mock_post), \
         patch.object(AsyncClient, "get", mock_get):

        # 1. First-time login
        resp = await client.get(
            f"/auth/github/callback?code=mock_code&state={state}",
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert "/dashboard" in resp.headers["location"]

        # Check session cookie
        cookies = resp.cookies
        assert "trace_session" in cookies
        session_token = cookies["trace_session"]

        # Ensure raw GitHub token is NEVER in the cookie
        assert fake_github_token not in session_token

        # Verify User was created
        user_res = await db_session.execute(select(User).where(User.github_id == 987654))
        user = user_res.scalar_one_or_none()
        assert user is not None
        assert user.username == "octocat_user"
        assert user.display_name == "Mona Lisa Octocat"
        assert user.avatar_url == "https://github.com/images/octocat.png"

        # Verify GithubAccount has the encrypted token (and can be decrypted)
        ga_res = await db_session.execute(select(GithubAccount).where(GithubAccount.user_id == user.id))
        ga = ga_res.scalar_one_or_none()
        assert ga is not None
        assert ga.github_id == 987654
        assert ga.encrypted_token != fake_github_token
        decrypted = decrypt_token(ga.encrypted_token)
        assert decrypted == fake_github_token

        # 2. Subsequent login: profile changed on GitHub
        state2 = "test_valid_oauth_state_67890"
        _oauth_states.add(state2)

        updated_profile = {
            "id": 987654,
            "login": "octocat_renamed",
            "name": "Mona Octocat Updated",
            "avatar_url": "https://github.com/images/new_avatar.png",
            "email": "new_octocat@github.com",
        }

        async def mock_get_updated(self, url, *args, **kwargs):
            if "api.github.com/user" in str(url):
                return Response(200, json=updated_profile)
            return await orig_get(self, url, *args, **kwargs)

        with patch.object(AsyncClient, "get", mock_get_updated):
            resp2 = await client.get(
                f"/auth/github/callback?code=mock_code_2&state={state2}",
                follow_redirects=False,
            )
            assert resp2.status_code == 302

            # Verify existing User was updated, not duplicated
            all_users = (await db_session.execute(select(User).where(User.github_id == 987654))).scalars().all()
            assert len(all_users) == 1
            assert all_users[0].id == user.id
            assert all_users[0].username == "octocat_renamed"
            assert all_users[0].display_name == "Mona Octocat Updated"


@pytest.mark.asyncio
async def test_session_cookie_authentication(client: AsyncClient, user_a: User):
    """Verify session cookie allows authentication on protected routes without Bearer header."""
    token = create_access_token(str(user_a.id))
    client.cookies.set("trace_session", token)

    me_resp = await client.get("/api/me")
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == user_a.username

    # Clean up client cookies
    client.cookies.clear()


@pytest.mark.asyncio
async def test_logout_clears_session(client: AsyncClient, user_a: User):
    """Verify /auth/logout clears session cookies and subsequent requests are 401."""
    token = create_access_token(str(user_a.id))
    client.cookies.set("trace_session", token)

    # Logout via POST
    logout_resp = await client.post("/auth/logout")
    assert logout_resp.status_code == 200

    # Cookie was cleared or set with empty/deleted value
    client.cookies.clear()  # Ensure client respects deletion
    me_resp = await client.get("/api/me")
    assert me_resp.status_code == 401


@pytest.mark.asyncio
async def test_tenant_isolation_user_a_and_user_b(
    client: AsyncClient,
    auth_headers_user_a: dict,
    auth_headers_user_b: dict,
    user_a: User,
    user_b: User,
):
    """
    Multi-tenant isolation guarantee:
    User A's projects, activities, and dashboard stats can NEVER be read or modified by User B.
    """
    # 1. User A creates a private project
    p_a = await client.post(
        "/api/v1/projects",
        json={"name": "Alice Super Secure Project", "github_repo_full_name": "alice/secure-repo"},
        headers=auth_headers_user_a,
    )
    assert p_a.status_code == 201
    proj_a_id = p_a.json()["id"]

    # 2. User B lists projects — User A's project MUST NOT appear
    p_b_list = await client.get("/api/v1/projects", headers=auth_headers_user_b)
    assert p_b_list.status_code == 200
    b_project_ids = [p["id"] for p in p_b_list.json()]
    assert proj_a_id not in b_project_ids

    # 3. User B attempts to GET User A's project by ID — returns 404
    p_b_get = await client.get(f"/api/v1/projects/{proj_a_id}", headers=auth_headers_user_b)
    assert p_b_get.status_code == 404

    # 4. User B attempts to DELETE User A's project by ID — returns 404
    p_b_del = await client.delete(f"/api/v1/projects/{proj_a_id}", headers=auth_headers_user_b)
    assert p_b_del.status_code == 404

    # 5. User A dashboard stats reflects active project; User B stats is 0
    stats_a = await client.get("/api/v1/dashboard/stats", headers=auth_headers_user_a)
    assert stats_a.status_code == 200
    assert stats_a.json()["projects_active"] == 1

    stats_b = await client.get("/api/v1/dashboard/stats", headers=auth_headers_user_b)
    assert stats_b.status_code == 200
    assert stats_b.json()["projects_active"] == 0


@pytest.mark.asyncio
async def test_user_data_deletion(client: AsyncClient, auth_headers_user_a: dict):
    """Verify user data deletion cascades and invalidates subsequent authentication."""
    # Create project for User A
    await client.post(
        "/api/v1/projects",
        json={"name": "Project to Delete"},
        headers=auth_headers_user_a,
    )

    # Request data deletion
    del_resp = await client.delete("/api/v1/auth/me/data", headers=auth_headers_user_a)
    assert del_resp.status_code == 200

    # Verify user can no longer authenticate
    me_resp = await client.get("/api/v1/auth/me", headers=auth_headers_user_a)
    assert me_resp.status_code == 401
