"""Conversation store + API tests (real writable Postgres connection).

Also guards the security invariant: the agent's public-schema introspection
must never see the app.conversations table.
"""
from fastapi.testclient import TestClient

from app.db import conversations as store
from app.db.schema import get_schema_info
from app.main import app

client = TestClient(app)


def setup_module():
    store.init_store()


def test_conversations_hidden_from_agent_schema():
    assert "conversations" not in get_schema_info()


def test_store_crud_roundtrip():
    cid = store.create_conversation("Test thread", [{"role": "user", "q": "hi"}])

    fetched = store.get_conversation(cid)
    assert fetched is not None
    assert fetched["title"] == "Test thread"
    assert fetched["messages"] == [{"role": "user", "q": "hi"}]

    assert store.update_conversation(cid, "Renamed", None) is True
    assert store.get_conversation(cid)["title"] == "Renamed"

    ids = [c["id"] for c in store.list_conversations()]
    assert cid in ids

    assert store.delete_conversation(cid) is True
    assert store.get_conversation(cid) is None


def test_api_crud_roundtrip():
    created = client.post(
        "/api/conversations", json={"title": "API thread", "messages": []}
    )
    assert created.status_code == 200
    cid = created.json()["id"]

    listed = client.get("/api/conversations")
    assert any(c["id"] == cid for c in listed.json())

    got = client.get(f"/api/conversations/{cid}")
    assert got.json()["title"] == "API thread"

    updated = client.put(
        f"/api/conversations/{cid}", json={"messages": [{"role": "user"}]}
    )
    assert updated.status_code == 200

    deleted = client.delete(f"/api/conversations/{cid}")
    assert deleted.status_code == 200

    assert client.get(f"/api/conversations/{cid}").status_code == 404


def test_missing_conversation_is_404():
    assert client.get("/api/conversations/00000000-0000-0000-0000-000000000000").status_code == 404
