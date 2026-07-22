"""Runs a validated SELECT against Postgres with two safety rails.

1. Statement timeout — a runaway query is killed at the DB level.
2. Auto-LIMIT — if the query has no LIMIT, we cap rows so an accidental
   full-table scan can't flood the response. The read-only role is the
   real security backstop; this is about resilience.
"""
import re

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_settings
from app.db.schema import get_engine

DEFAULT_ROW_LIMIT = 1000


def _ensure_limit(sql: str, limit: int = DEFAULT_ROW_LIMIT) -> str:
    """Append a LIMIT clause only if the query doesn't already have one."""
    if re.search(r"\blimit\b", sql, flags=re.IGNORECASE):
        return sql
    return f"{sql.rstrip().rstrip(';')}\nLIMIT {limit}"


def run_select(sql: str) -> dict:
    """Execute SELECT SQL and return {columns, rows, row_count}.

    Raises SQLAlchemyError (with the original Postgres message) on failure,
    so the caller / self-correction loop can feed the error back to the LLM.
    """
    settings = get_settings()
    limited_sql = _ensure_limit(sql)
    # int from config — Postgres SET can't take a bind parameter, so we
    # interpolate, but the value is never user-controlled.
    timeout_ms = int(settings.sql_statement_timeout_ms)

    engine = get_engine()
    with engine.begin() as conn:
        # SET LOCAL applies only within this transaction.
        conn.execute(text(f"SET LOCAL statement_timeout = {timeout_ms}"))
        result = conn.execute(text(limited_sql))
        columns = list(result.keys())
        rows = [dict(row) for row in result.mappings()]

    return {"columns": columns, "rows": rows, "row_count": len(rows)}


__all__ = ["run_select", "DEFAULT_ROW_LIMIT", "SQLAlchemyError"]
