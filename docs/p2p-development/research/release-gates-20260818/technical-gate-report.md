# P2P C40 — Technical Gate Report (Production Release-Gate Flow)

**Date:** 2026-08-18 (GMT+7)
**Candidate:** P2P-8.4.7-C-Codex-Edition-v24 (`e7f62384c8e51ef9c32e903688126642521d9570b648602fcf530aab25cbdc56`)
**Branch:** `p2p-c40-project-usable-release-pilot`, HEAD `3443fd8` (pre-release commit)
**Authorization:** Owner chat instruction of 2026-08-18: "Chạy đủ release gates để hoàn tất phát hành sản xuất cho gói C40"

## 1. Gate-by-gate results

| Gate | Status | Evidence |
|------|--------|----------|
| inventory | PASS | `release-gates.json` — candidate zip reconciled against 8.4.6-C baseline via stable-id hashes; all 1383 entries and 152 baseline entries reconciled. Note: the zip is a self-contained runtime bundle, so there is zero raw hash overlap with the 8.4.6-C snapshot — inventory passed by its own reconciliation semantics. |
| semantic_source_review | PASS | `release-gates.json` — every new/changed file reviewed: C40 release machine (`p2p_install_release.py`), PARTIAL-lane native closure machinery, pilot harnesses (Game Truyện, Gia Phả), evidence artifacts; no unrelated or risky changes. |
| fact_ledger_review | PASS | `fact-ledger.json` revision 2 → 3: 8 archival lines marked HISTORICAL_ONLY; drift-policy scoped registry extended (10 → 29+ entries) for archival C38/C39 evidence receipts. |
| fact_ledger_technical_preview | PASS | `technical-preview.json` — PASS_TECHNICAL_PREVIEW, runtime_facts 5, warnings 0. |
| fact_ledger_user_approval | PASS | Approval record `P2P-APR-20260818T155200Z-c40-release-gates-live-specs.json` (schema v2, conversation_explicit / active_user_message, Owner-decided, ledger-hash-bound). |
| live_specs_sync | PASS | `governance/live-specs.json` regenerated from ledger revision 3; lock file updated with approval reference. |
| project_evals | NO_POSITIVE_EVIDENCE (honest disclosure) | The only bundled eval suite (`p2p-uiux-eval-suite/1`) has zero recorded trials in any historical version and does not match the `p2p-codex-project-eval/2` schema; no deterministic re-run is possible. The release touches no UI/UX eval surface. |
| rag_retrieval_checks | NOT_APPLICABLE | P2P has no retriever, index, or grounded Q&A system; the `rag-gate` schema requires artifacts that do not exist. |
| protected_runtime_manifest | PASS | `lock-runtime` re-hashed 1012 protected files + 2 virtual hashes, reason recorded. |
| active_runtime_drift | PASS | `drift-final-report.json` — claims current, no unledgered volatile claims, no manifest divergence. |
| rollback_artifact | PASS | `rollback-artifact.zip` — git archive of HEAD 3443fd8, sha256 `57cc3e9eaa4029aeb23aef3472446e2fd17dfb6b3030d0a26226b1847881fdb1`. |
| package_doctor | PASS | `p2p_install_release.py doctor` on the P2P repo itself: HEALTHY probes, project permission BOUND. |
| candidate_hash_recheck | PASS | Candidate zip sha256 re-verified identical to the promoted hash `e7f62384...`. |

## 2. Honest disclosures

1. **Project evals contribute no positive evidence.** This is a pre-existing condition of the repository (no eval suite with recorded trials has ever existed); the release does not touch the UI/UX eval surface. The Owner is informed and retains the right to withhold final authorization on this basis.
2. **The inventory gate's zero raw hash overlap** is a property of the bundle format (self-contained runtime copy), not an absence of baseline continuity; reconciliation was performed via the stable-id hash mapping.
3. **Iterative re-locking was required** because the release-gates evidence file itself is a protected runtime file; each evidence write was followed by `lock-runtime` + `drift` until stable. All reasons recorded.
4. **The earlier C40 promotion approval record** (candidate promote, 2026-08-18T15:22) did not satisfy the full approval schema (request-id format, distinct requester/approver); it was accepted only because that step's gate validated provenance loosely. This flow's approval record satisfies the schema completely.

## 3. Residual risk

- The release has been pilot-verified on two independent web projects (Game Truyện, Gia Phả) with full install → dispatch → recovery → rollback loops closed and fingerprint-verified.
- Both pilots are web projects; no cross-framework pilot has been performed. The release scope documented in the promotion record is therefore "web projects similar to the two pilots".
- A rollback artifact and the candidate zip are preserved; every install keeps the owner-gate and rollback contract.

**Conclusion:** all runnable gates PASS; two gates carry no positive evidence by structural pre-existing conditions, disclosed above. The flow is complete pending final Owner approval (gate: final_user_approval), which is requested hash-bound to this report and the unchanged candidate hash.
