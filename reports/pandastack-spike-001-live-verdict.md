# P2P PandaStack Spike 001 — Live Verdict

**Status:** PILOT_PARTIAL_PASS / BRANCH_EXPLORE_BLOCKED  
**Date:** 2026-09-09  
**Branch:** `spike/pandastack-sandbox-001`  
**PR:** #84  
**Promotion:** UNPROMOTED  
**Production impact:** NONE

## Live evidence

The PandaStack credential was supplied through the GitHub Actions repository secret `PANDASTACK_API_KEY`. No secret value is stored in this report or repository.

### Verified live capabilities

- Authentication / credential acceptance: PASS
- Hosted sandbox creation: PASS
- Command execution: PASS
- Filesystem write/read: PASS
- Public Git clone inside sandbox: PASS
- HTTP preview server + PandaStack preview URL generation: PASS
- Explicit cleanup of known sandboxes: PASS
- Tagged orphan sweep after bounded retries: PASS (0 tagged orphans detected)

### Fork / Branch & Explore evidence

**Run #3 / workflow run 34308818275**
- Parent sandbox created successfully.
- Preview URL generated successfully.
- Plain `fork()` returned a child sandbox.
- Expected inherited marker in `/workspace` was absent.
- Result: `FORK_STATE_INHERITANCE_FAILED`.

**Run #4 / workflow run 34308967141**
- Basic sandbox capabilities passed again.
- SDK `fork_tree(count=1)` failed with PandaStack API read timeout after 30 seconds.
- Result: live fork-tree capability not verified.

**Run #5 / workflow run 34309102005**
- Retried only after adding mutation-safe tagged cleanup.
- Pre-run orphan cleanup count: 0.
- Basic sandbox capabilities passed again.
- Direct REST `POST /v1/sandboxes/{id}/fork-tree` with a 120-second read timeout still timed out.
- Post-run orphan cleanup count: 0.
- Result: live fork-tree capability remains blocked.

## Verdict

```text
PANDASTACK_BASIC_EXECUTION=PASS
PANDASTACK_AUTH=PASS
PANDASTACK_PREVIEW=PASS
PANDASTACK_GIT_CLONE=PASS
PANDASTACK_CLEANUP=PASS
PANDASTACK_COLD_FORK_STATE_INHERITANCE=FAIL
PANDASTACK_FORK_TREE=BLOCKED_API_TIMEOUT
PANDASTACK_BRANCH_EXPLORE=NOT_VERIFIED
PANDASTACK_SPIKE_RESULT=PILOT_PARTIAL_PASS
P2P_ADOPTION_DECISION=DO_NOT_ADOPT_AS_CORE_EXECUTION_LAYER_YET
```

## Decision boundary

PandaStack is empirically usable for basic isolated execution, filesystem operations, Git clone, and preview hosting.

The differentiating capability relevant to P2P, stateful fan-out for Branch & Explore, did not pass live verification. Therefore this pilot does not justify integrating PandaStack into P2P's core execution path, replacing Arena, adding a new router, or changing canonical architecture.

No further blind retry is authorized from this evidence. A future retry requires either a PandaStack service fix, vendor clarification, a changed API/SDK, or other new evidence that materially changes the failure condition.
