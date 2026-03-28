from pydantic import BaseModel


class ExerciseSummary(BaseModel):
    id: str
    title: str
    min_wpm: int
    min_accuracy: float
    target_length: int


class ExerciseProgress(BaseModel):
    exercise_id: str
    completed: bool
    stars: int  # 0-3
    best_wpm: float
    best_accuracy: float


class ExerciseDetail(ExerciseSummary):
    progress: ExerciseProgress | None = None


class LessonListItem(BaseModel):
    id: int
    title: str
    description: str
    is_unlocked: bool   # True if previous lesson completed or lesson 1
    is_completed: bool  # True if all 5 exercises completed
    stars_total: int    # sum of stars across all exercises (max 15)
    exercises_completed: int


class LessonDetail(LessonListItem):
    allowed_chars: list[str]
    exercises: list[ExerciseDetail]


class ExerciseText(BaseModel):
    text: str
    exercise_id: str
    lesson_id: int
