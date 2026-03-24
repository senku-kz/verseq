# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Project: VerseQ Web — Touch Typing Trainer

A browser-based touch typing trainer supporting **English** and **Russian** keyboards. Inspired by **VerseQ** (adaptive, phonetically-generated exercises) and **Ratatype** (structured progressive lessons + gamification). The goal is to teach blind typing in short daily sessions with both a guided course and free practice modes.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | Python 3.11+, FastAPI, Uvicorn |
| Frontend | Vue 3 (Composition API), Quasar Framework v2 |
| Database | SQLite (dev) / PostgreSQL (prod) via SQLAlchemy async |
| Auth | JWT (access + refresh tokens) |
| Package manager (BE) | `uv` or `pip` with `pyproject.toml` |
| Package manager (FE) | `npm` / `pnpm` with Quasar CLI |

---

## Development Commands

### Backend
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt
# or
uv sync

# Run dev server (auto-reload)
uvicorn app.main:app --reload --port 8000

# Run tests
pytest
pytest tests/test_lessons.py -v        # single test file
pytest -k "test_adaptive"              # single test by name

# Lint / format
ruff check .
ruff format .
```

### Frontend
```bash
cd frontend

# Install dependencies
npm install

# Run dev server (hot-reload, proxies /api → localhost:8000)
quasar dev

# Build for production
quasar build

# Lint
npm run lint
```

---

## Architecture Overview

```
verseq/
├── app/                        # FastAPI backend
│   ├── main.py                 # App factory, router registration, CORS
│   ├── core/
│   │   ├── config.py           # Settings (env vars via pydantic-settings)
│   │   └── security.py         # JWT creation/verification
│   ├── api/
│   │   ├── auth.py             # /auth/register, /auth/login, /auth/refresh
│   │   ├── lessons.py          # /lessons/* — course structure & content
│   │   ├── practice.py         # /practice/* — free practice & text generation
│   │   ├── sessions.py         # /sessions/* — submit results, history
│   │   └── stats.py            # /stats/* — WPM progress, heatmaps
│   ├── models/                 # SQLAlchemy ORM models
│   ├── schemas/                # Pydantic request/response schemas
│   ├── services/
│   │   ├── adaptive.py         # Adaptive algorithm: weak-key tracking
│   │   ├── generator.py        # Phonetic/ngram text generator
│   │   └── dictionary.py       # Word list loader (EN/RU)
│   └── data/
│       ├── en/                 # English word lists, ngram tables
│       └── ru/                 # Russian word lists, ngram tables
│
└── frontend/                   # Quasar/Vue 3 frontend
    ├── src/
    │   ├── pages/
    │   │   ├── LandingPage.vue
    │   │   ├── CoursePage.vue      # Lesson list + progress
    │   │   ├── LessonPage.vue      # Active typing lesson
    │   │   ├── PracticePage.vue    # Free practice / custom text
    │   │   └── StatsPage.vue       # WPM history, heatmap, achievements
    │   ├── components/
    │   │   ├── TypingZone.vue      # Core typing input + text display
    │   │   ├── KeyboardViz.vue     # On-screen keyboard with finger-zone colors
    │   │   ├── ResultsCard.vue     # Post-exercise WPM/accuracy summary
    │   │   └── HeatmapChart.vue    # Per-key error heatmap
    │   ├── stores/
    │   │   ├── auth.ts             # Pinia: user session
    │   │   ├── lesson.ts           # Pinia: current lesson state
    │   │   └── settings.ts         # Pinia: language, sound, keyboard theme
    │   └── composables/
    │       ├── useTypingEngine.ts  # WPM timer, error detection, input handling
    │       └── useKeyboard.ts      # Key → finger → color mapping
```

---

## Core Features & Behaviour

### 1. Typing Engine (`useTypingEngine.ts`)

The typing engine is the heart of the application. Rules:

- **Error blocking**: cursor does not advance past a wrong character. User must press `Backspace` to correct before continuing. This trains clean muscle memory (Ratatype model).
- **WPM calculation**: `net WPM = (correct_chars / 5) / elapsed_minutes`. Timer starts on first keypress, stops on last character.
- **CPM** is displayed alongside WPM (primary metric for Russian, secondary for English).
- **Accuracy**: `(total_chars - errors) / total_chars * 100` — counted per-attempt (not session).
- Text is split into `spans` with states: `pending | correct | error | corrected`.

### 2. Keyboard Visualizer (`KeyboardViz.vue`)

- Renders a full QWERTY / ЙЦУКЕН keyboard depending on active language.
- **8 finger-zone colors** (left pinky → right pinky; thumbs are spacebar/neutral).
- **Next-key highlight**: the key corresponding to the next character in the exercise glows.
- **Error flash**: when a wrong key is pressed, that key briefly flashes red.
- Can be toggled off for "advanced mode" (no visual aids).

Finger-zone color assignments must be consistent between `KeyboardViz.vue` and `useKeyboard.ts`.

### 3. Lesson Course Structure

A structured course of **15 lessons**, each with 5–10 exercises:

| Phase | Lessons | Focus |
|---|---|---|
| Foundation | 1–4 | Home row → index extensions → middle/ring → pinkies |
| Word drills | 5–8 | Real common words using learned keys |
| Patterns | 9–11 | Bigrams, vowel clusters, punctuation |
| Full keyboard | 12–15 | Numbers, Shift, capitals, full sentences |

Lesson 1 always starts with home row (ASDF / JKL; for EN, ФЫВА / ОЛДЖ for RU). The F/J tactile-bump concept is introduced in the UI onboarding.

Each exercise has a `min_accuracy` and `min_wpm` threshold — the user must meet both to earn the exercise star. Exercises can be retried.

### 4. Text Generation (`generator.py`)

Two modes:

**a) Structured (lessons 1–8)**: generate sequences using only the keys introduced so far. Algorithm:
1. Take the set of allowed keys for the current lesson.
2. Generate words by sampling from bigram/trigram frequency tables built from real corpus (restricted to allowed chars only).
3. Shuffle and pad to target length (~200–400 characters per exercise).

**b) Free/adaptive (lessons 9+ and Practice mode)**: full-keyboard phonetically plausible text.
- Load ngram frequency tables for the target language (EN/RU) from `app/data/`.
- Generate pseudo-words by Markov chain on character ngrams (order 3).
- Mix generated pseudo-words with real top-1000 frequency words (ratio ~40/60).
- Fallback: serve random lines from loaded dictionary file if generator is disabled.

### 5. Adaptive Algorithm (`adaptive.py`)

Tracks a per-user **error matrix**: a dict of `{bigram: error_count}` (e.g., `"th": 12`, `"ст": 5`). Updated after every submitted session.

In Practice / adaptive mode, the text generator biases toward bigrams where `error_count` is highest. This implements VerseQ's core principle: the system generates exercises targeting your personal weak spots.

Error matrix is persisted in the database per user. Anonymous users get a session-scoped in-memory matrix (stored in `localStorage` as serialised JSON).

### 6. Languages & Dictionaries

- Language is toggled globally via settings (EN / RU).
- Language affects: keyboard layout rendered, text generated, dictionary loaded, WPM/CPM display preference.
- Dictionary files: `app/data/en/words_10k.txt`, `app/data/ru/words_10k.txt` — one word per line, frequency-sorted.
- Ngram tables: `app/data/en/bigrams.json`, `app/data/ru/bigrams.json` — `{bigram: relative_frequency}`.

### 7. Statistics & Progress (`StatsPage.vue`, `/api/stats`)

- Per-session history: timestamp, language, WPM, accuracy, exercise_id, duration.
- WPM trend chart over last 30 days.
- Per-key error heatmap: overlaid on the keyboard visualizer, keys colored by error rate (green → yellow → red).
- Achievements: milestones for first lesson completed, 30 WPM, 50 WPM, 70 WPM, 7-day streak.
- Shareable certificate at 40/50/70 WPM + ≥96% accuracy thresholds.

---

## API Conventions

- All endpoints prefixed `/api/v1/`
- Auth: `Authorization: Bearer <access_token>` header
- Error responses: `{"detail": "message"}` (FastAPI default)
- Session submit payload: `{exercise_id, language, wpm, cpm, accuracy, duration_ms, error_matrix_delta}`
- Text generation endpoint: `GET /api/v1/practice/text?lang=en&mode=adaptive&length=300` returns `{text: "...", metadata: {...}}`

---

## Key Design Decisions

- **Error blocking over error counting** — do not allow advancing past a mistake. This is non-negotiable for lesson mode. Practice mode may have a "free flow" toggle.
- **No row-isolation restriction in Practice mode** — inspired by VerseQ: once the course is complete, free practice uses the full keyboard immediately.
- **WPM timer starts on first keypress**, not on page load.
- **Backspace corrects one character** — full-word delete (Ctrl+Backspace) is disabled to prevent skipping practice.
- **Keyboard visualizer is always visible in lessons**, optional in practice.
- **No account required for practice** — anonymous users get full practice mode with localStorage-backed progress. Account required for course progress persistence and stats.
