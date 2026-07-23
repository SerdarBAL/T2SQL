"""Schema introspection: turns the live DB catalog into an LLM-readable prompt.

The agent's generate_sql node needs to know table/column names and types
without us hand-maintaining a schema doc that drifts from reality.

We also enrich low-cardinality text columns (like order_status) with their
actual distinct values. Without this the LLM guesses values — e.g. inventing
order_status = 'not_delivered', which silently returns 0 rows instead of an
error, so self-correction never kicks in.
"""
from functools import lru_cache

from sqlalchemy import Engine, create_engine, inspect, text

from app.config import get_settings

# A text column with at most this many distinct values is treated as an enum;
# its values are inlined into the schema so the LLM uses them verbatim.
MAX_ENUM_VALUES = 30
# Text SQL types we consider for enum enrichment.
_TEXT_TYPES = ("CHAR", "TEXT", "VARCHAR")


@lru_cache
def get_engine() -> Engine:
    return create_engine(get_settings().database_url)


def _distinct_values(engine: Engine, table: str, column: str) -> list[str] | None:
    """Return the column's distinct values if there are few enough, else None.

    Identifiers come from introspection (never user input) but are still
    quoted defensively.
    """
    ident = f'"{table}"."{column}"'
    sql = text(
        f"SELECT DISTINCT {ident} AS v FROM \"{table}\" "
        f"WHERE {ident} IS NOT NULL LIMIT {MAX_ENUM_VALUES + 1}"
    )
    with engine.connect() as conn:
        rows = conn.execute(sql).scalars().all()
    if len(rows) > MAX_ENUM_VALUES:
        return None
    return sorted(str(r) for r in rows)


@lru_cache
def get_schema_info(engine: Engine | None = None) -> dict[str, list[dict]]:
    """Return {table: [{"name", "type", optional "values"}, ...]} for all tables.

    Cached: the distinct-value probes run once, not on every request.
    """
    engine = engine or get_engine()
    inspector = inspect(engine)

    schema: dict[str, list[dict]] = {}
    for table_name in inspector.get_table_names():
        columns: list[dict] = []
        for col in inspector.get_columns(table_name):
            col_type = str(col["type"])
            entry: dict = {"name": col["name"], "type": col_type}
            if any(t in col_type.upper() for t in _TEXT_TYPES):
                values = _distinct_values(engine, table_name, col["name"])
                if values is not None:
                    entry["values"] = values
            columns.append(entry)
        schema[table_name] = columns
    return schema


def format_schema_for_prompt(schema: dict[str, list[dict]]) -> str:
    """Render the schema dict as a compact text block for LLM prompts.

    Enum-like columns show their allowed values: `order_status text {delivered|...}`.
    """
    lines = []
    for table_name, columns in schema.items():
        parts = []
        for c in columns:
            piece = f"{c['name']} {c['type']}"
            if c.get("values"):
                piece += " {" + "|".join(c["values"]) + "}"
            parts.append(piece)
        lines.append(f"{table_name}({', '.join(parts)})")
    return "\n".join(lines)
