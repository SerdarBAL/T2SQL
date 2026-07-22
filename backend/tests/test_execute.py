"""Tests for the SQL execution layer: auto-LIMIT logic (unit) and a real run."""
from app.db.execute import DEFAULT_ROW_LIMIT, _ensure_limit, run_select


def test_ensure_limit_appends_when_missing():
    out = _ensure_limit("SELECT 1")
    assert out.endswith(f"LIMIT {DEFAULT_ROW_LIMIT}")


def test_ensure_limit_respects_existing_limit():
    sql = "SELECT 1 LIMIT 5"
    assert _ensure_limit(sql) == sql


def test_ensure_limit_strips_trailing_semicolon_before_appending():
    out = _ensure_limit("SELECT 1;")
    assert ";" not in out
    assert out.endswith(f"LIMIT {DEFAULT_ROW_LIMIT}")


def test_run_select_returns_rows():
    result = run_select("SELECT count(*) AS n FROM olist_orders")
    assert result["columns"] == ["n"]
    assert result["row_count"] == 1
    assert result["rows"][0]["n"] == 99441
