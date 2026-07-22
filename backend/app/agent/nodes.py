"""LangGraph node functions for the T2SQL agent.

Each node takes the current AgentState and returns a partial dict of the
keys it updates. Day 5 covers: classify_intent, fetch_schema, generate_sql,
validate_sql. execute_sql / self_correct / summarize arrive in later days.
"""
import re

from app.agent.llm import get_llm
from app.agent.sql_guard import SqlValidationError, validate_select_only
from app.agent.state import AgentState
from app.db.execute import SQLAlchemyError, run_select
from app.db.schema import format_schema_for_prompt, get_schema_info

# --- prompts -----------------------------------------------------------------

_CLASSIFY_PROMPT = """You classify a user's message into exactly one label.

Labels:
- sql_question: the user wants data/analytics that can be answered by querying
  the e-commerce database (revenue, orders, customers, products, categories...).
- chitchat: greetings, thanks, small talk, or questions about you.
- unsupported: anything that needs data we don't have, or is not a data question.

Reply with ONLY the label, nothing else.

Message: {question}
Label:"""

_GENERATE_SQL_PROMPT = """You are a PostgreSQL expert for a Brazilian e-commerce
(Olist) database. Write a single SQL query that answers the user's question.

Rules:
- PostgreSQL dialect only.
- SELECT queries only. Never write/modify data.
- Return ONLY the SQL query. No explanation, no markdown fences.
- Revenue is NOT a column: it is SUM(olist_order_items.price), joined to
  olist_orders on order_id.

Database schema (table(column type, ...)):
{schema}

Question: {question}

SQL:"""


# --- helpers -----------------------------------------------------------------

def _strip_code_fences(text: str) -> str:
    """Remove ```sql ... ``` markdown wrappers the LLM sometimes adds."""
    text = text.strip()
    fence = re.match(r"^```(?:sql)?\s*(.*?)\s*```$", text, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        return fence.group(1).strip()
    return text


# --- nodes -------------------------------------------------------------------

def classify_intent(state: AgentState) -> AgentState:
    llm = get_llm()
    raw = llm.invoke(_CLASSIFY_PROMPT.format(question=state["question"]))
    label = str(raw.content).strip().lower()

    if "sql" in label:
        intent = "sql_question"
    elif "chitchat" in label:
        intent = "chitchat"
    else:
        intent = "unsupported"
    return {"intent": intent}


def fetch_schema(state: AgentState) -> AgentState:
    schema = get_schema_info()
    return {"schema_text": format_schema_for_prompt(schema)}


def generate_sql(state: AgentState) -> AgentState:
    llm = get_llm()
    raw = llm.invoke(
        _GENERATE_SQL_PROMPT.format(
            schema=state["schema_text"],
            question=state["question"],
        )
    )
    sql = _strip_code_fences(str(raw.content))
    return {"sql": sql}


def validate_sql(state: AgentState) -> AgentState:
    try:
        cleaned = validate_select_only(state["sql"])
    except SqlValidationError as exc:
        return {"is_valid_sql": False, "validation_error": str(exc)}
    return {"is_valid_sql": True, "sql": cleaned, "validation_error": ""}


def execute_sql(state: AgentState) -> AgentState:
    try:
        result = run_select(state["sql"])
    except SQLAlchemyError as exc:
        # Keep the raw Postgres message; the self-correction loop (Day 8)
        # feeds it back to the LLM to repair the query.
        return {"execution_error": str(exc.orig) if exc.orig else str(exc)}
    return {
        "columns": result["columns"],
        "rows": result["rows"],
        "row_count": result["row_count"],
        "execution_error": "",
    }
