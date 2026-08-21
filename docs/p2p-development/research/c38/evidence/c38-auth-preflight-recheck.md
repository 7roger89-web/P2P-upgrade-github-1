# C38 Stage A Re-check — Manus AUTH VALID (evidence)

**Generated:** 2026-08-18 (C38 session)
**Rule honored:** Secret value never printed, persisted (in git), or committed. Stored only at `/home/ubuntu/.secrets/manus_api_key` (mode 600, outside the repository) and used as a request header. Only HTTP codes and non-secret response bodies are recorded here.

## Result

| Check | Method | Result |
| --- | --- | --- |
| `GET /v2/task.list?limit=1` with `x-manus-api-key` | curl, no secret in output | **HTTP 200**, `ok: true`, `data` contains 1 task (id, status running, agent_profile `manus-1.6`, credit_usage 0), `has_more: true` |
| `POST /v2/task.create` with `x-manus-api-key` | curl, body suppressed | **HTTP 200** (authenticated endpoint accepted) |
| Rate-limit headers | observed on task.list | `x-ratelimit-limit: 200` (healthy quota) |

## Classification

**Manus: AUTH_VALID** (current, live-verified, no model call consumed in this check — list/detail only, task.create accepted but not dispatched).

Historical states unchanged for other backends: Codex AUTH_INVALID (durable C27/C31 evidence, binary absent), Hermes AUTH_ABSENT (binary absent).

## Next governed action (per agreed Stage B entry sequence)

Verify C37 HEAD == 4e5ef54 → create branch `p2p-c38-live-role-certification` → carry Stage-A evidence → secret-scan → commit Stage-A checkpoint → Stage B first live role proof.
