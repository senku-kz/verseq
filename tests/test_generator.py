import json
import pytest
from httpx import AsyncClient

from app.services.generator import get_generator


# ─── unit: service layer ──────────────────────────────────────────────────────

def test_free_en():
    generator = get_generator()
    result = generator.generate(lang="en", mode="free", target_length=200)
    assert isinstance(result, str)
    assert 150 <= len(result) <= 300


def test_free_ru():
    generator = get_generator()
    result = generator.generate(lang="ru", mode="free", target_length=200)
    assert isinstance(result, str)
    assert 150 <= len(result) <= 300
    has_cyrillic = any("\u0400" <= ch <= "\u04ff" for ch in result)
    assert has_cyrillic, "Russian text should contain Cyrillic characters"


def test_structured_only_allowed_chars():
    generator = get_generator()
    allowed = {"a", "s", "d", "f", "j", "k", "l", " "}
    result = generator.generate(
        lang="en",
        mode="structured",
        allowed_chars=allowed,
        target_length=100,
    )
    assert isinstance(result, str)
    for ch in result:
        assert ch in allowed, f"Character '{ch}' is not in the allowed set {allowed}"


def test_adaptive_returns_text():
    generator = get_generator()
    weak_bigrams = {"th": 10, "he": 8}
    result = generator.generate(
        lang="en",
        mode="adaptive",
        weak_bigrams=weak_bigrams,
        target_length=200,
    )
    assert isinstance(result, str)
    assert len(result) > 0


# ─── API: /practice/text ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_api_free_en(client: AsyncClient):
    r = await client.get("/api/v1/practice/text?lang=en&mode=free&length=200")
    assert r.status_code == 200
    data = r.json()
    assert len(data["text"]) > 0
    assert data["language"] == "en"
    assert data["mode"] == "free"


@pytest.mark.asyncio
async def test_api_free_ru(client: AsyncClient):
    r = await client.get("/api/v1/practice/text?lang=ru&mode=free&length=200")
    assert r.status_code == 200
    data = r.json()
    assert len(data["text"]) > 0
    assert data["language"] == "ru"


@pytest.mark.asyncio
async def test_api_adaptive_returns_text(client: AsyncClient):
    r = await client.get("/api/v1/practice/text?lang=en&mode=adaptive&length=200")
    assert r.status_code == 200
    assert len(r.json()["text"]) > 0


@pytest.mark.asyncio
async def test_api_response_metadata(client: AsyncClient):
    """Response includes word_count, char_count matching the text."""
    r = await client.get("/api/v1/practice/text?lang=en&mode=free&length=200")
    data = r.json()
    assert data["word_count"] > 0
    assert data["char_count"] == len(data["text"])
    assert data["mode"] == "free"
    assert data["language"] == "en"


@pytest.mark.asyncio
async def test_api_length_min_boundary(client: AsyncClient):
    r = await client.get("/api/v1/practice/text?lang=en&mode=free&length=100")
    assert r.status_code == 200
    assert len(r.json()["text"]) >= 50


@pytest.mark.asyncio
async def test_api_length_max_boundary(client: AsyncClient):
    r = await client.get("/api/v1/practice/text?lang=en&mode=free&length=600")
    assert r.status_code == 200
    assert len(r.json()["text"]) >= 100


@pytest.mark.asyncio
async def test_api_length_below_minimum_returns_422(client: AsyncClient):
    r = await client.get("/api/v1/practice/text?lang=en&mode=free&length=50")
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_api_length_above_maximum_returns_422(client: AsyncClient):
    r = await client.get("/api/v1/practice/text?lang=en&mode=free&length=1000")
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_api_invalid_lang_returns_422(client: AsyncClient):
    r = await client.get("/api/v1/practice/text?lang=de&mode=free&length=200")
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_api_invalid_mode_returns_422(client: AsyncClient):
    r = await client.get("/api/v1/practice/text?lang=en&mode=turbo&length=200")
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_api_weak_bigrams_accepted(client: AsyncClient):
    """Anonymous adaptive: weak_bigrams JSON string is accepted."""
    wb = json.dumps({"th": 10, "st": 5, "er": 8})
    r = await client.get(
        f"/api/v1/practice/text?lang=en&mode=adaptive&length=200&weak_bigrams={wb}"
    )
    assert r.status_code == 200
    assert len(r.json()["text"]) > 0


@pytest.mark.asyncio
async def test_api_weak_bigrams_invalid_json_falls_back(client: AsyncClient):
    """Malformed weak_bigrams is silently ignored — still returns text."""
    r = await client.get(
        "/api/v1/practice/text?lang=en&mode=adaptive&length=200&weak_bigrams=notjson"
    )
    assert r.status_code == 200
    assert len(r.json()["text"]) > 0
