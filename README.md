# Kurukshetra 2026 Backend

This repository contains the local FastAPI backend for the Kurukshetra 2026 planning and operations platform. It includes authentication, organization/project management, task assignment, messaging simulation, AI planning fallback logic, and a seeded SQLite database for local development.

## Stack

- Python 3.13+
- FastAPI
- SQLAlchemy 2.x
- SQLite
- Pydantic v2
- JWT authentication
- bcrypt password hashing
- httpx for outbound LLM calls
- pytest for backend flow verification

## Local setup

1. Create a virtual environment if needed.
2. Copy `.env.example` to `.env` and fill in the required values.
3. Install dependencies:

   ```bash
   .venv\Scripts\python -m pip install -r requirements.txt
   ```

4. Run the app:

   ```bash
   .venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

5. Open the docs at `http://localhost:8000/docs`.

## Environment variables

The backend reads values from `.env` using pydantic-settings. The key variables are:

- `APP_ENV`
- `DATABASE_URL`
- `JWT_SECRET`
- `LLM_BASE_URL`
- `LLM_API_KEY`
- `LLM_MODEL`
- `MESSAGING_PLATFORM`

For local work, `MESSAGING_PLATFORM=simulator` is the default and keeps the messaging layer testable without external credentials.

## Core API behavior

- Auth: register, login, logout, token refresh, profile lookup
- Organizations: create and inspect organization membership
- Projects: create projects and add project members
- Tasks: create, update, assign, and list tasks with project-scoped access checks
- Messages: dispatch and simulate replies for project tasks
- AI: plan generation and fallback deterministic task creation when provider output is unusable
- Activity: list audit events for project tasks

## Validation

Run the backend flow suite:

```bash
.venv\Scripts\python -m pytest tests/test_core_flow.py -q
```

The current backend suite passes with the configured local SQLite database and simulator messaging mode.

## Notes

- The database is created automatically on startup.
- Seed data is skipped in test mode so IDs remain stable for deterministic API tests.
- LLM failures are handled gracefully and fall back to a safe plan rather than breaking the request flow.
