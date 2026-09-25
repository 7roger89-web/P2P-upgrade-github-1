# ARENA_FAST_CANARY_EXPERIMENT_V1 — RESULTS

Status: `COMPLETE`
Run date: 2026-09-22
Trials received: 10 independent Arena Agent chats
Repository: `7roger89-web/ziping-bazi-research`

## 1. Question

Can one short, real-task-first, read-only probe provide useful routing signal
for newly sampled Arena Agent sessions?

This experiment measures session quality only:

```text
FAST_CANARY_QUALITY_TEST != MODEL_FINGERPRINTING
SESSION_QUALITY > GUESSED_MODEL_NAME
```

## 2. Pinned state

- main: `8c5317a6986f14a3dd9c711d6543f570d20f9a42`
- PR: `#93`
- PR head: `2f8e0d7fa540707d6e10ecb68f47a7418d8c02c9`
- old PR base / true merge-base: `2ac7ae41c6a495fd0b24ca6efafca6221b077c7f`
- durable mutation during trial set: none

Durable GitHub ancestry verification after the 10 trials:

```text
compare 2ac7ae4 -> 8c5317a:
  status=ahead
  ahead_by=28
  behind_by=0
  merge_base=2ac7ae4

compare 8c5317a -> 2f8e0d7:
  status=diverged
  PR ahead_by=1
  PR behind_by=28
  merge_base=2ac7ae4
```

Therefore the correct material conclusion for the experiment state is:

```text
PR93_STATUS=READY_FOR_CURRENT_REVIEW
```

The PR is old and behind main, but it is NOT unrelated history. Its effective
8-file patch remains meaningful and applies cleanly to the pinned main. The
original experiment draft incorrectly recorded NEEDS_REFRESH as the golden
answer; that evaluator error is corrected here.

## 3. Critical methodological finding

The original prompt incorrectly asked the tested Arena session to output its own
`TRIAL_RESULT=GREEN|YELLOW|RED` and `SESSION_DECISION`, despite canonical
policy already stating that the tested model must not grade itself.

The 10 trials demonstrate why that is unsafe:

- 9 completed trials self-reported GREEN.
- 1 trial did not complete in a useful time.
- among the 9 self-GREEN trials, two (#4 and #10) made the same material false
  claim: no merge-base / unrelated histories.
- both false claims came from treating incomplete/shallow local Git history as
  repository truth.
- other sessions (#1 and #7) encountered shallow-history artifacts but recovered
  correctly by deepening/unshallowing and rechecking explicit refs.

New rule:

```text
EXECUTOR_RETURNS_EVIDENCE
CONTROL_TOWER_GRADES_CANARY
```

## 4. External Control Tower grading

| Trial | Executor self-report | CT grade | Material conclusion | Evidence quality | Key observation |
| --- | --- | --- | --- | --- | --- |
| 1 | GREEN | GREEN | READY | strong | caught shallow clone + corrected merge-tree invocation; clean merge-tree |
| 2 | GREEN | GREEN | READY | good | live GitHub mergeability + current-main identity + non-supersession evidence |
| 3 | no terminal result | RED | NOT_REACHED | failed | excessive thinking/non-completion |
| 4 | GREEN | RED | NEEDS_REFRESH | wrong | false empty merge-base/unrelated-history conclusion |
| 5 | GREEN | GREEN | READY | strong | patch apply-check passed; corrected pipeline exit-code capture |
| 6 | GREEN | GREEN | READY | strong/concise | direct `git apply --check`, minimal scope |
| 7 | GREEN | GREEN | READY | strong | detected shallow clone, unshallowed, explicit-SHA merge-tree clean |
| 8 | GREEN | YELLOW | READY | weaker | correct answer, but mostly trusted GitHub mergeability; limited non-supersession evidence |
| 9 | GREEN | GREEN | READY | strong | explicit patch apply-check with clear limitation statement |
| 10 | GREEN | RED | NEEDS_REFRESH | wrong | shallow clone/root-count artifact treated as durable history fact |

Distribution:

```text
CONTROL_TOWER_GREEN=6
CONTROL_TOWER_YELLOW=1
CONTROL_TOWER_RED=3
SELF_REPORTED_GREEN_AMONG_COMPLETED=9/9
```

## 5. What the experiment proves

### Useful signal exists — but only with external grading

The same bounded task exposed meaningful variation:

- some sessions recovered correctly from tool/sandbox artifacts;
- some reached the correct answer with minimal evidence;
- one session failed to terminate;
- two sessions made a material repository-history error while confidently
  self-reporting GREEN.

Therefore FAST_CANARY has routing value, but self-classification does not.

### Shallow-clone handling is a discriminating capability

A particularly useful signal was whether the session could distinguish:

```text
LOCAL_HISTORY_INCOMPLETE
from
REPOSITORY_HISTORY_UNRELATED
```

This is directly relevant to Arena because sandbox clones may be shallow.

## 6. Corrected executor contract for future trials

Future Arena canaries should return evidence only:

```text
CANARY_EVIDENCE_PACKET_V1
P2P_LAW_SOURCE=
CURRENT_STATE=
FACTS=<max 5>
DECISIVE_CHECK=
CHECK_RESULT=
ERRORS_ENCOUNTERED=
RECOVERY_ACTIONS=
DURABLE_MUTATION_CREATED=
MODEL_IDENTITY=UNKNOWN
```

Control Tower then independently returns:

```text
CANARY_CLASSIFICATION=GREEN|YELLOW|RED
SESSION_POLICY=KEEP_SESSION|LIMIT_SESSION|REROLL_OR_SWITCH_EXECUTOR
```

## 7. Decision

```text
EXPERIMENT_VERDICT=USEFUL_WITH_CORRECTION
FAST_CANARY_KEEP=YES
SELF_GRADING_KEEP=NO
SHALLOW_HISTORY_GUARD_REQUIRED=YES
MODEL_IDENTITY_INFERENCE=NO
```

Do not promote this one task shape into a universal model-quality score.
Validate the corrected gate on at least one different real task shape before
making stronger routing claims.
