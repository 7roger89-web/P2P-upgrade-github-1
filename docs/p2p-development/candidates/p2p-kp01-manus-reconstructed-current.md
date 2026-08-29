---json
{
  "schema": "p2p-kp01-candidate-evidence/1",
  "goal": "KP01",
  "candidate_status": "UNPROMOTED",
  "exact_candidate_object_available": false,
  "fresh_remote_main_sha": "8be14dafaaf5090e6a5cd22e92de19d174aa7d32",
  "fresh_remote_main_tree": "c83812241b8c51635feb6eab633fdc32afe17ac3",
  "approved_base_sha": "8be14dafaaf5090e6a5cd22e92de19d174aa7d32",
  "reconciliation_required": false,
  "implementation": "additive bounded repo-backed knowledge lifecycle",
  "storage": ".p2p/knowledge/<ORG>/<PROJECT>/<WORKSTREAM>/<record_id>.md",
  "focused_test_results": "7/7 PASS",
  "py_compile": "PASS",
  "diff_check": "PASS",
  "execution_authorization": "NOT_GRANTED",
  "autonomous_promotion": "NOT_CREATED",
  "production_touched": false,
  "release_status": "NOT_RELEASED",
  "deployment_status": "NOT_DEPLOYED"
}
---

# P2P-KP01 — Manus reconstructed candidate

This candidate is a **Lane B recovery**, not a promotion of the missing historical SHA. The exact approved commit `a195d8ba6be78144bc4230da3f0a6e2ed3f84ee2` was searched in the available local Git object stores, cloned repository objects, local refs, and remote branch data and was not mechanically available. The current authenticated `origin/main` was then resolved freshly as `8be14dafaaf5090e6a5cd22e92de19d174aa7d32` with tree `c83812241b8c51635feb6eab633fdc32afe17ac3`.

## Preserved contract

The implementation provides one `KnowledgeRecord` contract with JSON front matter in human-readable Markdown. It supports the required knowledge types `OWNER_DECISION`, `PROMOTION_RESULT`, and `ARCHITECTURE_DECISION`; lifecycle values `OBSERVATION`, `CANDIDATE`, `VERIFIED`, `CANONICAL`, and `SUPERSEDED`; current and as-of queries; explicit supersession; candidate-versus-canonical separation; authority-conflict fail-closed behavior; ORG/PROJECT/WORKSTREAM scope isolation; provenance lookup; canonical-only Control Tower reconstruction; and secret/private-reasoning rejection.

The module reuses the repository’s existing `trust` and `isolation` primitives. It does not add a vector database, graph database, embeddings, external memory framework, MCP surface, router, Control Tower, autonomous ingestion, or autonomous promotion. Every reconstructed Control Tower projection returns `execution_authorization=NOT_GRANTED`; retrieved knowledge is never labeled verified truth merely because it is newer.

## Focused evidence

| Check | Result | Evidence |
| --- | --- | --- |
| Focused KP01 suite | 7/7 PASS | `tests/test_p2p_kp01_knowledge_lifecycle.py` |
| Direct Python compilation | PASS | `knowledge_lifecycle.py`, focused test file |
| Diff whitespace check | PASS | `git diff --check` |
| Exact historical candidate object | NO | Candidate SHA absent from searched Git object stores and refs |
| Fresh remote main matched approved base | YES | `8be14dafaaf5090e6a5cd22e92de19d174aa7d32` |
| Broad regression | NOT RUN | Explicitly excluded by handoff risk rule |
| Promotion | NOT PERFORMED | Lane B requires Owner Gate after fresh candidate review |

## Owner Gate boundary

This rebuilt candidate must receive an independent exact-subject Supervisor review. It is not canonical, it is not released or deployed, and no promotion or force push is authorized by this candidate artifact. The final candidate commit and tree must be returned to the Owner for review rather than silently promoted.
