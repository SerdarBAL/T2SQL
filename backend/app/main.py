"""T2SQL FastAPI application entrypoint.

Endpoints:
  GET  /api/health  — liveness check
  POST /api/chat    — SSE stream of the agent answering a question
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router
from app.api.conversations import router as conversations_router
from app.db.conversations import init_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure the app.conversations table exists before serving requests.
    init_store()
    yield


app = FastAPI(title="T2SQL API", version="0.2.0", lifespan=lifespan)

# The Next.js frontend (Phase 3) runs on a different origin; allow it in dev.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(conversations_router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "t2sql-backend"}
