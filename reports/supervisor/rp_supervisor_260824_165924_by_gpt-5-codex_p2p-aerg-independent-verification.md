# Supervisor Report: AERG Independent Verification

Verdict: REJECT

Terminal verdict: `P2P_AERG_REJECTED_EXPIRED_EVIDENCE_RETURNS_SUPPORTED`

## Metadata

- Review time: `2026-08-24 16:59:24 +07:00`
- Reviewer: `gpt-5-codex`
- Worktree: `D:\AI\P2P_dev\P2P-upgrade-github\.tmp\p2p-post74-development-01`
- Branch: `codex/p2p-post74-development-01`
- Current HEAD: `92a1ee0acdbf21d549e786d0af27e7429f3c08bd`
- Scope: AERG source, repaired tests, QI/FW01 seams, capability record, fresh regressions, and protected development-plane state.
- Authority: current user request, `AGENTS.md`, current source, Git, direct runtime probes, fresh suites, and governance source-of-truth.

## Executive Summary

The prior no-mutation blocker is closed and the repaired test is
discriminating. Fresh source inspection, direct probes, the reconstructed A-Z
matrix, QI/FW01 inspection, and all required regression suites were performed.

Independent probing found a separate material production defect: an otherwise
valid observation whose age exceeds the freshness window, or whose explicit
freshness is `STALE`, is returned as `SUPPORTED` / `VERIFIED` with freshness
`CURRENT`. QI then returns `QUALITY_VERIFIED` with `checkpoint_allowed=True`.
This violates the required stale-evidence fail-closed contract.

The defect is not introduced by the test-only repair or report commits. It is
an unresolved semantic defect in the reviewed implementation. No repair was
performed.

## A. Exact subject and ancestry binding

The executable subject is the production implementation at
`fc1b9dc5cc23ddbcf4ccdf38539194131b9a8e99`, with the executable no-mutation
assertion repair at `c99145f3b67f33125598489030003db119facfa8`.

Commit roles are distinct:

- `fc1b9dc`: production AERG implementation checkpoint;
- `92f76b5`: initial evidence handoff;
- `3e5035c`: prior Supervisor REJECT;
- `c99145f`: test-only repair;
- `da72171`: evidence/report/documentation refresh;
- `92a1ee0`: Supervisor report artifact only.

Fresh ancestry checks all returned exit code `0`:

```text
fc1b9dc -> 92f76b5
92f76b5 -> 3e5035c
3e5035c -> c99145f
c99145f -> da72171
da72171 -> 92a1ee0
```

The capability-tree diff from `fc1b9dc` to HEAD contains only
`.p2p/system/p2p_capabilities/tests/test_aerg_reconciliation.py`. The four
protected production files have no Git diff from `fc1b9dc` to HEAD.

## B. Report-artifact relationship and historical REJECT

`92a1ee0` adds only
`reports/supervisor/rp_supervisor_260824_155502_by_gpt-5-codex_p2p-aerg-rereview-02.md`.
It is not executable AERG subject code and is not treated as authority.

The historical report
`reports/supervisor/rp_supervisor_260824_141738_by_gpt-5-codex_p2p-aerg-reconciliation.md`
remains unchanged: `git diff --name-status 3e5035c HEAD -- <that report>` was
empty, and the file still contains `Verdict: REJECT` and the original blocker.

## C. Claim-preservation finding

`AERGEngine._result` copies `claim.statement` into
`AERGResult.original_claim`, and `AERGResult.to_dict()` preserves it. A fresh
mutation probe returned:

```text
NO_MUTATION_PROOF_PASS CONTRADICTED CONTRADICTED ['MUTATION_CONTRADICTS_NO_MUTATION']
```

The original claim remained `no files changed`; it was not rewritten into a
true claim. Promotion, release, and deployment flags remained false.

## D. No-mutation contradiction proof

`.p2p/system/p2p_capabilities/tests/test_aerg_reconciliation.py:105-117`
now asserts exact equality for `result.decision == "CONTRADICTED"`,
`result.contradiction == "CONTRADICTED"`, the stable contradiction reason, and
the preserved original claim. Any of `SUPPORTED`, `PASS`, `VERIFIED`,
`UNKNOWN`, `STALE`, `SUBJECT_MISMATCH`, or `INSUFFICIENT` fails that test.

The fresh focused AERG suite ran `12` tests with `0` failures. This closes the
prior Supervisor blocker, but does not close the separate freshness defect.

## E. Contradiction precedence

Decision aggregation at `aerg_engine.py:153-160` and `:444-448` gives
`CONTRADICTED` precedence over subject mismatch, stale, and insufficient when
a contradiction decision is actually appended.

Fresh independent probes returned `CONTRADICTED` for non-zero exit code,
unhealthy Doctor, artifact SHA mismatch, source commit mismatch, and mutation
against a no-mutation claim. A combined stale-time signal plus source mismatch
and non-zero exit also returned `CONTRADICTED`.

## F. Subject, freshness, and provenance findings

Subject checks worked for the exercised dimensions: wrong subject ID returned
`SUBJECT_MISMATCH`; expected source mismatch and artifact mismatch returned
`CONTRADICTED`; tree and path are represented in the contracts.

Freshness is not fail-closed. At `aerg_engine.py:284-293`, the implementation
records `EVIDENCE_EXPIRED` or `EVIDENCE_NOT_CURRENT` and sets an internal
freshness variable to `STALE`, but does not append a `STALE` decision. At
`:442-451`, only `freshness == "UNKNOWN"` becomes `INSUFFICIENT`; with no
decision appended, the fallback is `SUPPORTED`.

Fresh direct observations using current production source:

```text
EXPIRED_BY_TIME decision= SUPPORTED status= VERIFIED freshness= CURRENT reasons= ['EVIDENCE_EXPIRED']
EXPLICIT_STALE decision= SUPPORTED status= VERIFIED freshness= CURRENT reasons= ['EVIDENCE_NOT_CURRENT']
```

The AERG test file has only the default `observed_at` fixture and case C's old
source commit (`test_aerg_reconciliation.py:43,70`); it has no age-only
`EVIDENCE_EXPIRED` or explicit `freshness="STALE"` case.

## G. Independence and authority findings

Fresh checks found that same producer/verifier and same evidence do not
self-upgrade a claim; case P returns `INSUFFICIENT`. Distinct producer/verifier
identities with a distinct verifier evidence reference can satisfy an explicit
independent claim. Executor evidence does not widen promotion, release, or
deployment authority, and `AERGEngine` has no `persist` API.

## H. Provider-neutrality finding

Direct source inspection and `inspect.getsource(AERGEngine)` found no
provider-specific `Manus`, `Codex`, `Claude`, or `Gemini` branching. Core
semantics operate on provider-neutral observations and expectations.

## I. Independent A-Z result

An independently reconstructed A-Z matrix ran all `26` expected semantic cases
successfully, including stale-by-source, wrong subject, artifact/source
mismatch, Doctor contradiction, exit contradiction, fixture/mock/live,
NOT_RUN, UNKNOWN, WARN, self-verification, unsupported origin, and observed
state precedence.

That matrix does not exercise age-only expiry or explicit stale metadata: case C
is stale because old source commit appends a `STALE` decision. The independent
freshness probe failed the broader contract despite the stored A-Z count being
green.

## J. QI and FW01 integration findings

Fresh direct QI mappings passed:

```text
CONTRADICTED -> QUALITY_REJECTED / QUALITY_CONFLICT
STALE -> QUALITY_UNKNOWN / STALE_EVIDENCE
SUBJECT_MISMATCH -> QUALITY_UNKNOWN / CERTIFICATION_SCOPE_MISMATCH
INSUFFICIENT -> QUALITY_REJECTED / MISSING_REQUIRED_EVIDENCE
```

But feeding the actual expired AERG result into QI returned:

```text
AERG SUPPORTED VERIFIED CURRENT ['EVIDENCE_EXPIRED']
QI QUALITY_VERIFIED True ()
```

Thus QI maps `STALE` correctly when received, but AERG can fail to emit it.
The integrated freshness invariant remains open.

FW01 source inspection shows AERG evaluation after `self.loop.step()` at
`p2p_fw01_loop.py:757,862-908`, using durable evidence references and the
existing optional QI seam. The fresh FW01 checkpoint suite ran `6` tests
successfully. The seam does not repair an expired observation that AERG marks
as supported.

## K. No-second-control-plane finding

Fresh source checks found no AERG core persistence, database, event bus,
scheduler, Work Queue, Lane Registry, promotion, release, or deployment API.
AERG remains an in-memory evidence/assurance layer; serialized authority flags
are fail-closed.

## L. Fresh regression results

| Check | Result |
| --- | --- |
| Independent reconstructed A-Z matrix | 26 cases passed; freshness probe failed |
| Focused AERG suite | 12 passed, 0 failed |
| Full capability suite | 347 passed, 6 skipped, 0 failed |
| QualityIntelligence suite | 44 passed, 1 skipped, 0 failed |
| FW01 checkpoint/integration | 6 passed, 0 failed |
| C43 + RF01 orientation/packaging | 18 passed, 0 failed |
| Compile/syntax boundary | exit `0` |
| Framework validator | 52/59; exit `1` due seven known failures |

The full suite emitted known bounded-documentation `ResourceWarning` messages
but no test failure. Green counts do not disprove the missing freshness case.

## M. Inherited/new failure matrix

The framework validator still has the same seven inherited classes:
`V01-schema-valid`, `V03-family-registered`, `V05-dep-integrity`,
`V09-freshness-vocab`, `V06-charter-no-competitor-patterns`,
`V12-origin-type-valid`, and `V20-pr-lineage-declared`. They remain out of
scope and were not repaired or marked green.

The freshness failure is a separate current production semantic defect, not a
validator debt item and not a test-count failure. It is not introduced by
`c99145f`, `da72171`, or `92a1ee0`; the four production files are unchanged
from `fc1b9dc`.

Current production SHA-256 fingerprints:

| File | SHA-256 |
| --- | --- |
| `aerg_model.py` | `60500940266bc08de151ff1bbfcb1b2541e5b3700bc841435a12d5cbdc533b61` |
| `aerg_engine.py` | `b6b9e6750f3abea0975b3f888ebec7c43d54337482262287322cb4c309a36c36` |
| `quality_intelligence.py` | `4a2dfcfdec0959c9f416045d9e9f8f9d2dcffdbf1996e10c7edb8d96eae47702` |
| `p2p_fw01_loop.py` | `97ef5fb0f86d27440f5be500420296cffb461eb7e5660e183b75d0685fb91ac1` |

## N. Protected-state proof

Fresh governance readback remains:

- official `.19`: `PROMOTED_VERIFIED`, SHA-256
  `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`;
- development `.74`: `SEALED_UNPROMOTED`, SHA-256
  `2b82dea10695abb1c99253be1205728335a114df42cececde2fcca5c1727fd12`;
- status: `ACTIVE_NONCANONICAL_NO_PROMOTION`;
- `promotion.allowed`: `false`, due to external GitHub private-repository
  host-protection limitation.

Targeted Git diff and worktree status were empty for governance,
`.p2p/system/governance`, candidate artifacts, release/deployment helpers, and
promotion surfaces. No Owner approval, release, deployment, GitHub host
mutation, or next Goal was performed.

Anvien was refreshed before graph use. The hidden `.p2p/system` source path is
not present in the registered file projection; direct source, Git, and runtime
evidence were used instead of claiming false graph coverage.

## O. Blocking finding and required next evidence

### [P1] Expired evidence is accepted as current support

File: `.p2p/system/p2p_capabilities/aerg_engine.py:284-293,442-451`

Issue: `EVIDENCE_EXPIRED` and explicit `freshness="STALE"` set a reason/state
but do not produce a `STALE` decision. The evaluator falls through to
`SUPPORTED`, reports `VERIFIED`, and can feed QI a checkpoint-allowing result.

Required closure in a separate repair lane:

1. Correct the production freshness decision contract so expired/non-current
   evidence fails closed and cannot be reported as supported.
2. Add discriminating tests for age-only expiry and explicit stale metadata,
   including the QI checkpoint boundary.
3. Rerun independent subject binding, A-Z, QI/FW01, full capability, and
   protected-state checks from the exact resulting commit.

## Final verdict

`P2P_AERG_REJECTED_EXPIRED_EVIDENCE_RETURNS_SUPPORTED`

The no-mutation blocker is closed, but AERG cannot be independently verified
for Owner review while stale evidence can become `SUPPORTED/VERIFIED` and
`QUALITY_VERIFIED`.

Hard stop: no Owner approval, next Goal, promotion, release, deployment, or
host action was started.
