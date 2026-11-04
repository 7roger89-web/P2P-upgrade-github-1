# Roger UI/UX v1 — executor packet

Task class: bounded P2P skill integration + linked Logistics runtime proof.
Status: READY_FOR_AUTHORIZED_EXECUTOR
Auto merge: NO
Deploy: NO

## 0. Mandatory actor preflight

The executing actor must perform its own fresh P2P Supreme Law read. Do not copy
the Control Tower receipt from chat, PR comments, or this packet.

Then perform the bounded ACTIVE experience lookup required by current P2P law.

If valid law context cannot be established, stop with
`LAW_CHECK=BLOCKED`.

## 1. Target truth

P2P repository:
`7roger89-web/P2P-upgrade-github-1`

P2P working PR:
`#297`

Primary integration target:
`.agents/skills/p2p-uiux/SKILL.md`

Integration specification:
`docs/p2p-development/ROGER-UI-UX-V1-INTEGRATION.md`

Regression contract:
`tests/test_p2p_uiux_lean_workflow_contract.py`

Linked real-product pilot:
`7roger89-web/logistics-work-desk#13`

Before mutation, fresh-check:
- current `main`;
- PR #297 head/base relation;
- current `p2p-uiux` contents;
- current integration packet;
- current test file.

Do not assume the SHAs recorded in older chat messages are still current.

## 2. Allowed P2P mutation

Edit the existing `.agents/skills/p2p-uiux/SKILL.md` only as needed to add the
lean workflow contract from the integration packet.

Required concepts:
- relevant project/codebase audit before layout;
- compact `UI_AUDIT` receipt when useful;
- `ARRIVE / DECIDE / ACT / EXCEPTIONS` user-job contract;
- one primary lane: `BUILD / REDESIGN / AUDIT / SYSTEM / VISUAL_REGRESSION`;
- `PROJECT TRUTH -> USER JOB -> INFORMATION PRIORITY -> REUSE -> LAYOUT DECISION -> IMPLEMENT -> RENDER -> VERIFY`;
- reuse-first order;
- minimum necessary Owner Gate;
- operational attention/action over decoration;
- design-system restraint.

Keep the entrypoint concise. Do not copy the whole Roger portable skill into
P2P.

## 3. Must preserve

Do not weaken or remove:
- `p2p-uiux` primacy;
- the single existing P2P router;
- `SOURCE_REVIEW` vs `RUNTIME_VISUAL_REVIEW`;
- `RUNTIME_UI_REVIEW_REQUIRED=YES` semantics;
- honest downgrade when runtime/browser is unavailable;
- provider-neutral browser classification;
- `CLICK_CAPABILITY != WRITE_AUTHORITY`;
- read-only review default;
- accessibility evidence boundary;
- `p2p_aesthetica` optional/noncanonical boundary;
- canonical denominator = 8;
- existing Supreme Law and Owner authority.

Do not create:
- `.agents/skills/roger-ui-ux` inside P2P;
- a second UI/UX router;
- a browser daemon/server/control plane;
- a screenshot database;
- another governance ledger.

## 4. Focused P2P verification

Run at minimum:

```text
python -m unittest tests.test_p2p_uiux_lean_workflow_contract -v
python -m unittest tests.test_p2p_live_browser_uiux_review_01 -v
python -m unittest tests.test_p2p_beginner_routing -v
```

Then run the normal affected/full repository regression required by current
task/repo instructions.

The lean-workflow contract test must move from:
`3 PASS / 1 SKIP`
to:
`4 PASS / 0 SKIP`

Do not interpret this focused result as full P2P release certification.

## 5. Independent review

After implementation, use an independent Supervisor/reviewer that:
- performs its own law read;
- reads the exact PR head;
- checks that no parallel UI/UX authority was added;
- verifies preserved runtime/browser/safety boundaries;
- reruns the focused tests;
- reviews the diff for unnecessary ceremony or context bloat.

Writer receipt != Supervisor receipt.

## 6. Linked Logistics runtime proof

Target:
`7roger89-web/logistics-work-desk#13`

Runtime harness:
`playwright/roger_uiux_shipment_workspace_pilot.cjs`

Static harness guard:
`tests/test_roger_uiux_shipment_pilot_harness.py`

Run on an isolated/test Streamlit runtime, not production.

Example:

```text
node playwright/roger_uiux_shipment_workspace_pilot.cjs
```

Optional environment overrides:

```text
LOGISTICS_BASE_URL=http://127.0.0.1:8520/
LOGISTICS_PILOT_SHIPMENT=LO-0306
```

Required runtime evidence:
- desktop 1440x900;
- mobile 390x844;
- action card before situation summary;
- situation summary before 3 main jobs;
- 5 overview items;
- 5-column desktop grid;
- 2-column mobile grid;
- no legacy `.shipment360-signal`;
- named actions for Export / Import / Finance;
- no horizontal document overflow;
- JSON report;
- Markdown report;
- desktop screenshot;
- mobile screenshot.

The harness is read-only. Do not click `Xử lý`, save, import, create, or mutate
production data.

## 7. Acceptance boundary

Do not claim terminal completion until both are true:

1. P2P:
   - lean workflow is active in existing `p2p-uiux`;
   - focused + required regression passes;
   - independent Supervisor accepts exact head.

2. Logistics pilot:
   - runtime harness actually ran against an identified runtime/build/URL;
   - screenshots and JSON/Markdown evidence were reviewed;
   - no material visual/runtime regression remains.

Keep these separate:

```text
TEST_PASS != VISUAL_PASS
VISUAL_PASS != BUSINESS_PASS
SOURCE_REVIEW != RUNTIME_VISUAL_REVIEW
```

No merge, promotion, release, or deploy without the authority required by the
current P2P law and target-repository instructions.

## 8. Return packet

Return compactly:

```text
TASK=ROGER_UIUX_V1_INTEGRATION
P2P_HEAD=<sha>
LOGISTICS_HEAD=<sha>
P2P_UIUX_INTEGRATION=ACTIVE|BLOCKED
P2P_FOCUSED_TESTS=<result>
P2P_FULL_OR_AFFECTED_REGRESSION=<result>
SUPERVISOR=<PASS|FAIL|NOT_RUN>
LOGISTICS_RUNTIME=<RUN|NOT_RUN|BLOCKED>
LOGISTICS_DESKTOP=<PASS|FAIL|NOT_RUN>
LOGISTICS_MOBILE=<PASS|FAIL|NOT_RUN>
VISUAL_PASS=<PASS|FAIL|NOT_CLAIMED>
BUSINESS_PASS=<PASS|FAIL|NOT_CLAIMED>
AUTO_MERGE=NO
LEARNING_RECONCILIATION=<NONE|CANDIDATE>
```
