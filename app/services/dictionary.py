from pathlib import Path


class DictionaryService:
    def __init__(self) -> None:
        self._words: dict[str, list[str]] = {}
        self._load_all()

    def _load_all(self) -> None:
        for lang in ("en", "ru"):
            path = Path(__file__).parent.parent / "data" / lang / "words_10k.txt"
            with open(path, encoding="utf-8") as f:
                self._words[lang] = [line.strip() for line in f if line.strip()]

    def get_words(self, lang: str, limit: int | None = None) -> list[str]:
        words = self._words.get(lang, [])
        return words[:limit] if limit else words

    def get_random_words(self, lang: str, n: int) -> list[str]:
        import random

        words = self._words.get(lang, [])
        return random.choices(words, k=n)


dictionary_service = DictionaryService()
