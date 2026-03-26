from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


# ---------------------------------------------------------------------------
# Auth schemas
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Session schemas
# ---------------------------------------------------------------------------


class SessionSubmit(BaseModel):
    exercise_id: str | None = None
    language: str
    wpm: float
    cpm: float
    accuracy: float
    duration_ms: int
    error_matrix_delta: dict[str, int] = {}


class SessionResponse(BaseModel):
    id: int
    wpm: float
    cpm: float
    accuracy: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Practice schemas
# ---------------------------------------------------------------------------


class TextResponse(BaseModel):
    text: str
    word_count: int
    char_count: int
    mode: str
    language: str


# ---------------------------------------------------------------------------
# Stats schemas
# ---------------------------------------------------------------------------


class SessionHistoryItem(BaseModel):
    wpm: float
    cpm: float
    accuracy: float
    created_at: datetime
    language: str

    model_config = ConfigDict(from_attributes=True)


class StatsResponse(BaseModel):
    sessions: list[SessionHistoryItem]
    avg_wpm: float
    best_wpm: float
    avg_accuracy: float
    total_sessions: int
    total_chars_typed: int
    streak_days: int


class HeatmapResponse(BaseModel):
    keys: dict[str, int]


class Achievement(BaseModel):
    id: str
    title: str
    description: str
    icon: str
    unlocked: bool
    unlocked_at: datetime | None = None


class AchievementsResponse(BaseModel):
    achievements: list[Achievement]


class CertificateResponse(BaseModel):
    eligible: bool
    tier: str | None
    wpm: float
    accuracy: float
    language: str
    date: datetime | None


class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int
