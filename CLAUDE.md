# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Agentic Text-to-SQL analytics & forecasting platform on the Olist dataset. Full requirements in `prd.md`, day-by-day roadmap in `plan.md`, SQL learning notes in `docs/sql-notes.md`.

## Working style (project-specific)
- **Chat with the user (Serdar) in Turkish.**
- This is a **learning project**: when SQL is generated or used, **explain the SQL** to the user in a teaching manner. New SQL concepts get recorded in `docs/sql-notes.md`.
- Two end goals drive decisions: (1) SQL skill at the level an AI engineer needs, (2) strong deployment skills — treat the DevOps phase as substantial, not an afterthought.

## Product language policy
- **v1: all UI text and the agent's summary output are English** (PRD §9.3), even when the user asks the question in Turkish. Multi-language support is deferred to v2.

## Commands
Backend lives in `backend/` with a project-local virtualenv at `backend/.venv` (Python 3.10).

```bash
# Activate venv (Git Bash)         # or PowerShell: backend\.venv\Scripts\Activate.ps1
source backend/.venv/Scripts/activate

# Install / update dependencies
pip install -r backend/requirements.txt

# Run the API (from backend/ so `app.main` resolves)
cd backend && uvicorn app.main:app --reload      # http://127.0.0.1:8000 , health: /api/health

# Tests (all / single)
cd backend && pytest
cd backend && pytest tests/test_file.py::test_name

# Lint
cd backend && ruff check .
```

Docker / Postgres, CI/CD, and the Next.js frontend do not exist yet — they arrive in later phases (see roadmap). The frontend will be a separate Next.js app under `frontend/`.

## Architecture (target design — being built incrementally)
The system is a **provider-agnostic LLM agent** wrapping PostgreSQL:

- **Backend** (`backend/app/`, FastAPI): exposes `/api/chat` (SSE streaming), `/api/schema`, `/api/health`.
  - `agent/` — a **LangGraph state machine** is the core. Flow: `classify_intent → fetch_schema → generate_sql → validate_sql → execute_sql`, with a **self-correction loop** (on a Postgres error, feed the error + SQL + schema back to the LLM, retry up to `MAX_SELF_CORRECT_RETRIES=3`, then graceful fail) → `decide_forecast → forecast → decide_visualization → summarize`. State is a single `AgentState` TypedDict threaded through nodes.
  - `db/` — SQLAlchemy/psycopg connection + schema introspection.
  - LLM via `langchain-google-genai` (Gemini), behind an abstraction so OpenAI/Anthropic can swap in via `.env`.
- **Data**: Olist (Brazilian e-commerce) in PostgreSQL 16. **Revenue is not a column** — it is `SUM(olist_order_items.price)` joined to `olist_orders.order_purchase_timestamp` via `order_id`. This JOIN is the most-used query pattern.
- **ML** (`models/`): a **pretrained** LSTM for revenue time-series forecasting. Trained offline; at runtime the `forecast` node pulls a series via SQL, normalizes with a saved scaler, runs inference, denormalizes. No online retraining.
- **Frontend** (`frontend/`, Next.js 14 + React + Tailwind + shadcn/ui + Framer Motion + Plotly.js): generic chat that animates a table/chart panel into view when results are tabular; a collapsible SQL-explanation panel serves the learning goal.

## Security invariants (enforce in the agent)
- **SELECT-only**: statically reject any SQL containing `INSERT/UPDATE/DELETE/DROP/ALTER/TRUNCATE/GRANT` in `validate_sql`.
- App connects to Postgres with a **read-only role** (defense-in-depth) and a statement timeout (`SQL_STATEMENT_TIMEOUT_MS=10000`).
- Secrets (Gemini key, DB URL) live only in `.env` (gitignored); `.env.example` documents the shape.

## Roadmap phases (start Mon 2026-07-20, ~25 days)
| Phase | Days | Topic | Output |
|-------|------|-------|--------|
| 0 — Setup & Data | 1–3 | Repo skeleton, load Olist into Postgres, SQL basics | Populated Olist DB |
| 1 — Agent core | 4–9 | FastAPI + Gemini, LangGraph nodes, self-correction, summarize, window functions | Question → SQL → correct result |
| 2 — Visualization | 10–11 | `viz_spec` generation, `/api/chat` SSE streaming | API returns chart/table specs |
| 3 — Frontend | 12–16 | Next.js chat UI, streaming, stepper, dynamic table (Framer Motion), Plotly, SQL panel | Working professional UI |
| 4 — LSTM | 17–18 | Offline revenue training (PyTorch), inference node, past+forecast chart | Forecasting live |
| 5 — DevOps ⭐ | 19–23 | Multi-stage Docker, full-stack compose, GitHub Actions CI, Railway deploy + CD | Live public URL + CI/CD |
| 6 — Polish | 24–25 | UX polish, rate limiting, README + demo, compile sql-notes | Portfolio-ready |

Current status: **Phase 0**. Commit + short demo at the end of each phase. Critical path: Phase 1 (agent) and Phase 3 (frontend).
