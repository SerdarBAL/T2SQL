"""The single state object threaded through every LangGraph node.

Each node reads what it needs and writes its output back into this dict.
LangGraph merges the partial dict a node returns into the running state,
so nodes only return the keys they change.
"""
from typing import Literal, TypedDict

Intent = Literal["sql_question", "chitchat", "unsupported"]


class AgentState(TypedDict, total=False):
    # --- input ---
    question: str

    # --- classify_intent ---
    intent: Intent

    # --- fetch_schema ---
    schema_text: str

    # --- generate_sql / validate_sql ---
    sql: str
    is_valid_sql: bool
    validation_error: str

    # --- execute_sql ---
    columns: list[str]
    rows: list[dict]
    row_count: int
    execution_error: str

    # --- terminal ---
    answer: str
    error: str
