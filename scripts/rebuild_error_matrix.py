"""
Rebuild UserErrorMatrix for all users from the stored error_matrix_delta
in typing_sessions. Run once after fixing user_id = NULL sessions.

Usage:
    python scripts/rebuild_error_matrix.py
    python scripts/rebuild_error_matrix.py --user-id 3   # single user
"""
import asyncio
import json
import sys
import argparse

sys.path.insert(0, ".")

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.models.models import Base, TypingSession, UserErrorMatrix


async def rebuild(user_id: int | None, session: AsyncSession) -> None:
    # Fetch all sessions that have a valid user_id and non-empty delta
    q = select(TypingSession).where(TypingSession.user_id.is_not(None))
    if user_id is not None:
        q = q.where(TypingSession.user_id == user_id)
    result = await session.execute(q)
    sessions = result.scalars().all()

    # Aggregate per user
    by_user: dict[int, dict[str, int]] = {}
    empty = 0
    for s in sessions:
        try:
            delta: dict[str, int] = json.loads(s.error_matrix_delta or "{}")
        except Exception:
            delta = {}
        if not delta:
            empty += 1
            continue
        uid = s.user_id
        if uid not in by_user:
            by_user[uid] = {}
        for bigram, count in delta.items():
            by_user[uid][bigram] = by_user[uid].get(bigram, 0) + count

    print(f"  Sessions processed : {len(sessions)}")
    print(f"  Sessions w/o errors: {empty}")
    print(f"  Users with errors  : {len(by_user)}")

    for uid, matrix in by_user.items():
        existing = (
            await session.execute(
                select(UserErrorMatrix).where(UserErrorMatrix.user_id == uid)
            )
        ).scalar_one_or_none()

        if existing:
            existing.matrix_json = json.dumps(matrix)
        else:
            session.add(UserErrorMatrix(user_id=uid, matrix_json=json.dumps(matrix)))

        top5 = sorted(matrix.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"  user_id={uid}: {len(matrix)} bigrams, top-5={top5}")

    await session.commit()
    print("Done.")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", type=int, default=None)
    args = parser.parse_args()

    engine = create_async_engine(get_settings().DATABASE_URL)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        await rebuild(args.user_id, session)

    await engine.dispose()


asyncio.run(main())
