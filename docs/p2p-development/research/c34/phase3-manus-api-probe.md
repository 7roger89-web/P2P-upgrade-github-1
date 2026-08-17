# Phase 3 — Manus API Probe (ACTUAL observed/verified contract, 2026-08-17)

## Credentials supplied by user
- Manus API key: redacted to `sk-DvH3…bzbTr` in this document (full key stored only at /home/ubuntu/.secrets/manus_api_key, outside the repository; see c34 notes)
- GitHub PAT: github_pat_11B3CGRWI... (already used for clone)

## Verified interface facts (docs open.manus.ai/v2, observed 2026-08-17)
- Base URL: https://api.manus.ai/v2/
- Auth header: x-manus-api-key (API key) OR Authorization: Bearer (OAuth2). Provide either, not both.
- task.create (POST /v2/task.create, body message.content[{type:text,text}], agent_profile "manus-1.6", optional project_id, title, structured_output_schema). Success: {"ok":true,"request_id","task_id","task_title","task_url","share_url"}. Error: {"ok":false,"error":{"code","message"}}.
- task.detail (GET /v2/task.detail?task_id=) → {"ok":true,"task":{"id","status","created_at","updated_at","title","credit_usage","task_url","created_by_api_key"}}. Status values: running/stopped/waiting/error. credit_usage = USAGE_EVIDENCE (credits).
- task.listMessages (GET /v2/task.listMessages?task_id=&order=&limit=&verbose=) → events: user_message, assistant_message, error_message, status_update (agent_status running/stopped/waiting/error), tool_used, plan_update, structured_output_result. verbose=true adds tool_used/plan_update/explanation. has_more/next_cursor pagination.
- Task lifecycle: running → poll listMessages; stopped → read results; waiting → confirmAction/sendMessage; error → error_message.
- Shortcut task_id: agent-default-main_task for IM main task.
- Input limit ~5000 tokens; InvalidArgument HTTP 400.
- task.sendMessage for follow-ups; task.stop (cancel/interrupt) expected to exist (see lifecycle guide).

## LIVE probe results (2026-08-17, real credentials)
- task.list with key → HTTP 200 ok, lists existing tasks (task p2p-4, running) → AUTH VALID.
- task.create with tiny prompt → ok, task_id REdjijwRAK5zJyxBfzsmFi, agent_profile manus-1.6-lite accepted.
- task.detail after ~90s → status stopped, credit_usage 0, created_by_api_key id/name LOG.
- task.listMessages (order=asc) → events: user_message, status_update(agent_status running/stopped), assistant_message content "4" (correct answer). Note: agent_status sits in status_update.status_detail.agent_status field.
- Manus API = provider AUTH VALID + LIVE_EXECUTION_PROVEN (real bounded run completed). Classification path: ADAPTER_IMPLEMENTED + LIVE_VALIDATED possible.

## Plan for real probe
1. curl task.create with a tiny prompt → assert task created, record task_id.
2. Poll task.detail until stopped → record status/credit_usage.
3. Fetch listMessages (verbose=false + once verbose=true) → evidence pointers; transcript pointer = task_url.
4. Expected classification: provider AUTH VALID (key supplied by user) → ADAPTER_IMPLEMENTED; LIVE_VALIDATED requires a real run — one real bounded run with tiny prompt counts as LIVE_EXECUTION_PROVEN.

## Live adapter probe via ManusAdapter.execute (2026-08-17)
- identity(): adapter_state ADAPTER_IMPLEMENTED, harness manus-1.6, provider manus-cloud, model manus-1.6-lite (observed from account task list).
- health(): VALID, AVAILABLE.
- execute() real run: task_id 8Eqa4QGo4x35raVTPnnA7c, stopped in ~11s, execution_status SUCCEEDED, exit_status stopped, artifact_pointers [manus-task:..., manus-messages:...], usage_evidence credit_usage 0, auth_state_after VALID, possible_mutation false, raw receipt pointer present.
- Answer "Four" preserved in evidence file c34-notes/evidence/manus-probe/c34-manus-probe-messages.json (answer extraction works).
- Evidence files: create/detail/messages JSON persisted under evidence dir (immutable pointers, raw receipt).
- Classification: ADAPTER_IMPLEMENTED + LIVE_VALIDATED (real bounded run through adapter).
