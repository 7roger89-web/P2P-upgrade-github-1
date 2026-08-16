# Supervisor Report: P2P-C08 route/profile live-gate integrity

Verdict: PASS

## Metadata

- Report file: `reports/supervisor/rp_supervisor_260814_131853_by_gpt-5-codex_p2p-c08-route-profile-gate.md`
- Review time: `2026-08-14 13:18:53 Asia/Saigon`
- Reviewer: `gpt-5-codex`
- Repo/project: `P2P-8.4.6-C-Codex-Edition-v4`
- Scope reviewed: C08 pre-registration, route/profile freeze, live host gate,
  existing C06/C07 boundary, canonical suite, validation output, and blocked
  benchmark report
- Claim reviewed: C08 may honestly stop before scored execution when the
  task-correct route/profile set cannot be bound to fresh official host identity
  receipts without changing the treatment or control plane
- Authority used: attached P2P-C08 request, repository `AGENTS.md`, existing
  C06/C07 source/contracts, current host config and Execution Ledger, current
  suite/fixtures, and current validation commands
- Related artifacts: `.tmp/p2p-c08-preflight-20260814/preregistration.json`,
  `.tmp/p2p-c08-preflight-20260814/router-observation.json`,
  `reports/benchmark/p2p-c08-real-context-ab-20260814.md`, C07 boundary report,
  official `.15`, candidate `.17`, and the C08 workflow Goal Contract snapshot

## Executive Summary

- Problem: the requested C08 benchmark requires 24 real paired trials using
  task-correct routes, but the current supported receipt path is profile-bound.
- Decision: PASS for the integrity of the blocked result. The benchmark was
  stopped before provider calls; no proxy result was promoted and no quality or
  efficiency claim was made.
- Required outcome: accept only the preflight/blocker result. Do not call C08 a
  completed A/B certification.

## Source-Level Clearance Notes

- `.p2p/system/p2p_capabilities/context.py`: clear and preserved. The C06 source
  contains the two intended modes and the focused 12-scenario contract; no C08
  treatment change was made.
- `.p2p/system/p2p_capabilities/live_execution.py`: clear for fail-closed use.
  `prepare_trial` binds scenario, condition, context, fixture, request, and
  artifact; `finalize_trial` requires a fresh official receipt with matching
  `agent_type` before setting `runtime_task_execution=true` (lines 364-454 and
  602-643). This source supports the stop; it does not provide missing host
  identity coverage.
- `.p2p/system/scripts/p2p_host_identity_hook.py`: clear and preserved. It
  allow-lists host lifecycle identity fields and does not infer identity from a
  profile.
- `.codex/config.toml`: clear for the reviewed state. The only configured
  `SubagentStart` matcher is `^p2p_aesthetica$` (lines 8-14), so the current
  proof surface is narrower than the C08 route set.
- `.p2p/evals/2026-08-14-context-efficiency-ab-proxy-suite.json` and frozen
  fixture: clear and preserved. Validation passes, but the suite's historical
  proxy results remain non-live and were not counted.

## Evidence Checked

Passed:

- Pre-registration JSON is valid and freezes the counterbalanced order before
  any scored execution; SHA-256 `f91cd585b33d5c83d6e3ed2243e3be61b47f5d6e7500889e07fb0f282986614e`.
- Router observation covers all 12 canonical scenarios; C6 remains `p2p-uiux`
  primary, C7 is the only Aesthetica-eligible route, and C1/non-UI routes are
  not assigned Aesthetica.
- Current ledger inspection found 18 valid host identity receipts, all
  `p2p_aesthetica`; no non-Aesthetica receipt was inferred.
- Focused C06/live/host-identity tests: `28/28 PASS`.
- Capability doctor: `PASS`; canonical identities exact, denominator `8`, full
  quorum `8/8`, Aesthetica optional/noncanonical.
- Governance validation: `PASS`; quorum validation: `PASS` with eight canonical
  identities and Aesthetica excluded from the denominator.
- Decision Trace evaluation: `24/24 PASS`.
- Canonical proxy suite validation/gate: `PASS`, but explicitly not live
  evidence.
- Existing C07 evidence independently limits its claim to four Aesthetica-backed
  C1/C7 dry-runs and does not claim full-suite quality or efficiency.
- The project workflow bookkeeping created a C08 Goal Contract snapshot but its
  generic linter classified the natural-language request as `SEPARATE GOALS`.
  This is another disclosed BLOCKED control-plane result, not a reason to
  fabricate trials or to weaken the benchmark protocol.
- A local workflow preflight then reached terminal `BLOCKED` at
  `run-20260814-062759-c08-live-eligibility`. It appended only four ordinary
  workflow events and zero `live_context_trial_receipt` events; no provider or
  child execution occurred.

Failed or limited, with disposition:

- The C08 live eligibility gate fails for the full route set: no fresh official
  identity proof is available for standard non-Aesthetica or `p2p-uiux` route
  profiles. Disposition: stop before trials.
- Package doctor, run with the correct development role, reports inherited
  placeholder-token findings in duplicated marketplace/reference files.
  Disposition: disclose; do not modify unrelated historical material under this
  measurement-only Goal.
- Installed-project doctor is not applicable to this development checkout and
  also reports inherited scan findings. Disposition: do not use it as C08 live
  evidence.
- C2/C3 have lexical UI hits in the existing router although their canonical
  task intent is non-UI/generic. Disposition: disclose route ambiguity and do
  not silently call a UI specialist.
- The C08 workflow Goal Contract and project status are now terminal `BLOCKED`;
  the ledger contains no new C08 live receipt. The four control-plane events are
  explicitly excluded from scored trial count.

Not run:

- All 24 C08 live executions, output capture, blinding, quality review,
  acceptance scoring, paired timing, token analysis, and hypothesis adoption
  matrix based on live results. These are not possible without closing the
  route/profile/host-identity gate.

## Invariant Closure

- Affected invariant: task-correct route/profile -> equivalent A/B request ->
  fresh official host identity -> `runtime_task_execution=true` -> receipt and
  output.
- Sibling surfaces checked: canonical suite and fixtures, C06 context builder,
  C07 live boundary, host hook, `.codex/config.toml`, `.codex/agents`, router
  output, Execution Ledger agent-type inventory, capability/governance/quorum,
  Decision Trace, and blocked benchmark report.
- Residual unverified same-invariant surfaces: non-Aesthetica host identity
  coverage remains missing; this is the declared blocker, not an unreported
  trial result. No narrower partial run was used to imply full-suite closure.

## Required Fix List For Resubmission

1. In a separate authorized Goal, add or otherwise expose a supported official
   host identity/receipt path for the task-correct non-Aesthetica and `p2p-uiux`
   execution profiles without changing C06/C07 treatment semantics.
2. Re-run the same frozen C08 pre-registration and prove every scored trial has
   matching route/profile, fresh official host identity, isolated root,
   `runtime_task_execution=true`, output hash, and receipt before reviewing
   quality.

## Overall Evaluation

The benchmark itself is not PASS-certified as an A/B result; it is correctly
BLOCKED. The current evidence supports the blocker and shows that the agent did
not fabricate live execution, reuse proxy scores, call Aesthetica for forbidden
scenarios, or alter the treatment. Supervisor PASS means the blocked outcome is
accepted as experimentally honest, not that B is better, non-inferior, or
adoptable.
