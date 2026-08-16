# Supervisor Report: P2P-C09 host-layer investigation

Verdict: REJECT

## Metadata

- Report file: `D:\AI\P2P_dev\P2P-8.4.6-C-Codex-Edition-v4\reports\supervisor\rp_supervisor_260814_173752_by_gpt-5-codex_p2p-c09-host-layer-investigation.md`
- Review time: 2026-08-14 17:37:52 Asia/Saigon
- Reviewer: `gpt-5-codex`
- Repo/project: `P2P-8.4.6-C-Codex-Edition-v4`
- Scope reviewed: C09 investigation of the historical Aesthetica receipts versus the fresh default worker
- Claim reviewed: identify the earliest proven failure layer across host event emission, matcher evaluation, hook execution, and receipt writing; classify P2P source defect, host limitation, and owner action without asking the owner to discover unsupported diagnostics
- Authority used: current user investigation brief, repository `AGENTS.md`, current source/config, Execution Ledger, current app-server SQLite log, native thread metadata, and existing C09 evidence
- Related artifacts: fresh default worker `019fffc5-89e8-7f82-b30a-ed376b15ea7e`, prior C09 reports, C09 plan/evidence/status files

## Executive Summary

- The known-good control is real but historical: the Execution Ledger has 18 valid `p2p_aesthetica` receipts, all `SubagentStart`, all `source=codex_official_hook`, and all for the exact project cwd.
- All 18 Aesthetica receipts predate the current C09 config and hook-source update at 2026-08-14 14:07:21 Asia/Saigon. They prove that the older Aesthetica path reached the official hook and writer; they do not prove that the current broadened matcher is active for `default`.
- The fresh default worker has current host-backed thread/turn execution metadata and completed read-only work, but it has no matching official receipt.
- `C:\Users\Admin\.codex\logs_2.sqlite` is a supported local app-server log source. It contains historical `codex_core::hook_runtime` warnings, but PID 4288 has zero `hook_runtime` records and no fresh host-owned event, matcher, handler, or writer outcome for the default worker.
- Earliest proven failure layer: none. Earliest unobservable boundary: `HOST EVENT EMISSION`.
- Classification: `EVENT_EVIDENCE_UNAVAILABLE`. This is not evidence of `EVENT_NOT_EMITTED`, a matcher defect, a handler failure, or a P2P source defect.
- Owner action: `NO`. No concrete supported Codex Desktop action was found that the owner can perform to close this boundary, so no generic diagnostic request is issued.

## Blocking Findings

### [P0] The current host does not expose enough evidence to classify the first failing layer

File: `C:\Users\Admin\.codex\logs_2.sqlite` and `D:\AI\P2P_dev\P2P-8.4.6-C-Codex-Edition-v4\.p2p\state\execution-ledger.jsonl`

Issue: the default worker completed, but the host-owned evidence boundary contains no fresh `SubagentStart` event record, matcher decision, hook-process invocation, exit result, or receipt-write attempt. Ledger absence is therefore an observation of missing proof, not proof that a particular layer failed.

Evidence:

- Current default thread metadata identifies execution `019fffc5-89e8-7f82-b30a-ed376b15ea7e`, turn `019fffc5-8ade-7022-9a6a-2e6f78b0a749`, model `gpt-5.6-luna`, exact project cwd, and completed/idle status.
- The current app-server process is PID 4288. Its process-scoped logs contain zero `codex_core::hook_runtime` rows.
- The only ten hook-runtime rows in the inspected SQLite database are historical warnings from other threads: legacy `after_agent` failures and two stop-hook parent-transcript resolution warnings. None is a fresh `SubagentStart` result for the default worker.
- The Execution Ledger contains 18 valid host receipts, with counts `p2p_aesthetica=18`, `default=0`, and `p2p_iris=0`.
- The current source/config boundary allows `default`, but source/config presence cannot prove that the active host emitted or matched the event.

Why this blocks acceptance: the C09 invariant requires host-owned identity proof. Worker completion, requested `agent_type`, thread title, and worker prose cannot substitute for the missing official receipt.

Fix direction: preserve the current fail-closed boundary. Do not patch the hook or synthesize a receipt until official host-owned evidence identifies the first failing layer.

Re-review evidence required: a current host-owned record for one eligible default execution that binds event, matcher, handler, and receipt outcome, or an official host statement that the event is unsupported for that executor class.

## Known-Good Aesthetica Path

The 18 valid control receipts have these properties:

- `agent_type=p2p_aesthetica`
- `event=SubagentStart`
- `source=codex_official_hook`
- exact cwd `D:\AI\P2P_dev\P2P-8.4.6-C-Codex-Edition-v4`
- model `gpt-5.6-luna`
- permission modes `default` or `bypassPermissions`
- three host sessions represented
- first receipt `2026-08-13T10:02:25+00:00`
- latest receipt `2026-08-14T05:29:11+00:00`

The corresponding profile file is `D:\AI\P2P_dev\P2P-8.4.6-C-Codex-Edition-v4\.codex\agents\p2p-aesthetica.toml`, with `name = "p2p_aesthetica"`.

Host logs also show historical native delegation requests with `agent_type: "p2p_aesthetica"`. The receipt, not the request text, is the identity authority.

The historical C09 plan records the pre-update project matcher as `^p2p_aesthetica$`. This matters because all 18 control receipts occur before the current C09 config/hook update. They establish a known-good older path, not current-path equivalence.

## Current Default Path

The current project config at `D:\AI\P2P_dev\P2P-8.4.6-C-Codex-Edition-v4\.codex\config.toml:8-14` contains the explicit matcher:

`^(?:default|p2p_(?:iris|tecton|axiom|vector|datos|anon|architecton|helios|aesthetica))$`

and the Windows command:

`py -3 .p2p/system/scripts/p2p_host_identity_hook.py --root .`

The fresh default thread has host-backed execution/turn metadata, but no observed profile field, agent role, agent path, session-bound receipt, or hook result. The default path therefore reaches the worker runtime but is not identity-certified.

## Four-Layer Trace

### 1. HOST EVENT EMISSION

Classification: `EVENT_EVIDENCE_UNAVAILABLE`.

No host-owned `SubagentStart` record for the fresh default worker was found in the ledger or app-server log. The available data cannot distinguish “event not emitted” from “event emitted but not logged/exposed.”

### 2. MATCHER EVALUATION

Classification: `EVIDENCE_UNAVAILABLE`.

The source matcher explicitly allows `default`. The active runtime matcher decision is not present in supported host evidence.

### 3. HOOK PROCESS EXECUTION

Classification: `EVIDENCE_UNAVAILABLE`.

There is no fresh host-owned command invocation, handler start, exit code, stdout, or stderr record for the default worker. The hook source itself is intentionally silent and returns success even when it cannot record proof.

### 4. RECEIPT WRITE

Classification: `EVIDENCE_UNAVAILABLE`, not `LEDGER_WRITE_FAILED`.

No append attempt or writer failure is recorded. The source writer path is directly covered by existing tests, including a synthetic `default` payload; this proves source behavior after invocation, not host invocation.

## Aesthetica Versus Default

Proven differences:

- Aesthetica is an explicit custom profile with a TOML profile file; `default` is the generic host executor class.
- Aesthetica has 18 historical official receipts; the fresh default has none.
- The 18 Aesthetica receipts predate the current C09 matcher/source update; the fresh default ran after that update and after the owner-reported host restart.
- Native thread metadata exposes execution/turn/model/cwd but does not expose observed profile/type for the fresh default.

Not proven:

- that Codex intentionally emits `SubagentStart` only for custom profiles;
- that `default` is unsupported by the host hook system;
- that the current matcher was not loaded;
- that the handler was invoked and failed to write.

The correct classification is therefore not a semantic profile limitation; it is missing host evidence.

## Official Alternative Host Evidence

Available and authoritative for execution existence:

- thread/execution ID;
- turn ID;
- model;
- exact cwd;
- completed status;
- requested `default` type in the native spawn request.

Unavailable for identity certification:

- observed profile/type;
- profile path or role provenance;
- a fresh host lifecycle event;
- session-bound identity receipt;
- matcher/handler/writer outcome.

The available rollout/session metadata is stale-proof for execution existence but insufficient to create a second identity authority. Worker prose remains non-authoritative.

## Classification

- Earliest proven failure layer: none.
- Earliest unobservable layer: `HOST EVENT EMISSION`.
- `P2P SOURCE DEFECT`: `NO` — no source defect is proven; direct source tests cover `default` receipt construction and writing.
- `HOST CAPABILITY LIMITATION`: `UNKNOWN` — no official host evidence proves a limitation.
- `OWNER_ACTION_REQUIRED`: `NO` — no concrete supported owner operation exists in the available Codex Desktop capability surface.
- `EXACT_OWNER_ACTION`: `N/A`.

## Source-Level Clearance Notes

- `D:\AI\P2P_dev\P2P-8.4.6-C-Codex-Edition-v4\.codex\config.toml:8-14`: clear; explicit matcher includes `default`, canonical eight, and Aesthetica; no wildcard or `p2p-uiux` profile.
- `D:\AI\P2P_dev\P2P-8.4.6-C-Codex-Edition-v4\.p2p\system\scripts\p2p_host_identity_hook.py:33-47`: clear; canonical, optional, and generic allow-lists are explicit.
- `D:\AI\P2P_dev\P2P-8.4.6-C-Codex-Edition-v4\.p2p\system\scripts\p2p_host_identity_hook.py:236-286`: clear; receipt append, malformed-payload handling, and fail-closed writer behavior are source-backed.
- `D:\AI\P2P_dev\P2P-8.4.6-C-Codex-Edition-v4\tests\test_p2p_host_identity_receipt.py:68-76`: clear; existing isolated test records a synthetic `default` payload as `HOST_DEFAULT / GENERIC`.

## Evidence Checked

Passed:

- Current project config strict parsing and hooks feature checks remain PASS.
- Exact project trust and trusted hook hash remain present.
- 18 historical Aesthetica receipts validate against the current ledger schema and source authority.
- Native thread metadata confirms the fresh default execution, turn, model, cwd, and completion.
- SQLite schema and current app-server process-scoped log inspection were read-only.
- No source/config/artifact mutation, private RPC, UI scraping, credential interception, bypass, or extra agent probe was used.

Failed:

- Fresh default official `SubagentStart` receipt: absent.
- Host event/matcher/handler/writer trace for the fresh default: absent.
- Current route-wide identity certification: not proven.

Not run:

- `p2p_iris` probe, by explicit gate.
- Normal UI route proof.
- New build/test run; no implementation source changed.

## Invariant Closure

- affected invariant: every eligible real subagent must be identity-certified by an authoritative host lifecycle receipt before role or route certification.
- sibling surfaces checked: current config, trust state, hook source, profile file, historical ledger receipts, current default thread metadata, app-server process logs, and existing source tests.
- residual unverified same-invariant surfaces: host event emission, active matcher decision, handler invocation, and receipt persistence for the fresh default.

## Required Fix List For Resubmission

1. Obtain an official host-owned event/matcher/handler/writer trace or official host capability statement; do not ask the owner to search for an unproven UI.
2. If that evidence proves a P2P source defect, patch only the proven layer and run the required impact/build/test gates.
3. If it proves a supported-host limitation, record `SUPPORTED_HOST_LIMITATION` without widening the matcher or synthesizing receipts.
4. Until then, keep `p2p_iris` gated and preserve candidate `.18`.

## Overall Evaluation

The historical Aesthetica path is genuinely known-good, but it is not a valid substitute for current default identity. The current P2P source/config boundary is internally consistent and fail-closed. The earliest current boundary is unobservable host event evidence, so the investigation cannot honestly claim `EVENT_NOT_EMITTED`, `MATCHER_NOT_MATCHED`, `HANDLER_FAILED`, `LEDGER_WRITE_FAILED`, or `SUPPORTED_HOST_LIMITATION`. C09 remains blocked without an owner action requirement.
