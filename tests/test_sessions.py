import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import TypingSession


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


# ─── DB-level field verification ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_authenticated_session_has_user_id_in_db(
    client: AsyncClient, db_session: AsyncSession
):
    """Core regression: authenticated submit must write user_id (not NULL) to DB."""
    token = await _register(client, "db_uid", "db_uid@example.com")
    resp = await _submit(client, token, wpm=50.0, cpm=250.0, accuracy=95.0)
    session_id = resp["id"]

    row = await db_session.get(TypingSession, session_id)
    assert row is not None, "Session not found in DB"
    assert row.user_id is not None, "user_id is NULL for authenticated session"


@pytest.mark.asyncio
async def test_authenticated_session_user_id_matches_token(
    client: AsyncClient, db_session: AsyncSession
):
    """user_id stored in DB must match the token owner's actual user id."""
    token = await _register(client, "db_match", "db_match@example.com")
    resp = await _submit(client, token, wpm=40.0)
    session_id = resp["id"]

    # Resolve the user from the token via /auth/me
    me = await client.get("/api/v1/auth/me", headers=_auth(token))
    expected_user_id = me.json()["id"]

    row = await db_session.get(TypingSession, session_id)
    assert row.user_id == expected_user_id


@pytest.mark.asyncio
async def test_anonymous_session_has_null_user_id_in_db(
    client: AsyncClient, db_session: AsyncSession
):
    """Anonymous submit must write user_id = NULL to DB (expected behaviour)."""
    resp = await _submit(client)
    session_id = resp["id"]

    row = await db_session.get(TypingSession, session_id)
    assert row is not None
    assert row.user_id is None


@pytest.mark.asyncio
async def test_all_numeric_fields_stored_correctly(
    client: AsyncClient, db_session: AsyncSession
):
    """All numeric fields (wpm, cpm, accuracy, duration_ms) reach the DB intact."""
    token = await _register(client, "db_fields", "db_fields@example.com")
    resp = await _submit(
        client, token,
        wpm=72.5, cpm=362.0, accuracy=98.7, duration_ms=61000, language="ru",
    )
    session_id = resp["id"]

    row = await db_session.get(TypingSession, session_id)
    assert row.wpm == pytest.approx(72.5)
    assert row.cpm == pytest.approx(362.0)
    assert row.accuracy == pytest.approx(98.7)
    assert row.duration_ms == 61000
    assert row.language == "ru"


@pytest.mark.asyncio
async def test_exercise_id_stored_in_db(
    client: AsyncClient, db_session: AsyncSession
):
    """exercise_id field is written to DB when provided."""
    token = await _register(client, "db_exid", "db_exid@example.com")
    resp = await _submit(client, token, exercise_id="en-1-1", wpm=35.0, accuracy=93.0)
    session_id = resp["id"]

    row = await db_session.get(TypingSession, session_id)
    assert row.exercise_id == "en-1-1"


@pytest.mark.asyncio
async def test_multiple_sessions_all_have_user_id(
    client: AsyncClient, db_session: AsyncSession
):
    """Every session in a multi-submit sequence stores the correct user_id."""
    token = await _register(client, "db_multi", "db_multi@example.com")
    ids = []
    for wpm in (30.0, 40.0, 50.0):
        r = await _submit(client, token, wpm=wpm)
        ids.append(r["id"])

    me = await client.get("/api/v1/auth/me", headers=_auth(token))
    expected_uid = me.json()["id"]

    result = await db_session.execute(
        select(TypingSession).where(TypingSession.id.in_(ids))
    )
    rows = result.scalars().all()
    assert len(rows) == 3
    for row in rows:
        assert row.user_id == expected_uid, f"Session {row.id} has user_id={row.user_id}"
