---
name: p2p-scope
description: >-
  Apply P2P SCOPE.HELM to decompose a large task into atomic steps, checkpoints, blockers,
  and stop conditions. Use when the user invokes $p2p-scope or asks to organize
  substantial multi-step work.
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

When **two or more material blockers** genuinely compete for the next action, perform one bounded bottleneck check: distinguish source-backed `FACT` from `INFERENCE` and `UNKNOWN`; ask which blocker, if resolved, would *causally* unlock another blocker or the acceptance condition; choose that blocker only when current evidence supports the dependency, then perform the smallest reversible check of that hypothesis. If blockers are independent or evidence is insufficient, say so and order work by verified dependencies, impact, and reversibility. Skip this check for direct tasks or an already-clear critical path. Do not invent a "principal contradiction", force a new output template, or add another review/coordination layer.
