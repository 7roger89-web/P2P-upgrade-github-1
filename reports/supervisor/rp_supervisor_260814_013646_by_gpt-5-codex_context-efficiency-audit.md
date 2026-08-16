# Supervisor Report: Context-Efficient Execution & Quality Audit

Verdict: REJECT

## Metadata

- Report file: `reports/supervisor/rp_supervisor_260814_013646_by_gpt-5-codex_context-efficiency-audit.md`
- Review time: `260814 013646 +07:00`
- Reviewer: `gpt-5-codex`
- Repo/project: `P2P-8.4.6-C-Codex-Edition-v4`
- Scope reviewed: audit plan, actual-status, evidence ledger, benchmark suite,
  current source contracts, official `.15` baseline, and validation artifacts
- Claim reviewed: the requested context-efficiency foundation audit can be
  accepted after the recorded 12-scenario A/B comparison.
- Authority used: user Goal, `AGENTS.md`, planner/eval/supervisor contracts,
  current source, governance, runtime validation, and Anvien graph evidence
- Related artifacts: audit plan/evidence/benchmark/actual-status, frozen
  fixture, proxy suite/evidence, official ZIP, current QA reports

## Executive Summary

- Problem: determine whether a candidate Capsule/Knowledge Delta/preflight
  contract reduces execution context without quality loss.
- Decision: reject acceptance of a completed quality audit. The evidence proves
  a bounded contract proxy and identifies real runtime gaps, but no real worker
  or provider task executed and no Q1–Q12 quality observation exists.
- Required outcome: keep the Goal `BLOCKED`; do not promote B, create `.16`, or
  claim token/cost/quality improvement until a real equivalent A/B execution
  surface and authoritative telemetry are available.

## Blocking Findings

### [CRITICAL] A/B quality non-inferiority is not observed

File: `reports/QA/rp_qa_20260814T011703_by_gpt-5-codex_context-efficiency-ab-proxy.json`

Issue: the 48 recorded trials are explicitly `contract_level_proxy` with
`runtime_task_executed: false`, and Q1–Q12 are `UNKNOWN`. The p2p-eval suite
structural score of `1.0` grades the proxy evidence shape, not task
correctness, acceptance, evidence quality, safety, regression, or beginner
usefulness.

Evidence: `E2-P2A-BENCH3..E2-P2A-BENCH6`, `E2-P2B-QUALITY1..E2-P2B-BLOCK1`;
the current proxy evidence SHA-256 is
`de9b33f7b5f068d57a50aa8d6f83a7f2245fe63d805509c47f49d311c4d629b4`.

Why this blocks acceptance: the user’s non-inferiority rule requires quality
to be equivalent or better before efficiency is counted. A byte reduction is
not sufficient evidence.

Fix direction: in a separate implementation/evaluation Goal, provide an
equivalent direct/delegated execution surface with the same fixture,
permissions, capabilities, acceptance checks, and independent blinded review.

Re-review evidence required: at least C1–C12, two isolated A trials and two
isolated B trials per case, real result/evidence hashes, Q1–Q12 observations,
and a quality non-inferiority decision.

### [HIGH] Current workflow has no bound worker return/execution contract

File: `scripts/p2p_workflow.py:379-416`, `scripts/p2p_workflow.py:1339-1590`

Issue: `select_agents()` records named selected-agent metadata, while
`run_workflow()` writes state, reports, and traces. The inspected path does not
invoke or verify child workers, provider calls, worker return bytes, or a
Knowledge Delta.

Evidence: Anvien current graph is fresh (`273` files, `10,502` nodes,
`11,924` relationships); file-detail reports `scripts/p2p_workflow.py` as
`258` symbols, `36` inbound refs, `44` linked flows, high risk, and
`changedSinceAnalyze: false`. `rg` over `scripts` and
`.p2p/system/p2p_capabilities` found no runtime `KNOWLEDGE_DELTA`,
`worker_return`, `input_tokens`, `cached_input_tokens`, or provider-call
contract.

Why this blocks acceptance: the proposed B condition is not a current
executable condition. Comparing A to an in-memory shape is not equivalent A/B
execution.

Fix direction: bind any future compact return contract to existing Evidence,
FACT_LEDGER, Decision Trace, Execution Ledger, and approvals; do not add a
second memory, scheduler, router, or worker pool.

Re-review evidence required: source-level contract and real runtime receipt
showing the bounded worker call, permission envelope, return delta, evidence,
and done-check path.

### [HIGH] Workflow/eval helper interface mismatch remains open

File: `scripts/p2p_workflow.py:296-318`, `scripts/p2p_workflow.py:1032-1053`

Issue: helper discovery prioritizes `.p2p/system/scripts/p2p_eval.py`, whose
current CLI is a UI/UX evaluator with no `design` subcommand. The portable
`scripts/p2p_eval.py` has the required v2 subcommands. The workflow bootstrap
therefore returned BLOCKED with an unrecognized-arguments error.

Evidence: `E0-P0A-WORKFLOW2`; direct `--help` inspection of both helpers;
`scripts/p2p_workflow.py` current source; current audit bootstrap output.

Why this blocks acceptance: the current Goal path cannot reliably create or
validate the intended project-specific eval through its selected helper.

Fix direction: separate repair Goal to define one compatible helper boundary,
then run its impact/eval/regression gates. Do not repair it during supervisor
review or silently switch helpers in the benchmark.

Re-review evidence required: fresh bootstrap output, v2 validate/gate output,
and regression evidence from the repaired boundary.

### [MEDIUM] Baseline validation and whole-repository secret scan are not clean

File: `scripts/doctor.py` and existing plugin-marketplace documentation

Issue: package doctor returned FAIL because the development checkout lacks two
expected root payload groups. Whole-repository secret scan reported five
existing high-confidence `GITHUB_TOKEN` example references in documentation and
preserved temporary source snapshots. Subtree scans for `.p2p/system` and
`scripts` passed.

Evidence: `E3-P3A-TEST7`, `E3-P3A-SECURITY1..E3-P3A-SECURITY4`.

Why this blocks acceptance: the requested CE26/security and package evidence
cannot be represented as unconditional PASS. The findings do not authorize
editing the official artifact or suppressing the scanner.

Fix direction: classify or quarantine the existing examples and resolve the
development-source payload/layout mismatch in a separately scoped audit or
release-preparation Goal.

Re-review evidence required: package doctor PASS for the intended filesystem,
secret scan with zero unclassified findings, and unchanged official `.15`
hash.

## Source-Level Clearance Notes

- `scripts/p2p_workflow.py`: **blocked for acceptance of runtime quality** —
  source was inspected and Anvien file-detail/impact evidence is current; it
  confirms state orchestration and metadata selection, not worker execution.
- `.p2p/system/p2p_capabilities/context.py`: **partial/unbound** — the source
  provides pointer metadata and stale/unknown filtering, but no content-section
  load or worker binding.
- `.p2p/system/p2p_capabilities/routing.py`: **partial/unbound** — readiness
  and AESTHETICA fallback are explicit, but the main workflow does not consume
  one unified capability/permission/budget preflight.
- `.p2p/system/p2p_capabilities/decision_trace.py`: **clear for its scoped
  invariant** — DT1–DT24 PASS and the trace remains a ledger projection; it
  does not prove worker quality.
- `governance/approval-policy.json`: **clear for its scoped invariant** —
  protected actions and approval gates remain separate from intent; this does
  not close the missing effect-authority vector.
- Production source changes: **none**. The audit-created files are fixtures,
  eval/report artifacts, and planner records.

## Evidence Checked

Passed:

- Official `.15` VERSION files and ZIP SHA-256 match the supplied baseline.
- Current Anvien graph refresh, workflow file-detail, and no source changes.
- `python -m unittest discover -s tests -p 'test_*.py'`: 76/76 PASS.
- Decision Trace DT1–DT24: PASS.
- Governance drift: PASS.
- Capability doctor: PASS with AESTHETICA resolved but not executable or
  identity-verified; canonical denominator 8 and full quorum 8/8.
- Audit suite v2 validate and gate: PASS for the structural proxy.
- Secret scans of `.p2p/system` and `scripts`: PASS.
- Fixture/evidence/suite JSON parse and SHA-256 checks: PASS.

Verification freshness: fresh for the current reviewed state; Anvien was
refreshed after audit artifacts were written, and `changedSinceAnalyze` is
false for the inspected workflow source.

Failed:

- `scripts/doctor.py --package .`: FAIL on missing root UI/UX and capability
  runtime payload groups.
- Whole-repository secret scan: FAIL with five existing documentation/example
  findings.
- Workflow bootstrap: BLOCKED on the installed eval-helper CLI mismatch.
- Final Anvien `detect-changes --scope all --json`: unable to run because Git
  diff exited 129; the workspace is not a Git repository. No commit/diff claim
  is accepted.

Verification freshness: current audit run; failures were preserved rather than
converted into PASS.

Not run:

- Real provider/child-worker A/B execution: unavailable in the host/runtime.
- Host input/cache/output token telemetry, raw tool-output volume, provider
  calls/cost, duplicate retrieval, and model wall time: not exposed; correctly
  recorded UNKNOWN/UNAVAILABLE.
- Release gate/final approval: not applicable because no release candidate was
  created.

## Invariant Closure

- affected invariant: quality-first context efficiency with equivalent A/B
  acceptance, evidence, safety, and project-state integrity.
- sibling surfaces checked: workflow entry/bootstrap, eval helper candidates,
  capsule writer, context pointers, capability routing/readiness, trust,
  Decision Trace, approval policy, project eval v2, package doctor, secret
  scans, and canonical quorum.
- residual unverified same-invariant surfaces: real worker/provider execution,
  host telemetry, worker return contract, and independent blinded quality review
  remain open.

## Required Fix List For Resubmission

1. Resolve the workflow/eval-helper boundary in a separate scoped Goal without
   modifying official `.15`.
2. Expose or truthfully capture an equivalent real A/B execution surface with
   the same fixtures, permissions, capabilities, and acceptance criteria.
3. Record worker return/evidence as a compact delta over existing authoritative
   ledgers; preserve failures, blockers, and missing evidence.
4. Run two isolated trials per condition for C1–C12 and have an independent
   blinded review score Q1–Q12 before claiming non-inferiority.
5. Re-run package/security/canonical validation and retain the exact official
   `.15` hash; do not create `.16` automatically.

## Overall Evaluation

The audit artifacts are useful and honest: they prove the current control
surfaces, a deterministic contract-level byte proxy, and several concrete
integration gaps. They do not prove the requested product/runtime outcome.
The correct supervisor result is REJECT for completion of the full audit claim,
with the Goal terminal state BLOCKED. No runtime change, release, scheduler,
worker pool, new router, or AESTHETICA research was authorized or performed.
