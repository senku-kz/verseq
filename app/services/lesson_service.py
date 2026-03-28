import json
from pathlib import Path

from app.services.generator import get_generator


class LessonService:
    def __init__(self):
        data_path = Path(__file__).parent.parent / "data" / "lessons.json"
        with open(data_path, encoding="utf-8") as f:
            self._data = json.load(f)

    def get_lessons(self, lang: str) -> list[dict]:
        return self._data.get(lang, [])

    def get_lesson(self, lang: str, lesson_id: int) -> dict | None:
        lessons = self.get_lessons(lang)
        return next((les for les in lessons if les["id"] == lesson_id), None)

    def get_exercise(self, lang: str, lesson_id: int, exercise_id: str) -> dict | None:
        lesson = self.get_lesson(lang, lesson_id)
        if not lesson:
            return None
        return next((e for e in lesson["exercises"] if e["id"] == exercise_id), None)

    def generate_exercise_text(self, lang: str, lesson_id: int, exercise_id: str) -> str:
        lesson = self.get_lesson(lang, lesson_id)
        if not lesson:
            raise ValueError(f"Lesson {lesson_id} not found")
        exercise = next((e for e in lesson["exercises"] if e["id"] == exercise_id), None)
        if not exercise:
            raise ValueError(f"Exercise {exercise_id} not found")

        allowed = set(lesson["allowed_chars"])
        # Always include space
        allowed.add("space")
        # Map "space" → " "
        allowed_chars = {" " if c == "space" else c for c in allowed}

        gen = get_generator()
        return gen.generate(
            lang=lang,
            mode="structured",
            allowed_chars=allowed_chars,
            target_length=exercise["target_length"],
        )

    def compute_progress(
        self,
        lesson: dict,
        progress_records: list,  # list of LessonProgress ORM objects
    ) -> dict:
        """Returns completed count, total stars, per-exercise progress."""
        progress_map = {p.exercise_id: p for p in progress_records}
        exercises_completed = 0
        stars_total = 0
        exercise_details = []
        for ex in lesson["exercises"]:
            p = progress_map.get(ex["id"])
            if p and p.completed:
                exercises_completed += 1
                stars_total += p.stars
            exercise_details.append(
                {
                    "id": ex["id"],
                    "title": ex["title"],
                    "min_wpm": ex["min_wpm"],
                    "min_accuracy": ex["min_accuracy"],
                    "target_length": ex["target_length"],
                    "progress": {
                        "exercise_id": ex["id"],
                        "completed": p.completed if p else False,
                        "stars": p.stars if p else 0,
                        "best_wpm": p.best_wpm if p else 0.0,
                        "best_accuracy": p.best_accuracy if p else 0.0,
                    }
                    if p
                    else None,
                }
            )
        return {
            "exercises_completed": exercises_completed,
            "stars_total": stars_total,
            "is_completed": exercises_completed == len(lesson["exercises"]),
            "exercise_details": exercise_details,
        }


lesson_service = LessonService()
