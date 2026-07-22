"""Assembles the agent nodes into a LangGraph state machine.

Day 5 scope: classify_intent -> fetch_schema -> generate_sql -> validate_sql.
Non-SQL questions short-circuit to END. execute_sql and the self-correction
loop are wired in on later days.
"""
from langgraph.graph import END, START, StateGraph

from app.agent.nodes import (
    classify_intent,
    execute_sql,
    fetch_schema,
    generate_sql,
    validate_sql,
)
from app.agent.state import AgentState


def _route_after_classify(state: AgentState) -> str:
    """Only real data questions continue into the SQL pipeline."""
    return "fetch_schema" if state.get("intent") == "sql_question" else END


def _route_after_validate(state: AgentState) -> str:
    """Run the query only if it passed the SELECT-only guard.

    Day 8 replaces the invalid branch with the self-correction loop.
    """
    return "execute_sql" if state.get("is_valid_sql") else END


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("classify_intent", classify_intent)
    graph.add_node("fetch_schema", fetch_schema)
    graph.add_node("generate_sql", generate_sql)
    graph.add_node("validate_sql", validate_sql)
    graph.add_node("execute_sql", execute_sql)

    graph.add_edge(START, "classify_intent")
    graph.add_conditional_edges(
        "classify_intent",
        _route_after_classify,
        {"fetch_schema": "fetch_schema", END: END},
    )
    graph.add_edge("fetch_schema", "generate_sql")
    graph.add_edge("generate_sql", "validate_sql")
    graph.add_conditional_edges(
        "validate_sql",
        _route_after_validate,
        {"execute_sql": "execute_sql", END: END},
    )
    graph.add_edge("execute_sql", END)

    return graph.compile()


# Compiled once at import; reused across requests.
agent_graph = build_graph()
