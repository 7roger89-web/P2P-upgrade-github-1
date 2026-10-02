# P2P Capability Drift Revalidation Sweep - evidence report

- Sweep schema: `p2p-capability-drift-sweep/1` (generated 2026-10-02T07:15:35Z)
- Swept tree: `a9ece0c26e5b4aef52629d2a6dc0122eb14d2d15` / tree `83230c9c0c80ebbd3b4311f0ebb444fcf6a92a28` (branch `arena/01a0fb13-p2p-upgrade-github-1`)
- Capability index: `docs/p2p-development/capability-ledger/capability-index.json` sha256 `40c82d77c13ec17d8ed10475529a076af48c9d993040ae2cad0da36b00d02515`
- Drift policy sha256: `c023e8e1a5a0cd83c1c6efae5f96016b28d1c9febb92faea94e16654e6ba1833`

## Totals

- total capability records accounted for: **191** (capability index: 191)
- VERIFIED_AT_EVIDENCE_TIME: **186**
- UNKNOWN_NOT_PROBED: **5**
- live-dependent records (flag only, never infer eligibility): 38
- records asserting current external eligibility: 0
- stale claims found: 1 (disclosed in-record: 1; pending reconciliation: 0)
- live probes run: 0

## Classification semantics

`VERIFIED_AT_EVIDENCE_TIME` means current exact-tree repository evidence is
sufficient to verify the bounded claim the record makes *now*. For records whose
status is PLANNED/DEFERRED/REJECTED/UNKNOWN the verified claim is only that the
record and its provenance exist and that no implementation or runtime eligibility
is being asserted. `implementation_eligibility` distinguishes that explicitly:
`STATICALLY_SUPPORTED` (current source/contract resolves) versus `NOT_CLAIMED`
(record/provenance only) versus `NOT_PROBED`.

`UNKNOWN_NOT_PROBED` means current eligibility cannot be freshly proven from
authorized evidence now (unre-probed live/provider/host dependence, or declared
anchors that do not resolve in the current tree). Historical certification stays
historical and is never promoted to current eligibility.

`live_dependency=yes` marks records that concern volatile external state; it is
an information flag and never implies current eligibility.

## Records by original status

| status | records |
| --- | --- |
| DEFERRED | 8 |
| FOUNDATION_READY | 44 |
| PARTIAL | 9 |
| PLANNED | 38 |
| REJECTED | 15 |
| UNKNOWN | 1 |
| VERIFIED_IMPLEMENTED | 76 |

## UNKNOWN_NOT_PROBED records (5)

| capability_id | status | reason | live | disclaimer |
| --- | --- | --- | --- | --- |
| ATLAS_CAPSULE | PARTIAL | DECLARED_IMPLEMENTATION_ANCHOR_IS_NON_DURABLE_STATE | yes | no |
| CONTEXT_CAPSULES | PARTIAL | DECLARED_IMPLEMENTATION_ANCHOR_IS_NON_DURABLE_STATE | yes | no |
| GOAL_CLOSURE_INTEGRITY_CHECK | FOUNDATION_READY | NO_DECLARED_IMPLEMENTATION_ANCHOR | no | no |
| DETERMINISTIC_CANDIDATE_REQUIREMENT_POLICY | FOUNDATION_READY | NO_DECLARED_IMPLEMENTATION_ANCHOR | no | no |
| LIVE_CERTIFICATION_RECORD | FOUNDATION_READY | NO_CURRENT_TREE_EVIDENCE_ANCHOR | yes | yes |

## Current-eligibility claims expired or corrected (2)

- **MANUS_EXECUTION_TARGET** (VERIFIED_IMPLEMENTED, `VERIFIED_AT_EVIDENCE_TIME`): asserted `được chứng nhận` and now carries an explicit historical/UNKNOWN_NOT_PROBED disclaimer, so the historical certification is retained as history and is not current eligibility.
- **LIVE_CERTIFICATION_RECORD** (FOUNDATION_READY, `UNKNOWN_NOT_PROBED`): asserted `currently eligible` and now carries an explicit historical/UNKNOWN_NOT_PROBED disclaimer, so the historical certification is retained as history and is not current eligibility.

## Stale claims found (1)

- **SAFE_INSTALLER** (VERIFIED_IMPLEMENTED, declared freshness `verified_against_filesystem`, action `DISCLOSED_IN_RECORD_HISTORY_PRESERVED`): `reports/PILOT_INSTALLATION_EVIDENCE.md` (ABSENT_IN_TREE)

## Structural findings (13)

- **SECURE_HOST_CONNECTION_ONBOARDING**: LEGACY_NESTED_IMPLEMENTATION_SHAPE(first_implementation.artifacts), MISSING_FIELD:name, MISSING_FIELD:principle
- **GOAL_CLOSURE_INTEGRITY_CHECK**: MISSING_FIELD:name
- **DETERMINISTIC_CANDIDATE_REQUIREMENT_POLICY**: MISSING_FIELD:name
- **C29_GOAL_CLOSURE_PACKAGING**: MISSING_FIELD:name
- **C30_COMPOSABLE_EXECUTION_TARGET_PACKAGING**: MISSING_FIELD:name
- **ZERO_TO_PROJECT_INTENT_COMPILER**: MISSING_FIELD:origin_type
- **LARGE_GOAL_COMPLETENESS**: MISSING_FIELD:origin_type
- **CONTEXT_INTELLIGENCE_COMPLETENESS**: MISSING_FIELD:origin_type
- **GOAL_DESIGN_INTELLIGENCE_COMPOSITION**: MISSING_FIELD:origin_type
- **BOUNDED_CODE_MUTATION_PRIMITIVE**: MISSING_FIELD:origin_type
- **ORCA_BOUNDED_CANDIDATE_FANOUT**: MISSING_FIELD:origin_type
- **MULTIHOST_COUNCIL_CERTIFICATION**: MISSING_FIELD:origin_type
- **RELEASE_INSTALL_LIFECYCLE_HARDENING**: MISSING_FIELD:origin_type

## Requires later Owner decision

- UNKNOWN_NOT_PROBED records keep their honest state. Converting any of them to VERIFIED requires new authorized evidence (a fresh live probe, or a resolvable current-tree anchor for an implementation claim); this sweep must not manufacture it.
- Records with structural findings do not satisfy the capability-ledger schema (missing required fields and/or the legacy nested implementation shape). Normalising them is a separate bounded change and was deliberately not performed by this read-only sweep.

Machine-readable sweep: `docs/p2p-development/capability-ledger/capability-drift-sweep.json`
