# P2P Arena Agent Mode Protocol

Status: `DEVELOPMENT_SOURCE_CANDIDATE` / `READY_FOR_OWNER_GATE`

Scope: GitHub-connected Arena Agent Mode for bounded P2P development

Canonical source: `docs/ARENA_AGENT_MODE_PROTOCOL.md`

This is the single canonical Arena protocol for this repository. It is a
documentation and project-projection policy. It does not add a router, agent,
registry entry, runtime executor, onboarding fast path, or provider/model
selector. P2P remains the source of policy; a project-scoped projection is a
derived, hash-bound view.

## 1. Execution unit and usage limits

The operational unit is a session, not an account quota or a prompt counter:

```text
ARENA_SESSION=EXECUTION_UNIT
ARENA_ORCHESTRATOR_MODEL=NOT_EXPOSED_BY_PRODUCT
ONE_SESSION_ONE_PR=YES
FIXED_PROMPT_COUNT_SESSION_POLICY=DO_NOT_USE
ARENA_CHAT_STATE_IS_EPHEMERAL
GITHUB_PROJECT_STATE_IS_CANONICAL
```

Arena has multiple independent constraints, including:

- session token/context limits;
- per-model rate limits;
- overall chat rate limits; and
- daily account usage limits.

Agent Mode uses conversation compaction. None of those facts supports a fixed
prompt allowance or a universal account quota.

The following historical assumptions are deprecated and must not be used as
active policy:

| Historical assumption | Canonical disposition |
| --- | --- |
| `TWO_PROMPTS_PER_ACCOUNT_ASSUMPTION` | `DEPRECATED` |
| `APPROX_TWO_USEFUL_SESSIONS_PER_ACCOUNT` | `DEPRECATED` |
| Fixed-count interpretation of `FIXED_PROMPT_COUNT_SESSION_POLICY` | `DO_NOT_USE` |

Session rotation is never triggered by prompt count alone.

## 2. GitHub-connected session lifecycle

For one GitHub-connected Arena development pass:

```text
ONE ARENA CHAT SESSION
    -> ONE BOUNDED DEVELOPMENT GOAL
    -> ONE WORKING BRANCH
    -> ONE PR
```

The lifecycle is `ONE ARENA CHAT SESSION → ONE BOUNDED DEVELOPMENT GOAL →
ONE WORKING BRANCH → ONE PR`.

Arena creates a sandbox or copy of the selected repository for the session.
The working branch is the session's bounded change surface. This lifecycle
does not make the Arena sandbox canonical and does not replace P2P project
state, evidence, or governance.

Before Owner merge or promotion, every durable item needed after the session
must already be pushed to the candidate branch, when applicable:

- implementation;
- tests and QA evidence;
- screenshots;
- durable reports;
- `docs/CURRENT_STATE.md`;
- `production/SESSION_INDEX.md`;
- handoff material; and
- visual evidence pinned to the candidate SHA.

An item that exists only in the Arena sandbox or chat is not a durable
candidate artifact.

## 3. Post-merge and post-close lock

The old session is not a write-back channel after the PR lifecycle ends:

```text
PR MERGED OR CLOSED
    -> OLD_SESSION_GITHUB_WRITE_CAPABILITY=TERMINATED
```

Canonical transition: `PR MERGED OR CLOSED → OLD_SESSION_GITHUB_WRITE_CAPABILITY=TERMINATED`.

Do not return to the same merged or closed Arena session for further GitHub
writes. Any correction that requires a new PR starts a new bounded session.

## 4. Session rotation

Use `CONTINUE_CURRENT_SESSION` only when all of the following remain true:

- the bounded goal is the same;
- the same PR remains open;
- context remains healthy; and
- the correction is small and directly related.

Use `START_NEW_SESSION` when any of the following is true:

- the PR was merged or closed;
- a new PR is required;
- a new bounded development goal begins;
- Arena reports session token or context exhaustion; or
- persistent context degradation or tool confusion is observed.

Do not rotate because a guessed prompt allowance was reached. The session
state decision is based on goal, PR, context health, and product-reported
limits.

## 5. Agent Mode model identity

The standard representation is:

```text
ARENA_ORCHESTRATOR_MODEL=NOT_EXPOSED_BY_PRODUCT
```

Standard Arena prompts and return templates omit legacy requested-model,
actual-execution-model, and request-honored fields. Orchestrator identity must
not be inferred from writing style, quality, tool use, or self-report. No
model-selection requirement is added unless Arena later exposes explicit Agent
Mode model selection.


### 5.1 Session-quality canary for hidden/random Agent Mode

Arena Agent Mode currently selects a dedicated orchestrator for a new chat and
does not expose that orchestrator identity. Product behavior may also switch the
underlying model when a response is likely to fail. Therefore P2P evaluates the
observed session capability, not a guessed model identity.

For a new Arena Agent session handling medium/high-risk work whose quality is
not yet proven, apply notebook RULE 19 `MODEL_CANARY_GATE_V1` before material
project mutation. Skip it for low-risk/mechanical tasks or when the real task
itself is already the cheapest representative probe.

The canary:

- uses at most three tiny probes;
- includes at least one task-representative probe;
- keeps coding probes disposable/non-durable (no canary-only PR/commit);
- may use a randomized animal × vehicle SVG probe only for relevant
  visual/spatial work;
- never treats the fixed pelican/bicycle prompt as a model ranking;
- never asks the tested Arena session to grade itself; and
- never infers model/provider/reasoning level from output style or quality.

Return only observable classification:

```text
CANARY_CLASS=GREEN | YELLOW | ORANGE | RED
MODEL_IDENTITY=UNKNOWN
CAPABILITY_EVIDENCE=<tests/render/diff/tool/recovery evidence>
SESSION_POLICY=KEEP_SESSION | LIMIT_SESSION | ADVISORY_ONLY | REROLL_OR_SWITCH
```

`RED` permits one evidence-justified fresh-session reroll by default; do not
reroll repeatedly to gamble for a preferred hidden model.


## 6. Prompt architecture and routing

The standard execution prompt is concise and follows:

```text
ASSESS
    -> IMPLEMENT
    -> VERIFY
    -> RETURN
```

In compact form: `ASSESS → IMPLEMENT → VERIFY → RETURN`.

Every P2P-generated Arena prompt must expose these user-facing routing fields:

```text
DESTINATION=ARENA AI
SESSION_ACTION=CONTINUE_CURRENT_SESSION | START_NEW_SESSION
SESSION_GOAL=
PR_EXPECTATION=
```

Before `ASSESS`, every Arena executor must complete the
`P2P_SUPREME_OPERATING_LAW_V1` preflight.

`TASK_BRANCH != LAW_AUTHORITY`.

`TARGET_PROJECT != LAW_SOURCE`.

The Arena target repository and working branch are execution state only. They
must never determine which Supreme Law version applies. A P2P-managed task in
another repository does not need to switch its working branch or copy P2P
source into that project merely to obtain the law. When Arena can access the
canonical P2P repository, read the law directly from
`7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md`
regardless of the selected target repository or task branch.

A notebook copied into an installed project or old task branch may be used only
when it contains `P2P_SUPREME_OPERATING_LAW_V1`; a stale branch-local copy does
not outrank the inline `SUPREME_LAW_CAPSULE`. The Control Tower prompt must
carry that capsule so Arena still receives the active minimum law when the
canonical P2P repository cannot be read.

Do not claim a repository file was read unless it actually was. The preflight
exists to shape execution; it must not expand into a separate planning/reporting
phase.

The Owner must not infer whether to reuse the current Arena chat or create a
new one. Within `ASSESS`, expose only:

```text
GOAL=
CURRENT_STATE=
MAIN_RISK=
PLAN=
```

Do not request private chain-of-thought. Do not repeat large P2P or project
architecture text when the canonical GitHub files already contain it. Use
risk-proportional tests and stop once sufficient evidence exists.

A minimal operational shape is:

```text
DESTINATION=ARENA AI
SESSION_ACTION=CONTINUE_CURRENT_SESSION | START_NEW_SESSION
SESSION_GOAL=<one bounded goal>
PR_EXPECTATION=<one working branch and one PR>

ASSESS
GOAL=<bounded outcome>
CURRENT_STATE=<durable file/evidence references>
MAIN_RISK=<largest material risk>
PLAN=<smallest defensible plan>

IMPLEMENT
<bounded implementation only>

VERIFY
<risk-proportional checks and durable evidence>

RETURN
<result, changed files, checks, candidate SHA/tree, blockers, next action>
```

## 7. Visual evidence law

For game, UI, and other visual work:

```text
SANDBOX_ARTIFACT != OWNER_VISIBLE_EVIDENCE

actual browser/runtime
    -> screenshot
    -> durable candidate-branch file
    -> PR inline image
    -> URL pinned to exact candidate SHA
    -> Owner-visible on mobile
```

The browser or runtime observation is the source event; the screenshot is the
captured evidence; the candidate-branch file is the durable attachment. A
candidate-only file must not use a relative link or a default-main URL that
resolves against an unmerged branch. A visual claim is not complete until the
Owner can open the exact-SHA URL, including on mobile.

## 8. Durable memory and fresh-session bootstrap

The state boundary is explicit:

```text
ARENA_CHAT_STATE_IS_EPHEMERAL
GITHUB_PROJECT_STATE_IS_CANONICAL
```

New Arena sessions reconstruct from GitHub project files and verified evidence,
not from an old Arena conversation transcript.

When the paths exist, use this bootstrap order:

1. `AGENTS.md`;
2. project master specification;
3. `docs/CURRENT_STATE.md`;
4. `production/SESSION_INDEX.md`;
5. latest accepted session report;
6. task-specific projected P2P capabilities;
7. this Arena Agent Mode protocol; and
8. the P2P operations notebook (`P2P_OPERATIONS_NOTEBOOK`) when the
   project's `AGENTS.md` block or this protocol points to it.

The current P2P development source binds the generic names to its real
surfaces: `docs/p2p-development/P2P-DEVELOPMENT-CHARTER.md` is the master
development specification, `governance/development-control.json` and
`docs/p2p-development/current-roadmap.md` carry current development state,
accepted reports are selected from the relevant
`docs/p2p-development/reports/` or candidate evidence path, the
task-specific capability projection is
`docs/p2p-development/capability-ledger/capability-index.json`, and the
canonical operations notebook is
`docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md`.

If a project has no `docs/CURRENT_STATE.md` or
`production/SESSION_INDEX.md`, do not create a fake duplicate solely for
Arena. Bind the protocol to that project's actual canonical state and session
index paths.

## 9. Project projection policy

The canonical direction is:

```text
P2P CANONICAL SOURCE
    -> SELECTIVE PROJECT PROJECTION
    -> APPLICABLE GITHUB PROJECT
```

The full policy source remains this file in the P2P repository. An applicable
project receives only the short operational content selected by the existing
P2P projection path. It must not maintain a hand-edited, divergent copy.

The existing projection contracts remain authoritative:

- `docs/SPEC/P2P-HOST-SKILL-PROJECTION-SPEC.md`;
- `docs/SPEC/P2P-PROJECTION-ONLY-PROJECT-IDENTITY-SPEC.md`;
- input schema `p2p-host-skill-projection-input/1`;
- pure plan schema `p2p-host-skill-projection-plan/1`; and
- projection binding schema `p2p-project-projection-binding/1`.

For an applicable project, protocol material is eligible only when the
existing selected plan declares it as a project-relative managed file. The
plan, exact content hash, ownership, and v2 projection pin are the projection
authority. Valid target roots remain project-scoped `.agents`, `.claude`,
`.gemini`, `.cursor`, and `.github`; user/global host paths are invalid.

The current Codex target family is
`.agents/skills/<capability_id>/SKILL.md` plus its declared metadata file.
There is no generic protocol materializer in this candidate, so no future
project target is claimed to have been materialized here. Future projection
work must use the existing plan and pin surfaces; it must not add a second
registry, router, schema, or manual synchronization path. A project without an
applicable selected plan is not claimed to have received the protocol.

`P2P-PROJECT-ONBOARDING-FASTPATH-01` is unchanged. This documentation and
projection-policy update exposes no missing invariant that justifies reopening
or prematurely implementing that workstream.

## 11. P2P operations notebook discovery

Arena executors operating a P2P-installed project discover the single
canonical operations notebook `P2P_OPERATIONS_NOTEBOOK` before generating
any P2P execution prompt or beginning implementation:

- P2P development source: `docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md`.
- Installed projects: the inherited digest in the project's `AGENTS.md` P2P
  block (`P2P_INSTALL => P2P_OPERATIONS_NOTEBOOK_ACTIVE_BY_DEFAULT`), which
  points to this protocol for the Arena session contract.

The notebook canonicalizes `P2P_SUPREME_OPERATING_LAW_V1`,
`P2P_BEGINNER_OPERATIONS_UX_V1`, and `RULE_ASSIMILATION_GATE_V1`. This protocol remains the canonical Arena
session contract (sections 1-10); it references the notebook for general
operations memory and does not maintain a divergent copy of notebook rules.

Completion-dialog handling ("Was this task successful?" — Yes / No / Keep
working) follows notebook RULE 15
(`ARENA_TASK_COMPLETION_DIALOG`): `YES` means the execution unit reached its
requested terminal state and returned the required ReturnPacket — an honest
`BLOCKED`/fail-closed result can still be `YES`; `KEEP WORKING` means more
work in the same chat; `NO` means Arena materially failed the execution
itself (wrong task, wrong repository/workstream, unusable result, ignored
required scope, or premature/incorrect termination), never merely a technical
`BLOCKED` outcome.

## 12. Evidence boundary

No usage observation in this documentation is a universal quota estimate. The
fixed-count policy is rejected by the execution-unit contract above, not by a
new usage benchmark.

This candidate changes documentation and policy only. It does not change
runtime logic, enable network/hooks/proxying, change onboarding execution,
release, deploy, push, promote, or approve an Owner gate.
