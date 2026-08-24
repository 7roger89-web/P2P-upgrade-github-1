# Independent Verification Report — AERG After Stale-Evidence Repair

Verdict: REJECT

## Metadata

- Report file: reports/supervisor/rp_supervisor_260824_184807_by_gpt-5-codex_aerg-independent-verification-after-repair.md
- Review time: 260824 184807 Asia/Saigon
- Reviewer: gpt-5-codex
- Repo/project: P2P-upgrade-github
- Worktree: D:\AI\P2P_dev\P2P-upgrade-github\.tmp\p2p-post74-development-01
- Branch: codex/p2p-post74-development-01
- Review-base HEAD: ad39230bda202f12a749f2068041c7ccd1840779
- Scope reviewed: AERG stale-evidence repair chain through the current ad39230 report-only descendant
- Claim reviewed: P2P_AERG_STALE_EVIDENCE_SUPERVISOR_PASS_FOR_INDEPENDENT_REVIEW_HANDOFF
- Authority used: current user Independent Verification brief, current AGENTS.md, capability execution/evidence and foundation specifications, Git/source/runtime evidence
- Related artifacts: 430c47d, 11c3e9e, a10be51, 5273133, 45ef5a2, ad39230, and the preserved prior REJECT report
- No repair boundary: no production source, test, governance, candidate, release, deployment, or host state was edited by this review

## Executive Summary

The core AERG repair works in its direct engine path: age-expired and explicit-stale evidence fail closed, serialization preserves stale truth, contradiction precedence remains correct, actual current QI rejects a stale AERG result, and fresh evidence remains supported. The exact A–Z reconstruction is 26/26, the two required freshness extensions are 2/2, and the fresh regression suites have zero test failures.

Acceptance nevertheless fails because the broader invariant is not closed:

1. The real FW01 step path can checkpoint an actual stale AERG observation as VERIFIED when its compatibility QI callable does not accept aerg_result and returns checkpoint_allowed=True. The compatibility seam drops the stale AERG input and trusts the returned decision.
2. The production build_quality_verdict API accepts required-evaluation statuses STALE, EXPIRED, WARN, and UNKNOWN without classifying them as failures. With SUCCESS execution and a declared required evaluation, it returns QUALITY_VERIFIED and checkpoint_allowed=True.

Both are execution-backed fail-open paths beyond the currently added AERG actor tests. The Supervisor PASS and stored test counts do not close them.

## Blocking Findings

### [HIGH] FW01 compatibility QI seam checkpoints an actual stale AERG result

Finding type: Confirmed Failure

Perturbation: Run the real Fw01Loop.step() on an isolated Git worktree, force the execution observation timestamp to 2026-08-24T11:50:00+00:00 while the AERG contract clock is 2026-08-24T12:00:00+00:00, and replace only the QI callable with a compatibility-signature function that omits aerg_result and returns QUALITY_VERIFIED / checkpoint_allowed=True.

Source path: .p2p/system/p2p_capabilities/p2p_fw01_loop.py:914-937 and .p2p/system/p2p_capabilities/p2p_fw01_loop.py:969-1038.

Expected: the stale AERG result must force a non-checkpointing quality outcome, QUALITY_REVIEW, and a blocked stop regardless of QI compatibility shape.

Actual execution output:

~~~
COMPAT_QI.out.status                    TASK_DONE_CONTINUE
COMPAT_QI.checkpoint.verification_state VERIFIED
COMPAT_QI.checkpoint.loop_status        CHECKPOINTED
COMPAT_QI.checkpoint.next_safe_action   NONE
~~~

The same run used the current AERG engine through the actual FW01 post-execution path. The clock perturbation produced a stale observation; the compatibility branch omitted aerg_result based on signature inspection, then accepted the compatibility return. This violates the invariant that stale evidence cannot reach VERIFIED or a checkpoint.

The canonical current QI path was also exercised with the same real FW01 path and correctly returned STOP_BLOCKED, QUALITY_REVIEW, and loop_status=BLOCKED. That does not close the compatibility path.

Broken invariant: execution -> durable observation -> AERG -> QI -> checkpoint must fail closed for stale evidence across both current and compatibility seams.

### [HIGH] QI required-evaluation status path upgrades stale/unknown evidence to verified

Finding type: Confirmed Failure

Perturbation: Call the production quality_intelligence.build_quality_verdict() directly with execution_status="SUCCESS", declared_required_evals={"stale": {}}, and each of the following required result values: STALE, EXPIRED, WARN, and UNKNOWN.

Source path: .p2p/system/p2p_capabilities/quality_intelligence.py:697-767.

Expected: a required result that is stale, expired, warning, or unknown must not be treated as proof and must not allow checkpointing.

Actual output for all four values:

~~~
quality_status=QUALITY_VERIFIED
checkpoint_allowed=True
quality_failures=()
~~~

The function currently recognizes only a small set of failure strings in this loop (FAIL*, REJECTED, EVAL_FAILED, NOT_AVAILABLE); unrecognized non-proof statuses fall through to the verified branch. The actual AERG-result parameter path does reject a real stale AERG result, but this alternate required-evaluation path remains fail-open.

Broken invariant: UNKNOWN != VERIFIED, WARN != HEALTHY, and stale/expired evidence must not become QUALITY_VERIFIED through a generic QI input surface.

## A. Exact subject and ancestry

Fresh Git checks established:

~~~
root   D:/AI/P2P_dev/P2P-upgrade-github/.tmp/p2p-post74-development-01
branch codex/p2p-post74-development-01
HEAD   ad39230bda202f12a749f2068041c7ccd1840779
~~~

Every required ancestry edge returned exit code 0:

~~~
430c47d -> 11c3e9e exit=0
11c3e9e -> a10be51 exit=0
a10be51 -> 5273133 exit=0
5273133 -> 45ef5a2 exit=0
45ef5a2 -> ad39230 exit=0
~~~

The executable repair subject is 5273133, with production behavior introduced by a10be51. The actual current HEAD is the report-only descendant ad39230, not 5273133; Git truth was used for all subject binding.

The preserved prior report exists at:

reports/supervisor/rp_supervisor_260824_165924_by_gpt-5-codex_p2p-aerg-independent-verification.md

and still contains:

P2P_AERG_REJECTED_EXPIRED_EVIDENCE_RETURNS_SUPPORTED

## B. Production/report commit separation

The repair chain is separated as follows:

- a10be51: one production file, .p2p/system/p2p_capabilities/aerg_engine.py, 3 insertions and 1 deletion.
- 5273133: one AERG test file, serialization assertions only.
- 45ef5a2: six evidence/plan/report documents only.
- ad39230: one Supervisor report artifact only.

Fresh git diff --name-status 5273133..HEAD -- .p2p/system/p2p_capabilities returned no output. The only post-5273133 production blobs are unchanged:

~~~
aerg_engine.py       527=c8e77ed8fe899d1ccfeb553843f60fff570789a7
                     HEAD=c8e77ed8fe899d1ccfeb553843f60fff570789a7
aerg_model.py        527=a54c951c2d839a769120481f302de7743d348c8e
                     HEAD=a54c951c2d839a769120481f302de7743d348c8e
quality_intelligence.py
                     527=fe3834363c6227018a973627942650c69401fb0e
                     HEAD=fe3834363c6227018a973627942650c69401fb0e
p2p_fw01_loop.py     527=51a1000a3348c36121c75dc08814fd62ad4c112a
                     HEAD=51a1000a3348c36121c75dc08814fd62ad4c112a
~~~

The prior independent REJECT report has no Git diff from 430c47d through the review base. No report was used as authority for the runtime conclusions.

## C. Age-expiry findings

Fresh direct AERG construction with otherwise-valid mechanical evidence and observation age ten minutes against a five-minute window returned:

~~~
decision=STALE
status=INCOMPLETE
freshness=STALE
reason=EVIDENCE_EXPIRED
~~~

No SUPPORTED, VERIFIED, or CURRENT value appeared in this direct age-only result.

Independent pre-repair reproduction from a10be51^ returned the old unsafe result:

~~~
decision=SUPPORTED
status=VERIFIED
freshness=CURRENT
reason=EVIDENCE_EXPIRED
~~~

## D. Explicit-stale findings

Fresh direct AERG construction with EvidenceObservation.freshness="STALE" returned:

~~~
decision=STALE
status=INCOMPLETE
freshness=STALE
reason=EVIDENCE_NOT_CURRENT
~~~

The parent implementation independently reproduced the old unsafe SUPPORTED / VERIFIED / CURRENT result with EVIDENCE_NOT_CURRENT.

## E. Threshold and timestamp boundary findings

The source contract uses age > timedelta(seconds=freshness_seconds). Fresh probes produced:

| Probe | Result |
|---|---|
| clearly inside, 299 seconds | SUPPORTED / VERIFIED / CURRENT |
| exactly 300 seconds | SUPPORTED / VERIFIED / CURRENT |
| just beyond, 301 seconds | STALE / INCOMPLETE / STALE, EVIDENCE_EXPIRED |
| timezone-aware exact-boundary -05:00 | SUPPORTED / VERIFIED / CURRENT after UTC normalization |
| timezone-aware just beyond | STALE / INCOMPLETE / STALE |
| malformed timestamp | INSUFFICIENT / INCOMPLETE / UNKNOWN, OBSERVED_AT_INVALID |
| timezone-naive timestamp | INSUFFICIENT / INCOMPLETE / UNKNOWN, OBSERVED_AT_INVALID |
| future timestamp | INSUFFICIENT / INCOMPLETE / UNKNOWN, OBSERVED_AT_IN_FUTURE |

The implementation therefore defines the exact threshold as inclusive. The reviewed SPEC cluster does not separately state inclusive versus exclusive boundary semantics; this is a contract-documentation ambiguity worth an Owner decision if the boundary policy is intended to change. It did not produce a false CURRENT result beyond the source-defined threshold.

## F. Multi-evidence aggregation findings

Fresh direct aggregation results:

| Combination | Decision | Status | Freshness |
|---|---|---|---|
| one CURRENT + one STALE | STALE | INCOMPLETE | STALE |
| multiple STALE | STALE | INCOMPLETE | STALE |
| STALE + SUBJECT_MISMATCH | SUBJECT_MISMATCH | INCOMPLETE | STALE |
| STALE + CONTRADICTED | CONTRADICTED | CONTRADICTED | STALE |
| UNKNOWN + STALE | STALE | INCOMPLETE | STALE |
| fresh supporting + stale supporting | STALE | INCOMPLETE | STALE |

Material staleness is not silently erased by current AERG aggregation. Contradiction still has precedence while stale freshness remains visible.

## G. Stale plus contradiction findings

Fresh direct construction with expired evidence and exit_code=1 returned:

~~~
decision=CONTRADICTED
status=CONTRADICTED
freshness=STALE
reasons=EVIDENCE_EXPIRED, EXIT_CODE_CONTRADICTS_PASS
~~~

The result is correct at the AERG engine boundary. The parent reproduction returned CONTRADICTED / CONTRADICTED / CURRENT, confirming that the repair specifically restored the lost stale signal without weakening contradiction precedence.

## H. Serialization findings

Fresh AERGResult.to_dict() checks for age-only stale, explicit stale, and stale-plus-contradiction returned respectively:

~~~
STALE INCOMPLETE STALE
STALE INCOMPLETE STALE
CONTRADICTED CONTRADICTED STALE
~~~

The current aerg_model.py serialization includes decision, status, freshness, reasons, and the fail-closed authority flags. No serialization downgrade to SUPPORTED / VERIFIED / CURRENT was observed.

## I. QI and FW01 end-to-end findings

### Actual current QI path

The actual current stale AERG result was passed first through AERGResult.as_quality_input() and then through AERGResult.to_dict() to the real quality_intelligence.build_quality_verdict() function. Both returned:

~~~
quality_status=QUALITY_UNKNOWN
quality_failures includes STALE_EVIDENCE
checkpoint_allowed=False
~~~

For the direct QI call, execution_status=SUCCESS did not upgrade the actual stale AERG result.

### Actual current FW01 path

The real Fw01Loop.step() path was executed in an isolated Git worktree with a stale observation timestamp. With the current QI module, it returned:

~~~
status=STOP_BLOCKED
reason=QUALITY_REVIEW_REQUIRED
quality_status=QUALITY_REJECTED
checkpoint.verification_state=QUALITY_REVIEW
checkpoint.loop_status=BLOCKED
~~~

This current path is safe for the tested stale clock perturbation.

### Compatibility bypass

The same real FW01 path with a compatibility-signature QI callable returned TASK_DONE_CONTINUE and persisted VERIFIED / CHECKPOINTED, as recorded in the blocking finding above. This is not a test-only source assertion: the production FW01 code actively performs signature-based compatibility dispatch and then trusts the returned checkpoint_allowed field.

## J. No-mutation and sibling invariant regression

Fresh no-mutation construction preserved the original claim and returned:

~~~
decision=CONTRADICTED
status=CONTRADICTED
reason=MUTATION_CONTRADICTS_NO_MUTATION
~~~

Adversarial provenance/authority probes also remained closed:

| Case | Result |
|---|---|
| wrong subject | SUBJECT_MISMATCH / INCOMPLETE |
| expected source commit mismatch | CONTRADICTED / CONTRADICTED |
| subject source commit stale | STALE / INCOMPLETE |
| expected artifact SHA mismatch | CONTRADICTED / CONTRADICTED |
| same producer/verifier self-verification | INSUFFICIENT / INCOMPLETE |
| fixture or mock presented as live | INSUFFICIENT / INCOMPLETE |
| missing external ID | INSUFFICIENT / INCOMPLETE |
| NOT_RUN | INSUFFICIENT / INCOMPLETE |
| WARN | INSUFFICIENT / INCOMPLETE |
| UNKNOWN | INSUFFICIENT / INCOMPLETE |

Current production SHA-256 values were freshly re-derived:

~~~
aerg_engine.py              0B14D04B3326D88FC8DDB4EE5FD8F8C7C570F517A262749BEF5F25F196D1BE2F
aerg_model.py               60500940266BC08DE151FF1BBFCB1B2541E5B3700BC841435A12D5CBDC533B61
quality_intelligence.py     4A2DFCFDEC0959C9F416045D9E9F8F9D2DCFFDBF1996E10C7EDB8D96EAE47702
p2p_fw01_loop.py            97EF5FB0F86D27440F5BE500420296CFFB461EB7E5660E183B75D0685FB91AC1
test_aerg_reconciliation.py EF79D8429C2C01A8B8C4B91B1CD25E41174191FF4B7A7105BB72EEE1A20DCBA8
~~~

The production diff remains anti-overengineered: only aerg_engine.py changed in a10be51; aerg_model.py, quality_intelligence.py, and p2p_fw01_loop.py are unchanged from the repair subject. No new state machine, freshness subsystem, database, scheduler, queue, router, daemon, verifier, promotion path, or release path was introduced.

## K. A–Z plus freshness adversarial result

The A–Z matrix was reconstructed from the current source with the exact minimal fixture shape used by the matrix, not by reading the stored test count:

~~~
AZ_BASELINE_INDEPENDENT=26/26
AZ_FAILURES={}
FRESHNESS_EXTENSIONS_INDEPENDENT=2/2
~~~

The two required extensions were independently observed as:

~~~
age-only       STALE / INCOMPLETE / STALE / EVIDENCE_EXPIRED
explicit stale STALE / INCOMPLETE / STALE / EVIDENCE_NOT_CURRENT
~~~

A preliminary exploratory script used an extra artifact field and was discarded as evidence; the exact-fixture rerun above is the authoritative matrix result for this review.

Additional multi-evidence, timestamp, QI, and compatibility perturbations were executed beyond the stored A–Z cases. They found the two blocking fail-open paths recorded in this report.

## L. Fresh regression table

Fresh commands and outputs:

| Suite/boundary | Fresh result |
|---|---|
| AERG focused | 17 tests, exit 0, OK |
| freshness subset | 5 tests, exit 0, OK |
| independent A–Z reconstruction | 26/26 |
| freshness extensions | 2/2 |
| Quality Intelligence | 44 tests, exit 0, OK (skipped=1) |
| FW01 checkpoint quality gate | 6 tests, exit 0, OK |
| full capability | 352 tests, exit 0, OK (skipped=6) |
| C43 + RF01 orientation/packaging | 18 tests, exit 0, OK |
| compile boundary | exit 0, no output |
| framework validator | exit 1, 52/59; seven inherited classes |

Known ResourceWarning output from test_bounded_documentation_write.py occurred during the full suite; no test failed. The test suite has NEW_TEST_FAILURES=0, but that does not negate the execution-backed compatibility/QI findings.

## M. Inherited/new failure matrix

Fresh framework validation returned exactly 52/59 checks passed and exactly these seven failures:

~~~
V01-schema-valid
V03-family-registered
V05-dep-integrity
V09-freshness-vocab
V06-charter-no-competitor-patterns
V12-origin-type-valid
V20-pr-lineage-declared
~~~

Fresh scoped Git comparison from a10be51^ through the review base found no change to the validator, governance, candidate, release/deployment, or CPT01-R2 paths. Therefore:

~~~
INHERITED_VALIDATOR_FAILURES=7
NEW_VALIDATOR_FAILURE_CLASSES=0
NEW_TEST_FAILURES=0
NEW_RUNTIME_FINDINGS=2
~~~

The validator is not being claimed as whole-framework PASS, and no inherited class was repaired in this review.

## N. Protected-state proof

Fresh governance/development-control.json inspection returned:

~~~
.19 official version       8.4.7-C-codex.19
.19 official status        PROMOTED_VERIFIED
.19 official SHA-256       3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8
.74 development version    8.4.7-C-codex.74
.74 development status     SEALED_UNPROMOTED
.74 development SHA-256    2b82dea10695abb1c99253be1205728335a114df42cececde2fcca5c1727fd12
plane status               ACTIVE_NONCANONICAL_NO_PROMOTION
promotion.allowed          False
promotion reason           external GitHub private repository host-protection limitation
CPT01-R2 status             HOST_CAPABILITY_BLOCKED
CPT01-R2 blocker            EXTERNAL_HOST_CAPABILITY_LIMITATION
CPT01-R2 preserved          True
~~~

No scoped diff was found in governance, candidate, release/deployment, or CPT01-R2 paths. RF01/C43 owner evidence files remain outside this review's mutation scope and were not edited. GitHub host state, Owner authority, release, deployment, promotion, and approval were not touched. The broad worktree remains dirty with pre-existing owner changes; those changes were preserved.

## Anvien evidence boundary

Anvien was freshly refreshed before graph inspection:

~~~
analyze exit 0
scanned=900 parsed_code=164 failed=0
documents=537 metadata=189 scripts=8
graph nodes=37528 relationships=43343
~~~

The current repository registry has duplicate names for this worktree. Path-based resolution still reported the hidden AERG file as not found and impact as status=not_found, while change detection correctly saw only the known owner-dirty adapter_registry.json. This limitation is disclosed and was not converted into a false no-impact claim. Direct Git/source/runtime evidence supplied the acceptance decision.

## Source-Level Clearance Notes

- .p2p/system/p2p_capabilities/aerg_engine.py: direct stale/contradiction/aggregation probes clear the repair's local engine invariant; no post-subject production diff.
- .p2p/system/p2p_capabilities/aerg_model.py: direct to_dict() and as_quality_input() checks preserve stale state and fail-closed authority flags; no post-subject diff.
- .p2p/system/p2p_capabilities/quality_intelligence.py: actual AERG result path is fail-closed, but generic required-evaluation statuses STALE/EXPIRED/WARN/UNKNOWN fall through to QUALITY_VERIFIED.
- .p2p/system/p2p_capabilities/p2p_fw01_loop.py: real current QI path blocks stale evidence, but signature-based compatibility dispatch can drop actual stale AERG input and checkpoint VERIFIED.
- .p2p/system/p2p_capabilities/tests/test_aerg_reconciliation.py: 17 tests pass; the test set does not cover the two executed compatibility/generic-QI bypasses.

## Evidence Checked

Passed:

- Exact Git subject/ancestry, source blobs, repair diff, and report-only descendant separation.
- Parent reproduction of the original stale-evidence defect.
- Direct current AERG age-only, explicit-stale, stale-contradiction, serialization, fresh, boundary, aggregation, no-mutation, provenance, and authority probes.
- Actual current QI stale-result rejection.
- Current FW01 stale clock perturbation with the real QI path.
- Exact-fixture A–Z 26/26 plus freshness extensions 2/2.
- AERG/QI/FW01/C43/RF01/full capability/compile regression commands.
- Protected-state and scoped worktree checks.

Failed:

- Executed FW01 compatibility QI seam: actual stale AERG result reached VERIFIED / CHECKPOINTED.
- Executed generic QI required-evaluation status path: stale/expired/warn/unknown values reached QUALITY_VERIFIED / checkpoint_allowed=True.
- Framework validator exit 1 with seven inherited failures; this is not attributed to the repair as a new failure.

Not run:

- No repair or test edit.
- No Owner approval, independent Owner-review handoff, promotion, release, deployment, publication, GitHub host mutation, or external communication.
- No UI/browser run; the reviewed invariant is a Python capability/runtime seam, not a visible UI surface.

## Invariant Closure

- Affected invariant: stale/expired evidence must fail closed across AERG aggregation, serialization, QI, FW01 checkpointing, and compatible integration boundaries.
- Sibling surfaces checked: AERG engine/model, QI direct result path, QI generic required-evaluation path, FW01 current and compatibility seams, A–Z/provenance/no-mutation paths, regression suites, governance, candidate/release/deployment/CPT01-R2 state, and prior REJECT history.
- Residual unverified same-invariant surfaces: none required to establish the REJECT; two executed fail-open surfaces already disprove acceptance.

## Required Fix List For Resubmission

1. Make FW01 compatibility dispatch fail closed whenever the actual AERG result is not SUPPORTED with current freshness, regardless of the compatibility callable's signature or returned checkpoint_allowed value.
2. Make build_quality_verdict() classify stale, expired, warning, unknown, not-run, and other non-proof required-evaluation statuses explicitly and fail closed; add direct regression coverage for the generic required-evaluation path.
3. Re-run the current adversarial matrix, actual FW01 compatibility perturbation, actual QI path, and all required regressions with fresh evidence. Preserve this REJECT report unchanged.

## Overall Evaluation

Implementation quality at the narrow AERG engine boundary is good and the original defect is repaired there. Evidence quality is sufficient to identify the remaining failure, not to accept the handoff. The two runtime-confirmed bypasses mean NEW_FAILURE=0 is not true for the complete requested invariant, even though test and validator failure counts did not change. Protected state and prior audit history remain intact.

## Final terminal

~~~
P2P_AERG_REJECTED_FW01_COMPAT_QI_CHECKPOINTS_STALE_AERG_AS_VERIFIED
~~~

Hard stop. No repair, Owner approval, promotion, release, deployment, publication, or new Goal was started.
