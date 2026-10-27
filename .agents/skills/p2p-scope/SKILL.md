---
name: p2p-scope
description: >-
  Apply P2P SCOPE.HELM to decompose a large task into atomic steps, checkpoints, blockers,
  and stop conditions. Use when the user invokes $p2p-scope or asks to organize
  substantial multi-step work, including choosing between competing material blockers.
---

Read `../p2p/references/codex-adaptation.md` before applying any Claude-edition
mechanism. The matching section in `../p2p/references/modes.md` is the runtime
contract. Current host permissions and current verified facts take precedence.

# P2P SCOPE.HELM

Classify the request before creating a Goal as `DIRECT TASK`, `PLAN FIRST`,
`GOAL`, or `SEPARATE GOALS`. Create or reuse the workflow Goal Contract before
decomposing long-running work. The plan must have one primary objective,
mandatory criteria with verification oracles, explicit mandatory/supporting/
optional/OUT-OF-SCOPE items, a time/attempt guard, evidence-reuse decisions,
work type, one primary lane plus at most one justified alternative, and the
three terminal states `PASS`, `BLOCKED`, and `REJECT`. When a check is already
trusted PASS and its relevant inputs have not changed, reuse it. Do not open
speculative improvement lanes, silently absorb a new objective, or keep
working after PASS. Use the host plan mechanism when available. Do not add
subagents unless the workflow's adaptive selection or an explicit user request
justifies them.

## Competing-blocker triage (conditional)

Activate only when two or more material blockers compete for the next action
and the dependency order is not already proven. Skip direct tasks, a single
blocker, or an already-clear critical path. Reuse existing Goal and evidence
labels; do not create another tracker.

1. Anchor the blocked mandatory acceptance condition. Separate verified
   `FACT` (current source or runtime evidence), testable `INFERENCE`, and
   `UNKNOWN`. An old report or simultaneous symptoms are not a causal link.
2. Ask whether resolving blocker A would actually unblock B or acceptance.
   Require observable dependency evidence. If that link is uncertain, make one
   small, reversible read-only check that could falsify the hypothesis.
3. When a prerequisite is proven, prefer it. For independent blockers, choose
   by mandatory impact, dependencies, risk, and reversibility; never fabricate
   a single principal cause. Existing permissions and Owner Gates still apply.
4. Give one smallest next check or correction, its expected evidence, and the
   condition that would disprove it. On contradiction, update priorities.
   Stop at verified acceptance or a genuine BLOCKED state.

Only include this reasoning in existing SCOPE/ATLAS output when it changes NEXT.
No extra form, mandatory template, agent, router, or review workflow.
