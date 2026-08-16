# P2P Native Decision Trace - Governance Reference Normalization Evidence Ledger

## Metadata

- Date: `2026-08-13`
- Plan: `docs/plans/2026-08-13-p2p-native-decision-trace-governance-reference-normalization/2026-08-13-p2p-native-decision-trace-governance-reference-normalization-plan.md`
- Evidence: `docs/plans/2026-08-13-p2p-native-decision-trace-governance-reference-normalization/2026-08-13-p2p-native-decision-trace-governance-reference-normalization-evidence.md`
- Benchmark: `docs/plans/2026-08-13-p2p-native-decision-trace-governance-reference-normalization/2026-08-13-p2p-native-decision-trace-governance-reference-normalization-benchmark.md`
- Actual status: `docs/plans/2026-08-13-p2p-native-decision-trace-governance-reference-normalization/2026-08-13-p2p-native-decision-trace-governance-reference-normalization-actual-status.md`

## Evidence Rules

- Evidence is fresh, command-backed, and scoped to this surgical Goal.
- Source inspection is not a substitute for runtime evidence.
- Valid references must resolve to exact files in governed roots.
- Deliberately invalid references must remain `MISSING_REFERENCE`.
- Historical trace bytes and the .5 artifact are immutable authorities.
- Temporary fixture writes stay under `.tmp`; user paths are preserve-only.
- No Git metadata exists; hashes, reports, and Anvien evidence are the local
  audit trail.

## E0 - P0 Evidence

Matching plan item: P0-A.

- E0-P0A-AUTH1: Approved `P2P-DECISION-TRACE-SPEC.md` and approved Capability
  Foundation/Execution/Trust SPECs were read. They require bounded read-only
  resolution, explicit missing/stale status, historical compatibility, safe
  export, exact canonical eight, and no external dependency.
- E0-P0A-BASE1: root `VERSION` and `.p2p/system/VERSION` are
  `8.4.7-C-codex.5`. Protected ZIP:
  `D:\AI\P2P_dev\P2P-8.4.7-C-Codex-Edition-v5.zip`; size 2,329,263 bytes;
  SHA-256 `f88dbf706c4ac85a8aadf38960923cdc8e4ba6e415b83f3f1726692fb3ad8dda`.
- E0-P0A-REPRO1: fresh .5 WHY reproduction returns 9 PRESENT links and exactly
  2 `MISSING_REFERENCE` links; query status is `PARTIAL`.
- E0-P0A-CASE1: value `approval-policy.json`; type `POLICY_REFS`; emitter
  `scripts/p2p_workflow.py` capture call line 1529 and policy list line 1541;
  expected `.p2p/system/governance/approval-policy.json`; actual lookup
  `<fresh-project>\approval-policy.json`; failure because resolver joins only
  project root and does not search governed policy roots.
- E0-P0A-CASE2: value `drift-policy.json`; type `POLICY_REFS`; emitter
  `scripts/p2p_workflow.py` capture call line 1529 and policy list line 1541;
  expected `.p2p/system/governance/drift-policy.json`; actual lookup
  `<fresh-project>\drift-policy.json`; same concrete failure.
- E0-P0A-ROOT1: filesystem read confirms both expected files exist under the
  installed `.p2p/system/governance` directory; root and project governance
  lookups are false.
- E0-P0A-EMIT1: workflow passes bare logical names only when a governed
  governance directory exists; current trace storage preserves them unchanged.
- E0-P0A-RESOLVE1: runtime `_governance_roots` knows governed roots, but the
  catalog does not index arbitrary policy files and `_resolve_reference` falls
  through to only `root / ref`.
- E0-P0A-IMPACT1: Anvien analyzed 191 files, 76 dependency edges, 8,699 graph
  nodes. Workflow is a high-risk hotspot with 143 local relationships and 36
  inbound references; it is inspect-only for this fix. The native runtime
  source is `.p2p/system/p2p_capabilities/decision_trace.py`.
- E0-P0A-BOUNDARY1: .5 ZIP, App Game Truyen, Logistics, and real user-project
  paths are preserve-only; no user project was modified in P0.
- E0-P0A-ROOTCAUSE1: root cause is narrowly classified as bare policy filename
  emitted by capture plus resolver interpretation as project-root path instead
  of governed policy-root reference. Windows separators, case, URI prefix,
  versioned location, and manifest indirection are not implicated by evidence.
- E0-P0A-STATUS1: P0 complete; P1-A is unblocked and edits only the native
  POLICY_REFS capture/resolve family, followed by direct tests.

## E1 - P1 Evidence

- E1-P1A-NORM1: staged and source probes pass. Bare
  `approval-policy.json` and Windows-separated `governance\\drift-policy.json`
  are stored as `governance/approval-policy.json` and
  `governance/drift-policy.json`; exact governed files resolve `PRESENT`.
- E1-P1A-COMPAT1: legacy trace simulation with bare
  `approval-policy.json` remains readable and resolves `PRESENT` with
  `NORMALIZED_REF=governance/approval-policy.json`; no old ledger line is
  rewritten by query.
- E1-P1B-NEG1: focused unittest
  `P2PDecisionTraceTests.test_policy_references_normalize_resolve_and_fail_honestly`
  passes. A deliberate `governance/does-not-exist.json` remains
  `MISSING_REFERENCE`; an absolute machine path is rejected by the capture
  boundary. The test also asserts no project-root path leak in query output.
- E1-P1B-PORT1: focused workflow and relationship tests pass. Native DT1-DT24
  evaluator reports `24/24 PASS`, baseline gap confirmed, canonical denominator
  `8`, full quorum `8/8`, Aesthetica noncanonical, and no external dependency.
  Protected hashes remain unchanged. `anvien detect-changes` reports the target
  is not a Git repository; commit evidence is `N/A`.
- E1-P1B-SRC1: changed production source is only
  `.p2p/system/p2p_capabilities/decision_trace.py`; changed direct test is
  `tests/test_p2p_decision_trace.py`. The workflow emitter, CLI wrapper,
  schema, ledger format, governance files, and .5 artifact remain untouched.

P1 decision: PASS. The smallest compatible rule is implemented at the native
capture/resolve boundary, so old workflow input remains compatible while new
records use a portable logical form.

## E2 - P2 Evidence

- E2-P2A-ARTIFACT1: Because the shipped runtime behavior changed, the next
  release was built under the existing version policy as
  `8.4.7-C-codex.6`. Artifact:
  `D:\\AI\\P2P_dev\\P2P-8.4.7-C-Codex-Edition-v6.zip`; size `2,336,913`
  bytes; SHA-256
  `b8689fb812a438f379fc1d84353f2e4e4c9c0c234c1e22539b2bc32fd15b8156`;
  ZIP member count `399`, packaged file count `397`, checksum count `398`.
  The protected `.5` artifact was rehashed unchanged at
  `f88dbf706c4ac85a8aadf38960923cdc8e4ba6e415b83f3f1726692fb3ad8dda` and
  `2,329,263` bytes.
- E2-P2A-DOCTOR1: Pristine extraction checks pass: package `verify`, package
  doctor `RESULT: PASS`, governance drift `PASS`, Capability Foundation
  doctor `PASS`, UIUX installed evaluator `DW1-DW18 PASS`, secret scan
  `PASS`, and direct ZIP boundary scan `399` members / `0` forbidden or
  transient members. Package doctor emitted only the existing non-blocking
  Aesthetica sandbox warning; it did not simulate identity and returned
  `RESULT: PASS`.
- E2-P2B-FRESH1: Fresh installation of `.6` into an isolated `new-project`
  fixture returned `FRESH_INSTALL` and `RESULT: PASS`. Repeating the exact
  architecture workflow produced `11` resolved links, including
  `governance/approval-policy.json` and `governance/drift-policy.json`, with
  query status `PASS`, integrity `VERIFIED`, and no missing policy link.
  Beginner WHY is plain language and contains no machine path.
- E2-P2B-UPGRADE1: An isolated copy of the verified `.5` fixture upgraded as
  `UPGRADE_FROM_8.4.7-C-codex.5` to `.6`. The historical ledger hash remained
  `2F643D028AA56751DA3D14065CB5BB2E74EFA833FE8BADBD57D0525A1BD00AF6`, the
  trace count remained `1`, and the old bare policy refs remained unchanged
  in the historical trace while resolving `PRESENT` with
  `NORMALIZED_REF=governance/...`.
- E2-P2B-REINSTALL1: Same-version reinstall returned
  `SAME_VERSION_REINSTALL`. Ledger hash, trace count, policy hashes, and
  backup count remained unchanged (`1` existing backup; no new backup), with
  `RESULT: PASS`.
- E2-P2C-PORTNEG1: WSL/POSIX query of the fresh installed fixture returned
  `PASS` and both policy refs `PRESENT`. A Windows-separator capture/query
  also returned `PRESENT` with normalized `governance/drift-policy.json`.
  A deliberately invalid `governance/does-not-exist.json` returned
  `MISSING_REFERENCE` and query `PARTIAL`; no fuzzy or nearest-file fallback
  occurred.
- E2-P2C-REGRESS1: Full unittest discovery passed `49/49`. Native DT1-DT24
  evaluator passed `24/24`; installed Decision Trace doctor passed; temporal
  reconstruction, supersession, contradiction, artifact reverse lookup,
  approval, FACT/RAG trust, Foundation, UIUX, canonical quorum, and
  installer lifecycle regressions passed. External dependency list is empty;
  redaction/secret scans are clean; the `.5` artifact and real user-project
  boundaries were preserved.
- E2-P2C-NEXT1: Exactly one residual-risk recommendation is produced from
  fresh evidence: separately verify real `p2p_aesthetica` execution identity
  when a real profile/execution proof exists. It remains optional,
  noncanonical, and is not simulated in this Goal. No other residual-risk
  recommendation is opened.

## Closure Evidence

- E3-P3A-SUPERVISOR1: Independent supervisor report
  `reports/supervisor/rp_supervisor_260813_091004_by_gpt-5-codex_p2p-native-decision-trace-governance-reference-normalization.md`
  is `PASS`. It reran the focused source tests (`3/3`), release lifecycle
  tests (`2/2`), full regression (`49/49`), fresh/legacy/invalid queries,
  artifact boundary checks, and fresh Anvien topology analysis.
- E3-P3A-RN1-RN20: RN1-RN20 are all PASS. The proof covers both sides of the
  contract: valid refs resolve (`2/2` in fresh WHY and `2/2` in legacy query),
  while a deliberate invalid ref remains `MISSING_REFERENCE` with query
  `PARTIAL`.
- E3-P3A-BOUNDARY1: `.5` SHA-256 and size remain exact; candidate ZIP has no
  forbidden/transient members; no App Game Truyen, Logistics, or real user
  project path was modified. The target has no Git metadata; commit is `N/A`.
- E3-P3A-NEXT1: exactly one residual-risk recommendation remains from fresh
  evidence: verify real `p2p_aesthetica` execution identity in a separate
  Goal when real execution proof exists. It remains optional/noncanonical and
  is not simulated. No other next recommendation is opened.
- E3-P3A-CLOSE1: supervisor accepted the source, candidate package,
  lifecycle, portability, negative honesty, temporal/supersession/
  contradiction, redaction/security, Foundation/UIUX, and canonical 8/8
  surfaces. Stop rule is satisfied.
