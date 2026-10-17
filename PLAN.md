# MöbiusPilot — Build Plan

Stack: Python 3.13 venv, FastAPI, sqlite3, Streamlit, NetworkX, pydantic, python-dotenv, httpx, pytest. LLM: Groq (OpenAI-compatible).

## Layout
- `app.py` FastAPI (health, inbound webhook if needed, approval API)
- `worker.py` inbound poller + `scheduled_jobs` poller
- `agent/` loop orchestrator, LLM client, prompts
- `tools/` registry with pydantic schemas and A/B/C permission enforcement
- `database/` schema, helpers, DEMO seed
- `messaging/` adapter interface, Google Chat (or approved alternative), SIMULATED adapter for tests
- `memory/` atomic Markdown writer/reader
- `intelligence/` ripple graph and deterministic scoring
- `recovery/` options, approvals, execution, outcome checks, follow-ups
- `dashboard/` Streamlit command center
- `scripts/check_setup.py`, `tests/`

## Phases
0. Setup and feasibility → human gate (credentials)
1. Real outbound + inbound message stored in DB → human gate (real reply)
2. Schema, seed, tool registry, agent loop with validated LLM output
3. Markdown memory + full event loop + idempotency
4. Ripple, scoring, recovery, approvals, outcome checks, follow-ups
5. Dashboard
6. Hardening, full tests, README, DEMO.md

Commit to `feature/mobiuspilot` after each phase. Never push without asking.
