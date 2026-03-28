import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import TypingSession


# ─── helpers ──────────────────────────────────────────────────────────────────

async def _register(client: AsyncClient, username: str, email: str) -> str:
    """Register a user and return their access token."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={"username": username, "email": email, "password": "password123"},
    )
    assert reg.status_code == 200
    return reg.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


async def _submit_session(
    client: AsyncClient,
    token: str,
    *,
    wpm: float = 30.0,
    cpm: float = 150.0,
    accuracy: float = 90.0,
    duration_ms: int = 60000,
    language: str = "en",
    exercise_id: str | None = None,
    error_matrix_delta: dict | None = None,
) -> dict:
    payload: dict = {
        "language": language,
        "wpm": wpm,
        "cpm": cpm,
        "accuracy": accuracy,
        "duration_ms": duration_ms,
    }
    if exercise_id:
        payload["exercise_id"] = exercise_id
    if error_matrix_delta is not None:
        payload["error_matrix_delta"] = error_matrix_delta
    response = await client.post(
        "/api/v1/sessions/",
        json=payload,
        headers=_auth(token),
    )
    assert response.status_code == 200
    return response.json()


async def _user_id(client: AsyncClient, token: str) -> int:
    r = await client.get("/api/v1/auth/me", headers=_auth(token))
    return r.json()["id"]


# ─── /stats/ ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stats_empty_for_new_user(client: AsyncClient):
    token = await _register(client, "st_empty", "st_empty@example.com")
    r = await client.get("/api/v1/stats/", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert data["total_sessions"] == 0
    assert data["avg_wpm"] == 0.0
    assert data["best_wpm"] == 0.0
    assert data["avg_accuracy"] == 0.0
    assert data["sessions"] == []
    assert data["total_chars_typed"] == 0
    assert data["streak_days"] == 0


@pytest.mark.asyncio
async def test_stats_computed_after_sessions(client: AsyncClient):
    token = await _register(client, "st_compute", "st_compute@example.com")
    await _submit_session(client, token, wpm=40.0, accuracy=90.0)
    await _submit_session(client, token, wpm=60.0, accuracy=100.0)

    r = await client.get("/api/v1/stats/", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert data["total_sessions"] == 2
    assert data["best_wpm"] == 60.0
    assert data["avg_wpm"] == 50.0
    assert data["avg_accuracy"] == 95.0


@pytest.mark.asyncio
async def test_stats_sessions_sorted_newest_first(client: AsyncClient):
    token = await _register(client, "st_order", "st_order@example.com")
    await _submit_session(client, token, wpm=20.0)
    await _submit_session(client, token, wpm=50.0)

    r = await client.get("/api/v1/stats/", headers=_auth(token))
    sessions = r.json()["sessions"]
    # Most recent session was the 50 WPM one
    assert sessions[0]["wpm"] == 50.0
    assert sessions[1]["wpm"] == 20.0


@pytest.mark.asyncio
async def test_stats_lang_filter_en(client: AsyncClient):
    token = await _register(client, "st_lang_en", "st_lang_en@example.com")
    await _submit_session(client, token, wpm=40.0, language="en")
    await _submit_session(client, token, wpm=80.0, language="ru")

    r = await client.get("/api/v1/stats/", params={"lang": "en"}, headers=_auth(token))
    data = r.json()
    assert data["total_sessions"] == 1
    assert data["best_wpm"] == 40.0


@pytest.mark.asyncio
async def test_stats_lang_filter_ru(client: AsyncClient):
    token = await _register(client, "st_lang_ru", "st_lang_ru@example.com")
    await _submit_session(client, token, wpm=40.0, language="en")
    await _submit_session(client, token, wpm=80.0, language="ru")

    r = await client.get("/api/v1/stats/", params={"lang": "ru"}, headers=_auth(token))
    data = r.json()
    assert data["total_sessions"] == 1
    assert data["best_wpm"] == 80.0


@pytest.mark.asyncio
async def test_stats_total_chars_computed(client: AsyncClient):
    # cpm=300, duration_ms=60000 → 300 * 60000 / 60000 = 300 chars
    token = await _register(client, "st_chars", "st_chars@example.com")
    await _submit_session(client, token, cpm=300.0, duration_ms=60000)

    r = await client.get("/api/v1/stats/", headers=_auth(token))
    assert r.json()["total_chars_typed"] == 300


@pytest.mark.asyncio
async def test_stats_no_cross_user_leak(client: AsyncClient):
    """User A's sessions must not appear in User B's stats."""
    token_a = await _register(client, "st_userA", "st_userA@example.com")
    token_b = await _register(client, "st_userB", "st_userB@example.com")
    await _submit_session(client, token_a, wpm=99.0)

    r = await client.get("/api/v1/stats/", headers=_auth(token_b))
    assert r.json()["total_sessions"] == 0


# ─── /stats/ cpm fields ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_stats_cpm_fields_present(client: AsyncClient):
    """Response includes avg_cpm and best_cpm fields."""
    token = await _register(client, "st_cpm_fields", "st_cpm_fields@example.com")
    r = await client.get("/api/v1/stats/", headers=_auth(token))
    data = r.json()
    assert "avg_cpm" in data
    assert "best_cpm" in data


@pytest.mark.asyncio
async def test_stats_cpm_zero_for_new_user(client: AsyncClient):
    token = await _register(client, "st_cpm_zero", "st_cpm_zero@example.com")
    r = await client.get("/api/v1/stats/", headers=_auth(token))
    data = r.json()
    assert data["avg_cpm"] == 0.0
    assert data["best_cpm"] == 0.0


@pytest.mark.asyncio
async def test_stats_best_cpm_computed(client: AsyncClient):
    token = await _register(client, "st_best_cpm", "st_best_cpm@example.com")
    await _submit_session(client, token, cpm=200.0)
    await _submit_session(client, token, cpm=350.0)
    await _submit_session(client, token, cpm=280.0)

    r = await client.get("/api/v1/stats/", headers=_auth(token))
    assert r.json()["best_cpm"] == 350.0


@pytest.mark.asyncio
async def test_stats_avg_cpm_computed(client: AsyncClient):
    token = await _register(client, "st_avg_cpm", "st_avg_cpm@example.com")
    await _submit_session(client, token, cpm=100.0)
    await _submit_session(client, token, cpm=300.0)

    r = await client.get("/api/v1/stats/", headers=_auth(token))
    assert r.json()["avg_cpm"] == 200.0


# ─── /stats/heatmap ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_heatmap_empty_for_new_user(client: AsyncClient):
    token = await _register(client, "hm_empty", "hm_empty@example.com")
    r = await client.get("/api/v1/stats/heatmap", headers=_auth(token))
    assert r.status_code == 200
    assert r.json()["keys"] == {}


@pytest.mark.asyncio
async def test_heatmap_populated_after_error_matrix(client: AsyncClient):
    """error_matrix_delta={'th': 5, 'st': 3} → keys t=8, h=5, s=3."""
    token = await _register(client, "hm_data", "hm_data@example.com")
    await _submit_session(client, token, error_matrix_delta={"th": 5, "st": 3})

    r = await client.get("/api/v1/stats/heatmap", headers=_auth(token))
    keys = r.json()["keys"]
    assert keys.get("t") == 8   # t from "th"=5 + "st"=3
    assert keys.get("h") == 5
    assert keys.get("s") == 3


@pytest.mark.asyncio
async def test_heatmap_accumulates_across_sessions(client: AsyncClient):
    """Second session adds to existing error matrix."""
    token = await _register(client, "hm_accum", "hm_accum@example.com")
    await _submit_session(client, token, error_matrix_delta={"th": 5})
    await _submit_session(client, token, error_matrix_delta={"th": 3})

    r = await client.get("/api/v1/stats/heatmap", headers=_auth(token))
    keys = r.json()["keys"]
    # "th" total = 8 → t=8, h=8
    assert keys.get("t") == 8
    assert keys.get("h") == 8


# ─── /stats/achievements ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_achievements_all_locked_new_user(client: AsyncClient):
    token = await _register(client, "ach_new", "ach_new@example.com")
    r = await client.get("/api/v1/stats/achievements", headers=_auth(token))
    assert r.status_code == 200
    achievements = r.json()["achievements"]
    assert len(achievements) == 10
    for a in achievements:
        assert a["unlocked"] is False
        assert a["unlocked_at"] is None


@pytest.mark.asyncio
async def test_achievement_first_session_unlocked(client: AsyncClient):
    token = await _register(client, "ach_fs", "ach_fs@example.com")
    await _submit_session(client, token)

    r = await client.get("/api/v1/stats/achievements", headers=_auth(token))
    by_id = {a["id"]: a for a in r.json()["achievements"]}
    assert by_id["first_session"]["unlocked"] is True
    assert by_id["first_session"]["unlocked_at"] is not None


@pytest.mark.asyncio
async def test_achievement_wpm_30_unlocked(client: AsyncClient):
    token = await _register(client, "ach_30", "ach_30@example.com")
    await _submit_session(client, token, wpm=30.0)

    by_id = {a["id"]: a for a in (
        await client.get("/api/v1/stats/achievements", headers=_auth(token))
    ).json()["achievements"]}
    assert by_id["wpm_30"]["unlocked"] is True
    assert by_id["wpm_50"]["unlocked"] is False
    assert by_id["wpm_70"]["unlocked"] is False


@pytest.mark.asyncio
async def test_achievement_wpm_50_unlocked(client: AsyncClient):
    token = await _register(client, "ach_50", "ach_50@example.com")
    await _submit_session(client, token, wpm=50.0)

    by_id = {a["id"]: a for a in (
        await client.get("/api/v1/stats/achievements", headers=_auth(token))
    ).json()["achievements"]}
    assert by_id["wpm_30"]["unlocked"] is True
    assert by_id["wpm_50"]["unlocked"] is True
    assert by_id["wpm_70"]["unlocked"] is False


@pytest.mark.asyncio
async def test_achievement_wpm_70_unlocked(client: AsyncClient):
    token = await _register(client, "ach_70", "ach_70@example.com")
    await _submit_session(client, token, wpm=70.0)

    by_id = {a["id"]: a for a in (
        await client.get("/api/v1/stats/achievements", headers=_auth(token))
    ).json()["achievements"]}
    assert by_id["wpm_30"]["unlocked"] is True
    assert by_id["wpm_50"]["unlocked"] is True
    assert by_id["wpm_70"]["unlocked"] is True


@pytest.mark.asyncio
async def test_achievement_accuracy_95_unlocked(client: AsyncClient):
    token = await _register(client, "ach_a95", "ach_a95@example.com")
    await _submit_session(client, token, accuracy=95.0)

    by_id = {a["id"]: a for a in (
        await client.get("/api/v1/stats/achievements", headers=_auth(token))
    ).json()["achievements"]}
    assert by_id["accuracy_95"]["unlocked"] is True
    assert by_id["accuracy_99"]["unlocked"] is False


@pytest.mark.asyncio
async def test_achievement_accuracy_99_unlocked(client: AsyncClient):
    token = await _register(client, "ach_a99", "ach_a99@example.com")
    await _submit_session(client, token, accuracy=99.0)

    by_id = {a["id"]: a for a in (
        await client.get("/api/v1/stats/achievements", headers=_auth(token))
    ).json()["achievements"]}
    assert by_id["accuracy_95"]["unlocked"] is True
    assert by_id["accuracy_99"]["unlocked"] is True


@pytest.mark.asyncio
async def test_achievement_first_lesson_unlocked(client: AsyncClient):
    token = await _register(client, "ach_les", "ach_les@example.com")
    await _submit_session(client, token, exercise_id="en-1-1", wpm=25.0, accuracy=95.0)

    by_id = {a["id"]: a for a in (
        await client.get("/api/v1/stats/achievements", headers=_auth(token))
    ).json()["achievements"]}
    assert by_id["first_lesson"]["unlocked"] is True
    assert by_id["first_lesson"]["unlocked_at"] is not None


@pytest.mark.asyncio
async def test_achievement_unlocked_at_is_set(client: AsyncClient):
    """unlocked_at timestamp is present and parseable for unlocked achievements."""
    token = await _register(client, "ach_ts", "ach_ts@example.com")
    await _submit_session(client, token, wpm=35.0)

    by_id = {a["id"]: a for a in (
        await client.get("/api/v1/stats/achievements", headers=_auth(token))
    ).json()["achievements"]}
    ts = by_id["wpm_30"]["unlocked_at"]
    assert ts is not None
    # Must be a valid ISO datetime string
    datetime.fromisoformat(ts.replace("Z", "+00:00"))


# ─── /stats/certificate ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_certificate_not_eligible_new_user(client: AsyncClient):
    token = await _register(client, "cert_new", "cert_new@example.com")
    r = await client.get("/api/v1/stats/certificate", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert data["eligible"] is False
    assert data["tier"] is None


@pytest.mark.asyncio
async def test_certificate_not_eligible_high_wpm_low_accuracy(client: AsyncClient):
    """Speed without accuracy — no certificate."""
    token = await _register(client, "cert_miss", "cert_miss@example.com")
    await _submit_session(client, token, wpm=80.0, accuracy=90.0)

    r = await client.get("/api/v1/stats/certificate", headers=_auth(token))
    assert r.json()["eligible"] is False


@pytest.mark.asyncio
async def test_certificate_silver_tier(client: AsyncClient):
    token = await _register(client, "cert_sil", "cert_sil@example.com")
    await _submit_session(client, token, wpm=42.0, accuracy=96.5)

    r = await client.get("/api/v1/stats/certificate", headers=_auth(token))
    data = r.json()
    assert data["eligible"] is True
    assert data["tier"] == "silver"
    assert data["wpm"] == 42.0
    assert data["accuracy"] == 96.5
    assert data["date"] is not None


@pytest.mark.asyncio
async def test_certificate_gold_tier(client: AsyncClient):
    token = await _register(client, "cert_gld", "cert_gld@example.com")
    await _submit_session(client, token, wpm=52.0, accuracy=98.0)

    r = await client.get("/api/v1/stats/certificate", headers=_auth(token))
    data = r.json()
    assert data["eligible"] is True
    assert data["tier"] == "gold"
    assert data["wpm"] == 52.0


@pytest.mark.asyncio
async def test_certificate_platinum_tier(client: AsyncClient):
    token = await _register(client, "cert_plt", "cert_plt@example.com")
    await _submit_session(client, token, wpm=72.0, accuracy=99.6)

    r = await client.get("/api/v1/stats/certificate", headers=_auth(token))
    data = r.json()
    assert data["eligible"] is True
    assert data["tier"] == "platinum"
    assert data["wpm"] == 72.0


@pytest.mark.asyncio
async def test_certificate_highest_tier_wins(client: AsyncClient):
    """When both silver and gold qualify, gold is returned."""
    token = await _register(client, "cert_best", "cert_best@example.com")
    await _submit_session(client, token, wpm=42.0, accuracy=96.5)  # silver only
    await _submit_session(client, token, wpm=55.0, accuracy=98.5)  # gold

    r = await client.get("/api/v1/stats/certificate", headers=_auth(token))
    data = r.json()
    assert data["eligible"] is True
    assert data["tier"] == "gold"
    assert data["wpm"] == 55.0


@pytest.mark.asyncio
async def test_certificate_best_wpm_selected_within_tier(client: AsyncClient):
    """Multiple gold-qualifying sessions — highest WPM session is chosen."""
    token = await _register(client, "cert_topwpm", "cert_topwpm@example.com")
    await _submit_session(client, token, wpm=51.0, accuracy=98.0)
    await _submit_session(client, token, wpm=58.0, accuracy=98.5)

    r = await client.get("/api/v1/stats/certificate", headers=_auth(token))
    data = r.json()
    assert data["tier"] == "gold"
    assert data["wpm"] == 58.0


@pytest.mark.asyncio
async def test_certificate_includes_language(client: AsyncClient):
    token = await _register(client, "cert_lang", "cert_lang@example.com")
    await _submit_session(client, token, wpm=42.0, accuracy=96.5, language="ru")

    r = await client.get("/api/v1/stats/certificate", headers=_auth(token))
    assert r.json()["language"] == "ru"


# ─── /stats/streak ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_streak_zero_new_user(client: AsyncClient):
    token = await _register(client, "str_new", "str_new@example.com")
    r = await client.get("/api/v1/stats/streak", headers=_auth(token))
    assert r.status_code == 200
    data = r.json()
    assert data["current_streak"] == 0
    assert data["longest_streak"] == 0


@pytest.mark.asyncio
async def test_streak_one_after_todays_session(client: AsyncClient):
    token = await _register(client, "str_one", "str_one@example.com")
    await _submit_session(client, token)

    r = await client.get("/api/v1/stats/streak", headers=_auth(token))
    data = r.json()
    assert data["current_streak"] == 1
    assert data["longest_streak"] == 1


@pytest.mark.asyncio
async def test_streak_multiple_sessions_same_day_count_as_one(client: AsyncClient):
    """Several sessions on the same day = streak of 1, not multiple."""
    token = await _register(client, "str_sameday", "str_sameday@example.com")
    await _submit_session(client, token)
    await _submit_session(client, token)
    await _submit_session(client, token)

    r = await client.get("/api/v1/stats/streak", headers=_auth(token))
    data = r.json()
    assert data["current_streak"] == 1


@pytest.mark.asyncio
async def test_streak_consecutive_days(client: AsyncClient, db_session: AsyncSession):
    """4 consecutive days (today included) → current_streak=4, longest=4."""
    token = await _register(client, "str_consec", "str_consec@example.com")
    uid = await _user_id(client, token)

    today = datetime.now(timezone.utc)
    for days_ago in [3, 2, 1, 0]:
        db_session.add(TypingSession(
            user_id=uid,
            language="en",
            wpm=40.0,
            cpm=200.0,
            accuracy=95.0,
            duration_ms=60000,
            created_at=today - timedelta(days=days_ago),
        ))
    await db_session.commit()

    r = await client.get("/api/v1/stats/streak", headers=_auth(token))
    data = r.json()
    assert data["current_streak"] == 4
    assert data["longest_streak"] == 4


@pytest.mark.asyncio
async def test_streak_gap_breaks_current(client: AsyncClient, db_session: AsyncSession):
    """Sessions on days 5, 4, 2, 1 ago → current_streak=2, longest=2."""
    token = await _register(client, "str_gap", "str_gap@example.com")
    uid = await _user_id(client, token)

    today = datetime.now(timezone.utc)
    for days_ago in [5, 4, 2, 1]:
        db_session.add(TypingSession(
            user_id=uid,
            language="en",
            wpm=40.0,
            cpm=200.0,
            accuracy=95.0,
            duration_ms=60000,
            created_at=today - timedelta(days=days_ago),
        ))
    await db_session.commit()

    r = await client.get("/api/v1/stats/streak", headers=_auth(token))
    data = r.json()
    assert data["current_streak"] == 2
    assert data["longest_streak"] == 2


@pytest.mark.asyncio
async def test_streak_longest_exceeds_current(client: AsyncClient, db_session: AsyncSession):
    """A long streak in the past, then a gap, then 1 day now → longest > current."""
    token = await _register(client, "str_hist", "str_hist@example.com")
    uid = await _user_id(client, token)

    today = datetime.now(timezone.utc)
    # A 5-day streak starting 20 days ago
    for days_ago in range(20, 15, -1):  # 20, 19, 18, 17, 16
        db_session.add(TypingSession(
            user_id=uid,
            language="en",
            wpm=40.0,
            cpm=200.0,
            accuracy=95.0,
            duration_ms=60000,
            created_at=today - timedelta(days=days_ago),
        ))
    # Session today only (streak of 1)
    db_session.add(TypingSession(
        user_id=uid,
        language="en",
        wpm=40.0,
        cpm=200.0,
        accuracy=95.0,
        duration_ms=60000,
        created_at=today,
    ))
    await db_session.commit()

    r = await client.get("/api/v1/stats/streak", headers=_auth(token))
    data = r.json()
    assert data["current_streak"] == 1
    assert data["longest_streak"] == 5
