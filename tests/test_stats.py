import pytest
from httpx import AsyncClient


async def _register_and_token(client: AsyncClient, username: str, email: str) -> str:
    reg = await client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": "password123"},
    )
    assert reg.status_code == 200
    return reg.json()["access_token"]


@pytest.mark.asyncio
async def test_stats_requires_auth(client: AsyncClient):
    response = await client.get("/api/v1/stats/")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_stats_with_auth_returns_valid_response(client: AsyncClient):
    token = await _register_and_token(client, "stats_user1", "statsuser1@example.com")
    response = await client.get(
        "/api/v1/stats/",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "avg_wpm" in data
    assert "best_wpm" in data
    assert "avg_accuracy" in data
    assert "total_sessions" in data
    assert "sessions" in data
    # Empty sessions is OK for a new user
    assert isinstance(data["sessions"], list)


@pytest.mark.asyncio
async def test_achievements_returns_10_for_new_user(client: AsyncClient):
    token = await _register_and_token(client, "achiev_user1", "achievuser1@example.com")
    response = await client.get(
        "/api/v1/stats/achievements",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "achievements" in data
    assert len(data["achievements"]) == 10
    # All should be unlocked=False for brand new user
    for a in data["achievements"]:
        assert a["unlocked"] is False


@pytest.mark.asyncio
async def test_certificate_eligible_false_for_new_user(client: AsyncClient):
    token = await _register_and_token(client, "cert_user1", "certuser1@example.com")
    response = await client.get(
        "/api/v1/stats/certificate",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["eligible"] is False


@pytest.mark.asyncio
async def test_streak_zero_for_new_user(client: AsyncClient):
    token = await _register_and_token(client, "streak_user1", "streakuser1@example.com")
    response = await client.get(
        "/api/v1/stats/streak",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["current_streak"] == 0
