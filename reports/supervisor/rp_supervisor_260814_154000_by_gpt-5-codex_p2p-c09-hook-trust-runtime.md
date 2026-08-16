# Supervisor Report: P2P-C09 active host hook trust boundary

Verdict: REJECT

## Metadata

- Report file: `reports/supervisor/rp_supervisor_260814_154000_by_gpt-5-codex_p2p-c09-hook-trust-runtime.md`
- Review time: 2026-08-14 15:40 Asia/Saigon
- Reviewer: `gpt-5-codex`
- Repo/project: `P2P-8.4.6-C-Codex-Edition-v4`
- Scope reviewed: C09 continuation; active project root, Codex runtime/config layer, project trust, hook trust state, fresh receipt boundary
- Claim reviewed: resolve the remaining host-activation blocker and accept C09 only after fresh authoritative `default` and `p2p_iris` `SubagentStart` receipts
- Authority used: current C09 user request, repository `AGENTS.md`, C09 plan/acceptance criteria, current Codex runtime state, source/config, and Execution Ledger
- Related artifacts: prior C09 Supervisor report, C09 coder report, current project-local `.codex/config.toml`, user Codex `config.toml`, current task/worker rollout files

## Executive Summary

- Problem: the local C09 boundary is implemented, but the active host has not produced fresh authoritative receipts for the generic/default and canonical probes.
- Decision: `REJECT`. The exact primary classification is `HOOK_TRUSTED_NOT_MATCHING`: the exact project hook slot has a persisted trusted hash, but the current project hook definition is a changed revision with no current trusted revision exposed by the runtime.
- Required outcome: the owner must complete the native Codex hook-trust review for this exact changed hook, then resume this same task for one fresh `default` probe followed by one fresh `p2p_iris` probe.

## Blocking Findings

### [P0] Current hook revision is pending trust review

File: `.codex/config.toml:8-15`; `C:\Users\Admin\.codex\config.toml:127-133`

Issue: the project-local `SubagentStart` hook is present and the project itself is trusted, but the user Codex trust state contains only a prior `trusted_hash` for the exact slot `...\.codex\config.toml:subagent_start:0:0`. The current project config was changed after the current C09 task was created, and the runtime does not expose a matching current trusted definition/hash.

Evidence:

- Current task metadata reports cwd `D:\AI\P2P_dev\P2P-8.4.6-C-Codex-Edition-v4`.
- `codex doctor --json` reports the same cwd, a successfully parsed user config, and the project terminal title sourced from project config.
- Project config declares matcher `default` plus the canonical eight and `p2p_aesthetica`, with the Windows command `py -3 .p2p/system/scripts/p2p_host_identity_hook.py --root .`.
- User config stores `trusted_hash = sha256:31416c6b4bd97db0683bfba86f035afc8fb4984bf79e1f457acd27cde6b8908d` for that exact hook slot and separately stores `trust_level = "trusted"` for the exact project root.
- Current source hashes are hook `974aab095fde4d9f758bc93725f99e006d1db7253378b70ccccd22fc66df11fc` and project config `1492e390d06dd57bc6982d38b479b23f9ac556d04276e4e84cc11c046114ec23`. Codex does not expose a recomputed current hook-definition trust hash through the available diagnostic surface, so the persisted state cannot be treated as trust for the changed revision.
- No `--dangerously-bypass-hook-trust` or equivalent was used.

Why this blocks acceptance: source equality and project trust do not prove that the active host loaded and trusted the changed hook. Without that proof, a missing receipt cannot be attributed to event emission, matcher evaluation, or receipt writing.

Fix direction: use the native Codex Desktop hook-trust review for the exact changed project hook. Do not edit `hooks.state`, change the matcher, or use a bypass flag.

Re-review evidence required: current host view/state showing the exact project hook source, active matcher, command, enabled/trusted status, and current trusted revision, followed by fresh official receipts.

### [P0] No fresh authoritative receipts exist for the required probes

File: `.p2p/state/execution-ledger.jsonl`

Issue: the two real read-only workers completed, but the authoritative ledger still contains 18 historical `host_subagent_identity_receipt` events, all `p2p_aesthetica`; it contains zero fresh `default` and zero fresh `p2p_iris` receipts.

Evidence:

- Rollout `019fff22-023e-70b1-adb1-cf3f8a00ce29` completed the real default worker probe without a matching receipt.
- Rollout `019fff25-73a3-7ab0-9794-b345391ef12c` completed the real `p2p_iris` worker probe without a matching receipt.
- Current ledger count is 18 host receipts: `default=0`, `p2p_iris=0`, `p2p_aesthetica=18`.

Why this blocks acceptance: worker labels and worker prose are not identity authority. The required session/turn/agent binding cannot be verified when the host receipt is absent.

Fix direction: after trust activation is proven, run only one fresh default probe and, only if it succeeds, one fresh `p2p_iris` probe.

Re-review evidence required: fresh `source=codex_official_hook` receipts with event `SubagentStart`, agent/session/turn/execution IDs, requested/observed identity, and matching current task context.

## Source-Level Clearance Notes

- `.p2p/system/scripts/p2p_host_identity_hook.py`: clear for this review; current source contains the explicit canonical/optional/generic allow-list and fail-closed receipt writer (`CANONICAL_HOST_AGENT_TYPES` at line 33, `process_payload` at line 258). No source defect was proven in this continuation.
- `.p2p/system/p2p_capabilities/live_execution.py`: clear for this review; the fresh host receipt lookup remains fail-closed (`_find_fresh_host_receipt` at line 577). It correctly cannot certify an absent host receipt.
- `.codex/config.toml`: source declaration is present and syntactically valid at lines 8-15, but active/trusted loading of the changed revision is not proven.

## Evidence Checked

Passed:

- Current Codex Desktop process family and CLI runtime were identified; CLI is `0.147.0`, active Desktop app-server binary reports `0.147.0-alpha.6.6`.
- Current project root and task cwd match exactly.
- User config parses successfully; exact project root is marked trusted.
- Project hook command and matcher are present; no `project_root_markers` override is present.
- Current C09 task remains the same task; no new architecture Goal was created.
- No `p2p-uiux` custom-agent profile exists; no `.git` directory exists.
- Historical C09 local implementation/package/regression evidence remains preserved and was not relabeled.

Failed:

- Fresh official `default` receipt: absent.
- Fresh official `p2p_iris` receipt: absent.
- Active host proof that the changed hook revision is trusted and loaded: absent; persisted trust state is for a prior hook revision.

Not run:

- No additional worker probe, because activation/trust was not proven.
- No C08 rerun.
- No code change, candidate `.19`, release promotion, trust bypass, or manual edit of user hook state.
- No new build/test/package run; there was no implementation change in this continuation.
- No Computer Use UI action; the available Windows automation skill explicitly prohibits automating the ChatGPT/Codex desktop UI and the exposed runtime did not provide a supported hook-state query tool.

## Invariant Closure

- affected invariant: official host identity must be proven by a fresh, allowlisted `SubagentStart` receipt; logical route must remain separate from host profile.
- sibling surfaces checked: project config, user project trust, persisted hook trust state, current task cwd, current worker rollouts, Execution Ledger, hook source, and live receipt lookup.
- residual unverified same-invariant surfaces: active host hook view/trust for the changed revision and fresh `default`/`p2p_iris` receipt emission.

## Required Fix List For Resubmission

1. Owner completes the native Codex hook-trust review for the exact changed hook at the current project root; do not bypass trust or edit the persisted state manually.
2. Resume this same C09 task and provide fresh authoritative `default` evidence; only then run the single fresh `p2p_iris` evidence path.
3. Re-run Supervisor review with the current hook state and receipts; PASS requires the normal `p2p-uiux` route proof, historical Aesthetica compatibility, and fail-closed behavior to remain intact.

## Overall Evaluation

The local implementation remains bounded and fail-closed, and the project root/config declarations are correct. Acceptance is rejected solely because the host-owned trust/emission boundary is not closed: a prior trusted hook state exists, but it does not prove trust for the changed current revision, and the required fresh official receipts remain absent.
