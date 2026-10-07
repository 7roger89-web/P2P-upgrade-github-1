# P2P — ANE CONTEXT CANARY 01 — FROZEN CRITERIA

Status: `PRE_RESULT_FROZEN`
Decision authority: `DOMAIN_CAPABILITY_ADMISSION_V1`
Candidate: `ericlam2k/ane-context-harness`
Candidate revision: `26d6fbb7a86fd47e1a3184dc4dc03d3867ac5835`
Target repository: `7roger89-web/P2P-upgrade-github-1`
Target baseline: `6ef4520781350db6f1c870e4cbbfeeaaa4e9c403`
Canary branch: `canary/ane-context-01-20261007`

## Claim under test

The useful claim is NOT "ANE cuts a full-repo dump".

The claim worth admitting is:

> On a real P2P repository and later in the same real coding-agent workflow,
> ANE can reduce context/agent input materially without losing task-critical
> evidence or degrading task success.

This canary is deliberately split because the Owner-authorized Codex host may
be unavailable independently of ANE.

## Stage A — real-repository context selection

Run on GitHub-hosted Linux against the exact P2P target snapshot and the exact
ANE candidate revision.

Frozen tasks: `experiments/ane-context-canary-01/tasks.jsonl`.

Frozen budget: `2000` ANE estimator tokens per task.

PASS requires ALL:

1. Candidate installs successfully on Python 3.13.
2. Focused upstream deterministic benchmark/tests pass.
3. Upstream token-savings measurement script runs successfully.
4. All 5 real P2P tasks return their predeclared primary evidence anchor.
5. Median local context reduction across the 5 tasks is >= 20%.

Stage A measures ANE's own deterministic context selector on a real repository.
It does NOT prove provider-billed token savings, Codex/OpenCode token savings,
or task completion quality.

## Stage B — real-agent A/B gate

Stage B is mandatory before any claim of real agent token optimization or P2P
admission.

Use the same:

- repository snapshot,
- task set,
- model,
- host,
- prompt wording,
- acceptance checks.

Compare:

- A = current agent workflow without ANE;
- B = same workflow with ANE context supplied through the smallest supported
  integration path.

PASS requires ALL:

1. Actual agent telemetry is available for both arms.
2. Total input tokens in B are >= 20% lower than A across the frozen task set.
3. Task success has zero material regression.
4. No task loses a required evidence anchor.
5. Wall-clock latency does not regress by more than 25% unless the token win is
   larger than 40% and task quality is unchanged.

If the agent host is unavailable, classify Stage B
`BLOCKED_EXTERNAL_HOST_OFFLINE`; do not substitute ANE's local token estimator.

## Admission contract

```text
STAGE_A_PASS != REAL_AGENT_TOKEN_WIN
LOCAL_CONTEXT_REDUCTION != PROVIDER_BILLED_TOKEN_REDUCTION
REQUIRED_EVIDENCE_SURVIVAL != TASK_SUCCESS
BOTH_STAGE_A_AND_STAGE_B_PASS => ADMIT_TASK_SCOPED_BOUNDED_CANDIDATE
ANY_STAGE_B_UNKNOWN_OR_BLOCKED => OBSERVE_ONLY
```

## Prohibitions

- no global ANE installation into P2P;
- no router/daemon/context service added to P2P;
- no API key creation;
- no secret exposure;
- no claim that ANE prevents hallucination;
- no claim of 40–60% real Codex/OpenCode savings without actual telemetry;
- no moving thresholds after results are known.
