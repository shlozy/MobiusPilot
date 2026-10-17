# MöbiusPilot — Specification

> Note: No original SPEC.md existed in this repo. This spec was reconstructed from the project brief.
> Sections marked **(reconstructed)** were written by the build agent and should be reviewed by the team.

## 1. Goal
MöbiusPilot is a bounded autonomous project-recovery agent. It talks to teammates over a real chat platform, notices blockers, computes their ripple impact across the dependency graph, proposes recovery actions, waits for human approval when needed, executes approved actions, and checks whether they worked.

## 2. Agent loop
OBSERVE → REASON → PLAN → ACT → EVALUATE → REPLAN or FINISH.
- `MAX_ITERATIONS` (default 6), per-step timeouts, duplicate-event protection, safe stop conditions.
- Every run, plan, step and tool call is stored in the DB.
- The LLM only selects a tool and its arguments. Deterministic code validates arguments and enforces permissions before anything runs.

## 3. Bounded autonomy
| Class | Examples | Rule |
|---|---|---|
| A | read, analyze, classify, record validated reports, audit, recalculate risk, draft plans | automatic |
| B | update to *reported* status, send an expected check-in, ask for clarification, permitted follow-up | automatic, with rate limits, dedupe, cooldowns and an audit log |
| C | reassign, change deadlines/priorities, create/delete consequential tasks, escalate to management, unusual/sensitive messages | needs an approved `approvals` record in the DB, enforced server-side |

## 4. Truthfulness
- "Finished" → `reported_complete`, never `verified`. `verified` only when code checked evidence.
- Low confidence or ambiguity → ask a clarifying question and change nothing.
- Never fabricate replies, evidence or success. Any simulator is labelled **SIMULATED** in UI, logs and Markdown.

## 5. Tools
get_task, get_project_context, get_task_dependencies, analyze_ripple_impact, record_progress_update, append_activity_log, draft_message, send_chat_message, propose_recovery_action, request_human_approval, check_action_outcome.

## 6. Data (SQLite, authoritative)
projects, users, tasks, dependencies, messages/events (unique event id, processed flag), agent_runs, agent_steps, tool_calls, recovery_actions, approvals, progress_reports (verification state), scheduled_jobs, audit_log.

Recovery lifecycle: detected → analyzed → proposed → approved/rejected → executed → outcome_checked → resolved/escalated.

## 7. Markdown memory
TEAM_PROGRESS.md, PROJECT_CONTEXT.md, ACTIVITY_LOG.md. Generated only from DB state and real events. Written atomically under a lock. The agent reads relevant memory before each decision.

## 8. Ripple Intelligence
NetworkX graph: immediate blocker, root blocker, downstream chain, affected owners/milestones/deadlines, confirmed impact vs estimated risk, deterministic explainable priority score, cycle detection. No LLM for graph or math; the LLM only explains the computed output.

## 9. Messaging
Adapter interface (send, receive/verify, dedupe). Primary: Google Chat. Inbound events must be authenticated. Any replacement platform requires team approval.

## 10. Follow-up
DB-backed `scheduled_jobs` polled by a worker thread. Restart-safe, no in-memory timers.

## 11. Dashboard
Streamlit, reads only real DB state: health, tasks, workload, blocked/overdue, dependency graph with ripple chain, root-blocker explanation, agent objective/plan, tool-call timeline, recovery options, approval queue (Approve/Reject/Modify), follow-up status, reported vs verified badges, System status (real vs simulated).

## 12. Demo script (reconstructed)
1. (0:00) Dashboard: demo project healthy, System status shows real integrations.
2. (0:30) Agent sends a real check-in to the owner of "API approval".
3. (1:00) Teammate replies with a real blocker from their phone.
4. (1:30) Agent run: plan and tool calls appear; task becomes blocked; Markdown updates.
5. (2:15) Ripple chain highlights Checkout integration → Mobile payment testing → Final release, with affected owners and the deadline at risk.
6. (3:00) Class C recovery proposal waits in the approval queue; the presenter approves it.
7. (3:30) Action executes; outcome check runs; follow-up is scheduled.
8. (4:15) Follow-up fires; the next real reply resolves or escalates the blocker.
9. (4:45) Full event-to-outcome history on screen.

## 13. Test scenarios (reconstructed)
1. Blocker reply → task blocked, ripple computed, Markdown updated.
2. "Done" reply → `reported_complete`, not `verified`.
3. Ambiguous reply → clarification sent, no state change.
4. Same event twice → state changes once.
5. Class C tool without approval → refused.
6. Approved action → executes and outcome is checked.
7. Action did not resolve the blocker → escalated/replanned.
8. Malformed LLM JSON → retry, then safe stop.
9. MAX_ITERATIONS reached → safe stop recorded.
10. Dependency cycle detected and reported.
11. Scheduled job survives restart and fires exactly once.
12. Class B rate limit / cooldown enforced.
13. LLM timeout → no fabricated result.
14. Unauthenticated inbound event rejected.

## 14. Security
Secrets only in `.env` (git-ignored). Credentials JSON git-ignored. Inbound authentication and an allowlist of known users. No destructive actions without approval.
