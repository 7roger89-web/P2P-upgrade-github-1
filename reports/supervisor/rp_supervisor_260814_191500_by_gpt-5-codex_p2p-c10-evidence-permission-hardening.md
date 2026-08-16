# Supervisor Report: P2P-C10 Evidence Authority and Permission Hardening

Verdict: PASS

## Metadata

- Report file: `reports/supervisor/rp_supervisor_260814_191500_by_gpt-5-codex_p2p-c10-evidence-permission-hardening.md`
- Review time: `2026-08-14 19:15:00 Asia/Saigon`
- Reviewer: `gpt-5-codex`
- Repo/project: `P2P-8.4.6-C-Codex-Edition-v4`
- Scope reviewed: current C10 worktree, source/runtime contracts, direct tests, full regression, governance, package candidate `.20`, and preserved C09/artifact state
- Claim reviewed: `EVIDENCE_PERMISSION_FOUNDATION_HARDENED` for the bounded C10 scope
- Authority used: latest user request, `AGENTS.md`, C10 plan/spec cluster, existing FACT_LEDGER/Live Specs/Decision Trace/Context/Execution Ledger contracts, source, runtime receipts, tests, and current gate outputs
- Related artifacts: C10 plan/evidence/benchmark/actual-status files; candidate `.20`; final Decision Trace report; final governance drift report

## Executive Summary

- Problem: material evidence claims and the bounded live trial had narrow fail-open gaps around provenance, freshness/binding, approval subject binding, permission separation, and secret-safe projection.
- Decision: PASS. The reviewed source closes those gaps with small extensions to existing contracts and preserves existing authority stores, C09 uncertainty, canonical 8/8 safety, and protected artifact hashes.
- Required outcome: accepted for this Goal only. No release, promotion, C08 rerun, official host claim, orchestration, or second truth store is authorized by this review.

## Blocking Findings

None.

## Source-Level Clearance Notes

- `.p2p/system/p2p_capabilities/evidence.py`: clear. Lines 75-94 project only bounded reference metadata and redact secret-like values; lines 108-143 bind `VERIFIED` evidence to source, time, freshness, scope, fingerprint, and required references, downgrading invalid claims to `INCOMPLETE`.
- `.p2p/system/p2p_capabilities/trust.py`: clear. Lines 50-80 keep retrieved/model/tool/specialist content non-canonical and require a structured approval reference with matching subject, SHA-256, approved state, and approve decision for protected claims.
- `.p2p/system/p2p_capabilities/live_execution.py`: clear. Lines 57-72 define the explicit action envelope; lines 272-326 fix the bounded read-only request and reject unauthorized values; lines 329-344 bind guardrails; lines 698-702 reject unproven host permission modes; lines 767-858 preserve the existing trial/receipt/ledger path while recording requested/observed permission state.
- `.p2p/system/p2p_uiux/security.py`: clear. Lines 7-14 retain real token detection and exclude only the proven all-`x` documentation placeholder; the focused test proves both behaviors.
- Direct tests: clear. The new security test is isolated and uses the existing scanner; no second evaluator or persistence store was introduced.

## Evidence Checked

Passed:

- Fresh Anvien root graph: `323` scanned, `31` parsed code, `12,004` nodes, `13,648` relationships.
- Fresh Anvien runtime graph: `44` files, `36` parsed code, `4,217` nodes, `5,043` relationships.
- Focused foundation: `28/28`; combined evidence/live/host/beginner: `57/57`; final full discovery: `119/119` in `118.001s`.
- Decision Trace evaluation: `DT1-DT24 = 24/24 PASS`; canonical identities exactly eight, denominator `8`, quorum `8/8`, Aesthetica noncanonical.
- Governance drift: PASS; Capability Foundation doctor: PASS; development doctor: PASS; source secret scan: PASS.
- Candidate package build, verify, portable doctor, capability doctor, and package secret scan: PASS; extracted package baseline inventory: `152/152`.
- Candidate `.20` contains the reviewed runtime changes and is hash-bound by the package manifest.
- Official `.15` and existing `.18` SHA-256 values were independently rechecked unchanged.

Failed:

- None in the final reviewed state.

Not run / intentionally not used as proof:

- Official host execution was not claimed; C09 remains `BLOCKED / EVENT_EVIDENCE_UNAVAILABLE`.
- `anvien detect-changes` could not produce a diff because the workspace has no `.git`; no Git repository was initialized and no commit is claimed.
- The legacy `.p2p/evals/rag-retrieval-check.json` is schema v1 and fails the current v2 validator; it was not used as a C10 PASS. Current v2 project and context-efficiency suites validate PASS.
- No release/deployment gate or owner release approval was run because release was explicitly out of scope.

## Invariant Closure

- Affected invariant: evidence authority/provenance, stale binding, protected-fact approval, requirement/evidence scope, bounded read-only permission, secret safety, and candidate/package integrity.
- Sibling surfaces checked: existing FACT_LEDGER/Live Specs, approval and drift governance, Decision Trace/Execution Ledger, context contracts, capability registry/doctor, host receipt path, package builder, package doctor, secret scanner, direct tests, full suite, and candidate extraction.
- Residual unverified same-invariant surfaces: none for the bounded local contracts reviewed. Official host permission/identity remains intentionally unknown rather than inferred.
- History closure: contradiction and supersession behavior remains in the existing Decision Trace/ledger tests; no historical record deletion or second history store was introduced.

## Overall Evaluation

The implementation is accepted for `EVIDENCE_PERMISSION_FOUNDATION_HARDENED`. The evidence quality is current and direct for local contracts, the implementation is present in the unpromoted candidate, and the affected invariant is closed without architecture expansion. The PASS does not imply C08/C09 recovery, unattended execution, release approval, or durable orchestration.
