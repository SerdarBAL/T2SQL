"""T2SQL FastAPI application entrypoint.

Endpoints:
  GET  /api/health  — liveness check
  POST /api/chat    — SSE stream of the agent answering a question
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router

app = FastAPI(title="T2SQL API", version="0.1.0")

# The Next.js frontend (Phase 3) runs on a different origin; allow it in dev.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "t2sql-backend"}
