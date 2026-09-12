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

## Next executor gate: bridge only because evidence requires it

Because B.AI free Chat Completions is proven live while free Responses is proven unsupported, a protocol bridge is now justified.

Smallest next path:

```text
Codex -> EchoBird local Responses-to-Chat bridge -> B.AI /chat/completions -> MiMo-V2.5
```

`hy3` remains a backup free B.AI model. New API is still not required.

The bridge is not accepted merely because text generation works. The executor acceptance task must exercise a complete tool loop:

1. receive prompt;
2. read a file;
3. edit a file;
4. run one narrow command/test;
5. consume the tool result;
6. finish successfully.

If EchoBird cannot preserve this tool loop with the chosen B.AI free model, record that incompatibility and change route rather than building more infrastructure around it.

Only after one real executor tool loop succeeds should P2P consider New API for automatic failover/quota routing.

## Acceptance for FREE MODEL POOL 01

- At least 2/3 providers Chat-live-probe successfully at test time.
- At least one live-proven provider completes a full executor tool-loop task.
- Direct Responses is preferred when a free model actually supports it; B.AI free does not, based on live evidence.
- A bridge is introduced only for a provider already proven useful; B.AI now satisfies that trigger.
- Provider switching requires no P2P project-code change.
- Any claim of "free" is tied to provider/account state observed at test time.

## OE Gate

**Không bị over engineering chứ?**

1. Simpler path: direct Responses was tested first and failed terminally; a bridge is now the simplest remaining Codex path for proven-free B.AI.
2. Material progress: yes — the bridge test will determine whether free B.AI can perform real Codex tool work, not just chat.
3. Necessity: Codex speaks Responses while the proven-free B.AI models accept Chat Completions only.
4. Core before support: yes — one local compatibility bridge, no gateway/router stack.
5. Smaller verifiable slice: one model, one bridge, one disposable tool-loop task.

Verdict: `DO_IT` for one EchoBird + B.AI + Codex tool-loop test; `DEFER_UNTIL_NEEDED` for New API/router/dashboard infrastructure.
