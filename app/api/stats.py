import json
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.models import LessonProgress, TypingSession, User, UserErrorMatrix
from app.schemas.schemas import (
    Achievement,
    AchievementsResponse,
    CertificateResponse,
    HeatmapResponse,
    SessionHistoryItem,
    StatsResponse,
    StreakResponse,
)

router = APIRouter(prefix="/api/v1/stats", tags=["stats"])

# ---------------------------------------------------------------------------
# Helper: calculate current and longest streaks from a list of session dates
# ---------------------------------------------------------------------------


def _compute_streaks(session_dates: list[date]) -> tuple[int, int]:
    """Return (current_streak, longest_streak) given a list of dates with sessions."""
    if not session_dates:
        return 0, 0

    unique_dates = sorted(set(session_dates), reverse=True)
    today = datetime.now(timezone.utc).date()

    # current streak: consecutive days ending at today or yesterday
    current_streak = 0
    if unique_dates[0] in (today, today - timedelta(days=1)):
        expected = unique_dates[0]
        for d in unique_dates:
            if d == expected:
                current_streak += 1
                expected -= timedelta(days=1)
            else:
                break

    # longest streak
    longest = 1
    run = 1
    for i in range(1, len(unique_dates)):
        if unique_dates[i - 1] - unique_dates[i] == timedelta(days=1):
            run += 1
            if run > longest:
                longest = run
        else:
            run = 1

    return current_streak, max(longest, current_streak)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/", response_model=StatsResponse)
async def get_stats(
    lang: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = (
        select(TypingSession)
        .where(TypingSession.user_id == current_user.id)
        .order_by(TypingSession.created_at.desc())
        .limit(90)
    )
    if lang:
        query = (
            select(TypingSession)
            .where(
                TypingSession.user_id == current_user.id,
                TypingSession.language == lang,
            )
            .order_by(TypingSession.created_at.desc())
            .limit(90)
        )

    result = await db.execute(query)
    sessions = result.scalars().all()

    session_items = [
        SessionHistoryItem(
            wpm=s.wpm,
            cpm=s.cpm,
            accuracy=s.accuracy,
            created_at=s.created_at,
            language=s.language,
        )
        for s in sessions
    ]

    wpm_values = [s.wpm for s in sessions]
    acc_values = [s.accuracy for s in sessions]
    avg_wpm = sum(wpm_values) / len(wpm_values) if wpm_values else 0.0
    best_wpm = max(wpm_values) if wpm_values else 0.0
    avg_accuracy = sum(acc_values) / len(acc_values) if acc_values else 0.0

    # total_chars_typed: sum of cpm * duration_ms / 60000
    total_chars = sum(int(s.cpm * s.duration_ms / 60000) for s in sessions)

    # streak from all sessions (not just the last 90)
    all_result = await db.execute(
        select(TypingSession.created_at).where(TypingSession.user_id == current_user.id)
    )
    all_dates = [row[0].date() if hasattr(row[0], "date") else row[0] for row in all_result.fetchall()]
    current_streak, _ = _compute_streaks(all_dates)

    return StatsResponse(
        sessions=session_items,
        avg_wpm=round(avg_wpm, 1),
        best_wpm=round(best_wpm, 1),
        avg_accuracy=round(avg_accuracy, 1),
        total_sessions=len(sessions),
        total_chars_typed=total_chars,
        streak_days=current_streak,
    )


@router.get("/heatmap", response_model=HeatmapResponse)
async def get_heatmap(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserErrorMatrix).where(UserErrorMatrix.user_id == current_user.id)
    )
    record = result.scalar_one_or_none()

    key_errors: dict[str, int] = {}
    if record:
        matrix: dict[str, int] = json.loads(record.matrix_json)
        for bigram, count in matrix.items():
            for char in bigram:
                if char:
                    key_errors[char] = key_errors.get(char, 0) + count

    return HeatmapResponse(keys=key_errors)


@router.get("/achievements", response_model=AchievementsResponse)
async def get_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Fetch all sessions for this user
    sessions_result = await db.execute(
        select(TypingSession)
        .where(TypingSession.user_id == current_user.id)
        .order_by(TypingSession.created_at.asc())
    )
    all_sessions = sessions_result.scalars().all()

    # Fetch lesson progress
    progress_result = await db.execute(
        select(LessonProgress).where(
            LessonProgress.user_id == current_user.id,
            LessonProgress.completed == True,  # noqa: E712
        )
    )
    completed_lessons = progress_result.scalars().all()

    # Pre-compute helpers
    session_count = len(all_sessions)
    best_wpm = max((s.wpm for s in all_sessions), default=0.0)

    # streak
    all_dates = [s.created_at.date() for s in all_sessions]
    current_streak, _ = _compute_streaks(all_dates)

    # First session that meets a WPM threshold
    def _first_session_with_wpm(threshold: float) -> TypingSession | None:
        return next((s for s in all_sessions if s.wpm >= threshold), None)

    def _first_session_with_accuracy(threshold: float) -> TypingSession | None:
        return next((s for s in all_sessions if s.accuracy >= threshold), None)

    # All 15 lessons completed for en or ru
    en_lessons = {lp.lesson_id for lp in completed_lessons if lp.exercise_id.startswith("en-")}
    ru_lessons = {lp.lesson_id for lp in completed_lessons if lp.exercise_id.startswith("ru-")}
    all_lessons_unlocked = len(en_lessons) >= 15 or len(ru_lessons) >= 15

    # Streak thresholds — find the date when streak first reached N days
    def _first_date_streak_reached(threshold: int) -> datetime | None:
        """Return created_at of the session that pushed streak to >= threshold."""
        sorted_dates = sorted(set(all_dates))
        run = 1
        for i in range(1, len(sorted_dates)):
            if sorted_dates[i] - sorted_dates[i - 1] == timedelta(days=1):
                run += 1
                if run >= threshold:
                    # Find first session on this date
                    target_date = sorted_dates[i]
                    for s in all_sessions:
                        if s.created_at.date() == target_date:
                            return s.created_at
            else:
                run = 1
        if threshold == 1 and sorted_dates:
            for s in all_sessions:
                if s.created_at.date() == sorted_dates[0]:
                    return s.created_at
        return None

    first_session = all_sessions[0] if all_sessions else None
    first_lesson_progress = completed_lessons[0] if completed_lessons else None

    achievements: list[Achievement] = [
        Achievement(
            id="first_session",
            title="First Steps",
            description="Complete your first typing session",
            icon="keyboard",
            unlocked=session_count >= 1,
            unlocked_at=first_session.created_at if first_session else None,
        ),
        Achievement(
            id="first_lesson",
            title="Student",
            description="Complete your first lesson exercise",
            icon="school",
            unlocked=len(completed_lessons) >= 1,
            unlocked_at=first_lesson_progress.updated_at if first_lesson_progress else None,
        ),
        Achievement(
            id="wpm_30",
            title="Warming Up",
            description="Reach 30 WPM",
            icon="speed",
            unlocked=best_wpm >= 30,
            unlocked_at=_first_session_with_wpm(30).created_at if _first_session_with_wpm(30) else None,
        ),
        Achievement(
            id="wpm_50",
            title="Getting Fast",
            description="Reach 50 WPM",
            icon="speed",
            unlocked=best_wpm >= 50,
            unlocked_at=_first_session_with_wpm(50).created_at if _first_session_with_wpm(50) else None,
        ),
        Achievement(
            id="wpm_70",
            title="Speed Demon",
            description="Reach 70 WPM",
            icon="speed",
            unlocked=best_wpm >= 70,
            unlocked_at=_first_session_with_wpm(70).created_at if _first_session_with_wpm(70) else None,
        ),
        Achievement(
            id="accuracy_95",
            title="Precise",
            description="Complete a session with 95% or higher accuracy",
            icon="verified",
            unlocked=any(s.accuracy >= 95 for s in all_sessions),
            unlocked_at=_first_session_with_accuracy(95).created_at if _first_session_with_accuracy(95) else None,
        ),
        Achievement(
            id="accuracy_99",
            title="Perfectionist",
            description="Complete a session with 99% or higher accuracy",
            icon="star",
            unlocked=any(s.accuracy >= 99 for s in all_sessions),
            unlocked_at=_first_session_with_accuracy(99).created_at if _first_session_with_accuracy(99) else None,
        ),
        Achievement(
            id="streak_3",
            title="Consistent",
            description="Practice for 3 days in a row",
            icon="local_fire_department",
            unlocked=current_streak >= 3,
            unlocked_at=_first_date_streak_reached(3),
        ),
        Achievement(
            id="streak_7",
            title="Dedicated",
            description="Practice for 7 days in a row",
            icon="emoji_events",
            unlocked=current_streak >= 7,
            unlocked_at=_first_date_streak_reached(7),
        ),
        Achievement(
            id="all_lessons",
            title="Graduate",
            description="Complete all 15 lessons in English or Russian",
            icon="emoji_events",
            unlocked=all_lessons_unlocked,
            unlocked_at=None,
        ),
    ]

    return AchievementsResponse(achievements=achievements)


@router.get("/certificate", response_model=CertificateResponse)
async def get_certificate(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TypingSession)
        .where(TypingSession.user_id == current_user.id)
        .order_by(TypingSession.created_at.desc())
    )
    all_sessions = result.scalars().all()

    # Tier thresholds: (tier_name, min_wpm, min_accuracy)
    tiers = [
        ("platinum", 70.0, 99.5),
        ("gold", 50.0, 97.8),
        ("silver", 40.0, 96.0),
    ]

    best_session = None
    best_tier = None

    for tier_name, min_wpm, min_acc in tiers:
        qualifying = [s for s in all_sessions if s.wpm >= min_wpm and s.accuracy >= min_acc]
        if qualifying:
            # Pick session with highest WPM among qualifying
            champion = max(qualifying, key=lambda s: s.wpm)
            best_session = champion
            best_tier = tier_name
            break

    if best_session is None:
        return CertificateResponse(
            eligible=False,
            tier=None,
            wpm=0.0,
            accuracy=0.0,
            language="",
            date=None,
        )

    return CertificateResponse(
        eligible=True,
        tier=best_tier,
        wpm=round(best_session.wpm, 1),
        accuracy=round(best_session.accuracy, 1),
        language=best_session.language,
        date=best_session.created_at,
    )


@router.get("/streak", response_model=StreakResponse)
async def get_streak(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TypingSession.created_at).where(TypingSession.user_id == current_user.id)
    )
    all_dates = [row[0].date() if hasattr(row[0], "date") else row[0] for row in result.fetchall()]
    current_streak, longest_streak = _compute_streaks(all_dates)

    return StreakResponse(current_streak=current_streak, longest_streak=longest_streak)
