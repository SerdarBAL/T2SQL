"""Conversation persistence — the app's own metadata, kept separate from Olist.

Stored in the `app` schema via a writable owner connection. The agent's schema
introspection only looks at `public`, so these tables never leak into prompts.

One table, `app.conversations`, holds the whole thread as a JSONB blob. That's
plenty for a single-user history sidebar; a messages table can come later if we
add search or multi-user.
"""
import json
import uuid
from functools import lru_cache

from sqlalchemy import Engine, create_engine, text

from app.config import get_settings

_DDL = """
CREATE SCHEMA IF NOT EXISTS app;

CREATE TABLE IF NOT EXISTS app.conversations (
    id          uuid PRIMARY KEY,
    title       text NOT NULL,
    messages    jsonb NOT NULL DEFAULT '[]'::jsonb,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);
"""


@lru_cache
def get_app_engine() -> Engine:
    return create_engine(get_settings().app_database_url)


def init_store() -> None:
    """Create the schema/table if they don't exist. Safe to call on startup."""
    engine = get_app_engine()
    with engine.begin() as conn:
        conn.execute(text(_DDL))


def list_conversations() -> list[dict]:
    """Return conversations without their message bodies, newest first."""
    engine = get_app_engine()
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                "SELECT id, title, updated_at FROM app.conversations "
                "ORDER BY updated_at DESC"
            )
        ).mappings()
        return [
            {"id": str(r["id"]), "title": r["title"], "updated_at": r["updated_at"]}
            for r in rows
        ]


def get_conversation(conversation_id: str) -> dict | None:
    engine = get_app_engine()
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT id, title, messages, created_at, updated_at "
                "FROM app.conversations WHERE id = :id"
            ),
            {"id": conversation_id},
        ).mappings().first()
    if row is None:
        return None
    return {
        "id": str(row["id"]),
        "title": row["title"],
        "messages": row["messages"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def create_conversation(title: str, messages: list) -> str:
    conversation_id = str(uuid.uuid4())
    engine = get_app_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO app.conversations (id, title, messages) "
                "VALUES (:id, :title, CAST(:messages AS jsonb))"
            ),
            {"id": conversation_id, "title": title, "messages": json.dumps(messages)},
        )
    return conversation_id


def update_conversation(
    conversation_id: str, title: str | None, messages: list | None
) -> bool:
    """Update title and/or messages; bumps updated_at. Returns False if absent."""
    sets = ["updated_at = now()"]
    params: dict = {"id": conversation_id}
    if title is not None:
        sets.append("title = :title")
        params["title"] = title
    if messages is not None:
        sets.append("messages = CAST(:messages AS jsonb)")
        params["messages"] = json.dumps(messages)

    engine = get_app_engine()
    with engine.begin() as conn:
        result = conn.execute(
            text(f"UPDATE app.conversations SET {', '.join(sets)} WHERE id = :id"),
            params,
        )
        return result.rowcount > 0


def delete_conversation(conversation_id: str) -> bool:
    engine = get_app_engine()
    with engine.begin() as conn:
        result = conn.execute(
            text("DELETE FROM app.conversations WHERE id = :id"),
            {"id": conversation_id},
        )
        return result.rowcount > 0
