# ARENA_FAST_CANARY_EXPERIMENT_V2_1 — Rebased Python edge-case diagnosis

Status: `COMPLETE`
Run date: 2026-09-22
Trials received: 5 independent NEW Arena Agent chats

## 1. Purpose

Re-run the intended V2 Python-semantic canary against the durable BAZI main
after V2 was invalidated by baseline drift.

This experiment measures session quality, not hidden-model identity.

## 2. Pinned state

Repository:
`7roger89-web/ziping-bazi-research`

Pinned main:
`81190346fd391f004efe81c62ba79fae655afd25`

Target files:

- `labs/multi-engine-interpretation/prepare_analysis.py`
- `labs/multi-engine-interpretation/test_prepare_analysis.py`

Pinned blobs:

- prepare_analysis.py: `381b4f5caa86c7bb08e36cfb98327adff09cdedd`
- test_prepare_analysis.py: `5e78dfc3e23fc92fb1a2de338bb899218d6de1c1`

Fresh Control Tower recheck after the five trials confirmed the same main and
same two blobs. No explicit `..` guard or focused mid-string `..` test had
landed during the experiment.

## 3. Ground truth

The documented case-name rule says `..` is forbidden, but current code uses:

```python
CASE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
```

which allows a mid-string name such as `case..01`.

The committed tests reject traversal/separator forms but do not exercise a
pattern-legal `..` name with an existing packet.

The decisive isolated runtime behavior is:

```text
temporary results/case..01.json exists
validate_case(tempdir, "case..01") -> None
```

Therefore:

```text
CONTRACT_STATUS=BUG_PRESENT
BUG_CLASS=VALIDATION_CONTRACT_GAP
```

## 4. External Control Tower grading

| Trial | CT grade | Contract result | Runtime isolation | Recovery/scope note |
| --- | --- | --- | --- | --- |
| 1 | GREEN | BUG_PRESENT | strong | exact temp packet + real validate_case; clean and bounded |
| 2 | YELLOW | BUG_PRESENT | strong | created repo-local __pycache__ during import, removed it, then correctly re-ran with -B; final evidence reliable but noisier than necessary |
| 3 | YELLOW | BUG_PRESENT | incomplete | pattern runtime + fallback reason were observed, but no temp packet was created to directly prove validate_case returns None for the `..` name |
| 4 | GREEN | BUG_PRESENT | strong | isolated temp packet and contrasted fallback behavior directly |
| 5 | GREEN | BUG_PRESENT | strong | isolated real validator with disposable temp packets; some extra controls but no material error |

Distribution:

```text
CONTROL_TOWER_GREEN=3
CONTROL_TOWER_YELLOW=2
CONTROL_TOWER_RED=0
```

## 5. What V2.1 shows

### FAST_CANARY generalized beyond Git history

All five sessions found the real validation gap, and three produced the intended
strong runtime isolation. The remaining two were still usable but weaker for
observable reasons.

This supports the core FAST_CANARY design across a second task shape:

```text
REAL_TASK_FIRST_SLICE = CANARY
EXECUTOR_RETURNS_EVIDENCE
CONTROL_TOWER_GRADES_CANARY
```

### But this task shape is not discriminating enough for reroll decisions

Unlike V1, V2.1 produced no RED sessions. The task was useful for checking code
reading, runtime evidence, and scope discipline, but too easy to strongly
separate unsafe from high-quality sessions.

Therefore:

```text
MORE_IDENTICAL_V2_1_TRIALS=NO
INFORMATION_GAIN_FROM_TRIALS_6_TO_10=LOW
```

Do not spend another five sessions repeating the same probe merely to increase
sample count.

### Recovery remains meaningful

Trial 2's accidental bytecode creation is a useful example: the final answer was
not RED because the session detected the side effect, removed it, re-ran with
bytecode disabled, and verified a clean worktree. Recovery quality is part of
agent quality, not an automatic failure.

### Exact-evidence quality still matters

Trial 3 reached the correct conclusion, but did not fully isolate the documented
contract from the fallback with an existing temp packet. Correct inference is
not identical to strongest evidence.

## 6. Cross-experiment synthesis

```text
V1:
  task = Git history / shallow environment
  CT = 6 GREEN / 1 YELLOW / 3 RED
  discrimination = strong

V2:
  task = invalidated by baseline drift
  secondary obedience signal = 5 GREEN / 2 YELLOW / 3 RED

V2.1:
  task = Python validation edge case
  CT = 3 GREEN / 2 YELLOW / 0 RED
  discrimination = weak-to-moderate
```

Current conclusion:

```text
FAST_CANARY_HAS_REAL_ROUTING_VALUE=YES
ONE_FIXED_BENCHMARK_AS_UNIVERSAL_GATE=NO
TASK_REPRESENTATIVE_PROBE_REQUIRED=YES
EXTERNAL_GRADING_REQUIRED=YES
```

For medium/high-risk Arena work, keep FAST_CANARY task-representative. If the
real first slice is too easy to separate sessions, do not manufacture more
ceremony; continue bounded work under normal verification rather than repeatedly
rerolling.

## 7. Decision

```text
EXPERIMENT_VERDICT=USEFUL_WITH_LIMITS
V2_1_COMPLETE=YES
RUN_TRIALS_6_TO_10=NO
BUG_FIX_NOW_ALLOWED=YES
NEXT=FIX_REAL_BAZI_VALIDATION_GAP_WITH_FOCUSED_TEST
```
