# P2P AERG Reconciliation — Development-Plane Evidence Report

**Date:** 2026-08-24
**Terminal verdict:** `P2P_AERG_POST_REVIEW_REPAIR_READY_FOR_SUPERVISOR_REREVIEW`
**Mode:** development-plane, evidence-first, noncanonical
**Current source HEAD:** `c99145f` (post-review test-only repair checkpoint)
**Original implementation checkpoint:** `fc1b9dc`
**AERG scoped subject fingerprint:** `bd14ca273d5c35fe02d177e329d24b73915f09ab89d079d0daf99124780f0d9c`

This report is derived from fresh local source, Git, and test observations. Historical AERG reports are treated as claims, not authority. No promotion, release, deployment, GitHub host mutation, `.19` mutation, or `.74` mutation occurred.

## Post-review repair update

The prior Supervisor review remains preserved at
`reports/supervisor/rp_supervisor_260824_141738_by_gpt-5-codex_p2p-aerg-reconciliation.md`
with verdict `REJECT`. Its sole blocker was a missing executable assertion for
the no-mutation contradiction. The owner-authorized repair was test-only:

- `.p2p/system/p2p_capabilities/tests/test_aerg_reconciliation.py:109-111`
  now asserts `decision == CONTRADICTED`,
  `contradiction == CONTRADICTED`, and
  `MUTATION_CONTRADICTS_NO_MUTATION`.
- Production `aerg_model.py`, `aerg_engine.py`, `quality_intelligence.py`,
  and `p2p_fw01_loop.py` were not changed.
- Post-review repair checkpoint: `c99145f`.

## A. Historical AERG subject/base recovery

The historical subject was recovered mechanically:

- Ref: `origin/p2p-aerg-provider-neutral-reliability-01`
- Historical head: `955bcc0c123b007c5886d15cf97eed824a51a559` — `AERG: Final handoff report and sealing`
- Exact base: `4ce6a85f5991b6d6c464fb4b59e177114698947e` — `seal exact immutable .72 candidate artifact durably`
- Current post-C43 development HEAD before the AERG checkpoint: `0950193149340e73b5569a1cf30e072b4fa5f4ac`
- AERG implementation checkpoint: `fc1b9dc`
- Historical branch commits after base: `16d1534d`, `573786f`, `955bcc0`
- Exact historical diff: 19 paths, 1044 insertions, 431 deletions.

The branch was not merged, rebased, cherry-picked, or copied wholesale. Historical reports and governance were separated from intended behavior before porting.

## B. Historical claims versus observed implementation

| Historical claim | Fresh observation | Reconciliation result |
| --- | --- | --- |
| Evidence Claim Model | Historical `Evidence`/`ReliabilityClaim` used raw content, timestamp-derived IDs, and string-only source metadata. | Replaced with structured, subject-bound observations and deterministic claim IDs; raw evidence content is excluded. |
| Deterministic contradiction detection | Historical checks only searched shell text and literal `FAIL`/`ERROR`; no structured exit, doctor, artifact, tree, mutation, or subject checks. | Ported structured precedence: contradiction > wrong subject > stale > insufficient > supported. |
| Provider-neutral integration | Historical core had no strong provider branch but its tests were weak and integration was not current-contract safe. | Current core has no provider-specific identifiers/branches; provider observations remain adapter data. |
| QI/FW01 integration | Historical FW01 called missing `get_claims()`, never called `verify_claim()`, and passed obsolete `reliability_claims` to current-incompatible QI. | Current optional `aerg_result` input is consumed only by current QI; FW01 reads durable post-execution evidence at the existing seam. |
| A–Z / final handoff PASS | Historical report claimed 26/26 and sealed handoff, but the above defects falsify that authority. | Fresh 26-case matrix is the only A–Z result used here. |

## C. Stale assumptions and governance identified

- `C44`, `RI-011`, `RA-EXT-035`, and `RM-AERG` are historical/provisional labels, not current canonical identities.
- Historical capability family `QUALITY_EVIDENCE_EVALUATION` is not registered in the current capability-ledger schema. Current AERG is normalized to `VERIFICATION_AND_EVALUATION`.
- Historical QI fields and status assumptions were stale: `reliability_claims`, old `classify_risk` changes, and historical `RELIABILITY_CONTRADICTION` were not copied.
- Historical final reports are not current evidence; the historical bundle’s implementation-head field was stale relative to later branch commits.
- Current framework validator residuals remain outside scope: missing `origin_type` at capability index 170; three unregistered legacy families; dependency-integrity defects; freshness/origin-type defects; charter competitor-pattern/RAW_OUTPUT items; and missing `pr_lineage` declarations.

## D. Reconciliation decisions

1. Reuse current `EvidenceClaim`/`EvidenceClaim.effective_status()` as the evidence projection; do not create a second canonical truth store.
2. Keep AERG dimensions separate: assurance, subject binding, freshness, provenance, authority, and contradiction.
3. Use a bounded AERG decision (`SUPPORTED`, `CONTRADICTED`, `STALE`, `SUBJECT_MISMATCH`, `INSUFFICIENT`) only as evidence-layer output. It is not a project/release truth state.
4. Preserve the original claim string exactly and attach evidence/result metadata without rewriting it.
5. Feed current QI using existing failure classes: `QUALITY_CONFLICT`, `STALE_EVIDENCE`, `CERTIFICATION_SCOPE_MISMATCH`, and `MISSING_REQUIRED_EVIDENCE`.
6. Keep AERG lazy and post-execution in FW01; RF01 README-first orientation does not load it automatically.
7. Reconcile one current ledger record as `AI_EXECUTION_RELIABILITY_GUARD = FOUNDATION_READY`; no official/promotion status is implied.

## E. Exact files changed

Implementation and tests:

- `.p2p/system/p2p_capabilities/aerg_model.py` — new bounded model.
- `.p2p/system/p2p_capabilities/aerg_engine.py` — new deterministic evaluator.
- `.p2p/system/p2p_capabilities/tests/test_aerg_reconciliation.py` — A–Z and integration contract tests.
- `.p2p/system/p2p_capabilities/quality_intelligence.py` — optional current AERG input and existing failure mapping.
- `.p2p/system/p2p_capabilities/p2p_fw01_loop.py` — post-execution durable-evidence adapter and backward-compatible QI seam call.

Current development-plane documentation:

- `docs/p2p-development/capability-ledger/capability-index.json` — one foundation-only current record.
- `docs/p2p-development/current-roadmap.md` — derived count/family projection refresh.
- `docs/plans/2026-08-24-p2p-aerg-reconciliation/` — plan, evidence, benchmark, and actual-status artifacts.
- `reports/reconciliation/p2p-aerg-reconciliation-20260824.md` — this report.

No C43 source, `.19`, `.74`, release, deployment, host, Work Queue, Lane Registry, or Integration Queue file was changed.

## F. Claim/evidence/truth model

The current model is:

```text
original claim
    + exact subject binding (subject/source/tree/artifact/path/process where applicable)
    + structured evidence observation (ref/source/origin/time/fingerprint/status/exit/doctor/mutation)
    + assurance dimension (NONE/DECLARED/MECHANICAL/DETERMINISTIC)
    + freshness dimension (CURRENT/STALE/UNKNOWN)
    + provenance dimension (BOUND/INCOMPLETE/INVALID)
    + authority dimension (MECHANICAL/INDEPENDENT/NOT_PROVEN)
    + contradiction dimension (NONE/CONTRADICTED/NOT_PROVEN/UNKNOWN)
    -> bounded evidence decision
    -> existing QI contract only
```

Important boundaries:

- JSON validity, self-hash, an executor-written PASS, a local fixture, an artifact’s existence, or README prose cannot upgrade assurance.
- `NOT_RUN`, `UNKNOWN`, `WARN`, fixture, mock, internal-child, missing external ID, and same producer/verifier remain insufficient for the assurance they do not prove.
- AERG has no persistence API and no merge/promote/release/deploy API. Its result explicitly carries all authority-widening flags as false.

## G. A–Z deterministic results

Fresh matrix command: `py -X utf8 -m unittest discover -s .p2p/system/p2p_capabilities/tests -p 'test_aerg_reconciliation.py'`
Result: **12 tests passed; 26/26 matrix cases passed; exit 0**.

The previously unasserted required contradiction is now executable: claim
`"no files changed"` with `mutation_state=MUTATED` and a changed path returns
`CONTRADICTED`, preserves the original claim, preserves evidence references,
and includes `MUTATION_CONTRADICTS_NO_MUTATION`.

| Case | Result | Case | Result | Case | Result |
| --- | --- | --- | --- | --- | --- |
| A self-claim | INSUFFICIENT | J fixture != live | INSUFFICIENT | S unsupported PASS | INSUFFICIENT |
| B mechanical evidence | SUPPORTED | K mock != live | INSUFFICIENT | T claim preserved | SUPPORTED |
| C stale evidence | STALE | L internal != external | INSUFFICIENT | U provenance preserved | SUPPORTED |
| D wrong subject | SUBJECT_MISMATCH | M NOT_RUN != PASS | INSUFFICIENT | V assurance gate | INSUFFICIENT |
| E artifact SHA | CONTRADICTED | N UNKNOWN != VERIFIED | INSUFFICIENT | W authority no widening | SUPPORTED, NOT_PROVEN authority |
| F source commit | CONTRADICTED | O WARN != HEALTHY | INSUFFICIENT | X no second control plane | SUPPORTED |
| G Doctor contradiction | CONTRADICTED | P self-verification | INSUFFICIENT | Y runtime seam regression | SUPPORTED contract path |
| H exit-code contradiction | CONTRADICTED | Q fresh evidence | SUPPORTED | Z observed state wins | CONTRADICTED |
| I missing external ID | INSUFFICIENT | R provider neutrality | SUPPORTED |  |  |

Contradiction precedence was separately asserted: a wrong expected source commit plus a non-zero exit code returns `CONTRADICTED`, not `STALE` or `INSUFFICIENT`.

## H. Provider-neutrality results

The AERG core contains no `Manus`, `Codex`, `Claude`, or `Gemini` branch/name. The source guard found no provider-specific core identifiers, queue/scheduler/control-plane terms, or promotion/release/deploy methods. The model accepts provider-neutral structured observations; adapters may map provider-specific observations before they enter the core.

## I. QualityIntelligence/Fw01 integration results

- `QualityIntelligence.build_quality_verdict` accepts one optional `aerg_result` mapping; no historical `reliability_claims` parameter was restored.
- `CONTRADICTED` maps to existing `QUALITY_CONFLICT` and rejects the quality checkpoint.
- `STALE` maps to `STALE_EVIDENCE` and remains `QUALITY_UNKNOWN`/not checkpointable.
- `SUBJECT_MISMATCH` maps to `CERTIFICATION_SCOPE_MISMATCH` and remains fail-closed.
- `INSUFFICIENT` maps to `MISSING_REQUIRED_EVIDENCE` and rejects the checkpoint.
- FW01 derives the observation from the durable goal event/evidence pointer after execution, binds it to the current source commit, and invokes AERG lazily at the existing post-execution seam.
- Existing seam mocks without the optional parameter remain valid and info-only through signature-compatible invocation; real current QI receives AERG.
- The existing FW01 checkpoint suite passes 6/6; composition gate passes 7/7.

## J. Regression results

| Boundary | Result |
| --- | --- |
| AERG matrix/integration | 12 passed; 26/26 cases; exit 0; no-mutation assertion explicit |
| Existing QualityIntelligence | 44 passed, 1 skipped; exit 0 |
| Full hidden capability suite | 347 passed, 6 skipped; exit 0 |
| FW01 checkpoint quality gate | 6 passed; exit 0 |
| FW01 composition gate | 7 passed; exit 0 |
| Capability foundation | 28 passed; exit 0 |
| C43 reconciliation | 9 passed; exit 0 |
| RF01 orientation + packaging | 9 passed; exit 0 |
| Full compile boundary | exit 0; one unrelated pre-existing SyntaxWarning in `tests/test_p2p_live_certification.py` |
| Framework validator | 52/59; exactly 7 inherited failures, unchanged in class and outside AERG scope |
| Rail consolidation validator | exit 1 on inherited `/home/ubuntu/fw01_work/auth-f01` path assumption before ledger validation |
| FW01 closure self-reference test | inherited environment/scope failure: `.tmp/fw01_fill_report.py` absent and fixture invokes unavailable `python` shim; not caused by AERG |

No AERG-specific NEW_FAILURE was observed in the focused or full hidden suites.

## K. Inherited/new failure matrix

| Classification | Finding | Action |
| --- | --- | --- |
| NEW_FAILURE | None in AERG scoped tests, QI, FW01 checkpoint/composition, C43, or RF01 tests. | None. |
| RESOLVED_VERIFICATION_EVIDENCE_GAP | No-mutation contradiction was previously constructed but not asserted. | Explicit decision, contradiction, and stable-reason assertions added; prior Supervisor REJECT retained as historical evidence. |
| RESOLVED_INHERITED_FAILURE | Historical AERG’s missing `get_claims()`/unverified-claim path and obsolete QI argument. | Replaced by current `aerg_result` contract and explicit evaluation. |
| RESOLVED_INHERITED_FAILURE | Historical raw-content/timestamp-ID/no-subject-binding behavior. | Replaced by structured exact binding, deterministic IDs, and current EvidenceClaim projection. |
| INHERITED_FAILURE | Seven framework-validator failures listed in section C. | Preserved; no cleanup-by-proximity. |
| INHERITED_FAILURE | Rail validator hard-coded external Linux path. | Preserved; no host/environment mutation. |
| INHERITED_FAILURE | FW01 closure fixture missing from this worktree and uses unavailable `python` alias. | Preserved; outside AERG. |

## L. Anti-overengineering audit

The reconciled slice adds exactly two runtime modules, one focused test module, and two narrow integration edits. It adds no database, event bus, vector store, distributed verifier, scheduler, Work Queue, Lane Registry, Integration Queue, policy DSL, second router, second release gate, or persistent evidence store. AERG remains in-memory and subordinate to current evidence/QI/role/owner authority.

## M. Exact current status: `.19`, `.74`, CPT01-R2, RF01, C43

- `.19`: `PROMOTED_VERIFIED`; governance authority SHA-256 remains `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`. The referenced `.19` ZIP is not present in this target worktree, so no file-level artifact rehash is claimed.
- `.74`: `SEALED_UNPROMOTED / NONCANONICAL`; candidate artifact `reports/candidates/P2P-8.4.7-C-Codex-Edition-v74.zip` rehashes to the governance-bound `2b82dea10695abb1c99253be1205728335a114df42cececde2fcca5c1727fd12`. No `.74` artifact or authority field was modified.
- CPT01-R2: `EXTERNAL_HOST_CAPABILITY_LIMITATION`.
- RF01: independently verified; README-first orientation tests remain 7/7 and packaging 2/2. AERG is not automatically loaded by orientation.
- C43: independently verified and owner-approved for development-plane closure; C43 regression remains 9/9. No C43 reconciliation semantics were changed.
- `promotion.allowed`: remains `false` under the current development-plane authority boundary.

## N. Next safe Goal

`P2P_AERG_SUPERVISOR_REREVIEW_02`: independently re-review the repaired subject at source checkpoint `c99145f`, scoped fingerprint `bd14ca273d5c35fe02d177e329d24b73915f09ab89d079d0daf99124780f0d9c`, and this report’s final bytes. Re-review must confirm the exact no-mutation assertion, production-source immutability, preserved prior REJECT, and seven inherited framework failures. Any later independent verification or promotion-readiness work is a separate owner-authorized goal; this repair does not authorize it.

**Hard stop:** do not start Work Queue, Lane Registry, Integration Queue, promotion, release, deployment, or host mutation from this result.
