"""/api/chat — streams the agent's progress to the client over SSE.

We stream LangGraph node updates (stream_mode="updates") and translate each
one into a typed SSE event the frontend can react to:

  step   -> a node started/finished; drives the UI stepper
  sql    -> the (validated) SQL is ready; show it in the SQL panel
  result -> rows + columns + chart spec are ready; animate the table/chart in
  answer -> the English summary + SQL explanation
  done   -> stream finished
  error  -> something went wrong

Keeping these as discrete events (not one big JSON at the end) is what makes
the UI feel live.
"""
import json

from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.agent.graph import agent_graph

router = APIRouter()

# Human-readable labels for the stepper, keyed by node name.
_STEP_LABELS = {
    "classify_intent": "Understanding your question...",
    "fetch_schema": "Reading the database schema...",
    "generate_sql": "Generating SQL...",
    "validate_sql": "Validating SQL...",
    "execute_sql": "Running query...",
    "self_correct": "Fixing the query...",
    "decide_visualization": "Choosing a chart...",
    "summarize": "Writing the answer...",
}


class ChatRequest(BaseModel):
    question: str


def _sse(event: str, payload: dict) -> dict:
    """Shape a dict for EventSourceResponse: named event + JSON data."""
    return {"event": event, "data": json.dumps(payload, default=str, ensure_ascii=False)}


async def _event_stream(question: str):
    # Each node returns only the keys it changed; accumulate them so events
    # can be built from the full running state.
    state: dict = {}
    try:
        async for update in agent_graph.astream(
            {"question": question}, stream_mode="updates"
        ):
            # update == {node_name: partial_state_it_returned}
            for node_name, node_output in update.items():
                state.update(node_output)

                yield _sse(
                    "step",
                    {"node": node_name, "label": _STEP_LABELS.get(node_name, node_name)},
                )

                if node_name in ("validate_sql", "self_correct") and state.get("sql"):
                    yield _sse("sql", {"sql": state["sql"]})

                if node_name == "decide_visualization":
                    yield _sse(
                        "result",
                        {
                            "columns": state.get("columns"),
                            "rows": state.get("rows"),
                            "viz_spec": state.get("viz_spec"),
                        },
                    )

                if node_name == "summarize":
                    yield _sse(
                        "answer",
                        {
                            "answer": state.get("answer"),
                            "sql_explanation": state.get("sql_explanation"),
                            "error": state.get("error"),
                        },
                    )

        yield _sse("done", {})
    except Exception as exc:  # noqa: BLE001 - surface any failure to the client
        yield _sse("error", {"message": str(exc)})


@router.post("/api/chat")
async def chat(request: ChatRequest) -> EventSourceResponse:
    return EventSourceResponse(_event_stream(request.question))
