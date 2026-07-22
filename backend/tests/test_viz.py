"""Unit tests for the chart-type heuristic — no LLM, no DB."""
from datetime import date

from app.agent.viz import build_viz_spec


def test_empty_result_is_table():
    assert build_viz_spec([], [])["chart_type"] == "table"


def test_single_scalar_is_table():
    spec = build_viz_spec(["n"], [{"n": 99441}])
    assert spec["chart_type"] == "table"


def test_category_plus_number_many_rows_is_bar():
    cols = ["category", "revenue"]
    rows = [{"category": f"c{i}", "revenue": i} for i in range(15)]
    spec = build_viz_spec(cols, rows)
    assert spec == {"chart_type": "bar", "x": "category", "y": "revenue"}


def test_two_cols_few_slices_is_pie():
    cols = ["category", "revenue"]
    rows = [{"category": f"c{i}", "revenue": i + 1} for i in range(4)]
    spec = build_viz_spec(cols, rows)
    assert spec["chart_type"] == "pie"


def test_date_plus_number_is_line():
    cols = ["order_month", "revenue"]
    rows = [{"order_month": date(2017, m, 1), "revenue": m * 100} for m in range(1, 6)]
    spec = build_viz_spec(cols, rows)
    assert spec == {"chart_type": "line", "x": "order_month", "y": "revenue"}


def test_date_by_name_is_line_even_if_string():
    cols = ["month", "revenue"]
    rows = [{"month": f"2017-0{m}", "revenue": m * 100} for m in range(1, 6)]
    spec = build_viz_spec(cols, rows)
    assert spec["chart_type"] == "line"
