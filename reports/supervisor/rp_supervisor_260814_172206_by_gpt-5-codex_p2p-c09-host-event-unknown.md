# Supervisor Report: P2P-C09 post-reload SubagentStart boundary

Verdict: REJECT

## Metadata

- Report file: `reports/supervisor/rp_supervisor_260814_172206_by_gpt-5-codex_p2p-c09-host-event-unknown.md`
- Review time: 2026-08-14 17:22 Asia/Saigon
- Reviewer: `gpt-5-codex`
- Repo/project: `P2P-8.4.6-C-Codex-Edition-v4`
- Scope reviewed: C09 continuation after owner trust action and Codex Desktop host restart
- Claim reviewed: one fresh default probe after the restart should produce an authoritative `SubagentStart` receipt
- Authority used: current C09 continuation request, repository `AGENTS.md`, C09 acceptance gate, current Codex process/config state, worker rollout, raw local log inspection, and Execution Ledger
- Related artifacts: prior host-reload Supervisor report, fresh default worker `019fffc5-89e8-7f82-b30a-ed376b15ea7e`

## Executive Summary

- Owner trust is present and a new Desktop app-server PID is observed after the owner-reported restart; the available timestamps do not independently prove that the trust record was loaded before that process began.
- The fresh default worker completed its bounded read-only task, but no authoritative `SubagentStart` receipt was recorded.
- The remaining failure is at the host event/matcher/writer boundary. Current evidence does not prove whether the host did not emit the event, the matcher did not select the hook, or the hook matched but failed to write the receipt.
- Decision: `REJECT` with classification `UNKNOWN`. Do not infer identity and do not run the gated `p2p_iris` probe.

## Blocking Findings

### [P0] Fresh post-reload receipt is absent, but the failing layer is not observable

Issue: the post-restart default probe produced no official ledger receipt. The available process, config, worker, and raw-log evidence is insufficient to distinguish these three states:

1. `SubagentStart` was not emitted by the host;
2. the event was emitted but the configured matcher did not match; or
3. the hook matched and the receipt writer failed or was not persisted.

Evidence:

- Exact C09 project root: `D:\AI\P2P_dev\P2P-8.4.6-C-Codex-Edition-v4`.
- Exact project trust remains `trusted` in `C:\Users\Admin\.codex\config.toml`.
- Exact trusted hook hash remains `sha256:345fc9dd085fcaa2ca40c1f324fbc6db300fb529e6189a33703968ad6eba5580`.
- User config last write: 2026-08-14 17:14:54.
- Current Desktop app-server: PID 4288, started 2026-08-14 17:14:01. The current user-config file mtime is 2026-08-14 17:14:54, so the mtime ordering is not sufficient to certify trust-layer activation; the owner separately reported that the restart followed the trust action.
- Project config strict parsing and `hooks=true` checks remain PASS.
- Fresh default worker `019fffc5-89e8-7f82-b30a-ed376b15ea7e` completed one bounded read-only inspection; it changed no files and spawned no children.
- Execution Ledger remains at 18 historical host receipt rows: `default=0`, `p2p_iris=0`, `p2p_aesthetica=18`.
- Read-only SQLite log inspection shows generic `SubagentStart`/hook-related strings, but no isolated fresh record that establishes event emission, matcher result, or receipt-writer outcome for this worker.
- A Unicode encoding traceback surfaced while printing a diagnostic query result; it is from the diagnostic command output path and is not evidence of a hook execution failure.

Why this blocks acceptance: a worker rollout/completion is not an authoritative role receipt. Ledger absence alone cannot classify the host boundary, so C09 cannot certify the default role or proceed to `p2p_iris`.

Required evidence: a supported host-maintained hook diagnostic or raw trace for this exact task that reports `SubagentStart` event receipt, matcher decision, handler exit, and receipt-write result. No further role probes are authorized before that evidence exists.

## Source-Level Clearance Notes

- `.codex/config.toml`: unchanged; intended C09 matcher and Windows hook command remain present.
- `.p2p/system/scripts/p2p_host_identity_hook.py`: unchanged; source SHA-256 is `974aab095fde4d9f758bc93725f99e006d1db7253378b70ccccd22fc66df11fc`.
- Project config SHA-256 remains `1492e390d06dd57bc6982d38b479b23f9ac556d04276e4e84cc11c046114ec23`.
- Owner trust state is current on disk; no trust bypass, matcher edit, source edit, or permission expansion was used.

## Evidence Checked

Passed:

- Owner trust state is present for the exact C09 hook slot.
- The exact project is trusted and a new active app-server PID is present after the owner-reported restart.
- Strict project config parsing and the hooks feature check pass.
- The fresh default worker completed without changing files or spawning children.
- No C08 work, code edit, hook-trust bypass, or additional probe was performed after the missing receipt.

Failed:

- Fresh default authoritative receipt: absent.
- C09 default-role certification: not proven.
- Host event/matcher/writer layer: not classifiable from supported evidence.

Not run by gate:

- `p2p_iris` probe.
- Normal UI route live proof.
- New build/test/package run; no implementation code changed.

## Invariant Closure

- Affected invariant: the active trusted host must identify each eligible real subagent through an authoritative `SubagentStart` receipt before role certification.
- Surfaces checked: user trust state, project config, current app-server start time, fresh worker rollout, task cwd, raw local logs, and Execution Ledger.
- Residual unverified surfaces: host event emission, matcher evaluation, hook handler outcome, and receipt persistence for the fresh default worker.

## Required Fix List For Resubmission

1. Expose or inspect the supported Codex Desktop host hook diagnostic for this exact C09 task; capture event-received, matcher-result, handler-exit, and receipt-write evidence.
2. Keep the current trust/config/source unchanged while collecting that evidence; no additional restart is required by the current evidence.
3. Only after a fresh authoritative default receipt is proven may the C09 gate authorize one `p2p_iris` probe and the normal UI route proof.

## Overall Evaluation

The owner trust action and a new host process after the reported restart are evidenced, but trust-layer activation is not independently visible from the available timestamps. The remaining C09 failure is `UNKNOWN` at the host `SubagentStart`/matcher/writer boundary, not a proven project-layer or source-layer defect. C09 remains blocked and fail-closed; no role identity is inferred from the fresh worker completion, and no further probes should be run until host-level hook diagnostics are available.
