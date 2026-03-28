import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import UserErrorMatrix


class AdaptiveService:
    async def get_error_matrix(self, user_id: int, db: AsyncSession) -> dict[str, int]:
        result = await db.execute(
            select(UserErrorMatrix).where(UserErrorMatrix.user_id == user_id)
        )
        record = result.scalar_one_or_none()
        if not record:
            return {}
        return json.loads(record.matrix_json)

    async def update_error_matrix(
        self, user_id: int, delta: dict[str, int], db: AsyncSession
    ) -> None:
        result = await db.execute(
            select(UserErrorMatrix).where(UserErrorMatrix.user_id == user_id)
        )
        record = result.scalar_one_or_none()
        if record:
            matrix = json.loads(record.matrix_json)
            for bigram, count in delta.items():
                matrix[bigram] = matrix.get(bigram, 0) + count
            record.matrix_json = json.dumps(matrix)
            record.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
        else:
            record = UserErrorMatrix(
                user_id=user_id,
                matrix_json=json.dumps(delta),
                updated_at=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            db.add(record)
        await db.commit()

    def get_weak_bigrams(self, matrix: dict[str, int], top_n: int = 20) -> dict[str, int]:
        sorted_items = sorted(matrix.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_items[:top_n])


adaptive_service = AdaptiveService()
