# P2P AERG Reconciliation — Evidence Ledger

This is the living evidence ledger for the bounded AERG reconciliation. It records what was actually observed, not historical report claims.

## P0 recovery and baseline

| Evidence ID | Observation | Result / boundary |
| --- | --- | --- |
| `E0-P0A-GIT1` | Historical ref `origin/p2p-aerg-provider-neutral-reliability-01` resolves to `955bcc0c123b007c5886d15cf97eed824a51a559`; exact base `4ce6a85f5991b6d6c464fb4b59e177114698947e`; current post-C43 HEAD `0950193149340e73b5569a1cf30e072b4fa5f4ac`. | Subject mechanically recoverable; no branch replay authorized. |
| `E0-P0A-DIFF1` | `git diff --stat 4ce6a85f..955bcc0c` reports 19 paths, 1044 insertions, 431 deletions. | Historical implementation, reports, governance, and tests must be separated. |
| `E0-P0A-SRC1` | Historical AERG code has timestamp-derived IDs, no subject/fingerprint binding, raw evidence text checks, no `get_claims()`, no explicit `verify_claim()`, and no independent-verifier enforcement. | Historical reports are untrusted claims; minimum semantic port required. |
| `E0-P0A-CONTRACT1` | Current `evidence.py` owns bounded evidence claims and statuses; current QI owns post-execution quality; current role verifier rejects self-claims and stale/mismatched receipts; current FW01 has the existing post-execution quality seam. | Reuse current contracts; no second truth-state or release gate. |
| `E0-P0A-LEDGER1` | Current capability schema registers `VERIFICATION_AND_EVALUATION`, not historical `QUALITY_EVIDENCE_EVALUATION`; current status vocabulary is fixed and contains no AERG record. | Normalize one current capability record; retain historical IDs only as provenance/report context. |
| `E0-P0A-AUTH1` | Current governance snapshot: `.19` `PROMOTED_VERIFIED`; `.74` `SEALED_UNPROMOTED/NONCANONICAL`; RF01/C43 independently verified; CPT01-R2 `EXTERNAL_HOST_CAPABILITY_LIMITATION`; `promotion.allowed=false`. | No promotion, release, deploy, host mutation, or `.19/.74` subject edits. |
| `E0-P0A-GRAPH1` | Fresh `anvien analyze --force`: exit 0, 883 files scanned, 164 parsed code files, 0 parse failures; hidden `.p2p/system` QI/FW01 files are not in the graph. | Use Anvien for visible graph/change evidence and direct source/tests for hidden runtime files. |
| `E0-P0A-WF1` | Project workflow inspect/plan/goal/bootstrap completed. Goal linter PASS; missing project profile/evals/status/ledger/trusted evidence were initialized without overwriting existing policy. | Workflow state is project scaffolding, not AERG proof. |
| `E0-BASE-QI` | Current QI suite: 44 tests, 1 skip, exit 0. | Baseline PASS for existing QI before AERG edits. |
| `E0-BASE-FW` | Framework validator: 52/59 checks passed, 7 failures. Failures are inherited ledger/schema/charter/lineage defects identified by C43 and outside AERG scope. | Not whole-framework PASS; preserve and classify later. |
| `E0-ANV-HIDDEN` | `anvien file-detail`/file impact for `.p2p/system/p2p_capabilities/quality_intelligence.py` returns not found. | No false Anvien symbol/impact claim for hidden files. |

## P1/P2/P3/P4 evidence slots

| Evidence ID | Required observation | Status |
| --- | --- | --- |
| `E1-AERG-AZ` | A–Z deterministic matrix output; all cases executed; seeded contradictions never support. | PASS: 26/26 cases, 12 tests, exit 0 |
| `E1-AERG-PROVIDER` | Provider-neutral source/test guard with no provider-specific core branching. | PASS: no provider/control-plane matches |
| `E1-AERG-SCOPE` | Core has no persistence, scheduler, queue, router, release, promotion, or deploy surface. | PASS: no forbidden core surface |
| `E2-QI-FW01` | QI/FW01 focused integration and ordering regressions. | PASS: QI 44/44 + 1 skip; checkpoint 6/6; composition 7/7 |
| `E2-C43-RF01` | Relevant C43 and RF01 orientation regressions. | PASS: C43 9/9; RF01 7/7 + packaging 2/2 |
| `E3-LEDGER` | Schema validation, registered family, dependency integrity, and current derived projection. | PASS scoped record/JSON/count; full validator remains 52/59 with 7 inherited failures |
| `E3-IMMUTABILITY` | `.19` baseline hash, `.74` source/candidate hashes, and protected governance status unchanged. | PASS for available `.74` artifact and governance status; `.19` ZIP absent, expected authority hash preserved |
| `E4-BUILD` | Full requested build/compile boundary and test discovery evidence. | PASS: full hidden suite 347/347 + 6 skips; compileall exit 0 |
| `E4-CHANGE` | Anvien/git change detection, exact intended path inventory, and no unrelated owner changes. | PASS/OBSERVED: final `anvien analyze --force` exit 0; final `anvien detect-changes --scope all` exit 0; graph reports 5 tracked changed files including pre-existing `adapter_registry.json`; hidden AERG/docs paths are outside the graph and were reconciled by direct Git/source/test evidence. |
| `E4-REPORT` | Final A–N reconciliation report and coder report hash-bound to the final subject. | PASS: reconciliation report and coder report written with source checkpoint/fingerprint/hash; supervisor review pending |

`NOT_RUN` remains `NOT_RUN`; it is never converted to PASS by report wording.
