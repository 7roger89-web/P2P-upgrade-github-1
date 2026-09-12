# P2P FREE MODEL POOL 01

Status: `EXPERIMENTAL_BOUNDED_SLICE`

## Goal

Prove that P2P can use disposable/free OpenAI-compatible model providers as opportunistic compute without changing P2P project code and without committing credentials.

This slice deliberately does **not** add New API, automatic routing, dashboards, provider registries, or a new P2P service. Those remain `DEFERRED_UNTIL_NEEDED` until at least two providers are proven live and one real executor task succeeds.

## Providers in v0

The probe currently knows three candidates:

- `cline` — Cline API; default free candidate `minimax/minimax-m2.5`.
- `bai` — B.AI; allowlisted candidates `glm-5.3-flash`, `mimo-v2.5`, `hy3`.
- `amd` — AMD Radeon Cloud Public Free Model API; allowlisted candidates `DeepSeek-V4-Flash`, `DeepSeek-V4-Flash-Vision-Exp`.

Free/promotional catalogs can change. The script therefore treats these as an allowlist for the experiment, not as a permanent guarantee of price or availability.

## Credential setup on Windows PowerShell

Set credentials only in the current shell/session or your secret manager. Do not paste them into GitHub files, issues, PR comments, screenshots, or chat logs.

```powershell
$env:CLINE_API_KEY="..."
$env:BAI_API_KEY="..."
$env:RADEON_API_KEY="..."
```

Optional model override:

```powershell
$env:CLINE_MODEL="minimax/minimax-m2.5"
$env:BAI_MODEL="glm-5.3-flash"
$env:RADEON_MODEL="DeepSeek-V4-Flash"
```

## Readiness probe

This mode does not send a chat completion. For providers supporting model discovery it authenticates, lists models, and selects only an allowlisted candidate. Cline currently skips discovery and uses the configured/documented candidate.

```powershell
python scripts/free_model_probe.py
```

Default acceptance is at least two providers in `READY` state.

## Tiny live probe

After checking each provider's dashboard/pricing page still shows the selected model as free/0-credit for your account, run one tiny completion:

```powershell
python scripts/free_model_probe.py --live
```

Default acceptance is at least two providers returning `PASS`.

The probe never prints API keys. It prints one JSON line per provider plus a final verdict.

## Real executor acceptance

A text response alone does not prove Codex compatibility. Current Codex custom providers use the Responses protocol while many free providers expose Chat Completions. EchoBird can serve as the local protocol bridge/model switcher.

After at least two live provider probes pass, the next bounded slice is:

```text
Codex -> EchoBird local bridge -> one proven free provider -> one tiny disposable repo task
```

The task must exercise a complete tool loop:

1. receive prompt;
2. read a file;
3. edit a file;
4. run one narrow command/test;
5. consume the tool result;
6. finish successfully.

Only after that succeeds should P2P consider New API for automatic failover/quota routing.

## Acceptance for FREE MODEL POOL 01

- At least 2/3 providers live-probe successfully at test time.
- No API key is committed to Git.
- At least one provider later completes the full Codex/EchoBird tool-loop task.
- Provider switching requires no P2P project-code change.
- Any claim of "free" is tied to the provider/account state observed at test time, never treated as permanent infrastructure.

## OE Gate

**Không bị over engineering chứ?**

1. Simpler path: yes — three providers plus one probe, no gateway yet.
2. Material progress: yes — proves usable external compute rather than architecture diagrams.
3. Necessity: live probe and real executor loop are required evidence; dashboards and smart routing are not.
4. Core before support: yes — prove execution capability first.
5. Smaller verifiable slice: this is already smaller than deploying New API or onboarding 10+ providers.

Verdict: `DO_IT` for the probe; `DEFER_UNTIL_NEEDED` for New API/router/dashboard infrastructure.
