# C38 Stage A — Auth Preflight Evidence

**Generated:** 2026-08-18 (C38 session, read-only preflight)
**Rule honored:** No secret values read, printed, persisted, or committed. Only presence/absence and auth responses reported.

## Method

Environment probe for presence-only (variable names checked, values never displayed); binary availability; connector configuration inspection; a no-credential API reachability check against api.manus.ai/v2 (no key sent).

## Per-backend findings

| Backend | Binary installed | Credential present in this session | Auth response observed | Classification |
| --- | --- | --- | --- | --- |
| **Manus** | n/a (API) | `MANUS_API_KEY` / `MANUS_*` env vars: absent; no Manus API connector in session config; only the read-only GitHub connector exists (P2P GitHub API) | `GET https://api.manus.ai/v2/task.list` with NO key → HTTP 401 (expected, no auth attempted) | **AUTH_ABSENT** (no usable credential available to this session) |
| **Codex / OpenAI** | `codex` binary: not found | Only `OPENAI_API_KEY` present — this is the Manus proxy credential (per durable C27/C31 evidence it is rejected by the Responses API: HTTP 401 pre-model-contact) | Not tested live this session (historical evidence binding: C31 live probe + C27) | **AUTH_INVALID** (historical, durable) / binary ABSENT in this sandbox |
| **Hermes** | `hermes` binary: not found | No Hermes credential env var present | Historical evidence binding (C34/C31): installed v0.20.2 elsewhere but never authenticated | **AUTH_ABSENT** (binary + credentials absent) |
| **Anthropic / Gemini** | absent | absent | — | **AUTH_ABSENT** |

## Auth path correction (2026-08-18, Owner review)

The initial report's instruction to "enable the Manus API connector in Settings → Connectors" was **incorrect**. Connectors are external services that a Manus API task calls out to (with a connector ID passed to `task.create`); they are NOT an authentication mechanism for P2P to call the Manus API itself. The correct path, per current official Manus API v2 documentation, is: **Manus webapp → API Integration settings → Create API Key** (key shown once; store securely in environment variable / secrets manager; never hard-code, never paste into chat). API v2 is the current version (v1 deprecated); `task.create` accepts `x-manus-api-key` or OAuth2 bearer. Suggested key name: `p2p-c38-live-certification`. If no secure secret input is visible in the Owner's Manus UI, the Owner should screenshot the visible API Integration/Settings page and send it (no key in the screenshot) before attempting anything.

## Conclusion

No currently usable live backend credential exists in this session. Current states are **AUTH_ABSENT** for all candidate backends; Codex carries durable **AUTH_INVALID** historical evidence in addition to the missing binary. Per C38 §5 and §29, the correct terminal action is:

> **STOP — BLOCKED / OWNER_AUTH_REQUIRED**

No branch, runtime, or implementation activity was created to wait for auth. Only the minimum safe preflight evidence (this file, plus the operating digest and task graph) was persisted under `docs/p2p-development/research/c38/`.
