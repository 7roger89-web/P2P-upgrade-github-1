# Supervisor Report: P2P-C09 host reload after hook trust

Verdict: REJECT

## Metadata

- Report file: `reports/supervisor/rp_supervisor_260814_160400_by_gpt-5-codex_p2p-c09-host-reload-runtime.md`
- Review time: 2026-08-14 16:04 Asia/Saigon
- Reviewer: `gpt-5-codex`
- Repo/project: `P2P-8.4.6-C-Codex-Edition-v4`
- Scope reviewed: C09 continuation after owner hook-trust action
- Claim reviewed: a fresh default probe should now produce an authoritative `SubagentStart` receipt
- Authority used: current C09 continuation request, repository `AGENTS.md`, C09 acceptance gate, current Codex process/config state, worker rollout, and Execution Ledger
- Related artifacts: prior C09 hook-trust Supervisor report, default worker `019fff80-d179-7d70-80bf-5cd55d393b4b`

## Executive Summary

- Problem: owner trust was recorded, but the active Codex Desktop host was not reloaded before the default probe.
- Decision: `REJECT`. The exact current classification is `PROJECT_LAYER_NOT_ACTIVE`.
- Required outcome: reload/restart the Codex Desktop host/server so the same project task uses the post-trust configuration, then resume C09. No `p2p_iris` probe is authorized yet.

## Blocking Findings

### [P0] Active app-server predates the owner trust update

File: `C:\Users\Admin\.codex\config.toml:129-130`

Issue: the owner action updated the exact C09 hook state to `sha256:345fc9dd085fcaa2ca40c1f324fbc6db300fb529e6189a33703968ad6eba5580`, but the active Codex Desktop app-server process serving this task started before that update.

Evidence:

- User config last write: 2026-08-14 15:59:40.
- Active Desktop app-server PID 6564 start: 2026-08-14 14:41:48.
- The fresh default worker `019fff80-d179-7d70-80bf-5cd55d393b4b` ran at approximately 16:01 through the existing task host.
- The project root and source config remain correct; CLI strict-config, doctor config loading, and `hooks=true` are all successful.
- The current Execution Ledger still has 18 historical host receipts, `default=0`, and `p2p_iris=0`.

Why this blocks acceptance: the owner trust record exists on disk, but the active host process has no fresh evidence that it reloaded the project/user hook layer. Source/config state alone cannot certify the running process.

Fix direction: owner reloads/restarts the Codex Desktop host/server for this project/task, then resumes this same C09 task. Do not edit code, matcher, or `hooks.state`; do not use hook-trust bypass.

Re-review evidence required: app-server start/reload after the trust timestamp, followed by one fresh `default` receipt. Only after that succeeds may `p2p_iris` run.

## Source-Level Clearance Notes

- `.codex/config.toml`: clear; matcher and command remain the intended C09 allow-list and Windows hook command.
- `.p2p/system/scripts/p2p_host_identity_hook.py`: clear; no source change or writer defect was introduced in this continuation.
- `.p2p/system/p2p_capabilities/live_execution.py`: clear; the live boundary correctly rejects missing authoritative receipts.

## Evidence Checked

Passed:

- Owner trust state is now present for the exact C09 hook slot.
- Exact project root remains trusted and current task cwd remains correct.
- CLI strict-config, doctor config parsing, and hooks feature are PASS.
- Default worker completed the bounded read-only inspection without modifying files.
- No C08 work, code edit, bypass, or additional worker was performed after the missing receipt.

Failed:

- Fresh default official receipt: absent.
- Active host reload after owner trust action: absent.
- Route-wide C09 readiness: not proven.

Not run:

- `p2p_iris` probe, gated on default receipt.
- Normal UI route live proof.
- New build/test/package run; no implementation code changed.

## Invariant Closure

- affected invariant: the active host must load the trusted project hook and emit an authoritative `SubagentStart` receipt.
- sibling surfaces checked: user trust state, project config, active app-server process time, worker rollout, current task cwd, and Execution Ledger.
- residual unverified same-invariant surfaces: post-reload hook activation and fresh default receipt.

## Required Fix List For Resubmission

1. Owner reloads/restarts the active Codex Desktop host/server for this project so it loads the trust state written at 15:59:40.
2. Resume this same C09 task and run exactly one fresh default probe.
3. If default passes, run one fresh `p2p_iris` probe and then complete normal `p2p-uiux` route proof.

## Overall Evaluation

The trust action itself is now recorded correctly. The remaining failure is operational: the running app-server predates that state and produced no official receipt for the default worker. C09 remains blocked at `PROJECT_LAYER_NOT_ACTIVE`; no identity is inferred from the worker result.
