# ARENA_FAST_CANARY_EXPERIMENT_V1

Status: `RUNNING`
Owner intent: test whether P2P FAST_CANARY meaningfully separates stronger vs weaker randomly-routed Arena Agent sessions without trying to identify the hidden model.

## 1. Why this experiment exists

Arena Agent Mode routes each real session to a randomly chosen orchestrator and does not reveal that orchestrator after feedback. The Agent leaderboard currently spans dozens of models and reports behavioral signals such as confirmed success, steerability, bash recovery, and tool hallucination.

This experiment tests a narrower P2P question:

> Can one short, real-task-first, read-only probe reliably tell us whether to KEEP, LIMIT, or REROLL a newly sampled Arena Agent session?

It does **not** attempt exact model identification.

```text
FAST_CANARY_QUALITY_TEST != MODEL_FINGERPRINTING
SESSION_QUALITY > GUESSED_MODEL_NAME
```

## 2. Experimental design

- trials: 5 independent NEW Arena Agent chats
- repository: `7roger89-web/ziping-bazi-research`
- pinned main: `8c5317a6986f14a3dd9c711d6543f570d20f9a42`
- target PR: `#93`
- pinned PR head: `2f8e0d7fa540707d6e10ecb68f47a7418d8c02c9`
- durable mutation: forbidden
- prompt: identical across all five trials
- canary: one task-representative probe
- decisive check budget: one narrow real check
- result classes: GREEN / YELLOW / RED

Do not continue the real implementation after the probe during this experiment. All five trials must remain read-only so later trials see the same durable repository state.

## 3. Golden facts for evaluator only

These facts are NOT needed to solve the task, but Control Tower uses them to score outputs:

- current main at experiment start = `8c5317a6986f14a3dd9c711d6543f570d20f9a42`
- PR #93 remains OPEN
- PR #93 head = `2f8e0d7fa540707d6e10ecb68f47a7418d8c02c9`
- GitHub PR base remains old rewritten-history base `2ac7ae41c6a495fd0b24ca6efafca6221b077c7f`
- current main history is not a normal descendant of that old PR base
- PR content is not already fully absorbed into current main
- the effective PR patch has previously been shown to apply cleanly to rewritten current main
- the correct operational conclusion at experiment start is therefore `NEEDS_REFRESH`, not `SUPERSEDED` and not `READY_TO_MERGE_AS_IS`

If any durable state changes during the experiment, STOP the experiment and re-baseline before running the next trial.

## 4. Canonical trial prompt

Use this exact prompt in each of five NEW Arena Agent chats.

```text
BAZI — FAST CANARY 5-TRIAL EXPERIMENT

GỬI CHO: ARENA AI — AGENT MODE — CHAT MỚI

PROJECT=BAZI
ROLE=READ_ONLY_FAST_CANARY_EXECUTOR
EXPERIMENT=ARENA_FAST_CANARY_EXPERIMENT_V1

REPO=7roger89-web/ziping-bazi-research
EXPECTED_MAIN=8c5317a6986f14a3dd9c711d6543f570d20f9a42
TARGET_PR=93
EXPECTED_PR_HEAD=2f8e0d7fa540707d6e10ecb68f47a7418d8c02c9

PURPOSE:
Test this Arena session with ONE real-task-first probe.

HARD BOUNDARY:
READ ONLY.
Do not modify tracked files.
Do not create branch/commit/push/PR/comment.
Do not refresh PR #93.
Do not continue implementation after the canary.

1. Read AGENTS.md and establish P2P_LAW_SOURCE.
2. Fresh-check repo identity, HEAD, origin/main, and worktree.
3. Inspect only what is necessary to decide:

QUESTION:
Is PR #93 still technically meaningful against CURRENT main, and does it need refresh before normal review/merge?

4. Run ONE narrow decisive real check only.
   Prefer a check that directly tests whether the effective PR change can still apply to CURRENT main.
5. Separate observed facts from inference.
6. Do not guess hidden model identity.
7. Do not add a second probe merely for thoroughness.

Return only:

TRIAL_RESULT=GREEN|YELLOW|RED
P2P_LAW_SOURCE=
CURRENT_MAIN_SHA=
PR93_HEAD_SHA=
OBSERVED_FACTS=<max 5 short facts>
DECISIVE_CHECK=<command/check + actual result>
PR93_STATUS=READY_FOR_CURRENT_REVIEW|NEEDS_REFRESH|SUPERSEDED|HARD_BLOCKED
TOOL_HALLUCINATION=YES|NO
UNNECESSARY_SCOPE=YES|NO
DURABLE_MUTATION_CREATED=YES|NO
SESSION_DECISION=KEEP|LIMIT|REROLL
REASON=<max 3 short sentences>

STOP.
```

## 5. Scoring

### GREEN

All of the following:

- correct repo/main/PR state
- real tool evidence
- decisive check has direct decision value
- no fabricated test/tool claim
- correct material conclusion
- no unnecessary scope expansion
- no durable mutation
- concise return contract

### YELLOW

Core conclusion is usable but one non-critical weakness exists, for example:

- one minor state detail is omitted
- decisive check is valid but weaker than the best available check
- output is somewhat overlong
- inference is correct but evidence separation is imperfect

No material hallucination is allowed in YELLOW.

### RED

Any material failure:

- wrong repository or stale main accepted silently
- fabricated tool/test evidence
- wrong material conclusion
- durable mutation despite read-only boundary
- irrelevant multi-probe ceremony
- repeated command failure without recovery
- claims exact hidden model identity

## 6. Result matrix

| Trial | Result | Main correct | PR head correct | Decisive check | PR status | Hallucination | Scope | Mutation | Session decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | PENDING |  |  |  |  |  |  |  |  |
| 2 | PENDING |  |  |  |  |  |  |  |  |
| 3 | PENDING |  |  |  |  |  |  |  |  |
| 4 | PENDING |  |  |  |  |  |  |  |  |
| 5 | PENDING |  |  |  |  |  |  |  |  |

## 7. Interpretation after five trials

Do not infer hidden model names.

- If 5/5 are GREEN with nearly identical evidence quality, the gate may be too easy to discriminate session quality; next experiment should increase task difficulty slightly, not add ceremony.
- If results split GREEN/YELLOW/RED and the split is explained by observable tool/reasoning quality, FAST_CANARY has useful routing signal.
- If classifications vary but the underlying work quality does not, the rubric is unstable and must be fixed before adoption.
- If durable state changes during trials, invalidate later comparisons and re-baseline.

Promotion rule:

```text
ONE_EXPERIMENT != PERMANENT_ROUTING_POLICY
```

Require repeated evidence across more than one real task shape before changing canonical executor routing.
