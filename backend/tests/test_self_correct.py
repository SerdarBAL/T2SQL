"""Self-correction tests.

- Unit: self_correct repairs a genuinely broken query (real LLM + real DB).
- Routing: the execute -> self_correct loop retries on error but stops at
  the retry cap, so the graph can never loop forever.
"""
from app.agent import graph as graph_module
from app.agent.nodes import self_correct
from app.config import get_settings
from app.db.execute import SQLAlchemyError, run_select
from app.db.schema import format_schema_for_prompt, get_schema_info


def test_self_correct_repairs_bad_column():
    bad_sql = "SELECT total_price FROM olist_orders LIMIT 5"
    try:
        run_select(bad_sql)
        raise AssertionError("expected the bad SQL to fail")
    except SQLAlchemyError as exc:
        error = str(exc.orig)

    out = self_correct(
        {
            "question": "Show 5 order prices",
            "schema_text": format_schema_for_prompt(get_schema_info()),
            "sql": bad_sql,
            "execution_error": error,
        }
    )
    assert out["correction_attempts"] == 1
    # The repaired query actually runs.
    result = run_select(out["sql"])
    assert result["row_count"] >= 1


def test_route_retries_on_error_until_cap():
    """The post-execute router: retry on error, stop at the cap, exit on success."""
    max_retries = get_settings().max_self_correct_retries

    # Error + attempts left -> keep correcting.
    assert (
        graph_module._route_after_execute(
            {"execution_error": "boom", "correction_attempts": 0}
        )
        == "self_correct"
    )
    # Error + cap reached -> graceful fail, hand off to summarize.
    assert (
        graph_module._route_after_execute(
            {"execution_error": "boom", "correction_attempts": max_retries}
        )
        == "summarize"
    )
    # No error -> proceed to visualization, then summarize.
    assert (
        graph_module._route_after_execute(
            {"execution_error": "", "correction_attempts": 0}
        )
        == "decide_visualization"
    )
