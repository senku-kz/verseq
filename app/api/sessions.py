import json
import re

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user, get_current_user_optional
from app.models.models import LessonProgress, TypingSession, User
from app.schemas.schemas import SessionResponse, SessionSubmit
from app.services.adaptive import adaptive_service

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])

# Pattern matching lesson exercise IDs: e.g. "en-1-1", "ru-10-3"
_EXERCISE_ID_RE = re.compile(r"^(en|ru)-(\d+)-(\d+)$")


def _parse_lesson_id_from_exercise(exercise_id: str) -> int | None:
    """Extract the numeric lesson_id from an exercise_id like 'en-3-2'."""
    m = _EXERCISE_ID_RE.match(exercise_id)
    if m:
        return int(m.group(2))
    return None


def _compute_stars(wpm: float, accuracy: float, min_wpm: int, min_accuracy: float) -> int:
    """1 star always on completion, +1 if accuracy >= 95%, +1 if wpm >= min_wpm."""
    stars = 1
    if accuracy >= 95.0:
        stars += 1
    if min_wpm > 0 and wpm >= min_wpm:
        stars += 1
    elif min_wpm == 0:
        # No WPM requirement — award the star freely
        stars += 1
    return stars


@router.post("/", response_model=SessionResponse)
async def submit_session(
    payload: SessionSubmit,
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    session = TypingSession(
        user_id=current_user.id if current_user else None,
        exercise_id=payload.exercise_id,
        language=payload.language,
        wpm=payload.wpm,
        cpm=payload.cpm,
        accuracy=payload.accuracy,
        duration_ms=payload.duration_ms,
        error_matrix_delta=json.dumps(payload.error_matrix_delta),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    # Update error matrix for authenticated users with non-empty delta
    if current_user is not None and payload.error_matrix_delta:
        await adaptive_service.update_error_matrix(
            user_id=current_user.id,
            delta=payload.error_matrix_delta,
            db=db,
        )

    # Update LessonProgress if this session belongs to a lesson exercise
    if current_user is not None and payload.exercise_id:
        lesson_id = _parse_lesson_id_from_exercise(payload.exercise_id)
        if lesson_id is not None:
            await _upsert_lesson_progress(
                db=db,
                user_id=current_user.id,
                lesson_id=lesson_id,
                exercise_id=payload.exercise_id,
                lang=payload.language,
                wpm=payload.wpm,
                accuracy=payload.accuracy,
            )

    return session


async def _upsert_lesson_progress(
    db: AsyncSession,
    user_id: int,
    lesson_id: int,
    exercise_id: str,
    lang: str,
    wpm: float,
    accuracy: float,
) -> None:
    """Upsert LessonProgress: only update if new stars > old or new best_wpm > old."""
    from app.services.lesson_service import lesson_service

    exercise = lesson_service.get_exercise(lang, lesson_id, exercise_id)
    if exercise is None:
        return

    min_wpm = exercise["min_wpm"]
    min_accuracy = exercise["min_accuracy"]
    new_stars = _compute_stars(wpm, accuracy, min_wpm, min_accuracy)

    result = await db.execute(
        select(LessonProgress).where(
            LessonProgress.user_id == user_id,
            LessonProgress.exercise_id == exercise_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing is None:
        progress = LessonProgress(
            user_id=user_id,
            lesson_id=lesson_id,
            exercise_id=exercise_id,
            completed=True,
            stars=new_stars,
            best_wpm=wpm,
            best_accuracy=accuracy,
        )
        db.add(progress)
    else:
        updated = False
        if new_stars > existing.stars:
            existing.stars = new_stars
            updated = True
        if wpm > existing.best_wpm:
            existing.best_wpm = wpm
            updated = True
        if accuracy > existing.best_accuracy:
            existing.best_accuracy = accuracy
            updated = True
        if not existing.completed:
            existing.completed = True
            updated = True
        if updated:
            db.add(existing)

    await db.commit()


@router.get("/", response_model=list[SessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(TypingSession)
        .where(TypingSession.user_id == current_user.id)
        .order_by(TypingSession.created_at.desc())
        .limit(50)
    )
    return result.scalars().all()
