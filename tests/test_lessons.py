import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_lessons_en_returns_15(client: AsyncClient):
    response = await client.get("/api/v1/lessons/?lang=en")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 15


@pytest.mark.asyncio
async def test_get_lesson_1_en_has_5_exercises(client: AsyncClient):
    response = await client.get("/api/v1/lessons/1?lang=en")
    assert response.status_code == 200
    data = response.json()
    assert len(data["exercises"]) == 5


@pytest.mark.asyncio
async def test_get_exercise_text_en(client: AsyncClient):
    response = await client.get(
        "/api/v1/lessons/1/exercises/en-1-1/text?lang=en"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["text"]) > 0


@pytest.mark.asyncio
async def test_lesson_1_text_only_allowed_chars(client: AsyncClient):
    response = await client.get(
        "/api/v1/lessons/1/exercises/en-1-1/text?lang=en"
    )
    assert response.status_code == 200
    text = response.json()["text"]
    allowed = set("asdfj kl;") | {" "}
    for ch in text:
        assert ch.lower() in allowed or ch == " ", f"Unexpected char: {repr(ch)}"


@pytest.mark.asyncio
async def test_list_lessons_ru_returns_15(client: AsyncClient):
    response = await client.get("/api/v1/lessons/?lang=ru")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 15


@pytest.mark.asyncio
async def test_get_lesson_99_returns_404(client: AsyncClient):
    response = await client.get("/api/v1/lessons/99?lang=en")
    assert response.status_code == 404
