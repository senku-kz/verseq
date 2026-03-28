import json as _json

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user_optional
from app.models.models import User
from app.schemas.schemas import TextResponse
from app.services.adaptive import adaptive_service
from app.services.generator import get_generator

router = APIRouter(prefix="/api/v1/practice", tags=["practice"])

VALID_LANGS = ("en", "ru")
VALID_MODES = ("free", "adaptive", "structured", "bigrams")


@router.get("/text", response_model=TextResponse)
async def get_practice_text(
    lang: str = Query("en"),
    mode: str = Query("free"),
    length: int = Query(300, ge=100, le=600),
    weak_bigrams: str = Query(None),  # JSON string for anonymous adaptive
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    if lang not in VALID_LANGS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"lang must be one of {VALID_LANGS}",
        )
    if mode not in VALID_MODES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"mode must be one of {VALID_MODES}",
        )

    generator = get_generator()
    wb: dict[str, int] | None = None

    if mode in ("adaptive", "bigrams"):
        if current_user is not None:
            matrix = await adaptive_service.get_error_matrix(current_user.id, db)
            wb = adaptive_service.get_weak_bigrams(matrix) if matrix else None
        elif weak_bigrams:
            try:
                wb = _json.loads(weak_bigrams)
            except Exception:
                wb = {}

    text = generator.generate(
        lang=lang,
        mode=mode,
        weak_bigrams=wb,
        target_length=length,
    )

    return TextResponse(
        text=text,
        word_count=len(text.split()),
        char_count=len(text),
        mode=mode,
        language=lang,
    )
