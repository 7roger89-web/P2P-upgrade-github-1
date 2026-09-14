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
- `mimo-v2.5` via Chat Completions: PASS (`P2P_PROBE_OK`);
- `hy3` via Chat Completions: PASS (`P2P_PROBE_OK`);
- focused probe tests after Responses support was added: 8/8 PASS;
- `mimo-v2.5` via `/responses`: FAIL, provider says model is not supported on `/v1/responses` and instructs use of `/v1/chat/completions`;
- `hy3` via `/responses`: same terminal endpoint incompatibility;
- `qwen3.8-flash` via `/responses`: same terminal endpoint incompatibility.

Terminal direct-free verdict:

```text
BAI_FREE_CHAT = PASS
BAI_FREE_RESPONSES = FAIL
BAI_FREE_CODEX_DIRECT = NOT_SUPPORTED
```

This is a valid terminal result for the direct B.AI free path. Do not continue trying more B.AI free models merely to manufacture a PASS.

## Protocol distinction

A successful `/chat/completions` call does **not** prove Codex compatibility.

The probe separates:

```text
CHAT_PASS       = provider/model works through /chat/completions
RESPONSES_PASS  = provider/model works through /responses
```

B.AI publishes `/responses` for Codex/agent use, but the free B.AI candidates tested here are explicitly rejected by that endpoint. Therefore direct Codex use is not the path for the proven-free B.AI models.

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

## Probe commands

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

## Executor bridge — PASSED; Provider #1 ACCEPTED (2026-09-12)

Because B.AI free Chat Completions is proven live while free Responses is proven unsupported, one protocol bridge was tested and passed:

```text
Codex -> EchoBird local Responses-to-Chat bridge -> B.AI /chat/completions -> MiMo-V2.5
```

Live evidence (Owner Windows session, 2026-09-12):

- Codex CLI pointed at the local EchoBird bridge (`127.0.0.1:53682/v1`), upstream B.AI `mimo-v2.5`;
- full tool loop verified: read `README.md` -> created `echobird_probe.py` -> executed it through tool calls -> recovered from shell-quoting errors without user intervention -> exact output `P2P_ECHOBIRD_OK` -> appended the exact line `EchoBird B.AI tool loop PASS` to `README.md`.

Verdict:

```text
ECHOBIRD_BAI_MIMO_BRIDGE = PASS
P2P_FREE_MODEL_POOL_PROVIDER_1 = ACCEPTED
```

`hy3` remains a backup free B.AI model. EchoBird remains a test bridge for this bounded evidence only — it is not accepted as general P2P infrastructure. No gateway adoption; no New API.

## Acceptance — two distinct bars

### Bar 1: probe capability (this slice) — MET

This PR's bounded deliverable is a minimal, credential-safe provider probe that keeps protocol verdicts honest:

- keys read only from environment variables, never printed or committed;
- Chat Completions and Responses probed separately (`CHAT_PASS` / `RESPONSES_PASS`), so a chat-only success is never mistaken for Codex/Responses compatibility;
- missing credentials yield explicit `MISSING_KEY` BLOCKED states, never invented failures;
- provider switching requires no P2P project-code change.

Evidence: focused tests 8/8 PASS; B.AI live Provider #1 accepted; EchoBird + B.AI + Codex real tool loop PASS.

```text
PROBE_CAPABILITY = READY
```

### Bar 2: multi-provider pool outcome (workstream) — NOT YET MET, DEFERRED

```text
PROVIDER_1_BAI_ECHOBIRD  = ACCEPTED
BAI_DIRECT_RESPONSES     = NOT_SUPPORTED (terminal)
PROVIDER_2_AMD           = BLOCKED_MISSING_KEY (not rejected)
PROVIDER_2_CLINE         = BLOCKED_MISSING_KEY (not rejected)
SECOND_PROVIDER          = NOT_YET_PROVEN
SECOND_PROVIDER_REQUIRED_FOR_PROBE_CAPABILITY = NO
SECOND_PROVIDER_DEFERRED_UNTIL_CREDENTIAL_AVAILABLE = YES
MULTI_PROVIDER_REDUNDANCY = NOT_YET_PROVEN
```

The full FREE MODEL POOL 01 workstream outcome still requires at least 2/3 providers chat-live-proven at test time, in addition to the already-proven provider tool loop. Provider #1 satisfies the tool-loop half; the second-provider half is blocked only on a credential (`RADEON_API_KEY` for AMD or `CLINE_API_KEY` for Cline) and is deferred — not dropped — until one is available in an executor environment. Do not retest B.AI (terminal result). Do not retry AMD/Cline without credentials. Do not invent Provider #3.

Merging this probe does not claim a resilient multi-provider pool. No auto-failover, no router, no gateway adoption; New API remains `DEFERRED_UNTIL_NEEDED` and may be considered only after a second provider is proven live and a real executor task needs it.

## OE Gate

**Không bị over engineering chứ?**

1. Simpler path: direct Responses was tested first and failed terminally; the bridge was the simplest remaining Codex path for proven-free B.AI.
2. Material progress: yes — the bridge test proved free B.AI can perform real Codex tool work, not just chat (tool loop PASSED 2026-09-12).
3. Necessity: Codex speaks Responses while the proven-free B.AI models accept Chat Completions only.
4. Core before support: yes — one local compatibility bridge, no gateway/router stack.
5. Smaller verifiable slice: one model, one bridge, one disposable tool-loop task (executed 2026-09-12).

Verdict: the one EchoBird + B.AI + Codex tool-loop test is DONE and PASSED (Provider #1 accepted). `DEFER_UNTIL_NEEDED` for New API/router/dashboard/failover infrastructure; second-provider testing resumes only when a credential becomes available.
