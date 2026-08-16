# P2P-C10 Evidence Authority and Permission Hardening Actual Status

Title: P2P-C10 Evidence Authority and Permission Hardening
Date: 2026-08-14
Status: P2 Complete — PASS
Companion plan: `docs/plans/2026-08-14-p2p-c10-evidence-authority-permission-hardening/2026-08-14-p2p-c10-evidence-authority-permission-hardening-plan.md`
Companion evidence: `docs/plans/2026-08-14-p2p-c10-evidence-authority-permission-hardening/2026-08-14-p2p-c10-evidence-authority-permission-hardening-evidence.md`
Companion benchmark: `docs/plans/2026-08-14-p2p-c10-evidence-authority-permission-hardening/2026-08-14-p2p-c10-evidence-authority-permission-hardening-benchmark.md`

## Purpose

This is the living current-state record for the bounded C10 hardening. It does not replace the evidence ledger or authorize promotion.

## Scope

Target scope: existing evidence provenance validation and existing read-only live execution permission binding.

Out of scope: FACT_LEDGER/Live Specs promotion, C09/C08, router/quorum, host hook, release, deployment, external I/O, memory, and orchestration.

## Evidence Architecture Map

| Existing structure | Writers | Readers | Authority / freshness | Conflict behavior | Links / current gap |
|--------------------|---------|---------|-----------------------|-------------------|--------------------|
| `governance/fact-ledger.json` (FACT_LEDGER) | governance workflow plus explicit owner-approved changes | Live Specs builder, doctor, drift, runtime eligibility checks | canonical project fact source; `checked_at`/`expires_at` and verification status | stale/ineligible claims are excluded; protected changes require approval | approval record, preview, Live Specs; no second fact store |
| `governance/live-specs.json` (Live Specs) | deterministic projection from FACT_LEDGER | runtime routing/readiness and gates | derived, hash-bound, expiry-aware projection | regeneration/drift detects mismatch | FACT_LEDGER and runtime lock; preserve-only in C10 |
| `EvidenceClaim` / `FactClaim` | callers, workflows, tests, existing runtime contracts | `evaluate_done`, trust boundary, direct consumers | evidence origin plus explicit binding/approval metadata; current/fresh evidence only for `VERIFIED` | `CONTRADICTED` stays visible; invalid claims become `INCOMPLETE` | required refs, source binding, fingerprint, approval subject; P1 closes fail-open gap |
| Execution Ledger / Native Decision Trace | existing trace writer and live receipt append path | reconstruction, evaluation, reports, gates | append-only durable audit projection; timestamps and integrity fields | contradiction, supersession, missing/stale refs remain explicit | fact/evidence/decision/consequence refs; no chain-of-thought |
| Goal Contract / project state | `p2p_workflow.py` and project bootstrap | workflow/eval/gates | scope and acceptance authority for the Goal, not canonical technical fact | unknown/blocking state is preserved | requirement/evidence references; no new store |
| Context manifests / pointers | existing `context.py` and live trial preparation | context delivery and live execution | source/scope/hash/freshness metadata; pointer is not permission | stale/conflicting pointers fail or remain explicit | artifact, fixture, source catalog, context fingerprint |
| Approval records / policy | request helper and explicit owner decision | governance, FACT/Live promotion, release gates | owner/governance authority; exact subject hash and TTL | failed technical gates cannot be overridden; silence/self-approval invalid | protected actions, technical report, subject SHA |
| Capability registry / trust boundary | manifests and foundation doctor | router/readiness and execution preflight | capability availability/readiness is data, not authorization | unavailable/unknown remains unavailable; retrieved content cannot grant permission | canonical 8/8, optional Aesthetica, `trust.py`; no ninth identity |
| Runtime/source manifests | package builder, installer, source inventory | doctor, package verify, drift | exact source/runtime/package state via hashes and manifests | mismatch fails validation | source inventory 152/152, runtime lock, conversion map |
| Governance/drift gates | protected policy and generated reports | doctor, drift, package/release checks | governance control-plane authority; expiry/as-of checks | failures stop promotion/release | FACT_LEDGER, Live Specs, runtime lock, approval records |
| Release hashes / candidate manifests | `package_release.py` and package build | verify, doctor, lifecycle tests | immutable candidate/artifact identity | checksum/hash mismatch fails | official `.15`, preserved `.18`, unpromoted `.20` |
| Existing permission representation | live request/receipt/guardrails in `live_execution.py` | preflight, finalize, receipt/ledger consumers | fixed request envelope plus observable host mode; intent does not grant it | altered values or non-read-only host observation fail closed | request fingerprint, receipt, existing trial root and ledger; no permission service |

## Relationship / Impact Evidence

The runtime capability directory is copied into packages but is not fully indexed as code by the current Anvien graph. The closest indexed wrappers and workflow owners must be checked before edits; this limitation is itself recorded rather than hidden.

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `.p2p/system/p2p_capabilities/evidence.py` | final runtime graph: 35 symbols, 22 local relationships, 117 unresolved; `_safe_actual_evidence` upstream impact: 1 file / 1 symbol, LOW | 1 direct process | evidence contract consumed by foundation tests and project workflows | high parser-risk / low blast-radius warning |
| `.p2p/system/p2p_capabilities/trust.py` | final runtime graph: 16 symbols, 18 local relationships, 24 unresolved; protected-fact contract direct impact: 1 file / 4 impacted symbols, LOW | 1 runtime file | protected fact authority and approval binding | high parser-risk / low blast-radius warning |
| `.p2p/system/p2p_capabilities/live_execution.py` | final runtime graph: 124 symbols, 97 local relationships, 422 unresolved | 13 linked flows | request/receipt validation, existing Execution Ledger append, C07/C09 tests | high security-boundary warning |
| `.p2p/system/p2p_uiux/security.py` | final runtime graph: 6 symbols, 1 local relationship, 20 unresolved; `scan_text` upstream impact: 1 file / 1 symbol, LOW | 0 linked flows | package/source secret scan | high parser-risk / low blast-radius warning |
| `.p2p/system/p2p_capabilities/decision_trace.py` | source/spec inspection | preserve-only | reference projection over existing Execution Ledger | preserve-only |
| `.p2p/system/p2p_capabilities/context.py` | source/spec inspection | preserve-only | hash-bound context pointers and stale validation | preserve-only |
| `governance/fact-ledger.json`, `governance/live-specs.json` | source inspection | preserve-only | canonical fact authority and deterministic projection | protected preserve-only |
| `governance/approval-policy.json`, `governance/drift-policy.json` | source inspection | preserve-only | protected actions, drift, and promotion gates | protected preserve-only |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already behaves as required. | Preserve and verify. |
| `partial` | Some required behavior exists, but gaps remain. | Edit only the missing contract. |
| `blocked` | Required authority or external evidence is unavailable. | Stop and report the exact blocker. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| FACT_LEDGER / Live Specs | existing canonical authority and deterministic projection | unchanged | correct | preserve-only | `E0-P0A-SRC1` | preserve |
| Approval / Drift governance | existing protected-action and drift gates | unchanged | correct | preserve-only | `E0-P0A-SRC1` | preserve |
| Decision Trace / Execution Ledger | existing append-only reference projection | unchanged | correct | preserve-only | `E0-P0A-SPEC1` | preserve |
| Context pointers | existing source hash, scope, freshness, conflict handling | unchanged | correct | preserve-only | `E0-P0A-SPEC1` | preserve |
| EvidenceClaim / FactClaim | projects only bound verified evidence, redacts secret-like metadata, and requires a structured approval subject binding for protected claims | verified claims and protected writes require bound metadata | bound-correct | 2 runtime files plus direct test consumers | `E0-P0A-GAP1`, `E1-P1A-EVID1`, `E1-P1A-TEST1` | preserve |
| Live execution request | explicit fixed read-only envelope, guardrails, request fingerprint, host-mode observation, and preflight root validation | read-only permission envelope cannot widen at handoff | bound-correct | 13 linked runtime flows | `E1-P1B-PERM1`, `E1-P1B-EDGE1` | preserve |
| Secret scan | high-confidence scanner now ignores only the proven all-`x` documentation placeholder while still detecting real GitHub-token shapes | global scan and doctor must be meaningful and fail closed | bound-correct | package/source scanner and direct tests | `E2-P2A-GATE1` | preserve |
| Capability routing | availability/readiness is not authorization | remains routing-only; execution must require explicit authorization | partial / preserve-only | preserve-only | `E0-P0A-SPEC1` | enforce only at live trial boundary |
| C09 host identity | no fresh official generic/default or canonical receipt | remain UNKNOWN/BLOCKED | blocked | preserve-only | `E0-P0A-C091` | no rerun or inference |
| Promoted/candidate artifacts | `.15` promoted; `.18` unpromoted candidate | unchanged | correct | protected | user request | preserve |
| Git checkpoint | no `.git` directory; `anvien detect-changes` cannot obtain a diff | honest limitation | blocked | N/A | final detect-changes output | report, do not initialize |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-08-14 | baseline before implementation | full C10 scope | initial classification | `E0-P0A-SRC1`..`E0-P0A-GAP1` | P1 limited to two contract slices |
| R1 | 2026-08-14 | after P1-A focused implementation and 27/27 foundation tests | evidence/trust contracts | partial -> bound-correct | `E1-P1A-EVID1`, `E1-P1A-TEST1` | proceed to P1-B; keep governance sources preserve-only |
| R2 | 2026-08-14 | after P1-B, scanner correction, final build, and full regression | live permission, secret projection, package gates | partial -> bound-correct; global doctor recovered | `E1-P1B-PERM1`, `E1-P1B-EDGE1`, `E2-P2A-TEST1`, `E2-P2A-GATE1` | Supervisor review; no promotion |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| `evidence.py`, `trust.py` | `tests/test_p2p_capability_foundation.py` | direct behavior test | P1-A | edit | `E0-P0A-GAP1` | preserve status and fact-origin vocabularies |
| `live_execution.py` | `tests/test_p2p_live_execution.py` | direct behavior test | P1-B | edit | `E0-P0A-GAP1` | preserve C09/C07 receipt taxonomy |
| `p2p_uiux/security.py` | `tests/test_p2p_security_scan.py`, doctor/package gates | source/package scanner | P2-A | edit | `E2-P2A-SEC1` | ignore only the proven documentation placeholder |
| `decision_trace.py` | `execution-ledger.jsonl` | existing source/projection | P1-A/P1-B | preserve-only | `E0-P0A-SPEC1` | no second ledger |
| `context.py` | context manifests/receipts | existing binding source | P1-A/P1-B | preserve-only | `E0-P0A-SPEC1` | no access expansion |
| governance files | live runtime and package gates | authority source | all | preserve-only | `E0-P0A-SRC1` | no promotion changes |

## Detailed Findings

### Evidence contract

Current state before P1-A: `EvidenceClaim.__post_init__` validated only the status enum; `evaluate_done()` trusted status and count. The execution-evidence SPEC requires fresh actual evidence with source and timestamp/fingerprint. `FactClaim` accepted any non-empty approval marker for a protected write.

Required state: a verified claim or protected write must be explicitly bound to safe source/provenance, observation time, freshness, scope, evidence identity, or an approval subject hash; missing or stale inputs remain incomplete/unknown rather than verified.

Evidence: `E0-P0A-GAP1`, `E1-P1A-EVID1`, `E1-P1A-TEST1`.

Classification: `bound-correct` for the scoped contract.

Allowed next action: preserve and regression-check.

Forbidden next action: create a second evidence store or replace FACT_LEDGER.

### Live permission boundary

Current state before P1-B: `default_execution_request()` exposed permission/network/task fields, but `_validate_execution_request()` only checked profile, worker count, and delegation policy. The host receipt permission mode was observed but not compared with a requested authorization contract.

Required state: the bounded trial carries an explicit read-only permission contract and rejects altered permission/network/task/delegation/secret access before handoff; observed host mode cannot widen it.

Evidence: `E0-P0A-GAP1`, existing C09 local contract evidence, the execution-evidence SPEC, `E1-P1B-PERM1`, and `E1-P1B-EDGE1`.

Classification: `bound-correct` for the bounded read-only trial; official host execution remains unproven.

Allowed next action: preserve; do not infer host permission beyond the receipt.

Forbidden next action: infer missing host identity or add a general permissions subsystem.

### C09 boundary

Current state: existing C09 artifacts report no fresh official generic/default or canonical `p2p_iris` receipt.

Required state: remain `BLOCKED / EVENT_EVIDENCE_UNAVAILABLE` until the official host emits matching evidence.

Classification: `blocked`.

Allowed next action: preserve and report.

Forbidden next action: rerun C08, accept worker labels/prose, or default to `p2p_iris`.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | Evidence/trust contracts and secret-safe projection are bound-correct | preserve |
| P1-B | Live permission boundary is bound-correct for the bounded read-only trial | preserve |
| P2 | Local gates and candidate checks are PASS; Supervisor accepted the bounded claim; C09 and Git remain external/workspace limitations | stop without promotion |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Each target file has fresh file-detail relationship count evidence before editing.
- [x] Phase Touch Map defines edit/preserve-only boundaries.
- [x] Correct and blocked parts have exact next actions.
- [x] P1 is limited to two implementation slices.
- [x] Status Refresh Log has an R0 baseline row.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [x] P0 complete. Next phase status, next action, and work steps are limited to the two proven gaps.

Decision note: P0 was completed before implementation with fresh Anvien file-detail/impact checks. The final state closes the two proven contract gaps and the scanner false positive without changing C09 or protected artifacts.

## Final Validation Snapshot

- Root Anvien graph: 323 scanned files, 31 parsed code files, 12,004 nodes, 13,648 relationships.
- Runtime Anvien graph: 44 files, 36 parsed code files, 4,217 nodes, 5,043 relationships.
- Focused final run: `119/119` full suite; capability foundation `28/28`; combined evidence/live/host/beginner `57/57`; security scan unit `2/2`.
- Decision Trace: `DT1-DT24 = 24/24 PASS`.
- Governance drift: `PASS`; capability doctor: `PASS`; development doctor: `PASS`; package verify/doctor/secret scan: `PASS`.
- Existing eval validation: `.p2p/evals/suite.json` and context-efficiency suite `PASS`; legacy `.p2p/evals/rag-retrieval-check.json` remains schema-v1 and is not treated as a C10 PASS.
- `anvien detect-changes` could not produce a diff because the workspace has no `.git`; no Git repository was initialized.
- Official `.15` and existing `.18` hashes were rechecked unchanged. New `.20` is unpromoted.
- Supervisor: PASS. Report: `reports/supervisor/rp_supervisor_260814_191500_by_gpt-5-codex_p2p-c10-evidence-permission-hardening.md`.
