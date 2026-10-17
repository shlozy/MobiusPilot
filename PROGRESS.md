# MöbiusPilot — Progress

## Phase 0 — Setup and feasibility (done, waiting at human gate)
- Branch `feature/mobiuspilot` created. Repo was empty and had no SPEC.md, so SPEC.md was reconstructed from the brief.
- `.gitignore`, `.env.example`, `requirements.txt`, `PLAN.md`, `scripts/check_setup.py` created.
- Python 3.13 `.venv` created and all dependencies import.
- LLM: Groq (`llama-3.3-70b-versatile`) via an OpenAI-compatible API.
- Google Chat feasibility (official docs, Chat Pub/Sub quickstart): needs a **Business/Enterprise Google Workspace** account and a Google Cloud project **with billing enabled**. Pub/Sub *pull* means no public URL or ngrok is needed on Windows.

### Human gate checklist
- [ ] Create a Groq API key at https://console.groq.com/keys
- [ ] CMD: `copy .env.example .env`, then paste the key into `LLM_API_KEY`
- [ ] Check whether you have a Business/Enterprise Workspace account with billing (a personal @gmail.com account is not enough)
- [ ] If not: approve or reject switching to Telegram
- [ ] CMD: `.venv\Scripts\python scripts\check_setup.py` (all lines should say OK)

## Phase 1 — Real messaging proof
Not started.
