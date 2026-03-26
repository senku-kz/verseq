from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user_optional
from app.models.models import User, LessonProgress
from app.services.lesson_service import lesson_service
from app.schemas.lesson_schemas import LessonListItem, LessonDetail, ExerciseDetail, ExerciseText

router = APIRouter(prefix="/api/v1/lessons", tags=["lessons"])


@router.get("/", response_model=list[LessonListItem])
async def list_lessons(
    lang: str = Query("en"),
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> list[LessonListItem]:
    """Return all lessons with completion status for authenticated user.
    For anonymous users: all lessons unlocked, no progress."""
    lessons = lesson_service.get_lessons(lang)
    if not lessons:
        return []

    # Fetch progress records for authenticated users
    progress_by_lesson: dict[int, list] = {}
    if user is not None:
        result = await db.execute(
            select(LessonProgress).where(LessonProgress.user_id == user.id)
        )
        all_progress = result.scalars().all()
        for p in all_progress:
            progress_by_lesson.setdefault(p.lesson_id, []).append(p)

    items: list[LessonListItem] = []
    prev_completed = True  # lesson 1 is always unlocked

    for lesson in lessons:
        lesson_id = lesson["id"]
        records = progress_by_lesson.get(lesson_id, [])
        prog = lesson_service.compute_progress(lesson, records)

        is_unlocked: bool
        if user is None:
            # Anonymous: all unlocked
            is_unlocked = True
        else:
            is_unlocked = prev_completed  # lesson 1: prev_completed starts True

        items.append(
            LessonListItem(
                id=lesson_id,
                title=lesson["title"],
                description=lesson["description"],
                is_unlocked=is_unlocked,
                is_completed=prog["is_completed"],
                stars_total=prog["stars_total"],
                exercises_completed=prog["exercises_completed"],
            )
        )

        # Update prev_completed for next iteration
        prev_completed = prog["is_completed"]

    return items


@router.get("/{lesson_id}", response_model=LessonDetail)
async def get_lesson(
    lesson_id: int,
    lang: str = Query("en"),
    user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
) -> LessonDetail:
    lesson = lesson_service.get_lesson(lang, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail=f"Lesson {lesson_id} not found")

    # Fetch progress
    records = []
    if user is not None:
        result = await db.execute(
            select(LessonProgress).where(
                LessonProgress.user_id == user.id,
                LessonProgress.lesson_id == lesson_id,
            )
        )
        records = result.scalars().all()

    prog = lesson_service.compute_progress(lesson, records)

    # Determine unlock status
    if user is None or lesson_id == 1:
        is_unlocked = True
    else:
        # Check if previous lesson is completed
        prev_lesson = lesson_service.get_lesson(lang, lesson_id - 1)
        if prev_lesson is None:
            is_unlocked = True
        else:
            prev_result = await db.execute(
                select(LessonProgress).where(
                    LessonProgress.user_id == user.id,
                    LessonProgress.lesson_id == lesson_id - 1,
                )
            )
            prev_records = prev_result.scalars().all()
            prev_prog = lesson_service.compute_progress(prev_lesson, prev_records)
            is_unlocked = prev_prog["is_completed"]

    exercises: list[ExerciseDetail] = [
        ExerciseDetail(**ex_data) for ex_data in prog["exercise_details"]
    ]

    return LessonDetail(
        id=lesson_id,
        title=lesson["title"],
        description=lesson["description"],
        is_unlocked=is_unlocked,
        is_completed=prog["is_completed"],
        stars_total=prog["stars_total"],
        exercises_completed=prog["exercises_completed"],
        allowed_chars=lesson["allowed_chars"],
        exercises=exercises,
    )


@router.get("/{lesson_id}/exercises/{exercise_id}/text", response_model=ExerciseText)
async def get_exercise_text(
    lesson_id: int,
    exercise_id: str,
    lang: str = Query("en"),
) -> ExerciseText:
    """Generate text for the exercise using TextGenerator in structured mode."""
    lesson = lesson_service.get_lesson(lang, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail=f"Lesson {lesson_id} not found")

    exercise = lesson_service.get_exercise(lang, lesson_id, exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail=f"Exercise {exercise_id} not found")

    try:
        text = lesson_service.generate_exercise_text(lang, lesson_id, exercise_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return ExerciseText(
        text=text,
        exercise_id=exercise_id,
        lesson_id=lesson_id,
    )
