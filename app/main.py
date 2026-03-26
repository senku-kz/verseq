from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, lessons, practice, sessions, stats

app = FastAPI(title="VerseQ API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:9000", "http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(practice.router)
app.include_router(lessons.router)
app.include_router(sessions.router)
app.include_router(stats.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
