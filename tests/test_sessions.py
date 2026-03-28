import pytest
from httpx import AsyncClient


# ─── helpers ──────────────────────────────────────────────────────────────────

async def _register(client: AsyncClient, username: str, email: str) -> str:
    reg = await client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": "password123"},
    )
    assert reg.status_code == 200
    return reg.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _submit(client: AsyncClient, token: str | None = None, **kwargs) -> dict:
    payload = {
        "language": "en",
        "wpm": 45.0,
        "cpm": 225.0,
        "accuracy": 92.5,
        "duration_ms": 30000,
        **kwargs,
    }
    headers = _auth(token) if token else {}
    r = await client.post("/api/v1/sessions/", json=payload, headers=headers)
    assert r.status_code == 200
    return r.json()


# ─── anonymous submit ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_submit_session_anonymous(client: AsyncClient):
    data = await _submit(client)
    assert "id" in data
    assert data["wpm"] == 45.0
    assert data["cpm"] == 225.0
    assert data["accuracy"] == 92.5
    assert "created_at" in data


@pytest.mark.asyncio
async def test_submit_session_response_fields(client: AsyncClient):
    """Response contains all required fields with correct values."""
    token = await _register(client, "sess_fields", "sess_fields@example.com")
    data = await _submit(client, token, wpm=55.0, cpm=275.0, accuracy=98.0, duration_ms=45000)
    assert data["wpm"] == 55.0
    assert data["cpm"] == 275.0
    assert data["accuracy"] == 98.0
    assert "id" in data
    assert "created_at" in data


# ─── authenticated submit ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_submit_session_with_auth(client: AsyncClient):
    token = await _register(client, "sess_auth", "sess_auth@example.com")
    data = await _submit(client, token, wpm=60.0, cpm=300.0, accuracy=97.0)
    assert "id" in data


@pytest.mark.asyncio
async def test_submit_session_appears_in_list(client: AsyncClient):
    """Session submitted with auth appears in GET /sessions/."""
    token = await _register(client, "sess_list", "sess_list@example.com")
    await _submit(client, token, wpm=42.0)

    r = await client.get("/api/v1/sessions/", headers=_auth(token))
    assert r.status_code == 200
    sessions = r.json()
    assert len(sessions) == 1
    assert sessions[0]["wpm"] == 42.0


@pytest.mark.asyncio
async def test_submit_multiple_sessions_all_appear(client: AsyncClient):
    token = await _register(client, "sess_multi", "sess_multi@example.com")
    await _submit(client, token, wpm=30.0)
    await _submit(client, token, wpm=40.0)
    await _submit(client, token, wpm=50.0)

    r = await client.get("/api/v1/sessions/", headers=_auth(token))
    assert len(r.json()) == 3


# ─── security ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_submit_invalid_token_returns_401(client: AsyncClient):
    """Invalid bearer token on session submit must return 401 (not save anonymously)."""
    r = await client.post(
        "/api/v1/sessions/",
        json={"language": "en", "wpm": 50.0, "cpm": 250.0, "accuracy": 95.0, "duration_ms": 30000},
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_list_sessions_requires_auth(client: AsyncClient):
    r = await client.get("/api/v1/sessions/")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_list_sessions_no_cross_user_leak(client: AsyncClient):
    """User B cannot see User A's sessions."""
    token_a = await _register(client, "sess_userA", "sess_userA@example.com")
    token_b = await _register(client, "sess_userB", "sess_userB@example.com")
    await _submit(client, token_a, wpm=99.0)

    r = await client.get("/api/v1/sessions/", headers=_auth(token_b))
    assert r.json() == []


# ─── error matrix ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_error_matrix_delta_updates_heatmap(client: AsyncClient):
    """error_matrix_delta submitted with session is reflected in heatmap."""
    token = await _register(client, "sess_hm", "sess_hm@example.com")
    await _submit(client, token, error_matrix_delta={"th": 7, "st": 3})

    r = await client.get("/api/v1/stats/heatmap", headers=_auth(token))
    keys = r.json()["keys"]
    assert keys.get("t") == 10   # th=7 + st=3
    assert keys.get("h") == 7
    assert keys.get("s") == 3


@pytest.mark.asyncio
async def test_empty_error_matrix_delta_is_ok(client: AsyncClient):
    """Session without error_matrix_delta submits cleanly."""
    token = await _register(client, "sess_noerr", "sess_noerr@example.com")
    data = await _submit(client, token)
    assert "id" in data


# ─── lesson progress ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_lesson_exercise_session_creates_progress(client: AsyncClient):
    """Session with lesson exercise_id creates LessonProgress, visible in lesson detail."""
    token = await _register(client, "sess_prog", "sess_prog@example.com")
    await _submit(client, token, exercise_id="en-1-1", wpm=30.0, accuracy=96.0)

    r = await client.get("/api/v1/lessons/1?lang=en", headers=_auth(token))
    exercises = {e["id"]: e for e in r.json()["exercises"]}
    prog = exercises["en-1-1"]["progress"]
    assert prog is not None
    assert prog["completed"] is True
    assert prog["best_wpm"] == 30.0


@pytest.mark.asyncio
async def test_lesson_progress_updates_on_better_result(client: AsyncClient):
    """Re-submitting with higher WPM updates best_wpm."""
    token = await _register(client, "sess_best", "sess_best@example.com")
    await _submit(client, token, exercise_id="en-1-1", wpm=25.0, accuracy=90.0)
    await _submit(client, token, exercise_id="en-1-1", wpm=40.0, accuracy=97.0)

    r = await client.get("/api/v1/lessons/1?lang=en", headers=_auth(token))
    exercises = {e["id"]: e for e in r.json()["exercises"]}
    assert exercises["en-1-1"]["progress"]["best_wpm"] == 40.0
