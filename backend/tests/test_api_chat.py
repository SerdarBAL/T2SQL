"""/api/chat SSE endpoint tests (real agent behind a FastAPI TestClient)."""
import json

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _parse_sse(text: str) -> list[tuple[str, dict]]:
    """Turn a raw SSE body into a list of (event, data_dict)."""
    events = []
    event_name = None
    for line in text.splitlines():
        if line.startswith("event:"):
            event_name = line.split(":", 1)[1].strip()
        elif line.startswith("data:") and event_name:
            events.append((event_name, json.loads(line.split(":", 1)[1].strip())))
    return events


def test_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_chat_streams_full_pipeline():
    resp = client.post("/api/chat", json={"question": "How many orders are there?"})
    assert resp.status_code == 200

    events = _parse_sse(resp.text)
    names = [e for e, _ in events]

    assert "step" in names
    assert "sql" in names
    assert "result" in names
    assert "answer" in names
    assert names[-1] == "done"

    answer_payload = next(data for name, data in events if name == "answer")
    assert answer_payload["answer"]

    result_payload = next(data for name, data in events if name == "result")
    assert result_payload["viz_spec"]["chart_type"]


def test_chat_chitchat_has_answer_but_no_sql():
    resp = client.post("/api/chat", json={"question": "hi there"})
    events = _parse_sse(resp.text)
    names = [e for e, _ in events]

    assert "answer" in names
    assert "sql" not in names  # chitchat never generates SQL
