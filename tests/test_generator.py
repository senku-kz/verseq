import pytest

from app.services.generator import get_generator


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
    # Check result contains Cyrillic characters
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
    # Every non-space char in result must be in the allowed set
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
