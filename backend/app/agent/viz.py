"""Pick a chart type from the shape of a result set — no LLM needed.

The frontend renders Plotly from this spec. We only need to decide the
chart type and which columns map to x / y; deterministic rules are faster,
free, and easy to test.

Rules (first match wins):
- 0 rows or 1 cell            -> table (nothing to plot)
- a date-like col + a number  -> line  (time series)
- a category col + a number,
  few rows                    -> bar
- exactly 2 cols, few rows,
  numbers sum to a whole      -> pie   (parts of a whole)
- otherwise                   -> table
"""
from datetime import date, datetime
from numbers import Number

_DATE_HINTS = ("date", "month", "day", "week", "year", "timestamp", "time")
_MAX_CATEGORY_ROWS = 30
_MAX_PIE_SLICES = 8


def _is_number(value) -> bool:
    return isinstance(value, Number) and not isinstance(value, bool)


def _is_date_like(name: str, value) -> bool:
    if isinstance(value, (date, datetime)):
        return True
    lowered = name.lower()
    return any(hint in lowered for hint in _DATE_HINTS)


def build_viz_spec(columns: list[str], rows: list[dict]) -> dict:
    """Return {"chart_type": ..., "x": col, "y": col} (x/y omitted for table)."""
    if not rows or not columns:
        return {"chart_type": "table"}

    # A single scalar (one row, one column) is just a number — show as table.
    if len(rows) == 1 and len(columns) == 1:
        return {"chart_type": "table"}

    first = rows[0]
    # Date-like wins over numeric: EXTRACT(MONTH) is an int named "month",
    # but it belongs on the time axis, not as the measured value.
    date_cols = [c for c in columns if _is_date_like(c, first.get(c))]
    numeric_cols = [
        c for c in columns if _is_number(first.get(c)) and c not in date_cols
    ]
    category_cols = [c for c in columns if c not in numeric_cols and c not in date_cols]

    # Time series -> line. With year+month, the last date col is the most
    # granular one and makes the better x-axis.
    if date_cols and numeric_cols:
        return {"chart_type": "line", "x": date_cols[-1], "y": numeric_cols[0]}

    if category_cols and numeric_cols and len(rows) <= _MAX_CATEGORY_ROWS:
        # Few slices with 2 columns reads well as a pie (share of total).
        if len(columns) == 2 and len(rows) <= _MAX_PIE_SLICES:
            return {"chart_type": "pie", "x": category_cols[0], "y": numeric_cols[0]}
        return {"chart_type": "bar", "x": category_cols[0], "y": numeric_cols[0]}

    return {"chart_type": "table"}
