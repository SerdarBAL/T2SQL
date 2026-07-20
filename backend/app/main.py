"""T2SQL FastAPI application entrypoint.

Phase 0: minimal skeleton with a health check.
The LangGraph agent, /api/chat (SSE), /api/schema endpoints are added in later phases.
"""
from fastapi import FastAPI

app = FastAPI(title="T2SQL API", version="0.0.1")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "t2sql-backend"}
