"""End-to-end graph tests (real Gemini + real Postgres schema).

Day 5 goal: a data question flows classify -> schema -> generate -> validate
and produces valid SELECT SQL; a greeting short-circuits before SQL.
"""
from app.agent.graph import agent_graph


def test_data_question_produces_valid_select():
    result = agent_graph.invoke({"question": "How many orders are there in total?"})

    assert result["intent"] == "sql_question"
    assert result["schema_text"]  # schema was fetched
    assert result["is_valid_sql"] is True
    assert result["sql"].upper().startswith(("SELECT", "WITH"))


def test_greeting_short_circuits_before_sql():
    result = agent_graph.invoke({"question": "hi, how are you?"})

    assert result["intent"] in ("chitchat", "unsupported")
    assert "sql" not in result  # SQL pipeline never ran


def test_data_question_runs_and_returns_rows():
    """Day 6 happy path: question -> SQL -> real result set."""
    result = agent_graph.invoke({"question": "How many orders are there in total?"})

    assert result["is_valid_sql"] is True
    assert result["execution_error"] == ""
    assert result["row_count"] >= 1
    assert result["columns"]  # at least one column returned


def test_full_pipeline_ends_with_english_answer():
    """Day 9: question -> ... -> summarize produces answer + SQL explanation."""
    result = agent_graph.invoke({"question": "How many orders are there in total?"})

    assert result["answer"]
    assert result["sql_explanation"]
