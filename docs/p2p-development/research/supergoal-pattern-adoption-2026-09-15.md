# Supergoal pattern adoption — 2026-09-15

Status: `BOUNDED_PATTERN_ADOPTION_CANDIDATE`

## Decision

P2P does **not** install Supergoal as another control plane. It adopts only the
small mechanisms that improve execution while preserving existing P2P state,
evidence, permission, verifier, and governance authority.

```text
SUPERGOAL_AS_SECOND_CONTROL_PLANE = REJECTED
NATIVE_GOAL_HOST_PRIMITIVE = ADOPT_PATTERN
COMPLETE_WORKTREE_VS_BASELINE = ADOPT_PATTERN
FINAL_ORIGINAL_CONTRACT_REPLAY = ADOPT_PATTERN
FIXED_THREE_STRIKES_HARD_STOP = REJECTED
SUPERGOAL_STATE_ROADMAP_PROTOCOL_AUTHORITY = REJECTED
SUPERGOAL_MEMORY_AUTHORITY = REJECTED
THINKING_MD_PRIVATE_REASONING_ARTIFACT = REJECTED
```

## Upstream provenance

- Upstream repository: `robzilla1738/supergoal`
- License: MIT (`LICENSE`, copyright 2026 Robert Courson)
- Research snapshot observed on 2026-09-15: GitHub code search resolved the
  relevant Supergoal files at commit
  `ec2f6eb8eb3304a4ed32f1f18948a6c6198fcd67`.
- Relevant upstream mechanisms inspected:
  - `skills/supergoal/SKILL.md`
  - `skills/supergoal/templates/PROTOCOL.md`
  - `skills/supergoal/scripts/repo-state.sh`
  - `skills/supergoal/references/repo-state-comparison.md`

No Supergoal state files, protocol files, retry framework, memory store, daemon,
or scheduler are vendored into P2P. The worktree comparison is an independent
P2P implementation of the general Git technique; it is not a copied shell
script.

## Why the three-strike policy is rejected

Supergoal's bounded recovery sequence (probe/retry, focused fix spec, then
handoff) is useful as a diagnostic shape, but the fixed attempt count conflicts
with P2P Supreme Law. P2P recovery is failure-class aware:

deterministic repair, stochastic sampling, transient infrastructure, and
unknown-side-effect recovery do not share one retry budget. A permission or
unknown-side-effect failure may require an immediate stop; a transient provider
failure may justify later retry; repeated deterministic non-progress should
change diagnosis/route rather than mechanically consume a strike counter.

The adopted native-goal projection therefore carries:

```text
recovery_policy = P2P_ADAPTIVE_FAILURE_CLASSIFICATION
fixed_retry_hard_stop = null
```

No `attempt == 3 => BLOCKED` rule is introduced.

## Pattern 1 — host-native `/goal` as a projection, not authority

`native_goal_bridge.py` projects the existing canonical P2P GoalPlan/TaskPlan
into a short host-native `/goal` condition. It creates no P2P state and performs
no execution itself.

Host semantics are intentionally not flattened:

### Claude Code

Current official documentation checked 2026-09-15:
`https://code.claude.com/docs/en/goal`

Claude Code documents `/goal <condition>` as an evaluator-driven session loop:
a separate small evaluator checks the transcript after each turn and may cause
Claude to continue. The evaluator sees transcript context only; it does not
independently run tools/read files. Therefore the evaluator is useful host
control, **not P2P acceptance evidence**.

### Codex CLI

Current official documentation checked 2026-09-15:
`https://learn.chatgpt.com/docs/developer-commands?surface=cli`

Codex documents `/goal <objective>` plus view/edit/pause/resume/clear and says
the goal remains attached to the active chat while work continues. P2P does
**not** infer Claude-style automatic continuation or a separate independent
evaluator where the Codex documentation does not claim them.

Both surfaces currently document a 4,000-character objective/condition limit;
the P2P projection fails closed if its generated condition exceeds that bound.

## Pattern 2 — complete working-tree evidence

`scripts/p2p_worktree_evidence.py` compares an exact 40-character Git baseline
commit with the complete current worktree.

Load-bearing comparison:

```text
tracked committed-after-baseline + staged + unstaged + deleted
  => git diff <baseline>        # one revision, not <baseline>..HEAD

untracked
  => git ls-files --others --exclude-standard
```

The helper is read-only, does not read file contents, and is explicitly
non-authoritative evidence support. It fails closed on an invalid/non-exact
baseline instead of silently degrading to a weaker comparison.

## Pattern 3 — replay the original contract before completion

`build_contract_replay_manifest()` re-projects each original P2P task in exact
goal task order and fingerprints the immutable intent fields. It carries the
original scope/non-scope, acceptance requirements, required evidence, and
permission needs.

This is deliberately a projection:

```text
ORIGINAL P2P GOAL/TASK STATE = AUTHORITY
REPLAY MANIFEST = CHECKLIST / HOST INPUT
NATIVE /goal EVALUATOR = NOT ACCEPTANCE AUTHORITY
P2P INDEPENDENT VERIFIER EVIDENCE = COMPLETION AUTHORITY
```

The final native-goal condition tells the executor to reload durable state and
replay these original contracts before it can claim completion. Drift in a
host transcript, self-report, phase note, or executor PASS cannot rewrite the
original contract.

## Evidence boundary for this slice

The focused tests can prove:

- projection preserves P2P authority boundaries;
- Claude/Codex semantics are kept distinct in the projection;
- fixed three-strike recovery is absent;
- replay fingerprints/order/acceptance/evidence fields are deterministic;
- whole-worktree comparison sees committed-after-baseline, staged, unstaged,
  deleted, and untracked changes;
- baseline/path validation fails closed.

They **cannot** prove a live Claude or Codex `/goal` loop, account permissions,
provider availability, model behavior, or production execution. Those require
a later representative host probe and remain separate evidence.

## Anti-overengineering boundary

This first slice intentionally does not add the new helpers to the release
package/install projection yet. First prove the bounded mechanism in this
repository. Package/install transport is a successor step only if the focused
and hosted regression evidence is sufficient and the capability is actually
selected for installation.
