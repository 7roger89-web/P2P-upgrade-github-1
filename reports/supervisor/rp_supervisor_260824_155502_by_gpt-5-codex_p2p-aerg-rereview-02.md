# Supervisor Re-review 02: AERG No-Mutation Contradiction Repair

## Verdict

**PASS**

Terminal verdict:

`P2P_AERG_SUPERVISOR_REREVIEW_PASS_FOR_INDEPENDENT_REVIEW_HANDOFF`

Classification:

`VERIFICATION_EVIDENCE_GAP_REPAIR`

This is a Supervisor re-review only. No production repair, independent
verification, promotion, release, deployment, or host-authority action was
performed.

## A. Exact subject and commit binding

- Worktree: `D:\AI\P2P_dev\P2P-upgrade-github\.tmp\p2p-post74-development-01`
- Branch: `codex/p2p-post74-development-01`
- Current HEAD: `da72171a1dc94e290da5c09ef000fdeedc2a5336`
- Prior implementation checkpoint: `fc1b9dc5cc23ddbcf4ccdf38539194131b9a8e99`
- Prior evidence handoff: `92f76b5cb7c80472a963e970a90c7177eae86833`
- Prior Supervisor REJECT: `3e5035c5975dd8e9ae0cef5aecb6d4bd7276225b`
- Test repair: `c99145f3b67f33125598489030003db119facfa8`
- Evidence/report refresh: `da72171a1dc94e290da5c09ef000fdeedc2a5336`

Fresh ancestry checks all returned exit code `0`:

- `fc1b9dc -> c99145f`
- `92f76b5 -> c99145f`
- `3e5035c -> c99145f`
- `c99145f -> da72171`

`c99145f` changes only
`.p2p/system/p2p_capabilities/tests/test_aerg_reconciliation.py`. Its diff
adds the three executable assertions required by the prior rejection.

`da72171` changes only the AERG plan/evidence/benchmark/status notes and the
allowed `reports/coder/` and `reports/reconciliation/` evidence surfaces. It
does not change production source or governance state.

The exact reviewed source subject is the current AERG reconciliation
implementation at HEAD, with the repaired executable test and its evidence
handoff bound to that same repository/worktree.

## B. Prior REJECT preservation

The historical report remains at:

`reports/supervisor/rp_supervisor_260824_141738_by_gpt-5-codex_p2p-aerg-reconciliation.md`

`git diff --name-status 3e5035c HEAD -- <that report>` returned no output. The
current file still contains `Verdict: REJECT`, the original blocker, and the
explanation that the seeded contradiction was previously unasserted. It was
not deleted, overwritten, rewritten, or replaced.

## C. Exact repaired assertion proof

In `test_claim_and_provenance_are_preserved` (lines 105-117), the seeded case
is:

- original claim: `original claim: no files changed`;
- observation: `mutation_state="MUTATED"` and `changed_paths=("src/a.py",)`;
- assertions:
  - `result.original_claim == claim_text`;
  - `result.decision == "CONTRADICTED"`;
  - `result.contradiction == "CONTRADICTED"`;
  - `"MUTATION_CONTRADICTS_NO_MUTATION" in result.reasons`.

The contract assertions also preserve `original_claim`, the evidence
reference, and the fail-closed `can_promote`, `can_release`, and `can_deploy`
flags.

## D. Discriminating-test proof

The repaired test uses exact equality for both decision fields, not a
non-null, negative, or loose assertion. Therefore a result classified as
`SUPPORTED`, `PASS`, `VERIFIED`, `UNKNOWN`, `STALE`, `SUBJECT_MISMATCH`, or
`INSUFFICIENT` fails the executable assertion. The stable contradiction-reason
assertion independently fails if the evaluator omits the required reason.

The same focused file retains the full A-Z expected-decision matrix. Fresh
execution ran all 12 tests successfully, including the seeded contradiction
test.

## E. Production-source immutability

`git diff --name-status fc1b9dc HEAD` for all four protected production files
returned no output. The complete capability-tree diff from `fc1b9dc` to HEAD
contains only the repaired AERG test file.

Git blob comparisons against `fc1b9dc` also report `unchanged=True` for each
file. Current SHA-256 fingerprints are:

| File | SHA-256 |
| --- | --- |
| `.p2p/system/p2p_capabilities/aerg_model.py` | `60500940266bc08de151ff1bbfcb1b2541e5b3700bc841435a12d5cbdc533b61` |
| `.p2p/system/p2p_capabilities/aerg_engine.py` | `b6b9e6750f3abea0975b3f888ebec7c43d54337482262287322cb4c309a36c36` |
| `.p2p/system/p2p_capabilities/quality_intelligence.py` | `4a2dfcfdec0959c9f416045d9e9f8f9d2dcffdbf1996e10c7edb8d96eae47702` |
| `.p2p/system/p2p_capabilities/p2p_fw01_loop.py` | `97ef5fb0f86d27440f5be500420296cffb461eb7e5660e183b75d0685fb91ac1` |

The repaired test SHA-256 is
`e630f3b0ee2c93cdf3c858c7725b04917e79098bc4e7dd4deb7393a70010900d`.

## F. Fresh direct runtime observations

Using the current production source and a fresh isolated in-memory engine:

```text
MUTATED_PATH CONTRADICTED CONTRADICTED ['MUTATION_CONTRADICTS_NO_MUTATION'] no files changed
UNCHANGED SUPPORTED NONE [] no files changed
MISSING_MUTATION_STATE INSUFFICIENT NONE ['MUTATION_STATE_REQUIRED'] no files changed
```

The direct probe agrees with the repaired executable test; the test is not
being replaced by a manual probe.

## G. Fresh regression results

All required fresh checks completed:

| Check | Result |
| --- | --- |
| Focused AERG reconciliation | 12 passed, 0 failed |
| Full capability suite | 347 passed, 6 skipped, 0 failed |
| QualityIntelligence | 44 passed, 1 skipped, 0 failed |
| FW01 checkpoint/integration | 6 passed, 0 failed |
| C43 regression + RF01 orientation/packaging | 18 passed, 0 failed |
| Compile boundary | exit `0` |

The full capability run emitted the known bounded-documentation
`ResourceWarning` messages but no test failure.

## H. A-Z closure finding

The executable AERG reconciliation contract now proves:

`NO MUTATION CLAIM + OBSERVED MUTATION = CONTRADICTED`

The seeded mutation contradiction is explicitly asserted in the same
reconciliation test suite and passes fresh execution. A support classification
for that seeded mutation is no longer possible without failing the test.

## I. Inherited versus new failure classification

The fresh framework validator remains `52/59` with the same seven known
inherited failures:

`V01-schema-valid`, `V03-family-registered`, `V05-dep-integrity`,
`V09-freshness-vocab`, `V06-charter-no-competitor-patterns`,
`V12-origin-type-valid`, and `V20-pr-lineage-declared`.

The repair commit changes only the AERG test, and the evidence refresh changes
only documentation/report surfaces; validator inputs and validator code were
not changed. These failures therefore remain inherited framework debt, were
not caused by this repair, and were not silently marked green. They are out of
scope and were not repaired.

Anvien was refreshed before graph checks. Its registered graph does not index
the hidden `.p2p/system` test path; file-detail/impact returned `not_found`.
That tooling limitation is recorded rather than presented as false graph
evidence. Direct source/diff/test evidence is authoritative for this review.

## J. Protected-state boundary

Fresh governance readback remains:

- official baseline `.19`, `PROMOTED_VERIFIED`, SHA-256
  `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`;
- development base `.74`, `SEALED_UNPROMOTED`, SHA-256
  `2b82dea10695abb1c99253be1205728335a114df42cececde2fcca5c1727fd12`;
- `promotion.allowed = false`, reason: external GitHub private-repository
  host-protection limitation;
- development-plane status: `ACTIVE_NONCANONICAL_NO_PROMOTION`.

`git diff --name-status fc1b9dc HEAD` and targeted worktree status were empty
for `governance`, `.p2p/system/governance`, `reports/candidates`, release and
deployment helpers, and the protected baseline/promotion surfaces. No change
was made to CPT01-R2, RF01, C43, promotion authority, release, deployment,
GitHub host protection, Owner authority, Work Queue, Lane Registry, or
Integration Queue. Existing unrelated owner worktree modifications and
untracked C43/RF01 evidence were preserved.

## K. Final decision

All six PASS conditions are satisfied:

1. the sole prior blocker is mechanically closed;
2. the repaired test is discriminating;
3. production source is unchanged;
4. relevant regressions are clean;
5. no new material failure was introduced;
6. the historical REJECT remains preserved.

Final verdict:

`P2P_AERG_SUPERVISOR_REREVIEW_PASS_FOR_INDEPENDENT_REVIEW_HANDOFF`

Hard stop: independent verification and the next development Goal are not
started by this task.
