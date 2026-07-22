"""SELECT-only static guard — the app's first line of defense.

The read-only DB role is the real backstop, but rejecting dangerous SQL
before it ever reaches Postgres gives faster, clearer failures and keeps
mistakes out of the query log.
"""
import re

# Statements that write, change structure, or grant rights — never allowed.
FORBIDDEN_KEYWORDS = (
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "TRUNCATE",
    "GRANT",
    "REVOKE",
    "CREATE",
    "REPLACE",
    "MERGE",
)


class SqlValidationError(Exception):
    """Raised when generated SQL fails a security check."""


def _strip_sql_comments(sql: str) -> str:
    """Remove -- line comments and /* */ block comments before scanning."""
    sql = re.sub(r"--[^\n]*", " ", sql)
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    return sql


def validate_select_only(sql: str) -> str:
    """Return the cleaned SQL if safe; raise SqlValidationError otherwise.

    Checks, in order:
      1. non-empty
      2. starts with SELECT or WITH (a CTE that feeds a SELECT)
      3. contains no forbidden write/DDL keyword (as a whole word)
      4. is a single statement (no stacked queries via `;`)
    """
    if not sql or not sql.strip():
        raise SqlValidationError("Empty SQL.")

    cleaned = _strip_sql_comments(sql).strip().rstrip(";").strip()

    # Reject stacked statements like "SELECT ...; DELETE ..."
    if ";" in cleaned:
        raise SqlValidationError("Multiple statements are not allowed.")

    first_word = cleaned.split(None, 1)[0].upper()
    if first_word not in ("SELECT", "WITH"):
        raise SqlValidationError(f"Only SELECT queries are allowed, got: {first_word}")

    upper = cleaned.upper()
    for keyword in FORBIDDEN_KEYWORDS:
        if re.search(rf"\b{keyword}\b", upper):
            raise SqlValidationError(f"Forbidden keyword detected: {keyword}")

    return cleaned
