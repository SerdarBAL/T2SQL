# T2SQL — Agentic Text-to-SQL Analytics & Forecasting Platform

Natural-language business questions → **agentic** SQL generation → PostgreSQL execution with
**self-correction** → natural-language answer + **dynamic tables/charts**, plus **LSTM-based
revenue forecasting**. Built on the Brazilian E-Commerce (Olist) dataset.

> Portfolio + learning project. Goals: (1) master SQL to the level an AI engineer needs,
> (2) build strong end-to-end deployment skills.

## Stack
| Layer | Tech |
|-------|------|
| Frontend | Next.js 14, React, TypeScript, Tailwind, shadcn/ui, Framer Motion, Plotly.js |
| Backend | FastAPI, LangGraph, LangChain, SQLAlchemy, psycopg |
| LLM | Gemini API (`langchain-google-genai`), provider-agnostic |
| Database | PostgreSQL 16 (Olist dataset) |
| ML | PyTorch (pretrained LSTM) |
| DevOps | Docker, Docker Compose, GitHub Actions, Railway |

## Documentation
- [`prd.md`](./prd.md) — Product requirements
- [`plan.md`](./plan.md) — Day-by-day roadmap
- [`docs/sql-notes.md`](./docs/sql-notes.md) — SQL learning notes

## Project structure
```
T2SQL/
├── backend/          # FastAPI + LangGraph agent
│   ├── app/
│   │   ├── agent/    # LangGraph nodes & state machine
│   │   └── db/       # DB connection, schema introspection
│   └── tests/
├── frontend/         # Next.js chat UI (scaffolded in Phase 3)
├── models/           # Pretrained LSTM artifacts
├── data/raw/         # Olist CSVs (not committed)
└── docs/
```

## Status
🚧 In development — see `plan.md`. Currently: **Phase 0 (Setup)**.

## Local development
_TBD — added in Phase 5 (Docker Compose)._
