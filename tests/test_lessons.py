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


async def _submit_exercise(
    client: AsyncClient,
    token: str,
    exercise_id: str,
    lang: str = "en",
    wpm: float = 30.0,
    accuracy: float = 96.0,
) -> None:
    r = await client.post(
        "/api/v1/sessions/",
        json={
            "language": lang,
            "wpm": wpm,
            "cpm": wpm * 5,
            "accuracy": accuracy,
            "duration_ms": 60000,
            "exercise_id": exercise_id,
        },
        headers=_auth(token),
    )
    assert r.status_code == 200


# ─── lesson list ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_lessons_en_returns_15(client: AsyncClient):
    r = await client.get("/api/v1/lessons/?lang=en")
    assert r.status_code == 200
    assert len(r.json()) == 15


@pytest.mark.asyncio
async def test_list_lessons_ru_returns_15(client: AsyncClient):
    r = await client.get("/api/v1/lessons/?lang=ru")
    assert r.status_code == 200
    assert len(r.json()) == 15


@pytest.mark.asyncio
async def test_list_lessons_anonymous_all_unlocked(client: AsyncClient):
    """Anonymous users see all lessons unlocked."""
    r = await client.get("/api/v1/lessons/?lang=en")
    lessons = r.json()
    for lesson in lessons:
        assert lesson["is_unlocked"] is True


@pytest.mark.asyncio
async def test_list_lessons_authenticated_only_lesson1_unlocked_initially(client: AsyncClient):
    """New authenticated user: lesson 1 unlocked, lesson 2 locked."""
    token = await _register(client, "les_lock", "les_lock@example.com")
    r = await client.get("/api/v1/lessons/?lang=en", headers=_auth(token))
    lessons = r.json()
    assert lessons[0]["is_unlocked"] is True   # lesson 1
    assert lessons[1]["is_unlocked"] is False  # lesson 2


# ─── lesson detail ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_lesson_1_en_has_5_exercises(client: AsyncClient):
    r = await client.get("/api/v1/lessons/1?lang=en")
    assert r.status_code == 200
    assert len(r.json()["exercises"]) == 5


@pytest.mark.asyncio
async def test_get_lesson_1_ru_has_5_exercises(client: AsyncClient):
    r = await client.get("/api/v1/lessons/1?lang=ru")
    assert r.status_code == 200
    assert len(r.json()["exercises"]) == 5


@pytest.mark.asyncio
async def test_get_lesson_returns_allowed_chars(client: AsyncClient):
    r = await client.get("/api/v1/lessons/1?lang=en")
    data = r.json()
    assert "allowed_chars" in data
    assert "a" in data["allowed_chars"]
    assert "f" in data["allowed_chars"]


@pytest.mark.asyncio
async def test_get_lesson_99_returns_404(client: AsyncClient):
    r = await client.get("/api/v1/lessons/99?lang=en")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_lesson_2_locked_for_new_user(client: AsyncClient):
    token = await _register(client, "les_l2lock", "les_l2lock@example.com")
    r = await client.get("/api/v1/lessons/2?lang=en", headers=_auth(token))
    assert r.status_code == 200
    assert r.json()["is_unlocked"] is False


@pytest.mark.asyncio
async def test_lesson_2_unlocks_after_completing_lesson_1(client: AsyncClient):
    """Completing all 5 exercises of lesson 1 unlocks lesson 2."""
    token = await _register(client, "les_unlock", "les_unlock@example.com")
    for i in range(1, 6):
        await _submit_exercise(client, token, f"en-1-{i}", wpm=30.0, accuracy=96.0)

    r = await client.get("/api/v1/lessons/2?lang=en", headers=_auth(token))
    assert r.json()["is_unlocked"] is True


@pytest.mark.asyncio
async def test_lesson_no_progress_for_new_user(client: AsyncClient):
    token = await _register(client, "les_noprog", "les_noprog@example.com")
    r = await client.get("/api/v1/lessons/1?lang=en", headers=_auth(token))
    exercises = r.json()["exercises"]
    for ex in exercises:
        assert ex["progress"] is None


@pytest.mark.asyncio
async def test_lesson_progress_visible_after_session(client: AsyncClient):
    token = await _register(client, "les_prog", "les_prog@example.com")
    await _submit_exercise(client, token, "en-1-1", wpm=35.0, accuracy=97.0)

    r = await client.get("/api/v1/lessons/1?lang=en", headers=_auth(token))
    exercises = {e["id"]: e for e in r.json()["exercises"]}
    assert exercises["en-1-1"]["progress"]["completed"] is True
    assert exercises["en-1-2"]["progress"] is None


# ─── exercise text ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_exercise_text_en(client: AsyncClient):
    r = await client.get("/api/v1/lessons/1/exercises/en-1-1/text?lang=en")
    assert r.status_code == 200
    data = r.json()
    assert len(data["text"]) > 0
    assert data["exercise_id"] == "en-1-1"
    assert data["lesson_id"] == 1


@pytest.mark.asyncio
async def test_get_exercise_text_ru(client: AsyncClient):
    r = await client.get("/api/v1/lessons/1/exercises/ru-1-1/text?lang=ru")
    assert r.status_code == 200
    assert len(r.json()["text"]) > 0


@pytest.mark.asyncio
async def test_exercise_text_en_only_allowed_chars(client: AsyncClient):
    """Lesson 1 EN text only contains home row keys."""
    r = await client.get("/api/v1/lessons/1/exercises/en-1-1/text?lang=en")
    text = r.json()["text"]
    allowed = set("asdfj kl;") | {" "}
    for ch in text:
        assert ch.lower() in allowed or ch == " ", f"Unexpected char: {repr(ch)}"


@pytest.mark.asyncio
async def test_exercise_text_ru_only_allowed_chars(client: AsyncClient):
    """Lesson 1 RU text only contains home row keys."""
    r = await client.get("/api/v1/lessons/1/exercises/ru-1-1/text?lang=ru")
    text = r.json()["text"]
    allowed = set("фывапролджё ") | {" "}
    for ch in text.lower():
        assert ch in allowed or ch == " ", f"Unexpected char: {repr(ch)}"


@pytest.mark.asyncio
async def test_get_nonexistent_exercise_returns_404(client: AsyncClient):
    r = await client.get("/api/v1/lessons/1/exercises/en-1-99/text?lang=en")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_exercise_wrong_lesson_returns_404(client: AsyncClient):
    r = await client.get("/api/v1/lessons/99/exercises/en-99-1/text?lang=en")
    assert r.status_code == 404
