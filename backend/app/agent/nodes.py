"""LangGraph node functions for the T2SQL agent.

Each node takes the current AgentState and returns a partial dict of the
keys it updates. Day 5 covers: classify_intent, fetch_schema, generate_sql,
validate_sql. execute_sql / self_correct / summarize arrive in later days.
"""
import json
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

_SELF_CORRECT_PROMPT = """The SQL you wrote failed when run on PostgreSQL.
Fix it. Return ONLY the corrected SQL query — no explanation, no markdown fences.

Database schema (table(column type, ...)):
{schema}

Original question: {question}

Failed SQL:
{sql}

PostgreSQL error:
{error}

Corrected SQL:"""

# v1 language policy (PRD 9.3): the product always answers in English,
# even when the user asked in another language.
_SUMMARIZE_PROMPT = """Answer the user's question in clear, concise English,
based only on the query result below. State the key numbers. Do not invent data.
If the result is empty, say no matching data was found.

Question: {question}

Query result (first rows, JSON):
{result}

Answer:"""

_EXPLAIN_SQL_PROMPT = """Explain the following SQL query to a learner in 2-4 short
sentences of English. Cover what it selects, the joins, and any aggregation.
Be concrete but brief.

SQL:
{sql}

Explanation:"""

_CHITCHAT_PROMPT = """You are T2SQL, an assistant that answers questions about a
Brazilian e-commerce database. Reply briefly in English. If the user is just
greeting or chatting, respond warmly and invite them to ask a data question.

User: {question}

Reply:"""


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
        # Keep the raw Postgres message; the self-correction loop
        # feeds it back to the LLM to repair the query.
        return {"execution_error": str(exc.orig) if exc.orig else str(exc)}
    return {
        "columns": result["columns"],
        "rows": result["rows"],
        "row_count": result["row_count"],
        "execution_error": "",
    }


def self_correct(state: AgentState) -> AgentState:
    """Feed the Postgres error + failed SQL + schema back to the LLM.

    Returns a repaired SQL and bumps the attempt counter. The graph loops
    self_correct -> execute_sql until it succeeds or hits the retry cap.
    """
    llm = get_llm()
    raw = llm.invoke(
        _SELF_CORRECT_PROMPT.format(
            schema=state["schema_text"],
            question=state["question"],
            sql=state["sql"],
            error=state["execution_error"],
        )
    )
    fixed_sql = _strip_code_fences(str(raw.content))
    attempts = state.get("correction_attempts", 0) + 1
    return {"sql": fixed_sql, "correction_attempts": attempts}


# How many result rows to hand the LLM for summarization — enough to describe
# the answer without blowing up the prompt on large result sets.
_SUMMARY_ROW_SAMPLE = 50


def summarize(state: AgentState) -> AgentState:
    """The single exit node: turn whatever happened into an English answer.

    Three cases: non-SQL chitchat, a query that failed all retries (graceful
    fail), and a successful result (answer + learner-facing SQL explanation).
    """
    llm = get_llm()

    # Case 1: not a data question — just reply.
    if state.get("intent") != "sql_question":
        raw = llm.invoke(_CHITCHAT_PROMPT.format(question=state["question"]))
        return {"answer": str(raw.content).strip()}

    # Case 2: SQL question that never produced a result.
    if state.get("execution_error") or not state.get("is_valid_sql", False):
        return {
            "answer": (
                "I couldn't answer that from the database. "
                "Try rephrasing your question."
            ),
            "error": state.get("execution_error") or state.get("validation_error", ""),
        }

    # Case 3: success — summarize the data and explain the SQL.
    sample = state.get("rows", [])[:_SUMMARY_ROW_SAMPLE]
    result_json = json.dumps(sample, default=str, ensure_ascii=False)

    answer_raw = llm.invoke(
        _SUMMARIZE_PROMPT.format(question=state["question"], result=result_json)
    )
    explain_raw = llm.invoke(_EXPLAIN_SQL_PROMPT.format(sql=state["sql"]))

    return {
        "answer": str(answer_raw.content).strip(),
        "sql_explanation": str(explain_raw.content).strip(),
    }
