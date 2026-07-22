"""Schema introspection: turns the live DB catalog into an LLM-readable prompt.

The agent's generate_sql node needs to know table/column names and types
without us hand-maintaining a schema doc that drifts from reality.
"""
from functools import lru_cache

from sqlalchemy import Engine, create_engine, inspect

from app.config import get_settings


@lru_cache
def get_engine() -> Engine:
    return create_engine(get_settings().database_url)


def get_schema_info(engine: Engine | None = None) -> dict[str, list[dict[str, str]]]:
    """Return {table_name: [{"name": col, "type": col_type}, ...]} for all tables."""
    engine = engine or get_engine()
    inspector = inspect(engine)

    schema: dict[str, list[dict[str, str]]] = {}
    for table_name in inspector.get_table_names():
        schema[table_name] = [
            {"name": col["name"], "type": str(col["type"])}
            for col in inspector.get_columns(table_name)
        ]
    return schema


def format_schema_for_prompt(schema: dict[str, list[dict[str, str]]]) -> str:
    """Render the schema dict as a compact text block for LLM prompts."""
    lines = []
    for table_name, columns in schema.items():
        col_list = ", ".join(f"{c['name']} {c['type']}" for c in columns)
        lines.append(f"{table_name}({col_list})")
    return "\n".join(lines)
