# P2P-C15 Bounded Foreground Delegation & Worker Handoff Controller Evidence Ledger

## Metadata

- Date: `2026-08-15`
- Plan: `docs/plans/2026-08-15-p2p-c15-bounded-foreground-delegation/2026-08-15-p2p-c15-bounded-foreground-delegation-plan.md`
- Evidence: `docs/plans/2026-08-15-p2p-c15-bounded-foreground-delegation/2026-08-15-p2p-c15-bounded-foreground-delegation-evidence.md`
- Benchmark: `docs/plans/2026-08-15-p2p-c15-bounded-foreground-delegation/2026-08-15-p2p-c15-bounded-foreground-delegation-benchmark.md`
- Actual status: `docs/plans/2026-08-15-p2p-c15-bounded-foreground-delegation/2026-08-15-p2p-c15-bounded-foreground-delegation-actual-status.md`

## Evidence Rules

Evidence IDs are stable and phase-scoped. Source inspection, graph/impact output, runtime behavior, tests, package validation, and protection checks are recorded as they occur. Test output is evidence only when it proves trigger -> processing -> observable result at the nearest real boundary. Long numeric measurements belong in the benchmark ledger.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-SRC1`: Attached user brief `C:\Users\Admin\.codex\attachments\4187463e-2c8b-4e69-bea6-3558b45fb371\pasted-text.txt`, read as the C15 authority; it requires DIRECT/DELEGATE/BLOCKED, one child/depth one, child subset permissions/scope, parent verification, explicit UNKNOWN identity, bounded retries, and preservation of `.19`, C08, C09, canonical eight.
- `E0-P0A-SRC2`: C11 source and plan inspection show durable task state, preflight, transitions, checkpoint/resume, dependency handoff without automatic start, and existing ledger/completion gates; no worker or scheduler path exists.
- `E0-P0A-SRC3`: C12 source and plan inspection show direct-only finite foreground execution, existing `ExecutionBudget`, `ExecutionIntent`, `ActionResult`, `VerificationResult`, artifact receipts, and no worker/background/queue/remote executor.
- `E0-P0A-SRC4`: Package/doctor source inspection shows the runtime module and script allowlists that must be extended only for the new C15 module/CLI.
- `E0-P0A-GRAPH1`: `anvien analyze D:\AI\P2P_dev\P2P-8.4.6-C-Codex-Edition-v4 --force --skip-git` PASS; graph refreshed with 359 files scanned, 36 parsed code files, 0 failed, 13,755 nodes, 15,608 relationships, and 36 unresolved references in the root projection.
- `E0-P0A-GRAPH2`: `anvien file-detail p2p_capabilities/foreground_execution.py --repo p2p-system --json --format compact` reports parsed/stale=false, 197 symbols, 35 outbound, 360 local relationships, 876 unresolved, 34 linked flows, risk `high`; related source is `task_state.py`.
- `E0-P0A-GRAPH3`: `anvien file-detail p2p_capabilities/task_state.py --repo p2p-system --json --format compact` reports parsed/stale=false, 249 symbols, 35 inbound, 432 local relationships, 965 unresolved, 70 linked flows, risk `high`.
- `E0-P0A-IMPACT1`: `anvien impact symbol ExecutionBudget --repo p2p-system --direction upstream --depth 1 --include-tests --json` reports risk `CRITICAL`, impacted count 5, one affected module, five affected processes; this is a scope warning, not a prohibition.
- `E0-P0A-IMPACT2`: `anvien impact symbol ExecutionIntent --repo p2p-system --direction upstream --depth 1 --include-tests --json` reports risk `HIGH`, impacted count 7, one affected module, three affected processes.
- `E0-P0A-IMPACT3`: `anvien impact symbol _foundation_required_paths --repo P2P-8.4.6-C-Codex-Edition-v4 --direction upstream --depth 1 --include-tests --json` reports risk `CRITICAL`, impacted count 2, one affected module, eight affected processes.
- `E0-P0A-GRAPH4`: `anvien file-detail scripts/p2p_foreground_execution.py --repo P2P-8.4.6-C-Codex-Edition-v4 --json --format compact` reports parsed/stale=false, 28 symbols, 7 local relationships, 130 unresolved references, risk `high`.
- `E0-P0A-GRAPH5`: `anvien file-detail scripts/package_release.py --repo P2P-8.4.6-C-Codex-Edition-v4 --json --format compact` reports parsed/stale=false, 62 symbols, 33 local relationships, 271 unresolved references, 8 linked flows, risk `high`.
- `E0-P0A-GRAPH6`: `anvien file-detail p2p_capabilities/__init__.py --repo p2p-system --json --format compact` reports parsed/stale=false, no symbols/relationships, risk `low`; it is an additive export surface.
- `E0-P0A-SRC5`: `Get-FileHash D:\AI\P2P_dev\P2P-8.4.7-C-Codex-Edition-v19.zip -Algorithm SHA256` matches user-supplied `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`; `.git` is absent.
- `E0-P0A-REG1`: Existing focused C11/C12 tests cover durable task state and direct foreground execution; C15 delegation behavior is missing and requires a new focused suite.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`, `P1-C`

- `E1-P1A-SRC1`: Added `.p2p/system/p2p_capabilities/bounded_delegation.py` as an additive C11/C12 adapter with typed strategy, permission, budget, request, handoff, result, and fingerprint contracts. Direct C12 source remains unchanged.
- `E1-P1A-IMPACT1`: Refreshed system Anvien file detail for `bounded_delegation.py`: parsed/stale=false, 268 symbols, 590 local relationships, 797 unresolved references, 56 outbound, 29 linked flows, risk `high`. The blast radius is isolated to the new module plus explicit exports/package/doctor surfaces.
- `E1-P1A-TEST1`: `python -m unittest tests.test_p2p_bounded_delegation -v` PASS, 23 tests; covers DIRECT-first, material-value DELEGATE, blocked gates, subset/fingerprint stability, UNKNOWN identity, retry and mutation boundaries, and the mutation owner gate.
- `E1-P1A-CONTRACT1`: The handoff fingerprint excludes only the random handoff identifier from its canonical hash, so equivalent task/candidate/context/permission contracts produce the same fingerprint while candidate changes produce a different fingerprint. Optional preflight/context maps normalize `None` to empty objects without widening permissions.
- `E1-P1B-EXEC1`: Callback-backed execution writes the bounded handoff/result/checkpoint artifacts under `.p2p/state/foreground-executions/delegations/`, enforces one child/depth one/no-grandchild, and keeps child output proposal-only.
- `E1-P1B-VERIFY1`: Focused C15 parent-verification tests PASS for `DONE` only after current candidate binding plus C10 EvidenceClaim; missing/failed verification remains non-DONE; uncertain mutation returns `UNKNOWN`/`NEEDS_RECHECK` and suppresses direct fallback.
- `E1-P1B-TRACE1`: C15 material strategy rationale is recorded through existing `p2p_capabilities.decision_trace`/Execution Ledger; no second ledger was introduced.
- `E1-P1C-CLI1`: `python scripts/p2p_delegation.py --help` PASS and thin CLI test PASS; no child spawn/shell/network/model/profile control is exposed.
- `E1-P1C-REG1`: `python -B -m unittest tests.test_p2p_bounded_delegation tests.test_p2p_task_state tests.test_p2p_foreground_execution` PASS after the contract refinement; 63 tests.
- `E1-P1C-GRAPH1`: Post-edit Anvien refresh PASS: root 364 scanned/37 parsed code/0 failed/14,077 nodes/16,025 relationships; system 50 scanned/40 parsed code/0 failed/8,345 nodes/11,326 relationships.
- `E1-P1C-DETECT1`: `anvien detect-changes --repo P2P-8.4.6-C-Codex-Edition-v4 --scope all` and the matching `p2p-system` command return `Git diff failed: exit status 129` because `.git` is absent; no repository was initialized.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

- `E2-P2A-REG1`: `python -B -m unittest tests.test_p2p_bounded_delegation` PASS, 23 focused C15 tests; `python -B -m unittest tests.test_p2p_bounded_delegation tests.test_p2p_task_state tests.test_p2p_foreground_execution` PASS, 63 tests; `python -m unittest discover -s tests -v` PASS, 198 tests. C15 tests use isolated repo-local temporary roots for task-state fixtures.
- `E2-P2A-EVAL1`: Existing schema-v2 beginner/UIUX paired suite validation and gate PASS: 5 cases, 2 baseline and 2 P2P trials per case, baseline mean 1.0, P2P mean 1.0, delta 0.0, P2P pass rate 1.0, zero case regressions, zero score spread.
- `E2-P2A-DT1`: Native decision-trace evaluation PASS, DT1-DT24 24/24; canonical denominator 8, full quorum 8/8, Aesthetica noncanonical, external dependencies empty, protected hashes unchanged.
- `E2-P2B-DOCTOR1`: Development doctor PASS with `--root . --role development`; UI/UX runtime doctor PASS; capability doctor PASS with canonical 8/8 and no simulated identity; runtime secret scan PASS with empty findings.
- `E2-P2B-GOV1`: `p2p_governance.py prepare-live --governance governance --as-of 2026-08-16` PASS technical preview/user approval required; no Live Specs promotion performed. Initial `lock-runtime` PASS with 832 protected files and 2 virtual hashes; final closure refresh PASS with 833 protected files and 2 virtual hashes; governance drift PASS.
- `E2-P2B-PKG1`: `scripts/package_release.py ... build` PASS for unpromoted candidate `D:\AI\P2P_dev\P2P-8.4.6-C-Codex-Edition-v4\.tmp\p2p-c15\candidates\P2P-8.4.7-C-Codex-Edition-v15-c15-candidate.zip`, version `8.4.7-C-codex.15`, SHA-256 `ae39b78972c03ca17855e0cc86e18fbd997f1eb4d62116e909674abc86d90b1e`, size 2,485,657 bytes. Internal build verification and clean extracted verify PASS: 408 files, 409 checksums; portable doctor PASS.
- `E2-P2B-PROTECT1`: Official artifact `D:\AI\P2P_dev\P2P-8.4.7-C-Codex-Edition-v19.zip` rechecked as `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`; unchanged and not overwritten/promoted.
- `E2-P2C-ANVIEN1`: Final graph refresh PASS: root 365 scanned/38 parsed code/0 failed/14,308 nodes/16,290 relationships; system 50 scanned/40 parsed code/0 failed/8,370 nodes/11,378 relationships. Final C15 file detail: 280 symbols, 605 local relationships, 817 unresolved references, 59 outbound, 32 linked flows, high warning, stale=false. Package impact MEDIUM; doctor impact HIGH; warnings are scoped, not prohibitions.
- `E2-P2C-DETECT1`: Final root and `p2p-system` Anvien `detect-changes --scope all` both return `Git diff failed: exit status 129`; `.git` is absent and no repository was initialized.
- `E2-P2C-HOST1`: Live disposable generic child probe not run because no repository-level callable host callback binding is available; no worker/identity receipt was simulated. C15 reports host-unavailable/UNKNOWN in that condition.

## E2 - P2 Current C15 Follow-up Evidence (2026-08-16)

- `E2-P2C-FIX1`: A fresh affected run exposed one real regression in
  `test_handoff_fingerprint_is_stable_when_only_handoff_id_changes`: the
  handoff fingerprint still inherited volatile plan/preflight identity. The
  bounded fix adds `_plan_contract_fingerprint` for immutable semantic task
  inputs and removes `decided_at` from the decision-trace identity. The test
  now passes repeatedly in isolated fresh roots.
- `E2-P2C-REG2`: Current focused C15 suite is `24/24 PASS`; the affected
  C15+C11+C12 slice is `64/64 PASS`; the full repository suite is `218/218
  PASS` (`python -B -m unittest discover -s tests`).
- `E2-P2C-FIELD1`: Reusable project-style field harness
  `scripts/p2p_c15_field_test.py` reports A-F `all_checks_pass=true` using real
  C11 task state, C15 controller, filesystem artifacts, and parent evidence.
  Fresh JSON `.tmp/p2p-c15-field-test-20260816.json` has SHA-256
  `69fa8143c065d6960ec0ae4540aabcbc0ad8f4df8bffd05011ed024023437dc0`.
- `E2-P2C-EVAL18`: The 18-case C15 matrix in
  `2026-08-16-p2p-c15-eval-matrix.md` is fully mapped to focused runtime tests
  and field A-F observations; all 18 cases are `PASS`.
- `E2-P2C-ANVIEN2`: Fresh root/system Anvien analysis has zero parse failures.
  Current C15 file detail is `stale=false`, 283 symbols, 607 local
  relationships, 832 unresolved references, and high file warning. File-level
  impact reports 69 contained/impacted symbols. The two edited method names
  are not resolved by the current graph index; that is recorded as an index
  limitation rather than zero impact.
- `E2-P2C-DETECT2`: Fresh `anvien detect-changes` returns Git exit 129 because
  the project has no `.git`; no repository was initialized and no commit is
  claimed.
- `E2-P2C-GOV2`: Fresh development doctor and governance drift are not clean
  because the existing protected file
  `docs/notes_decisions_log/notes_decisions_log_20260816.md` is drifted. The
  C15 runtime, canonical 8/8, package metadata `.15`, installed foundation,
  and decision-trace checks pass; the protected notes log was not changed,
  deleted, suppressed, or repaired in this C15 follow-up.
- `E2-P2C-PKG2`: A fresh package build is intentionally blocked by the existing
  lineage guard: development source `8.4.7-C-codex.15` is below promoted
  baseline `8.4.7-C-codex.19`. No metadata promotion, package overwrite, or
  release was attempted. The prior `.15` candidate remains unpromoted and is
  not claimed to contain this follow-up.
- `E2-P2C-HOST2`: Current Codex host exposed a real `multi_agent_v1` surface.
  Exactly one read-only subagent completed with receipt
  `01a008ca-1c74-7592-a316-4e45894027ce` (`Lagrange`). The proposal reports no
  edits, network, subprocess, background, parallel, grandchild, Logistics, or
  DONE claim. This proves a real generic host subagent surface, not a C15
  native callback integration.
- `E2-P2C-CONTROL2`: Fresh direct control and bad-result controls are `3/3
  PASS`; fresh project-style A-F field checks remain `all_checks_pass=true`.
  The local C15 foundation is still PASS.
- `E2-P2C-LINEAGE2`: Content comparison against official `.19` maps 403
  entries, with 390 byte-identical entries and 13 mismatches. Shared C10-C12
  files match; official `.19` contains no C15 bounded-delegation module or CLI.
  Classification is `CANONICAL .19 + C15 DELTA = NOT_PROVEN`.

## Closure Evidence

- `E3-SUPERVISOR1`: `reports/supervisor/rp_supervisor_260816_003300_by_gpt-5-codex_p2p-c15-bounded-foreground-delegation.md` independently reviews source, tests, package candidate, governance lock/drift, protected artifact, and Anvien output; verdict `PASS`.
- `E3-SUPERVISOR2`: Final closure re-review `reports/supervisor/rp_supervisor_260816_003700_by_gpt-5-codex_p2p-c15-bounded-foreground-delegation.md` verifies the final P2/Pn plan/status/evidence/benchmark state after documentation-only closure updates; verdict `PASS`.
- `E3-SUPERVISOR3`: Final governance-lock closure review `reports/supervisor/rp_supervisor_260816_004000_by_gpt-5-codex_p2p-c15-bounded-foreground-delegation.md` rechecks the 833-file runtime lock, development/portable/capability doctors, governance drift, secret scan, regression/package evidence, and official-artifact immutability; verdict `PASS`.
- `E3-SUPERVISOR4`: Fresh independent review
  `reports/supervisor/rp_supervisor_260816_092000_by_gpt-5-codex_p2p-c15-current-fix.md`
  inspects the fingerprint correction, field harness, 18-case matrix, current
  24/64/218 regression, Anvien impact, governance/lineage boundaries, and
  official artifact hash; verdict `PASS / BOUNDED_DELEGATION_FOUNDATION_READY`.
- `E3-SUPERVISOR5`: Fresh hardening review
  `reports/supervisor/rp_supervisor_260816_112735_by_gpt-5-codex_p2p-c15-hardening.md`
  independently accepts the generic host receipt and local controls but
  rejects the stronger claim of C15 real-host end-to-end proof and canonical
  `.19 + C15` integration safety. Verdict `REJECT`; C16 remains unopened.
- `E3-CLEANUP1`: Plan-created temporary outputs are quarantined under repo-local `.tmp/p2p-c15/` (candidate ZIP, clean extraction, governance preview, decision-trace outputs, and disposable verification roots); no dead production helper or stale source fallback remains. No broad deletion was performed.
- `E3-CLOSE1`: Final plan/status/benchmark/evidence/coder/supervisor reports are self-contained; no Git commit was created because `.git` is absent. Terminal status is `PASS` for `BOUNDED_DELEGATION_FOUNDATION_READY`, with live host callback/identity, existing protected notes-log drift, stale `.15` package lineage, and C09/C08 explicitly outside the certified scope.
