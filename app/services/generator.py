import json
import random
from pathlib import Path

from .dictionary import DictionaryService


class TextGenerator:
    def __init__(self, dictionary: DictionaryService) -> None:
        self._bigrams: dict[str, dict[str, float]] = {}
        self._transitions: dict[str, dict[str, dict[str, float]]] = {}
        self._dict = dictionary
        self._load_bigrams()
        self._build_transitions()

    def _load_bigrams(self) -> None:
        for lang in ("en", "ru"):
            path = Path(__file__).parent.parent / "data" / lang / "bigrams.json"
            with open(path, encoding="utf-8") as f:
                self._bigrams[lang] = json.load(f)

    def _build_transitions(self) -> None:
        for lang, bigrams in self._bigrams.items():
            trans: dict[str, dict[str, float]] = {}
            for bigram, freq in bigrams.items():
                if len(bigram) == 2:
                    c1, c2 = bigram[0], bigram[1]
                    trans.setdefault(c1, {})[c2] = freq
            self._transitions[lang] = trans

    def _markov_word(
        self,
        lang: str,
        allowed_chars: set[str] | None = None,
        length: int | None = None,
    ) -> str:
        trans = self._transitions.get(lang, {})
        if allowed_chars:
            # Filter transitions to allowed chars only
            filtered = {
                c: {n: p for n, p in nexts.items() if n in allowed_chars}
                for c, nexts in trans.items()
                if c in allowed_chars
            }
            trans = {k: v for k, v in filtered.items() if v}
        if not trans:
            return ""
        word_len = length or random.randint(3, 8)
        start = random.choice(list(trans.keys()))
        word = [start]
        for _ in range(word_len - 1):
            current = word[-1]
            nexts = trans.get(current, {})
            if not nexts:
                break
            chars = list(nexts.keys())
            weights = list(nexts.values())
            word.append(random.choices(chars, weights=weights, k=1)[0])
        return "".join(word)

    def generate(
        self,
        lang: str,
        mode: str = "free",
        allowed_chars: set[str] | None = None,
        weak_bigrams: dict[str, int] | None = None,
        target_length: int = 300,
    ) -> str:
        words: list[str] = []
        current_len = 0

        if mode == "structured":
            # Only use words containing allowed chars + generate pseudo-words
            if allowed_chars:
                allowed_lower = {c.lower() for c in allowed_chars if c != " "}
                real_words = [
                    w
                    for w in self._dict.get_words(lang)
                    if all(c in allowed_lower for c in w.lower())
                ]
            else:
                real_words = self._dict.get_words(lang)

            while current_len < target_length:
                if real_words and random.random() < 0.5:
                    word = random.choice(real_words)
                else:
                    word = self._markov_word(lang, allowed_chars)
                if word:
                    words.append(word)
                    current_len += len(word) + 1

        elif mode == "adaptive" and weak_bigrams:
            # Build weighted word pool biased toward weak bigrams
            all_words = self._dict.get_words(lang, limit=5000)

            def word_weight(w: str) -> float:
                score = 1.0
                for i in range(len(w) - 1):
                    bg = w[i : i + 2]
                    score += weak_bigrams.get(bg, 0) * 0.5
                return score

            weighted_words = [(w, word_weight(w)) for w in all_words]
            pool_words = [w for w, _ in weighted_words]
            pool_weights = [wt for _, wt in weighted_words]

            while current_len < target_length:
                if random.random() < 0.4:
                    word = self._markov_word(lang)
                else:
                    word = random.choices(pool_words, weights=pool_weights, k=1)[0]
                words.append(word)
                current_len += len(word) + 1

        elif mode == "bigrams":
            # Generate text as a sequence of bigrams separated by spaces.
            # If weak_bigrams provided, bias toward those; otherwise use corpus frequencies.
            if weak_bigrams:
                pool = list(weak_bigrams.keys())
                weights = [float(v) for v in weak_bigrams.values()]
            else:
                all_bigrams = self._bigrams.get(lang, {})
                pool = list(all_bigrams.keys())
                weights = [float(v) for v in all_bigrams.values()]

            if not pool:
                return ""

            while current_len < target_length:
                bigram = random.choices(pool, weights=weights, k=1)[0]
                words.append(bigram)
                current_len += len(bigram) + 1

        else:  # free mode
            while current_len < target_length:
                if random.random() < 0.1:
                    word = self._markov_word(lang)
                else:
                    word = self._dict.get_random_words(lang, 1)[0]
                words.append(word)
                current_len += len(word) + 1

        text = " ".join(words)
        # Trim to roughly target_length
        if len(text) > target_length + 50:
            last_space = text.rfind(" ", 0, target_length)
            text = text[:last_space] if last_space > 0 else text[:target_length]
        return text.strip()


_generator: TextGenerator | None = None


def get_generator() -> TextGenerator:
    global _generator
    if _generator is None:
        from .dictionary import dictionary_service

        _generator = TextGenerator(dictionary_service)
    return _generator
