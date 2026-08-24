# Supervisor Review — AERG Stale-Evidence Production Repair

## Review metadata

- Reviewer: GPT-5 Codex Supervisor
- Review mode: read-first, no repair, no feature development
- Review date: 2026-08-24 (Asia/Saigon)
- Workspace: `D:\AI\P2P_dev\P2P-upgrade-github\.tmp\p2p-post74-development-01`
- Branch: `codex/p2p-post74-development-01`
- Reviewed base HEAD: `45ef5a29ff549199293ad0ea389abba91460caf0`
- Repair subject: `5273133` (`Test: assert serialized AERG stale contract`)
- Production repair: `a10be51` (`Fix: fail closed on stale AERG evidence`)
- Test-first RED commit: `11c3e9e`
- Prior independent REJECT: `430c47d868da084771afc9fbae039f4d4dda637a`
- Evidence handoff commit: `45ef5a29ff549199293ad0ea389abba91460caf0`
- Claimed terminal under review: `P2P_AERG_STALE_EVIDENCE_REPAIR_READY_FOR_SUPERVISOR_REVIEW`

## Verdict

**PASS**

The stale-evidence repair is accepted for the explicitly permitted independent-review handoff. The AERG production defect is reproduced before the repair, the production change is minimal and localized, the required stale/contradiction/fresh/serialization/QI/FW01/no-mutation invariants are independently closed, the full capability regression suite is green, and the seven framework-validator failures are unchanged inherited failures outside this repair subject.

This review did not launch independent verification, request Owner approval, create a Goal, promote, release, deploy, publish, or mutate a host.

## Exact claim and acceptance boundary

The claim reviewed was:

> AERG must fail closed when evidence is stale because of age or explicit stale metadata; stale evidence must remain visible in serialized output; contradiction precedence must be preserved; actual stale AERG output must be rejected by Quality Intelligence; the FW01 seam must continue to use the real AERG/QI path; no-mutation contradiction behavior must remain closed; the existing A–Z baseline must remain green with two freshness extensions; and unrelated protected state must remain unchanged.

The review boundary was the current development worktree and the exact ancestry above. No result here is an Owner approval, an independent verification certificate, a promotion decision, or a release/deployment authorization.

## A. Subject and ancestry

Fresh ancestry checks returned exit code 0 for all four links:

1. `430c47d` → `11c3e9e`
2. `11c3e9e` → `a10be51`
3. `a10be51` → `5273133`
4. `5273133` → `45ef5a2`

Commit-role inspection shows:

- `11c3e9e` adds the regression cases and repair plans.
- `a10be51` changes only `.p2p/system/p2p_capabilities/aerg_engine.py`.
- `5273133` changes only `.p2p/system/p2p_capabilities/tests/test_aerg_reconciliation.py` for serialized-contract assertions.
- `45ef5a2` adds only evidence/report documents; it does not change the repair source or test.

The coder report records `Current HEAD: 5273133`, while the actual review base is its later evidence-only descendant `45ef5a2`. This is a historical report-metadata snapshot, not a source or test divergence: the scoped source/test blobs and diffs confirm that the repair subject remains `5273133`.

## B. Independent pre-repair reproduction

The parent version of `aerg_engine.py` was loaded from Git (`a10be51^`) without modifying the worktree. With the current unchanged model/QI dependencies, the parent produced:

```text
PARENT_AGE_EXPIRED SUPPORTED VERIFIED CURRENT ['EVIDENCE_EXPIRED']
PARENT_EXPLICIT_STALE SUPPORTED VERIFIED CURRENT ['EVIDENCE_NOT_CURRENT']
PARENT_STALE_CONTRADICTION CONTRADICTED CONTRADICTED CURRENT ['EVIDENCE_EXPIRED', 'EXIT_CODE_CONTRADICTS_PASS']
PARENT_QI QUALITY_VERIFIED True []
PRE_REPAIR_REPRODUCTION_CONFIRMED
```

This independently confirms both parts of the prior REJECT: stale evidence was aggregated as `CURRENT`, and a stale contradiction lost its freshness signal before QI evaluation.

## C. Production diff and root-cause clearance

The production diff is exactly one file with 3 insertions and 1 deletion:

`.p2p/system/p2p_capabilities/aerg_engine.py`

The repair makes aggregate freshness derive from the observations themselves, then explicitly records `STALE` in the observation decision list. It does not add a new subsystem, state machine, queue, scheduler, persistence layer, provider branch, router, or authority path. Existing aggregate precedence remains:

`CONTRADICTED > SUBJECT_MISMATCH > STALE > INSUFFICIENT > SUPPORTED`.

Protected production quartet blob checks show no repair-subject change to `aerg_model.py`, `quality_intelligence.py`, or `p2p_fw01_loop.py`.

Current filesystem SHA-256 evidence:

```text
aerg_engine.py       0B14D04B3326D88FC8DDB4EE5FD8F8C7C570F517A262749BEF5F25F196D1BE2F
aerg_model.py        60500940266BC08DE151FF1BBFCB1B2541E5B3700BC841435A12D5CBDC533B61
quality_intelligence.py
                     4A2DFCFDEC0959C9F416045D9E9F8F9D2DCFFDBF1996E10C7EDB8D96EAE47702
p2p_fw01_loop.py     97EF5FB0F86D27440F5BE500420296CFFB461EB7E5660E183B75D0685FB91AC1
test_aerg_reconciliation.py
                     EF79D8429C2C01A8B8C4B91B1CD25E41174191FF4B7A7105BB72EEE1A20DCBA8
```

## D–K. Required invariant probes

The current source was probed directly with real `AERGEngine` and `EvidenceObservation` objects. The actual outputs were:

```text
AGE_EXPIRED STALE INCOMPLETE STALE ['EVIDENCE_EXPIRED']
EXPLICIT_STALE STALE INCOMPLETE STALE ['EVIDENCE_NOT_CURRENT']
STALE_CONTRADICTION CONTRADICTED CONTRADICTED STALE ['EVIDENCE_EXPIRED', 'EXIT_CODE_CONTRADICTS_PASS']
FRESH_VALID SUPPORTED VERIFIED CURRENT []
SERIALIZED STALE INCOMPLETE STALE
SERIALIZED STALE INCOMPLETE STALE
SERIALIZED CONTRADICTED CONTRADICTED STALE
QI_ACTUAL_STALE QUALITY_UNKNOWN False ['STALE_EVIDENCE']
NO_MUTATION CONTRADICTED CONTRADICTED ['MUTATION_CONTRADICTS_NO_MUTATION']
CURRENT_REPAIR_DIRECT_PROBE_PASS
```

These results close the following required points:

- Age-only expiry is `STALE`, not `SUPPORTED` or `CURRENT`.
- Explicit stale metadata is `STALE`, not `VERIFIED` or `CURRENT`.
- Stale plus contradiction remains `CONTRADICTED` while retaining freshness `STALE`.
- A fresh valid observation remains `SUPPORTED / VERIFIED / CURRENT`.
- `AERGResult.to_dict()` preserves status, decision, and freshness for stale and contradictory cases.
- The QI probe used the actual stale AERG result, not a synthetic result, and returned `QUALITY_UNKNOWN` with `STALE_EVIDENCE`.
- The no-mutation contradiction remains `CONTRADICTED / CONTRADICTED` with `MUTATION_CONTRADICTS_NO_MUTATION`.

The current QI source maps `STALE` to `STALE_EVIDENCE`, makes the verdict `QUALITY_UNKNOWN`, and allows checkpoint quality only for `SUCCESS` plus `QUALITY_VERIFIED`. The FW01 source still calls `loop.step()` and uses the lazy post-execution real AERG/QI seam; no FW01 production source changed.

## L. A–Z and freshness extensions

The reconstructed standalone semantic baseline reported:

```text
AZ_BASELINE_PASS 26/26
FRESHNESS_EXTENSIONS_PASS 2/2
SEMANTIC_COVERAGE 26_BASELINE_PLUS_2_EXTENSIONS
```

The two extensions are the age-only expiry and explicit-stale cases. The stale-contradiction and serialization assertions are additionally exercised by the current AERG test module and direct probes.

## M. Regression and boundary validation

Fresh validation evidence:

| Boundary | Result |
|---|---|
| AERG reconciliation tests | 17 tests, exit 0, `OK` |
| Freshness-focused AERG subset | 5 tests, exit 0, `OK` |
| Quality Intelligence tests | 44 tests, exit 0, `OK (skipped=1)` |
| C43 + RF01 framework/orientation/packaging tests | 18 tests, exit 0, `OK` |
| Capability compile check | exit 0 |
| FW01 checkpoint quality gate | 6 tests, exit 0, `OK`, 257.177 seconds |
| Full capability test suite | 352 tests, exit 0, `OK (skipped=6)`, 357.459 seconds |

The full suite emitted only the known `ResourceWarning` messages from `test_bounded_documentation_write.py`; there were no test failures. One initial FW01 invocation without the required `PYTHONPATH` had an import error; the canonical invocation with `.p2p/system` on `PYTHONPATH` passed all six FW01 tests. The initial invocation is classified as a harness-command error, not a product failure.

## N. Framework validator

The fresh validator returned exit code 1 with `52/59 checks passed`. The seven failures are exactly the inherited classes already present before this repair:

```text
V01-schema-valid
V03-family-registered
V05-dep-integrity
V09-freshness-vocab
V06-charter-no-competitor-patterns
V12-origin-type-valid
V20-pr-lineage-declared
```

The validator, governance files, candidate artifacts, release/deploy paths, and CPT01-R2 paths have no repair-subject changes. Therefore these are `INHERITED_FAILURE` findings with `NEW_FAILURE=0`, not evidence that the AERG production repair regressed the framework. This review does not relabel the overall framework validator as green.

## O. Prior REJECT preservation

The prior independent REJECT report remains unchanged. A scoped Git comparison from `430c47d` through the review base produced no change for the prior independent report. Its original terminal remains preserved as audit history:

`P2P_AERG_REJECTED_EXPIRED_EVIDENCE_RETURNS_SUPPORTED`

The prior Supervisor REJECT on the earlier no-mutation assertion gap is also preserved. The current direct probe and current tests close that earlier gap without rewriting either historical report.

## P. Protected state and worktree integrity

Fresh protected-state inspection found:

```text
official version/status  8.4.7-C-codex.19 / PROMOTED_VERIFIED
official SHA-256         3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8
development version      8.4.7-C-codex.74
development SHA-256      2b82dea10695abb1c99253be1205728335a114df42cececde2fcca5c1727fd12
development status       SEALED_UNPROMOTED
plane status             ACTIVE_NONCANONICAL_NO_PROMOTION
promotion.allowed        False
promotion reason         external GitHub private repository host-protection limitation
CPT01-R2 status          HOST_CAPABILITY_BLOCKED
CPT01-R2 blocker         EXTERNAL_HOST_CAPABILITY_LIMITATION
CPT01-R2 preserved       True
```

No scoped diff was found in governance, candidate, release/deploy, or CPT01-R2 paths. The broader worktree remains dirty with owner changes; those changes were preserved. The review report was written as an additional evidence artifact only.

## Anvien evidence boundary

Anvien was refreshed before graph inspection:

```text
analyze exit 0
scanned 899
parsed_code 164
failed 0
documents 536
metadata 189
scripts 8
graph nodes 37511
graph relationships 43326
```

The hidden `.p2p/system/p2p_capabilities/aerg_engine.py` path was not resolved by the current Anvien repository index (`file-detail` reported not found; file impact reported `not_found`). This is disclosed as an evidence limitation, not converted into a false zero-impact claim. Direct Git ancestry/blob/diff checks, source inspection, dynamic probes, and real test execution supplied the review evidence. Anvien change detection saw only the known owner-dirty `adapter_registry.json` and no affected files for the repair scope.

## Source clearance and residual risk

- No production source was edited during this Supervisor review.
- No test, governance, candidate, release, deployment, or protected baseline was repaired during this review.
- No provider-specific branch, persistence route, scheduler, queue, router, or second certification system was introduced.
- No residual unverified surface remains for the requested stale-evidence invariants within the reviewed source/test boundary.
- External host-protection limitation remains a real, preserved promotion blocker; it is outside this local AERG repair and was not bypassed.
- Framework-validator inheritance remains visible and is not being promoted to PASS.

## Final terminal

```text
P2P_AERG_STALE_EVIDENCE_SUPERVISOR_PASS_FOR_INDEPENDENT_REVIEW_HANDOFF
```

Hard stop. No independent verification task, Owner approval request, next Goal, promotion, release, deployment, publication, or host mutation was performed.
