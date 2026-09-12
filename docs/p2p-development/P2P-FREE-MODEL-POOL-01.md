# P2P FREE MODEL POOL 01

Status: `EXPERIMENTAL_BOUNDED_SLICE`

## Goal

Prove that P2P can use disposable/free model providers as opportunistic compute without changing P2P project code and without committing credentials.

This slice deliberately does **not** add New API, automatic routing, dashboards, provider registries, or a new P2P service. Those remain `DEFERRED_UNTIL_NEEDED` until at least two providers are proven live and one real executor task succeeds.

## Providers in v0

The probe currently knows three candidates:

- `cline` — Cline API; default free candidate `minimax/minimax-m2.5`.
- `bai` — B.AI; current free/promotional candidate order `mimo-v2.5`, `hy3`, `qwen3.8-flash`.
- `amd` — AMD Radeon Cloud Public Free Model API; allowlisted candidates `DeepSeek-V4-Flash`, `DeepSeek-V4-Flash-Vision-Exp`.

Free/promotional catalogs can change. The script treats these as an experiment allowlist, not as a permanent guarantee of price or availability.

## B.AI evidence — 2026-09-12

Owner-account live evidence from the v0 probe:

- authentication + `/models` discovery: PASS (`47` models returned);
- `glm-5.3-flash` via Chat Completions: FAIL on insufficient balance;
- `mimo-v2.5` via Chat Completions: `CHAT_PASS` equivalent (`P2P_PROBE_OK`);
- `hy3` via Chat Completions: `CHAT_PASS` equivalent (`P2P_PROBE_OK`).

The probe allowlist was updated after this evidence and current provider documentation: `glm-5.3-flash` is no longer treated as a free candidate; `mimo-v2.5`, `hy3`, and `qwen3.8-flash` are the current free/promotional candidates for this experiment.

## Protocol distinction

A successful `/chat/completions` call does **not** prove Codex compatibility.

The probe now separates:

```text
CHAT_PASS       = provider/model works through /chat/completions
RESPONSES_PASS  = provider/model works through /responses
```

B.AI publishes `/responses` for Codex/agent use, but currently documents that endpoint for supported GPT and DeepSeek model families. The currently free B.AI candidates above are MiMo, Hy3, and Qwen, so direct free Codex compatibility is an open question that must be tested rather than assumed.

## Credential setup on Windows PowerShell

Set credentials in the current shell/session or a secret manager.

```powershell
$env:CLINE_API_KEY="..."
$env:BAI_API_KEY="..."
$env:RADEON_API_KEY="..."
```

Optional model override:

```powershell
$env:CLINE_MODEL="minimax/minimax-m2.5"
$env:BAI_MODEL="mimo-v2.5"
$env:RADEON_MODEL="DeepSeek-V4-Flash"
```

## Readiness probe

Chat readiness:

```powershell
python scripts/free_model_probe.py --providers bai --protocol chat --require 1
```

Responses readiness checks auth/model discovery only. It does not prove endpoint compatibility until `--live` is used:

```powershell
python scripts/free_model_probe.py --providers bai --protocol responses --require 1
```

## Tiny live probes

Chat Completions:

```powershell
python scripts/free_model_probe.py --providers bai --protocol chat --require 1 --live
```

Responses:

```powershell
python scripts/free_model_probe.py --providers bai --protocol responses --require 1 --live
```

The live result is explicit: `CHAT_PASS`, `RESPONSES_PASS`, `CHAT_CALL_FAIL`, or `RESPONSES_CALL_FAIL`.

If no explicit `BAI_MODEL` override is set, HTTP 400 model-specific failures can fall through to the next allowlisted free candidate. Auth and network failures are not blindly retried. If `BAI_MODEL` is set, only that model is tested.

## Direct Codex gate

Only a `RESPONSES_PASS` on a free candidate justifies the next direct path:

```text
Codex -> B.AI Responses API -> one tiny disposable repo task
```

Provider configuration shape:

```toml
model = "<RESPONSES_PASS model>"
model_provider = "bai"

[model_providers.bai]
name = "B.AI"
base_url = "https://api.b.ai/v1"
env_key = "BAI_API_KEY"
wire_api = "responses"
requires_openai_auth = false
```

If all free B.AI candidates return `RESPONSES_CALL_FAIL` because the endpoint rejects those model families, that is a valid terminal result for the direct-B.AI-free path. Do not buy credits merely to manufacture a PASS. Move to another free provider and use a protocol bridge only when a live-proven provider actually requires one.

## Real executor acceptance

The eventual executor task must exercise a complete tool loop:

1. receive prompt;
2. read a file;
3. edit a file;
4. run one narrow command/test;
5. consume the tool result;
6. finish successfully.

Only after that succeeds should P2P consider New API for automatic failover/quota routing.

## Acceptance for FREE MODEL POOL 01

- At least 2/3 providers Chat-live-probe successfully at test time.
- No API key is committed to Git.
- At least one live-proven provider later completes a full executor tool-loop task.
- Direct Responses is preferred when a free model actually supports it; otherwise a bridge is introduced only for a provider already proven useful.
- Provider switching requires no P2P project-code change.
- Any claim of "free" is tied to provider/account state observed at test time.

## OE Gate

**Không bị over engineering chứ?**

1. Simpler path: yes — protocol probe before installing any bridge/gateway.
2. Material progress: yes — distinguishes cheap chat inference from actual Codex transport compatibility.
3. Necessity: without a live Responses test, direct Codex compatibility is an unsupported assumption.
4. Core before support: yes — test the executor transport before adding routing infrastructure.
5. Smaller verifiable slice: one B.AI `/responses` request is smaller than installing EchoBird or New API.

Verdict: `DO_IT` for the Responses probe; `DEFER_UNTIL_NEEDED` for EchoBird/New API/router/dashboard infrastructure.
