# P2P AERG Reconciliation — Bounded Development-Plane Implementation

**Date:** 2026-08-24
**Working tree:** `codex/p2p-post74-development-01`
**Current HEAD:** `fc1b9dc` (AERG implementation checkpoint; source-bound subject commit)
**Terminal target:** `P2P_AERG_IMPLEMENTATION_READY_FOR_SUPERVISOR_REVIEW` or a precise `P2P_AERG_BLOCKED_*` result.

## Goal

Reconcile the recoverable historical AERG candidate onto the current post-C43 development plane as a provider-neutral evidence/assurance layer. AERG must preserve original claims, bind observations to the evaluated subject, distinguish assurance from provenance/freshness/authority, and deterministically classify unsupported, contradicted, stale, wrong-subject, and insufficient evidence.

The result is development-source and noncanonical. It must not promote `.74`, alter official `.19`, release, deploy, mutate GitHub host protection, replace `scripts/p2p_gate.py`, or manufacture independent verification.

## Scope boundary

In scope:

- Recover and document the historical branch, exact base, exact diff, and historical implementation defects.
- Port the minimum provider-neutral AERG model/engine using the current evidence vocabulary and existing evidence/quality contracts.
- Add a deterministic A–Z falsification matrix covering the user-required cases, with contradiction precedence and `NOT_RUN`/`UNKNOWN`/`WARN` fail-closed behavior.
- Integrate only at the existing post-execution `QualityIntelligence` / `Fw01Loop` seam.
- Reconcile one current capability-ledger record into the registered `VERIFICATION_AND_EVALUATION` family, preserving stale historical IDs as provenance in the report rather than canonical authority.
- Produce fresh reconciliation, coder, and validation evidence; preserve inherited failures as inherited.

Out of scope:

- Any change to `.19`, `.74` artifact bytes, promotion state, release packaging, deployment, GitHub settings, host credentials, or external communication.
- Work Queue, Lane Registry, Integration Queue, second router/control plane, scheduler, database, vector store, event bus, policy DSL, or new persistence store.
- Repair of unrelated C43 capability-ledger/charter/validator debt.
- Automatic AERG loading during RF01 README-first orientation.
- C43 semantic changes unless a direct AERG compatibility defect is mechanically proven.

## Preflight questions and resolved evidence

| Question | Resolution | Evidence |
| --- | --- | --- |
| Is the historical subject recoverable? | Yes. Historical ref `origin/p2p-aerg-provider-neutral-reliability-01` resolves to `955bcc0c123b007c5886d15cf97eed824a51a559`; exact merge base is `4ce6a85f5991b6d6c464fb4b59e177114698947e`. | `E0-P0A-GIT1` |
| What changed historically? | 19 paths, 1044 insertions, 431 deletions; implementation, QI/FW01 splice, governance, reports, and tests were mixed together. | `E0-P0A-DIFF1` |
| Does historical integration fit current code? | No. Historical `p2p_fw01_loop.py` calls missing `AERGEngine.get_claims()` and never verifies claims; historical QI passes a removed `reliability_claims` parameter. | `E0-P0A-SRC1`, `E0-P0A-CONTRACT1` |
| Which current surfaces are authoritative? | Current `evidence.py`, `quality_intelligence.py`, `role_verifier.py`, and the existing FW01 post-execution seam. AERG remains subordinate to these. | `E0-P0A-CONTRACT1` |
| Is Anvien complete for the edit targets? | No. The fresh graph is healthy for visible sources, but ignored hidden `.p2p/system` sources are not indexed. Direct source inspection and focused runtime tests are required for QI/FW01/AERG. | `E0-P0A-GRAPH1` |
| What current governance must be preserved? | `.19` is `PROMOTED_VERIFIED`; `.74` is `SEALED_UNPROMOTED/NONCANONICAL`; RF01 and C43 are independently verified; CPT01-R2 is `EXTERNAL_HOST_CAPABILITY_LIMITATION`; `promotion.allowed=false`. | `E0-P0A-AUTH1` |

## Work slices

### P0 — Recovery and semantic reconciliation (complete before implementation)

- **Goal:** establish exact historical subject and current contract delta.
- **Steps:** recover ref/base/head; compute old-base→head diff; read historical modules/reports; inspect current evidence/QI/role/FW01 contracts; classify stale IDs/families/statuses.
- **Implementation gate:** no merge/rebase/cherry-pick/copy of the historical branch; implementation may start only because recovery is mechanically complete.
- **Acceptance:** recovery proof, semantic diff, stale governance list, and exact current authority boundary are recorded.
- **Evidence targets:** `E0-P0A-GIT1`, `E0-P0A-DIFF1`, `E0-P0A-SRC1`, `E0-P0A-CONTRACT1`, `E0-P0A-LEDGER1`, `E0-P0A-AUTH1`, `E0-P0A-GRAPH1`.
- **Commit boundary:** documentation-only plan/evidence artifacts may be committed with the first scoped implementation slice; no historical branch content is committed.

### P1 — Provider-neutral AERG core and A–Z matrix

- **Goal:** implement deterministic claim/evidence normalization without a second truth store.
- **Scope:** `.p2p/system/p2p_capabilities/aerg_model.py`, `.p2p/system/p2p_capabilities/aerg_engine.py`, focused AERG tests.
- **Non-goals:** release authority, independent-verifier manufacture, raw evidence persistence, provider-specific branching.
- **Work steps:** define subject binding, structured observations, deterministic claim IDs, separate dimensions, contradiction precedence, current `EvidenceClaim` projection, and bounded result serialization; then implement A–Z tests.
- **Implementation gate:** no function edit without direct source inspection; hidden graph limitation remains explicit; no raw content or secret-like fields enter the model.
- **Acceptance:** all A–Z cases pass; a seeded contradiction never returns support; original claims and evidence provenance remain unchanged; no provider names/branches or persistence/control-plane surfaces appear in core.
- **Evidence targets:** AERG test output, source inspection, `git diff --check`, compile/import checks, benchmark timing.
- **Commit boundary:** one commit after P1 tests and scope checks pass.

### P2 — Existing QI/FW01 seam integration

- **Goal:** make current post-execution quality evaluation consume AERG results without changing orchestration topology.
- **Scope:** add an optional AERG result input to current `build_quality_verdict`; map contradiction/stale/scope/insufficient states to existing QI failure vocabulary; invoke AERG only in the existing FW01 post-execution section from durable evidence.
- **Non-goals:** new router, new checkpoint system, new certification authority, or automatic RF01 loading.
- **Acceptance:** direct QI tests prove supported mechanical evidence can be evaluated, contradiction cannot checkpoint, stale/mismatch/insufficient cannot checkpoint, and historical `get_claims()`/`reliability_claims` incompatibility is absent. Existing QI and FW01 ordering/regression tests remain clean.
- **Evidence targets:** focused QI/FW01 test output, current C43 regression, source-level seam assertions, impact limitation record.
- **Commit boundary:** one commit after integration and affected regressions pass.

### P3 — Current governance/evidence reconciliation

- **Goal:** re-derive current development-plane metadata from fresh implementation evidence.
- **Scope:** one schema-valid `AI_EXECUTION_RELIABILITY_GUARD` ledger record under registered `VERIFICATION_AND_EVALUATION`; derived roadmap count/projection update if required; fresh AERG reconciliation report with A–N output.
- **Non-goals:** importing `C44`, `RI-011`, `RA-EXT-035`, or `RM-AERG` as current authority; changing `.19/.74` or promotion state.
- **Acceptance:** ledger schema/validator results distinguish inherited failures from new failures; current record is foundation/development status only; report binds implementation/test hashes and explicitly states no promotion/release/deploy.
- **Evidence targets:** ledger JSON/schema checks, report hashes, exact status snapshot, `.74` immutability checks.
- **Commit boundary:** one commit after governance and report validation pass.

### P4 — Full affected validation and supervisor handoff

- **Goal:** verify the completed bounded slice and stop at supervisor review.
- **Steps:** run focused AERG/QI/FW01 tests, full build/compile boundary, relevant C43/RF01 regressions, framework validator, change detection, clean-diff/secret/scope checks; classify NEW/INHERITED/RESOLVED_INHERITED failures; write coder report.
- **Acceptance:** no required AERG test is `NOT_RUN`; no AERG contradiction is supported; no forbidden mutation occurred; no release/promotion/deployment action is run; final terminal state is implementation-ready or precise blocked.
- **Evidence targets:** final actual-status/evidence/benchmark, coder report, reconciliation report, change detection, final hashes.
- **Commit boundary:** commit each verified slice before supervisor review; no supervisor repair in this task.

## Safety and stop rules

- Preserve unrelated owner modifications and all existing untracked C43/RF01 reports.
- Stop with `P2P_AERG_BLOCKED_HISTORICAL_SUBJECT_NOT_RECOVERABLE` only if mechanical recovery becomes unavailable; this condition is currently not present.
- Stop with a precise `P2P_AERG_BLOCKED_*` on a new material dependency or unresolved contradiction; do not guess.
- `PASS` for this task is never official, promoted, released, or deployed.
- After the implementation-ready result, stop and hand off to Supervisor; do not start Work Queue/Lane Registry.
