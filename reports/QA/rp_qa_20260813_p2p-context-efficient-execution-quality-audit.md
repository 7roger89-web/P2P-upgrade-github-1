# QA Report - P2P Context-Efficient Execution and Quality Audit

- Date: 2026-08-13
- Subject: `D:\AI\P2P_dev\P2P-8.4.6-C-Codex-Edition-v4`
- Runtime baseline: `8.4.7-C-codex.9`
- QA mode: read-only audit/evaluation; no implementation or release work
- Verdict: `BLOCKED`

## Scope and boundary

This audit covers the current P2P development source, its local capability
runtime, existing synthetic fixtures, current Goal/CAPSULE/evidence/ledger
behavior, and isolated evaluator outputs. It does not integrate or import
`codex_workflow` or `trycompai/crm`, does not invoke private AgentControl APIs,
does not require Aesthetica, and does not modify P2P, Aesthetica, installer,
release, or any user project.

The audit itself is complete. The Goal is `BLOCKED` because the host/runtime
does not expose the token and delegation telemetry needed to pass the required
context-economics, quality-adjusted-cost, and orchestration-tax criteria.

## Current baseline

| Surface | Evidence | Result |
|---|---|---|
| Package doctor | `doctor.py` | PASS, package `8.4.7-C-codex.9` |
| Core regression | `python -B -m unittest discover -s tests -p 'test_*.py'` | 50/50 PASS |
| Native Decision Trace | DT1-DT24 evaluator | 24/24 PASS |
| Capability Foundation | capability doctor | PASS; Aesthetica `RESOLVED`, execution not proven |
| Beginner lifecycle | 4 isolated scenarios, 205 rows | Harness PASS; `CERTIFIED_WITH_LIMITATIONS` |
| UI/UX evaluator | DW1-DW18 | 17/18 PASS; DW12 fails |
| Canonical governance | registry and quorum | exact 8, denominator 8, full quorum 8/8 |

The current UI/UX DW12 failure is concrete baseline evidence: the manifest
declares package `.9`, while `.p2p/system/release.json` records package `.3`.
The installed evaluator therefore rejects the release-version consistency
check. This was recorded, not repaired.

## Synthetic execution baseline

The six isolated probes below exercise the current orchestration/state path.
They are not real application implementation or model-agent quality claims.
The acceptance harness explicitly labels its PASS as synthetic and does not
claim a real eight-thread quorum.

| Case | Current classification | Result | Selected roles | State bytes* |
|---|---|---:|---:|---:|
| Medium multi-file implementation | GOAL / medium | synthetic PASS, 6/6 criteria | 4 | 30,546 |
| Long-running debug | GOAL / medium | synthetic PASS, 6/6 criteria | 4 | 30,459 |
| Research/evidence | SEPARATE GOALS / small | BLOCKED, 3/6 criteria | 1 | 32,905 |
| Existing maintenance | GOAL / small | synthetic PASS, 6/6 criteria | 1 | 30,116 |
| Trivial change | DIRECT TASK / small | synthetic PASS, 6/6 criteria | 1 | 29,680 |
| Delegation unavailable | SEPARATE GOALS / small | BLOCKED, 4/6 criteria | 1 | 30,896 |

`*` Contract JSON + report JSON + CAPSULE + execution ledger bytes. These are
local artifact sizes, not API token counts. Every probe left the protected
P2P source hashes unchanged. No ledger contained a child-thread or subagent
execution event; `full_quorum_used` remained false.

## Context and token economics

Measured:

- local workflow wall-clock for the six isolated probes: approximately
  318-426 ms per local Python orchestration run;
- persistent state artifact size: approximately 29.7-32.9 KB per synthetic
  run;
- contract/report/CAPSULE/ledger duplication is visible and measurable;
- selective evidence reuse is observable in the existing-project fixture.

Not measurable from the current host/runtime:

- main-context growth;
- input, cached-input, output, and total model tokens;
- raw tool-output tokens/bytes as seen by the model;
- repeated file reads and repeated summaries;
- actual context compactions, handoffs, worker startup, aggregation, repair,
  or total system cost.

The current P2P ledger/report/CAPSULE schemas contain no authoritative token
counter or host tool-trace field. Consequently, no token-efficiency or system
cost improvement is claimed.

## Quality baseline

- Core tests, DT1-DT24, capability safety, trust/data boundary, no-progress,
  independent done-check, canonical safety, and beginner harness integrity
  pass.
- Beginner readiness remains `CERTIFIED_WITH_LIMITATIONS`; 35 partial rows
  include missing persisted discovery questions, distributed WHY evidence,
  synthetic-only repair, unproven deployment, and occasional route/classifier
  limitations.
- The six probes measure orchestration/state behavior only. They do not supply
  real implementation acceptance, product defect counts, regression quality,
  or blinded direct-vs-delegated quality equivalence.
- A saved local state artifact is not evidence that a model worker performed
  the requested implementation.

## Execution-shape comparison

- `DIRECT`: represented by `DIRECT TASK` classification and is the clear
  default for trivial or tightly coupled work; an end-to-end direct model run
  was not available in this CLI-only audit.
- `GUIDED`: substantially represented by Goal Contract, evidence reuse,
  context pointers, governance gates, CAPSULE, ledger, no-progress, and done
  checks.
- `DELEGATED_BOUNDED`: represented only as selected named-role metadata and
  quorum guards. The current `p2p_workflow.py` does not spawn or verify host
  workers. Delegation is therefore an acceleration layer, not a correctness
  dependency, but its tax cannot be measured here.

Qualitatively, P2P already covers most of the governance/continuity shape
(roughly the requested 70-80% control surface), but not 70-80% of measured
token efficiency. That percentage is an architecture observation, not a
benchmark result.

## CAPSULE audit

Current `p2p-capsule/2` captures a useful continuation index: goal/objective,
eligibility, current/next state, blockers, bottleneck, reusable evidence,
failed approaches, approval state, progress, verified report, and artifact
paths. It is pointer-based, which avoids copying the full Goal and ledger.

Observed omissions against the bounded execution-capsule hypothesis:

- owned scope and protected areas are indirect pointers, not explicit capsule
  fields;
- relevant facts and relevant decisions/rationale are not materialized;
- dependencies/interfaces, invariants, and regression boundary are absent as
  explicit fields;
- escalation conditions and expected return format are not explicit;
- there is no explicit resume instruction; `Next action` is only a short
  continuation hint.

This is a real rediscovery/error-risk gap, but it does not justify a second
memory or orchestration system.

## Knowledge Delta and repair-loop findings

There is no current first-class `KNOWLEDGE_DELTA` schema. The proposed return
contract is best classified as a small output contract over existing
Execution Ledger, Evidence Contract, FACT_LEDGER, and Decision Trace—not a
new capability or store. A useful delta would contain status/outcome, new
verified facts, changed contracts, invalidated assumptions, review decisions,
risks, verification evidence, and exact references; raw logs should remain at
their original evidence location.

The existing repair controls cover the safety core:

- repeated identical incomplete state produces `ESCALATE` with
  `framework_retry=false`;
- independent done-check returns `VERIFIED` only with actual evidence and
  explicitly separates agent-done from Goal-done;
- exploration permits one primary and one lowest-risk alternative, then
  blocks instead of opening an unbounded lane.

The beginner evaluator confirms that a repair demonstration is controlled by
the synthetic fixture controller, not an automatic runtime repair loop. A
local repair loop therefore remains a hypothesis, not a measured runtime
capability.

## Capability, budget, and safety findings

- Capability preflight is strong for the current surfaces: unavailable
  Aesthetica is not simulated or repeatedly retried; stale/unknown context is
  excluded; unknown optional providers remain non-fatal; the core stays
  usable.
- Goal guards provide `max_work_items`, `max_agent_calls`, one optional full
  quorum call when explicitly required, and risk-based 30/90/180 minute
  limits. They do not provide runtime token, provider-call, repair-round, or
  per-child budgets.
- Evidence strength is validator/runtime-based, not model self-confidence.
  `UNKNOWN`, `PARTIAL`, `MISSING_REFERENCE`, and `CONTRADICTED` remain valid
  outcomes.
- Intent does not grant permission: protected actions require existing policy
  and approval gates; retrieved content cannot grant tools or permissions;
  bare approval booleans are rejected.
- A unified per-execution permission envelope for READ/WRITE/NETWORK/SECRETS/
  DESTRUCTIVE_ACTION/PROVIDER_ACCESS is not present in the P2P capability
  manifest. Host sandbox and project policy provide partial boundaries, but
  access, logging, persistence, and egress are not one auditable contract.
- Redaction and local no-network evaluation are present for Decision Trace and
  provider boundaries. A host-owned per-tool egress/logging receipt is not
  available in this runtime evidence.

Structural enforcement classification:

| Invariant | Current enforcement |
|---|---|
| Canonical identities and denominator 8 | validator + registry + tests |
| Aesthetica optional/noncanonical | validator + quorum runtime |
| Retrieved content cannot grant authority | runtime trust classifier |
| Bare approval boolean invalid | Decision Trace validator/runtime |
| Unsupported evidence cannot be VERIFIED | independent done-check runtime |
| Unknown/stale/missing references remain visible | context/trace runtime |
| Host sandbox/egress and per-task effect envelope | partial host/policy boundary; not unified |
| Prompt wording and specialist behavior | prompt/profile policy only |

## Long-run and beginner findings

The 15-stage beginner journey provides longitudinal evidence, but it is not a
token-pollution test. Current runtime CAPSULE creation is tied to workflow
state/reporting; the legacy prompt documentation describes message/context
triggers, but no current host telemetry proves automatic checkpoint timing or
context reduction. A bounded project checkpoint is `USEFUL`, with the existing
FACT/Live/Decision Trace/ledger continuity preserved.

The beginner does not need to choose DIRECT/GUIDED/DELEGATED or understand
tokens, workers, or budgets. That is a strength. The measured limitations are
mostly internal: discovery questions are not persisted in the Goal Contract,
some colloquial tasks classify poorly, and synthetic PASS can be mistaken for
real implementation unless the report boundary is read.

## Failure-mode coverage

| Failure mode | Current evidence | Finding |
|---|---|---|
| Worker unavailable | no host worker call in workflow | no correctness dependency shown; real tax unavailable |
| Network unavailable | no external provider/network dependency in evaluator | core remains usable |
| Optional capability missing | readiness/router negative path | fail closed, no simulation |
| Test failure/repair | no-progress + beginner synthetic repair | bounded; runtime repair not proven |
| Large tool output | no host tool trace | UNKNOWN |
| Stale context | context pointer test | excluded as STALE |
| Conflicting evidence | Decision Trace evaluator | explicit contradiction/PARTIAL |
| Scope expands | Goal classification/update and out-of-scope backlog | bounded/blocked behavior present |
| Large task is trivial | direct-task classifier | classification exists; quality/cost comparison unavailable |

## Quality-adjusted classification

1. `ADOPT_NOW` (future implementation Goal only): add a read-only benchmark
   harness that records host-provided token counters, raw tool bytes, repeated
   reads, handoffs, repair rounds, wall-clock, and the same acceptance/
   regression/defect/evidence metrics for DIRECT/GUIDED/DELEGATED runs.
   Expected context saving: measurable; quality gain: neutral/positive only if
   equivalence holds; total cost: initially higher; complexity: medium;
   beginner benefit: indirect; security effect: positive if telemetry is
   redacted and local.
2. `ADOPT_NOW` (future implementation Goal only): define a small
   `KNOWLEDGE_DELTA` return block and refine the existing CAPSULE by pointers,
   not a new store/router. Expected quality gain: lower rediscovery and clearer
   handoff; context saving: likely but unproven; total cost: small serialization
   overhead; complexity: low; beginner benefit: lower hidden ceremony;
   security effect: positive if raw logs stay local and references are redacted.
3. `ADOPT_NOW` (future implementation Goal only): add a single capability/budget
   preflight decision to existing Goal execution, covering availability,
   provider/network prerequisites, bounded child/repair/provider budgets, and
   direct fallback. Do not hardcode numbers before measurement. Expected
   quality gain: fewer futile retries; context saving: indirect; total cost:
   lower on blocked paths; complexity: low-medium; beginner benefit: invisible;
   security effect: positive.

## DEFER / REFERENCE_ONLY / REJECT

- `DEFER`: Code-Impact/dependency-graph integration, persistent worker pools,
  automatic memory learning, new provider integrations, and real delegated
  A/B certification until host identity/telemetry is available.
- `REFERENCE_ONLY`: the external `codex_workflow` route distinction and
  summary/handoff ideas; the public Reddit vexp claim of a token-budgeted
  dependency capsule; and Comp AI CRM's explicit UI source-of-truth and
  read/write/egress boundary documentation. These are hypotheses or design
  references, not P2P evidence: [codex_workflow](https://github.com/viettran-edgeAI/codex_workflow), [Reddit context-capsule discussion](https://www.reddit.com/r/ClaudeCode/comments/1rdo5ul/i_cut_claude_codes_token_usage_by_65_with_a_local/), [Comp AI design rules](https://github.com/trycompai/crm/blob/release/docs/design.md), [Comp AI security boundaries](https://github.com/trycompai/crm/blob/release/SECURITY.md).
- `REJECT`: claiming token savings from main-context reduction alone; copying
  an external framework; making delegation a correctness dependency; treating
  generic subagents as named specialists; persisting raw prompts/logs as
  memory; or changing canonical 8 to 9/9.

## Code-Impact boundary and regression safety

Repeated repo rediscovery was not measured because no host tool trace exists.
The result is evidence for a future P2P Code-Impact Evidence Contract only;
Anvien, Repowise, Graphify, and other external code-intelligence providers were
not integrated.

Protected source hashes remained unchanged for `VERSION`, `AGENTS.md`, the
Codex config/profile, the manifest, and the capability registry. No P2P source,
config, installer, release artifact, Aesthetica profile, or user project was
modified. Only audit outputs were created under `.tmp` and the two QA/supervisor
report paths.

## CE status

| CE | Status | Reason |
|---|---|---|
| CE1 | PASS | six-case current execution baseline measured |
| CE2 | BLOCKED | token/context/read/handoff telemetry unavailable |
| CE3 | BLOCKED | no quality-equivalent cost comparison |
| CE4 | PARTIAL | six shapes exercised synthetically, not real model work |
| CE5 | BLOCKED | delegation tax not observable |
| CE6 | PASS | current CAPSULE audited; content remains partial |
| CE7 | PASS | Knowledge Delta classified as a small output contract |
| CE8 | PASS | repair hypothesis evaluated against existing guards |
| CE9 | PASS | capability preflight evaluated |
| CE10 | PARTIAL | execution guards exist; token/provider/repair budgets missing |
| CE11 | PASS | evidence/self-confidence boundary audited |
| CE12 | PASS | UNKNOWN/PARTIAL safety verified |
| CE13 | PASS | intent/permission boundary verified |
| CE14 | PARTIAL | policy/redaction exists; unified egress/effect telemetry absent |
| CE15 | PASS | structural enforcement matrix completed |
| CE16 | PARTIAL | checkpoint useful, automatic long-run pollution reduction unmeasured |
| CE17 | PASS | beginner burden evaluated |
| CE18 | PARTIAL | fallback is conceptually safe, not a host-unavailable comparison |
| CE19 | PASS | ADOPT/DEFER/REFERENCE/REJECT classification complete |
| CE20 | PASS | exactly three bounded recommendations |
| CE21 | PASS | no external repository integrated |
| CE22 | PASS | no new agent created |
| CE23 | PASS | no P2P runtime modified |
| CE24 | PASS | no user project modified |

The Goal remains `BLOCKED` until CE2, CE3, CE4, and CE5 can be satisfied by a
separate telemetry-backed, quality-equivalent benchmark. No implementation was
performed in this audit.

