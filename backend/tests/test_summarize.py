"""summarize node tests: success answer + explanation, chitchat, graceful fail."""
from app.agent.nodes import summarize


def test_success_produces_answer_and_explanation():
    state = {
        "intent": "sql_question",
        "is_valid_sql": True,
        "execution_error": "",
        "question": "How many orders are there?",
        "sql": "SELECT count(*) AS n FROM olist_orders",
        "columns": ["n"],
        "rows": [{"n": 99441}],
    }
    out = summarize(state)
    assert out["answer"]
    assert "99441" in out["answer"] or "99,441" in out["answer"]
    assert out["sql_explanation"]


def test_chitchat_replies_without_touching_data():
    out = summarize({"intent": "chitchat", "question": "hi there"})
    assert out["answer"]
    assert "sql_explanation" not in out


def test_graceful_fail_when_execution_error_set():
    state = {
        "intent": "sql_question",
        "is_valid_sql": True,
        "execution_error": 'column "x" does not exist',
        "question": "bad question",
        "rows": [],
    }
    out = summarize(state)
    assert out["answer"]
    assert out["error"] == 'column "x" does not exist'
