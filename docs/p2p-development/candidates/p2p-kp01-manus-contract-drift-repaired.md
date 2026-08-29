---json
{
  "schema": "p2p-kp01-contract-drift-repair/1",
  "goal": "KP01",
  "repair_status": "READY_FOR_OWNER_GATE",
  "old_reconstructed_candidate_sha": "a0832e263ba5a7bcc77ab8ee93cbb0e4faa59f2b",
  "old_reconstructed_candidate_tree": "08137e7d6913a88129d09a3c834121efb3363e54",
  "fresh_current_main_sha": "8be14dafaaf5090e6a5cd22e92de19d174aa7d32",
  "fresh_current_main_tree": "c83812241b8c51635feb6eab633fdc32afe17ac3",
  "authority_widening_fixed": true,
  "direct_canonical_construction_blocked": true,
  "candidate_direct_promotion_blocked": true,
  "verified_promotion_required": true,
  "knowledge_type_preserved_on_promotion": true,
  "focused_test_results": "16/16 PASS",
  "broad_regression_run": false,
  "canonical_promoted": false,
  "execution_authorization": "NOT_GRANTED"
}
---

# P2P-KP01 — Contract-drift repair

Control Tower review identified material semantic drift in the previous reconstructed candidate `a0832e263ba5a7bcc77ab8ee93cbb0e4faa59f2b`. That candidate is explicitly **not promoted**. This repair is bounded to the original KP01 contract and does not introduce a new architecture.

## Repaired invariants

| Invariant | Result |
| --- | --- |
| Canonicalization authority is bounded to `OWNER` and `GOVERNANCE` | PASS |
| `RUNTIME_EVIDENCE` and `OFFICIAL_SOURCE` remain evidence authorities only | PASS |
| Generic direct `CANONICAL` construction | REJECTED |
| Direct `CANDIDATE` or `OBSERVATION` promotion | REJECTED |
| Promotion source lifecycle | `VERIFIED` only |
| Knowledge type during promotion | Preserved; promotion event is not substituted for record type |
| Scope hierarchy | `ORG`, `PROJECT`, and `WORKSTREAM` with hierarchical required fields |
| Supersession | Explicit canonical-to-canonical state transition |
| Temporal interval | Half-open: `valid_from <= t < valid_until` |
| Control Tower projection | Canonical records only |
| Execution authorization | `NOT_GRANTED` |

## Preserved good properties

The repair retains repo-backed Markdown with JSON front matter, provenance lookup, secret/private-reasoning rejection, immutable record collision handling, reuse of the existing isolation primitive, current/as-of queries, canonical-only Control Tower reconstruction, and the absence of vector DB, graph DB, embeddings, router, second Control Tower, autonomous ingestion, or autonomous promotion.

## Evidence

The focused suite contains **16/16 passing tests** covering all handoff requirements A–O, including authority separation, direct-construction rejection, verified-only promotion, both OWNER and GOVERNANCE approval, all three scope levels, type preservation, explicit supersession, exact timestamp behavior, canonical-only reconstruction, execution authorization, and canonical precedence over newer noncanonical observations. Direct compilation and `git diff --check` are required before freezing the new candidate.

This artifact is evidence for Owner review only. The new candidate remains unpromoted and unreleased.
