# Coder Report — AERG/FW01 Compatibility Verdict Shape Fail-Closed Repair

## Terminal

`P2P_AERG_COMPAT_VERDICT_SHAPE_REPAIR_READY_FOR_SUPERVISOR_REVIEW`

This is an implementation handoff only. Supervisor review, independent
verification, Owner approval, promotion, release, deployment, and host action
were not performed.

## Subject and authority binding

- Worktree: `D:\\AI\\P2P_dev\\P2P-upgrade-github\\.tmp\\p2p-post74-development-01`
- Branch: `codex/p2p-post74-development-01`
- Current HEAD: docs/report-only descendant after the executable repair subject
  `6c1746d6716bcfe9042ae82b37bf319eda50ea1a` (exact tip is Git-bound at handoff).
- Executable source/test repair subject: `6c1746d6716bcfe9042ae82b37bf319eda50ea1a`
- Prior rejected executable subject: `a716a5066db4b213af8ef44a392afbf0e4329ce6`
- RED parent/current pre-fix subject: `360cf3503fd49fe4bc086cf97c33c49170812d82`
- RED commit: `1b22745527fb31e6299a65cc631f14ab4c754502`
- Production repair commit: `6c1746d6716bcfe9042ae82b37bf319eda50ea1a`

Git ancestry is:

`36f6877` RED reproduction -> `66657b3` FW01 status projection -> `c4c5fc9`
unsafe mapping falsification -> `a716a50` fixture contract subject ->
`00b1b5f` report handoff -> `360cf35` report correction -> `1b22745` RED
test-only checkpoint -> `6c1746d` production repair plus matrix completion ->
docs/report-only handoff.

## A. Exact root cause

The legacy QI compatibility callable omits `aerg_result`, which is an allowed
signature compatibility case. FW01 previously copied its return value with
`dict(...)`, returned it unchanged whenever actual AERG was safe, and later
authorized the durable checkpoint using truthiness. Therefore this malformed
output was accepted:

```text
quality_status = QUALITY_VERIFIED
checkpoint_allowed = "yes"
quality_failures = "not-a-sequence"
```

The actual AERG result was safe (`SUPPORTED / VERIFIED / CURRENT`), but the
compatibility verdict itself was not a valid QI verdict. The string was truthy
and reached durable `VERIFIED / CHECKPOINTED`.

## B. Test-first RED evidence

Before the production edit, the exact real-loop test was run against
`360cf3503fd49fe4bc086cf97c33c49170812d82`:

```text
python -X utf8 -m unittest test_aerg_qi_fw01_fail_closed.Fw01CompatibilityVerdictShapeFailClosedTests.test_exact_malformed_compatibility_verdict_fails_closed
```

Result: `Ran 1 test`; expected failure `TASK_DONE_CONTINUE != STOP_BLOCKED`.
The pre-fix loop therefore allowed the malformed compatibility verdict to
continue toward the durable verification path. The test-only RED checkpoint is
`1b22745527fb31e6299a65cc631f14ab4c754502`.

## C. Exact accepted verdict contract

The current QI source defines these canonical quality statuses:

`QUALITY_VERIFIED`, `QUALITY_PARTIAL`, `QUALITY_UNKNOWN`,
`QUALITY_REJECTED`.

The real QI return contract uses a mapping with:

- recognized string `quality_status`;
- tuple `quality_failures` (`tuple(failures)` in QI);
- actual boolean `checkpoint_allowed`;
- the remaining QI fields where supplied by the canonical callable.

The legacy compatibility boundary intentionally accepts the minimal three
fields needed from an older callable, then FW01 attaches the actual AERG
result. It does not accept missing/wrong types for those three authorization
fields.

Checkpoint authorization now requires all of:

1. mapping shape;
2. recognized canonical quality status;
3. tuple `quality_failures` shape;
4. `quality_status == QUALITY_VERIFIED`;
5. `type(checkpoint_allowed) is bool` and `checkpoint_allowed is True`;
6. safe actual AERG and existing execution/checkpoint requirements.

`SUCCESS` remains the QI execution outcome. `TASK_DONE_CONTINUE` remains the
FW01/AutoPilot loop-control state; it was not added to QI's vocabulary.

## D. Exact production change

Only `.p2p/system/p2p_capabilities/p2p_fw01_loop.py` changed in production.
The repair adds two small predicates at the existing seam:

- `_quality_verdict_shape_is_valid()` validates mapping, canonical status,
  literal bool, and tuple failure container;
- `_quality_verdict_allows_checkpoint()` requires canonical
  `QUALITY_VERIFIED` plus literal boolean `True`.

The AERG clamp now validates the compatibility output even on the safe-AERG
branch and converts malformed output to the existing fail-closed vocabulary.
The durable checkpoint branch uses the strict predicate rather than
`dict.get(..., False)` truthiness.

No schema framework, dependency, second QI, second state machine, scheduler,
queue, router, database, or policy DSL was added.

## E. Malformed compatibility matrix

The real-loop matrix in
`.p2p/system/p2p_capabilities/tests/test_aerg_qi_fw01_fail_closed.py` covers
18 subcases. All 18 persisted `verification_state=QUALITY_REVIEW` and
`loop_status=BLOCKED`, with loop result `STOP_BLOCKED` and reason
`QUALITY_REVIEW_REQUIRED`:

- `None`, `{}`, `[]`, and a non-mapping string;
- missing `quality_status` or `checkpoint_allowed`;
- `quality_status=None` and unknown quality status;
- canonical `QUALITY_UNKNOWN`/`QUALITY_REJECTED` with `True`;
- `checkpoint_allowed` values `"yes"`, `"true"`, `1`, `None`, and `object()`;
- `quality_failures` string, mapping, and object.

The exact malformed case is separately asserted. Valid blocked
`QUALITY_UNKNOWN / False / tuple` remains blocked.

## F. Valid fresh compatibility control

The real FW01 loop with actual AERG
`SUPPORTED / VERIFIED / CURRENT` and valid compatibility output
`QUALITY_VERIFIED / True / ()` returns `TASK_DONE_CONTINUE` and persists:

```text
verification_state = VERIFIED
loop_status = CHECKPOINTED
```

The canonical QI path still receives `execution_status=SUCCESS`.

## G. Unsafe actual-AERG compatibility controls

The existing AERG clamp remains authoritative. The compatibility regression
keeps the real stale-AERG path blocked, and the direct unsafe-AERG matrix
covers `STALE`, `CONTRADICTED`, `SUBJECT_MISMATCH`, and `INSUFFICIENT` shapes.
An affirmative valid compatibility verdict cannot override those results;
all remain quality review / blocked rather than verified.

## H. Durable checkpoint evidence

Assertions read the actual isolated FW01 checkpoint JSON after `step()`, not
only transient return objects:

| Input | Durable result |
|---|---|
| valid fresh compatibility + safe AERG | `VERIFIED / CHECKPOINTED` |
| malformed compatibility output | `QUALITY_REVIEW / BLOCKED` |
| valid blocked compatibility | `QUALITY_REVIEW / BLOCKED` |
| affirmative compatibility + stale AERG | `QUALITY_REVIEW / BLOCKED` |

## I. Status-contract regression

The prior status-contract tests remain green. Explicit successful execution
states project to QI `SUCCESS` only in the proven completion context; failed,
blocked, not-run, unknown, arbitrary, and `TASK_*` non-completion values do
not become QI success. The fresh caller state remains `TASK_DONE_CONTINUE`.

## J. AERG/QI invariant regression

The focused AERG suite remains `17/17`. QI remains `44 PASS / 1 SKIP`, and the
FW01 quality-checkpoint gate remains `6/6`. Existing freshness, contradiction,
required-status, provenance, subject, aggregation, serialization, and
no-mutation tests are included in the full UTF-8 capability run and remain
green. AERG core files were not changed.

## K. Regression table

| Surface | Result | Classification |
|---|---:|---|
| New AERG/QI/FW01 fail-closed module | 15/15 | PASS |
| Malformed compatibility matrix | 18/18 subcases blocked | PASS |
| FW01 checkpoint gate | 6/6 | PASS |
| QI | 44 pass / 1 skip | PASS |
| AERG focused | 17/17 | PASS |
| Full capability, `python -X utf8` | 367 pass / 6 skip | PASS; five new tests included |
| C43 | 9/9 | PASS |
| RF01 orientation | 7/7 | PASS |
| RF01 packaging | 2/2 | PASS |
| Compile boundary | PASS | PASS |
| Framework validator | 52/59; 7 failures | inherited debt, not repaired |

The validator failures are exactly V01-schema-valid,
V03-family-registered, V05-dep-integrity, V09-freshness-vocab,
V06-charter-no-competitor-patterns, V12-origin-type-valid, and
V20-pr-lineage-declared. No new validator failure class appeared.

Known runner distinction is preserved: the prior ordinary Windows full-suite
run produced nine identical cp1252 `UnicodeDecodeError` runner failures at
the certification test boundary, while the authoritative UTF-8 invocation is
green. No encoding repair was attempted in this task. Full capability also
emitted pre-existing `ResourceWarning` messages from bounded documentation
tests; they did not fail the run and were not changed.

## L. Production diff scope

`git diff 360cf3503fd49fe4bc086cf97c33c49170812d82..6c1746d` contains only:

- `.p2p/system/p2p_capabilities/p2p_fw01_loop.py` (production);
- `.p2p/system/p2p_capabilities/tests/test_aerg_qi_fw01_fail_closed.py`
  (regression coverage).

`quality_intelligence.py`, `aerg_engine.py`, and `aerg_model.py` are unchanged
in this repair window. Scoped production/test paths are clean after commit.
The broad owner-dirty worktree, including generated/owner-dirty
`.p2p/system/.p2p/state/adapter_registry.json`, was preserved and not staged.

Anvien was refreshed before source work and exact-path detect-changes was run
before the implementation commit. The hidden capability path did not expose
file-level semantic impact in Anvien; direct Git/source/runtime evidence was
used, and the reported changed-file risk was low with no affected flows.

## M. Failure classification

- Resolved in this slice: `MALFORMED_COMPATIBILITY_VERDICT_TYPE_VALIDATION_DEFECT`.
- New test/runtime findings after repair: `0`.
- Inherited validator findings: `7`, listed above; intentionally untouched.
- Runner portability observation: nine ordinary cp1252 decode failures;
  authoritative UTF-8 behavior is green; out of scope.

## N. Protected and audit state

Direct source readback confirms:

- official `.19`: `PROMOTED_VERIFIED`;
- development `.74`: `SEALED_UNPROMOTED`;
- CPT01-R2: `HOST_CAPABILITY_BLOCKED`, blocker
  `EXTERNAL_HOST_CAPABILITY_LIMITATION`;
- `promotion.allowed=false`;
- `governance/development-control.json` SHA-256:
  `5820a855d52ae5d44c3fe30ce9d4b0a112f8ad75a44cfbd6c73126314e332029`.

Prior reject-report files were read and not modified. Current SHA-256 values:

| Historical report | SHA-256 |
|---|---|
| `rp_supervisor_260824_165924_by_gpt-5-codex_p2p-aerg-independent-verification.md` | `F51B46610FB950FD2B98B279DAB2BB850B360CC62A8693E7E9F28ADB4863B594` |
| `rp_supervisor_260824_184807_by_gpt-5-codex_aerg-independent-verification-after-repair.md` | `3CC29EC2C4021462940FC445495D3B3E3B6FF1D25A5BB2286B1C87D217EE4C16` |
| `rp_supervisor_260824_214613_by_gpt-5-codex_aerg-final-independent-verification.md` | `A95A806A460EE12EB65A833122AA1F869FA9D06FC99E76432E913E5E42E7851C` |
| `rp_supervisor_260824_232108_by_gpt-5-codex_aerg-final-independent-verification.md` | `5B4A1D26DC638CC3F9BA1839626842CECC6826F2162B7DDA7CA33CE0F293EBB2` |

RF01, C43, release/deployment state, Owner authority, GitHub host state, and
owner-dirty files were not intentionally changed. No promotion, release,
deployment, or host mutation was performed.

## O. Commits

1. `1b22745527fb31e6299a65cc631f14ab4c754502` —
   `test: reject malformed FW01 compatibility verdicts` (RED, test-only).
2. `6c1746d6716bcfe9042ae82b37bf319eda50ea1a` —
   `fix: fail closed malformed FW01 compatibility verdicts` (narrow FW01
   production repair plus completed matrix assertions).

## P. Next review state

The implementation slice is complete and ready for a fresh Supervisor review
of the current Git tip, a docs/report-only descendant of executable source/test
repair subject `6c1746d6716bcfe9042ae82b37bf319eda50ea1a`.
