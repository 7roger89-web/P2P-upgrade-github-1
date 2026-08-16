# P2P Current Development Roadmap

> **Canonical source declaration.** This document is a **derived, human-readable projection**. It must never be edited as a source of truth.
> - Goal/development governance truth: `governance/development-control.json` (`current_development`, `candidate_records`, `roadmap`, `capability_status`, `research_decisions`).
> - Capability knowledge truth: `docs/p2p-development/capability-ledger/capability-index.json` (this directory).
> - Charter truth: `docs/p2p-development/P2P-DEVELOPMENT-CHARTER.md`.
> If this file disagrees with any canonical source, the canonical source wins. Regenerate this file whenever governance or the ledger changes.

**Generated:** 2026-08-17 by the P2P-C25 durable development session (derived, not authored-by-hand as a decision document).

## 1. Official baseline

| Item | Value |
| --- | --- |
| Official baseline version | `8.4.7-C-codex.19` |
| Baseline SHA-256 | `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8` |
| Promotion status | `PROMOTED_VERIFIED` |
| Source version (working tree) | `8.4.7-C-codex.21` |

## 2. Candidate lineage (from `development-control.json`)

| Goal | Status in governance | Candidate artifact | Promotion |
| --- | --- | --- | --- |
| C07 | DONE | — | — |
| C08 | **DEFERRED** | — | — |
| C09 | **BLOCKED** (`EVENT_EVIDENCE_UNAVAILABLE`) | — | — |
| C10 | DONE | — | — |
| C11 | DONE | — | — |
| C12 | DONE | — | — |
| C13 | DONE | — | — |
| C14 | DONE | — | `PROMOTED_VERIFIED` (baseline 8.4.7-C-codex.19) |
| C15 | DONE | — | — |
| C16 | DONE | — | — |
| C17 | DONE | — | — |
| C18 | DONE | — | — |
| C19 | DONE | `P2P-8.4.7-C-Codex-Edition-v21-c19-cross-platform-reconciled-final-candidate.zip` | **UNPROMOTED** (PASS) |
| C20 | DONE (foundation) | `P2P-8.4.7-C-Codex-Edition-v21-c20-host-executor-neutrality-foundation-final-candidate.zip` | UNPROMOTED |
| C21 | DONE (foundation) | `P2P-8.4.7-C-Codex-Edition-v21-c21-compatible-host-discovery-selection-foundation-final-candidate-v2.zip` | UNPROMOTED (`HOST_SELECTION_POLICY_FOUNDATION_READY`) |
| **C22, C23, C24** | **NOT RECORDED in this copy** | No candidates found in `reports/candidates/` | Not recovered |
| **C25** | **IN PROGRESS** (this document) | `P2P-8.4.7-C-Codex-Edition-v21-c25-durable-development-charter-ledger-framework-candidate.zip` (pending build) | UNPROMOTED |

> **Honesty note on C22–C24.** A handoff prompt for C25 expected C24 = DONE/PASS with candidate `P2P-8-4-7-C-codex-24-c24-evidence-backed-multi-host-adapter-conformance-candidate-v1.zip` (SHA `6c5b3b29fbaaab6df0b9f0c8a2f88ff579390b3b060c5c0d2f076cadec37d879`). That candidate and the C22/C23/C24 governance records were searched for durably and **do not exist** in this copy of the project. Per the project's durability rule ("durable project evidence outranks this prompt"), roadmap progression beyond C21 is marked not-recovered, and multi-host live certification remains **UNKNOWN** pending durable evidence.

## 3. Capability landscape snapshot (from the ledger)

Counts per family in `capability-index.json` at generation time (109 records, 12 families):

| Family | Count | Dominant statuses |
| --- | --- | --- |
| Truth & Governance | 12 | VERIFIED_IMPLEMENTED |
| Durable Project Intelligence | 11 | mix, incl. rejected-pattern preservation |
| Context & Knowledge | 16 | VERIFIED_IMPLEMENTED + FOUNDATION_READY |
| Skill & Learning | 5 | VERIFIED_IMPLEMENTED |
| Execution & Orchestration | 16 | VERIFIED_IMPLEMENTED + rejected patterns |
| Design & Product Intelligence | 7 | VERIFIED_IMPLEMENTED |
| Multi-AI Interoperability | 19 | FOUNDATION_READY + UNKNOWN (C22–C24 gap) |
| Routing & Cognitive Economy | 4 | mix |
| Verification & Evaluation | 8 | VERIFIED_IMPLEMENTED |
| Recovery & Continuation | 6 | mix |
| Beginner Lifecycle | 8 | mix |
| Outcome Learning | 3 | mix |

Status vocabulary used by the ledger: `VERIFIED_IMPLEMENTED`, `FOUNDATION_READY`, `PARTIAL`, `PLANNED`, `DEFERRED`, `REJECTED`, `OBSOLETE`, `UNKNOWN`.

## 4. Ready-now foundations (declared ready by governance)

- `TASK_TARGETED_CONTEXT_RETRIEVAL_FOUNDATION_READY` (C19)
- `CONTEXT_COVERAGE_ACCOUNTING_READY` (C19)
- `CACHE_AWARE_CONTEXT_REUSE_FOUNDATION_READY` (C19)
- `PORTABLE_EXECUTION_ENVELOPE_READY`, `PORTABLE_RESULT_RECEIPT_READY`, `CROSS_HOST_CONTINUATION_CONTRACT_READY` (C20)
- `HOST_REQUIREMENT_PROFILE_READY`, `HOST_CAPABILITY_DISCOVERY_FOUNDATION_READY` (C21)
- `HOST_SELECTION_POLICY_FOUNDATION_READY` (C21)
- `TASK_TARGETED_STATE_ARCHITECTURE_FOUNDATION_READY`, `RECOVERY_TESTABILITY_FOUNDATION_READY`, `TASK_STATE_RECOVERY_IMPLEMENTED` (C13/C19 lineage)
- `DURABLE_PROJECT_TRUTH_PACKAGING_FOUNDATION_READY` (C25 — pending this goal's close)

## 5. Recommended next goals (ordered, NOT auto-started)

Ordering follows the ledger's dependency graph and governance's `research_decisions`. Starting any goal still requires a new chat, an owner prompt, and that goal's own evidence contract. No goal starts automatically.

1. **C22 — Live host adapter conformance evidence.** The single largest evidence gap: live certification of Manus/Codex adapters on real hosts. Depends on C21 foundations. Resolves the `C22_C24_ADAPTER_LIVE_CERTIFICATION` UNKNOWN records.
2. **C23 — Live delegation and parallel execution certification.** Depends on C22 evidence. Upgrades `DELEGATION` and `PARALLEL_EXECUTION` from FOUNDATION_READY.
3. **C24 — Cross-host continuation and round-trip binding.** Depends on C22/C23. Upgrades `CROSS_HOST_CONTINUATION_CONTRACT`, `ROUND_TRIP_BINDING`, `CROSS_HOST_RESUME`.
4. **C26 — Beginner control center view layer.** Depends on nothing new; beginner-friendly dashboard for status/decisions (control center, health views, decision inbox).
5. **C27 — RAG scope re-opening decision.** Only after evidence contracts for vector retrieval are written as a goal; currently `DEFERRED`.
6. **Roadmap hygiene (ongoing):** reconcile the expected-but-missing C22–C24 state with the other copy of the project the owner may hold, before claiming progression.

## 6. Regeneration rule

Any session that changes `development-control.json`, `capability-index.json`, or the charter must regenerate this file so that the projection never drifts from its sources.
