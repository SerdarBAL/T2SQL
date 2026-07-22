"""Day 4 smoke tests: LLM reachable, schema introspection returns real tables.

These hit the live Gemini API and the local Postgres — not mocked — because
the goal today is confirming the wiring works end to end, not unit coverage.
"""
from app.agent.llm import get_llm
from app.db.schema import format_schema_for_prompt, get_schema_info


def test_llm_returns_plain_text_answer():
    llm = get_llm()
    response = llm.invoke("Reply with exactly the word: PONG")
    assert "PONG" in response.content


def test_schema_introspection_finds_olist_tables():
    schema = get_schema_info()
    assert "olist_orders" in schema
    assert "olist_order_items" in schema
    assert any(col["name"] == "order_id" for col in schema["olist_orders"])


def test_schema_formats_as_readable_prompt_block():
    schema = get_schema_info()
    text = format_schema_for_prompt(schema)
    assert "olist_orders(" in text
