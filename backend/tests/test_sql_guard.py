"""Unit tests for the SELECT-only guard — no LLM, no DB, fast and deterministic."""
import pytest

from app.agent.sql_guard import SqlValidationError, validate_select_only


def test_plain_select_passes():
    sql = "SELECT count(*) FROM olist_orders"
    assert validate_select_only(sql) == sql


def test_cte_with_passes():
    sql = "WITH t AS (SELECT 1 AS n) SELECT n FROM t"
    assert validate_select_only(sql) == sql


def test_trailing_semicolon_is_stripped():
    assert validate_select_only("SELECT 1;") == "SELECT 1"


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM olist_orders",
        "UPDATE olist_orders SET price = 0",
        "INSERT INTO olist_orders VALUES (1)",
        "DROP TABLE olist_orders",
        "TRUNCATE olist_orders",
        "ALTER TABLE olist_orders ADD COLUMN x int",
    ],
)
def test_write_and_ddl_rejected(sql):
    with pytest.raises(SqlValidationError):
        validate_select_only(sql)


def test_stacked_statement_rejected():
    with pytest.raises(SqlValidationError):
        validate_select_only("SELECT 1; DROP TABLE olist_orders")


def test_forbidden_keyword_hidden_in_comment_is_ignored():
    # The DELETE is only in a comment, so the query is genuinely a safe SELECT.
    sql = "SELECT 1 -- todo: DELETE later"
    assert validate_select_only(sql) == "SELECT 1"


def test_empty_sql_rejected():
    with pytest.raises(SqlValidationError):
        validate_select_only("   ")
