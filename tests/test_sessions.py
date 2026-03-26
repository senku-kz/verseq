import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_submit_session_anonymous(client: AsyncClient):
    """POST /sessions/ without auth saves session and returns id."""
    response = await client.post(
        "/api/v1/sessions/",
        json={
            "language": "en",
            "wpm": 45.0,
            "cpm": 225.0,
            "accuracy": 92.5,
            "duration_ms": 30000,
            "error_matrix_delta": {},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data


@pytest.mark.asyncio
async def test_submit_session_with_auth(client: AsyncClient):
    """POST /sessions/ with auth token saves session linked to user."""
    # Register user
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "session_test_user",
            "email": "sessiontest@example.com",
            "password": "password123",
        },
    )
    assert reg.status_code == 200
    token = reg.json()["access_token"]

    response = await client.post(
        "/api/v1/sessions/",
        json={
            "language": "en",
            "wpm": 60.0,
            "cpm": 300.0,
            "accuracy": 97.0,
            "duration_ms": 25000,
            "error_matrix_delta": {"as": 1, "sd": 2},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "id" in data


@pytest.mark.asyncio
async def test_list_sessions_requires_auth(client: AsyncClient):
    """GET /sessions/ without token returns 401."""
    response = await client.get("/api/v1/sessions/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_sessions_with_auth(client: AsyncClient):
    """GET /sessions/ with auth returns a list."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "list_sessions_user",
            "email": "listsessions@example.com",
            "password": "password123",
        },
    )
    token = reg.json()["access_token"]

    response = await client.get(
        "/api/v1/sessions/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
