# P2P-C15 Safe Project-Style Field Test Evidence

## Scope

This is a disposable local project-style fixture, not a synthetic assertion
against isolated dataclasses and not a user production project. The runner
uses the real `TaskPlan`, `TaskStateStore`, `BoundedDelegationController`,
`EvidenceClaim`, filesystem artifact boundary, and existing decision/ledger
paths. The worker is the explicitly supported foreground callback surface;
there is no host identity simulation.

## Command

```text
python -B scripts/p2p_c15_field_test.py --output .tmp/p2p-c15-field-test-20260816.json
```

Result: `PASS`, `all_checks_pass=true`.

Evidence JSON: `.tmp/p2p-c15-field-test-20260816.json`  
SHA-256: `69fa8143c065d6960ec0ae4540aabcbc0ad8f4df8bffd05011ed024023437dc0`  
Runtime: `local-supported-foreground-callback`  
Fixture: repo-local disposable project roots with `src/main.py`, `README.md`,
and durable `.p2p/state`.

## A-F Acceptance Matrix

| ID | Observed behavior | Result |
|---|---|---|
| A | No material delegation value selects `DIRECT`; bounded read-only action and current evidence reach `DONE`. | PASS |
| B | Specialist/context-isolation value selects `DELEGATE`; the bounded handoff contains only scoped inputs and no model/profile selection. | PASS |
| C | Parent verification returns incomplete evidence; task remains non-DONE with `VERIFICATION_FAILED`. | PASS |
| D | Parent rereads the current fixture, accepts a C10 `EvidenceClaim`, and the existing C11 task reaches `DONE`; worker output remains proposal-only. | PASS |
| E | Child result attempts `child_delegation_allowed=true`; the controller returns `CONTROL_PLANE_ERROR` / `CHILD_DELEGATION_FORBIDDEN` and no grandchild is started. | PASS |
| F | Foreground callback interruption leaves durable task `ACTIVE`, persists `SAFE_TO_RESUME` checkpoint state, and resume classification is `SAFE_TO_RESUME` with `automatic_start=false`. | PASS |

## Safety Observations

- `synthetic_host_identity=false`.
- `no_external_side_effects=true`.
- No network, subprocess, scheduler, queue, background task, parallel child,
  release, deployment, or Logistics project access was used.
- All fixture roots were temporary and repo-local; no production/business data
  was changed.

## Current follow-up verification

- Focused C15 after the deterministic-fingerprint fix: `24/24 PASS`.
- Affected C15+C11+C12 slice: `64/64 PASS`.
- Full repository suite: `218/218 PASS`.
- The field JSON above is the fresh rerun after those checks; its six acceptance
  checks remain true.
