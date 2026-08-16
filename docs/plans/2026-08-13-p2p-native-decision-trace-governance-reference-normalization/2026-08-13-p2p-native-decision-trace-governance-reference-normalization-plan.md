# P2P Native Decision Trace - Governance Reference Normalization Plan

## Metadata

- Date: `2026-08-13`
- Status: `complete`
- Plan: `docs/plans/2026-08-13-p2p-native-decision-trace-governance-reference-normalization/2026-08-13-p2p-native-decision-trace-governance-reference-normalization-plan.md`
- Evidence: `docs/plans/2026-08-13-p2p-native-decision-trace-governance-reference-normalization/2026-08-13-p2p-native-decision-trace-governance-reference-normalization-evidence.md`
- Benchmark: `docs/plans/2026-08-13-p2p-native-decision-trace-governance-reference-normalization/2026-08-13-p2p-native-decision-trace-governance-reference-normalization-benchmark.md`
- Actual status: `docs/plans/2026-08-13-p2p-native-decision-trace-governance-reference-normalization/2026-08-13-p2p-native-decision-trace-governance-reference-normalization-actual-status.md`

## Goal

Fix only the proven governance/policy reference normalization defect in the
P2P development source. Valid policy references emitted by material workflow
capture must resolve deterministically in development, installed, packaged,
upgrade, reinstall, Windows, and supported POSIX contexts. Genuinely invalid
references must remain `MISSING_REFERENCE`.

## Rules

- Baseline is `8.4.7-C-codex.5`; preserve its ZIP and SHA-256 exactly.
- Do not rewrite historical .5 trace records or Decision Basis.
- New policy references use one portable logical form; machine paths are never
  canonical identity.
- Normalization is exact mapping only: no fuzzy match, nearest-file choice,
  fabricated evidence, or missing-reference suppression.
- The existing execution ledger remains the only durable trace store.
- Canonical identities remain exactly eight; denominator is 8; full quorum is
  8/8; `p2p_aesthetica` remains optional/noncanonical and is not simulated.
- Do not modify the old .5 release, App Game Truyen, Logistics, or any user
  project. Temporary fixtures remain under repository `.tmp`.
- No external dependency, agent, specialist, database, graph, RDF, MCP,
  Anvien integration, Semantica, Brigade/Tideline, UIUX redesign, discovery
  fix, or unrelated Decision Trace hardening.
- Anvien impact/detect-changes is attempted; the target has no Git metadata,
  so commit evidence is `N/A`.

## Problem

The verified .5 fresh-install WHY scenario stores `approval-policy.json` and
`drift-policy.json` in `POLICY_REFS`. Workflow capture emits these bare
logical names, while the resolver checks only `project-root / reference`.
The installed files are present under `.p2p/system/governance/`, so valid
references are incorrectly reported as `MISSING_REFERENCE`.

## Scope

- Reproduce and record the exact two baseline failures before editing.
- Define the smallest compatible policy-reference normalization rule.
- Normalize new policy refs to `governance/<POSIX-relative-path>`.
- Resolve canonical refs from exact governed roots and legacy bare refs from
  those roots without changing historical ledger bytes.
- Add direct tests for canonical, legacy, Windows-separator, POSIX, invalid,
  package, and backward-compatibility cases.
- Build the next full release only if packaged runtime behavior changes, using
  the existing version policy.
- Run fresh, upgrade, reinstall, package doctor, security, and regressions.

## Non-Goals

- No Decision Trace schema redesign, reference database, or history rewrite.
- No attempt to make all missing references disappear.
- No change to evidence/fact/source reference semantics.
- No user-project, App Game Truyen, or Logistics installation/upgrade.

## Requirements and Acceptance

RN1 exact two failures reproduced; RN2 root cause proven; RN3 minimal portable
normalization; RN4 valid references resolve; RN5 invalid references remain
missing; RN6 no fuzzy/fabricated resolution; RN7 Windows; RN8 POSIX where
supported; RN9 legacy .5 readable; RN10 fresh WHY; RN11 upgrade; RN12
same-version reinstall; RN13 temporal/supersession/contradiction; RN14
redaction/security; RN15 package doctor; RN16 canonical eight; RN17 denominator
8; RN18 no external dependency; RN19 no user project; RN20 exactly one fresh
residual-risk recommendation.

PASS requires fresh evidence for RN1-RN20, including both valid resolution and
the deliberately invalid negative test. A nonzero missing count is acceptable
only when each remaining item is genuinely invalid/unresolved.

## Checklist

- [x] P0-A: Complete actual status before implementation.
  - Goal: classify authority, baseline, exact failures, impact, and boundaries.
  - Work Steps: read approved SPECs; verify .5 hash; rerun baseline WHY;
    inspect emitter/resolver; run Anvien file-detail/impact; record status.
  - Implementation Gate: actual-status contains evidence IDs, relationship
    counts, invariant-family map, touch modes, and a final P0 decision.
  - Acceptance: root cause is concrete and P1 is narrow and unblocked.

### P1: Minimal normalization and compatibility

- Phase Goal: close the POLICY_REFS invariant family in the native runtime.
- In scope: native runtime capture/resolver and direct behavior tests.
- Out of scope: other reference fields, authority, UI, agents, discovery,
  packaging until runtime tests pass.
- Dependencies: P0-A.

- [x] P1-A: Add exact canonical policy normalization and legacy resolver.
  - Goal: new traces store portable logical refs; old bare refs resolve through
    exact governed roots.
  - Editable: `.p2p/system/p2p_capabilities/decision_trace.py`.
  - Inspect-only: workflow emitter, wrappers, governance files, .5 artifact.
  - Preserve-only: schema, ledger format, history, redaction, temporal,
    contradiction, supersession, canonical governance.
  - Work Steps: add one exact logical normalization rule and a resolver branch
    limited to `.p2p/system/governance` and `governance`; preserve old records;
    verify no ledger rewrite or duplicate event.
  - Implementation Gate: P0-A complete and target file-detail evidence exists.
  - Acceptance: valid canonical and legacy refs resolve; unsafe/invalid refs
    remain missing; no absolute path becomes a canonical ref.
  - Evidence Targets: E1-P1A-NORM1, E1-P1A-COMPAT1.

- [x] P1-B: Add positive, negative, and portability regression tests.
  - Goal: make the defect and honest failure contract executable.
  - Editable: `tests/test_p2p_decision_trace.py` and focused evaluator only
    if required by existing test architecture.
  - Preserve-only: existing DT1-DT24 behavior and unrelated fixtures.
  - Work Steps: test canonical/legacy/invalid references through capture to
    query; test backslash input, POSIX logical identity, no path leaks, and
    legacy trace readability.
  - Implementation Gate: P1-A focused probes pass.
  - Acceptance: valid resolves, invalid remains `MISSING_REFERENCE`, and no
    test asserts zero missing references globally.
  - Evidence Targets: E1-P1B-NEG1, E1-P1B-PORT1.

P1 exit: PASS. The focused normalization test, existing workflow/relationship
tests, and DT1-DT24 evaluator all pass. P2 may proceed; no emitter or schema
change was needed.

### P2: Package and lifecycle certification

- Phase Goal: prove changed behavior from actual candidate package lifecycle.
- In scope: package, fresh install, upgrade, reinstall, POSIX, WHY, security,
  and same-invariant regressions.
- Out of scope: old artifact mutation and real projects.
- Dependencies: P1.

- [x] P2-A: Build and doctor next full candidate.
  - Goal: package the runtime change under existing release policy.
  - Acceptance: candidate version/path/size/count/hash recorded; package
    doctor, manifest, drift, secret, and boundary checks pass.
  - Evidence Targets: E2-P2A-ARTIFACT1, E2-P2A-DOCTOR1.

- [x] P2-B: Fresh install, upgrade, and same-version reinstall.
  - Goal: valid refs resolve through all supported lifecycle states while
    preserving old state and traces.
  - Acceptance: fresh WHY resolves valid refs; upgrade preserves old bytes and
    resolves legacy refs; new trace uses canonical form; reinstall has zero
    ledger/policy/backup churn.
  - Evidence Targets: E2-P2B-FRESH1, E2-P2B-UPGRADE1, E2-P2B-REINSTALL1.

- [x] P2-C: POSIX, negative, WHY, security, and full regressions.
  - Goal: close same-invariant surfaces and select one fresh residual risk.
  - Acceptance: supported POSIX passes; invalid remains missing; temporal,
    supersession, contradiction, artifact lookup, redaction, canonical 8/8,
    Foundation/UIUX, FACT/RAG, installer, and secret checks pass.
  - Evidence Targets: E2-P2C-PORTNEG1, E2-P2C-REGRESS1, E2-P2C-NEXT1.

### P3: Supervisor acceptance and closure

- [x] P3-A: Independent supervisor review.
  - Goal: verify source, artifact, lifecycle, negative test, regressions, and
    boundaries; write exactly one PASS or REJECT report.
  - Gate: P1/P2 complete or explicitly blocked.
- [x] P3-B: Remove dead plan-created work.
  - Goal: keep temporary/evaluator material out of the candidate package.
  - Acceptance: boundary scan passes and required evidence is preserved.
- [x] P3-C: Close plan and Goal.
  - Goal: finalize reports/hashes/status; call `update_goal complete` only
    after supervisor PASS and RN1-RN20 are evidenced.

P2 exit: PASS. Candidate `.6` package, fresh install, `.5` upgrade,
same-version reinstall, Windows separator, WSL/POSIX, invalid-reference,
Decision Trace, UIUX, Foundation, security, drift, and full regression
evidence all pass. P3 remains for independent supervisor acceptance and final
RN1-RN20 closure.

P3 exit: PASS. Independent supervisor reran focused source tests, package
lifecycle tests, full regression, fresh/legacy/invalid queries, artifact
boundary checks, and Anvien topology evidence. Supervisor report is PASS and
RN1-RN20 are closed. Stop; no optional work was started.

## Risk Notes

- Target has no Git metadata; hashes, reports, and Anvien output are the local
  audit trail and commit is `N/A`.
- POSIX is tested only through the supported Bash/WSL path; unsupported
  execution is reported honestly.
- A new artifact is expected because shipped runtime behavior changes; .5 is
  immutable.
