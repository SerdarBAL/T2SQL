"""Low-cardinality text columns get their real values inlined into the schema.

This prevents the LLM from inventing values like order_status='not_delivered',
which returns 0 rows (no error) and so never triggers self-correction.
"""
from app.db.schema import format_schema_for_prompt, get_schema_info


def test_order_status_values_present_in_schema():
    schema = get_schema_info()
    status_col = next(
        c for c in schema["olist_orders"] if c["name"] == "order_status"
    )
    assert "values" in status_col
    assert "delivered" in status_col["values"]
    assert "shipped" in status_col["values"]


def test_high_cardinality_column_has_no_values():
    schema = get_schema_info()
    order_id_col = next(
        c for c in schema["olist_orders"] if c["name"] == "order_id"
    )
    # ~99k distinct ids — must not be inlined.
    assert "values" not in order_id_col


def test_prompt_renders_enum_values():
    text = format_schema_for_prompt(get_schema_info())
    assert "order_status TEXT {" in text
    assert "delivered" in text
