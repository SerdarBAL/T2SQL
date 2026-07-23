"""Pick a chart type from the shape of a result set — no LLM needed.

The frontend renders Plotly (or a KPI card) from this spec. We only decide
the chart type and which columns map to x / y; deterministic rules are
faster, free, and easy to test.

Rules (first match wins):
- 0 rows / empty                 -> table
- 1 row, 1 numeric value         -> kpi    (one big number)
- a date-like col + a number     -> line   (time series)
- 2 numeric cols, many rows      -> scatter(relationship between two measures)
- category + number, 2 cols,
  few rows                       -> pie    (share of a whole, donut)
- category + number, few rows    -> bar    (vertical)
- category + number, many rows   -> hbar   (horizontal; long labels stay readable)
- otherwise                      -> table
"""
from datetime import date, datetime
from numbers import Number

_DATE_HINTS = ("date", "month", "day", "week", "year", "timestamp", "time")
_MAX_CATEGORY_ROWS = 30
_MAX_PIE_SLICES = 6
_MAX_VERTICAL_BARS = 8


def _is_number(value) -> bool:
    return isinstance(value, Number) and not isinstance(value, bool)


def _is_date_like(name: str, value) -> bool:
    if isinstance(value, (date, datetime)):
        return True
    lowered = name.lower()
    return any(hint in lowered for hint in _DATE_HINTS)


def build_viz_spec(columns: list[str], rows: list[dict]) -> dict:
    """Return {"chart_type": ..., "x": col, "y": col}.

    x/y are omitted for table; kpi carries only y (the value column).
    """
    if not rows or not columns:
        return {"chart_type": "table"}

    first = rows[0]
    # Date-like wins over numeric: EXTRACT(MONTH) is an int named "month",
    # but it belongs on the time axis, not as the measured value.
    date_cols = [c for c in columns if _is_date_like(c, first.get(c))]
    numeric_cols = [
        c for c in columns if _is_number(first.get(c)) and c not in date_cols
    ]
    category_cols = [c for c in columns if c not in numeric_cols and c not in date_cols]

    # A single number -> KPI card.
    if len(rows) == 1 and len(numeric_cols) == 1 and len(columns) == 1:
        return {"chart_type": "kpi", "y": numeric_cols[0]}

    # Time series -> line. With year+month, the last date col is the most
    # granular one and makes the better x-axis.
    if date_cols and numeric_cols:
        return {"chart_type": "line", "x": date_cols[-1], "y": numeric_cols[0]}

    # Two measures, no category axis -> scatter (relationship).
    if len(numeric_cols) >= 2 and not category_cols and not date_cols and len(rows) > 1:
        return {"chart_type": "scatter", "x": numeric_cols[0], "y": numeric_cols[1]}

    if category_cols and numeric_cols and len(rows) <= _MAX_CATEGORY_ROWS:
        x, y = category_cols[0], numeric_cols[0]
        if len(columns) == 2 and len(rows) <= _MAX_PIE_SLICES:
            return {"chart_type": "pie", "x": x, "y": y}
        if len(rows) <= _MAX_VERTICAL_BARS:
            return {"chart_type": "bar", "x": x, "y": y}
        # Many categories: horizontal bars keep long labels legible.
        return {"chart_type": "hbar", "x": x, "y": y}

    return {"chart_type": "table"}
