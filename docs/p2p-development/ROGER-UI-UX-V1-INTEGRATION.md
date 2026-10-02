# Roger UI/UX v1 — integration packet for existing p2p-uiux

Status: PROPOSED / NOT ACTIVE
Target: `.agents/skills/p2p-uiux/SKILL.md`
Parallel P2P UI/UX skill: FORBIDDEN

This packet converts the Evon + Logistics pilot findings into a bounded change
for the existing P2P UI/UX skill. It is not a second skill authority and does
not replace the existing router, runtime-evidence contract, browser provider
classification, read-only review safety, accessibility boundary, or optional
Aesthetica boundary.

## Change set

### 1. Preflight: project truth before layout

Add a lean project/codebase audit before layout or implementation:

```text
UI_AUDIT=<stack> | REUSE=<existing components/tokens> | STYLE=<observed style> | PRIMARY_VIEWPORT=<evidence-backed viewport>
```

Inspect only the relevant screen/component and nearby project truth. Identify
stack, styling approach, tokens/theme, component library, copy/i18n, responsive
patterns, and reusable components. Do not scan the whole repository by ritual.

### 2. User-job contract

For each materially changed screen establish:

```text
ARRIVE=<why the user comes here>
DECIDE=<what they inspect or compare>
ACT=<primary action or next operational step>
EXCEPTIONS=<states that materially change the decision>
```

Derive these facts from repository/product evidence and the request. Do not
invent personas, interviews, metrics, or business rules.

### 3. Execution lanes

Choose exactly one primary lane:

- BUILD
- REDESIGN
- AUDIT
- SYSTEM
- VISUAL_REGRESSION

Small component tasks use the nearest lane without heavyweight ceremony.

### 4. Core loop

Use:

```text
PROJECT TRUTH -> USER JOB -> INFORMATION PRIORITY -> REUSE -> LAYOUT DECISION -> IMPLEMENT -> RENDER -> VERIFY
```

Preserve the existing runtime evidence contract:
`SOURCE_REVIEW != RUNTIME_VISUAL_REVIEW`.

### 5. Reuse-first order

Prefer:

1. existing project component;
2. existing project token/theme;
3. existing project library primitive;
4. new local component;
5. new dependency only when existing choices cannot reasonably satisfy the task.

Do not silently create a duplicate ordinary UI primitive.

### 6. Minimum Owner Gate

Do not require approval for every brief or wireframe. Proceed autonomously when
the task/user job is clear, the decision is reversible, and workflow/business
behavior is unchanged.

Use an Owner Gate only when plausible alternatives materially change workflow,
information architecture, product/business behavior, a hard-to-reverse design
system direction, or an unresolved subjective brand choice.

If a gate is required, present 2–3 structurally different options rather than
cosmetic color variants.

### 7. Operational UI

For workflow-heavy products:

- attention and action outrank decoration;
- do not mirror the database onto the primary surface;
- keep dense tables dense when density improves scanning/comparison;
- name actions by outcome instead of generic repeated labels;
- treat journey/progress UI as orientation, not an alarm board;
- surface derived exceptions near the decision area when they change the next action.

### 8. Design-system restraint

Do not automatically create a full design system merely because the UI scope is
large. Use lightweight contract mode unless the task explicitly asks for a
system, an approved system needs updating, or repeated real screens/components
prove shared primitives are necessary.

## Preserve unchanged

The integration must preserve:

- `p2p-uiux` as the single primary P2P UI/UX skill;
- the existing P2P router;
- runtime visual evidence classification and honest downgrade behavior;
- provider-neutral browser capability classification;
- read-only review safety;
- accessibility evidence rules;
- Aesthetica as optional/noncanonical;
- eight-member canonical governance denominator;
- existing P2P law and Owner Gates.

## Regression acceptance

After applying the instruction change, run at minimum:

```text
python -m unittest tests.test_p2p_uiux_lean_workflow_contract -v
python -m unittest tests.test_p2p_live_browser_uiux_review_01 -v
python -m unittest tests.test_p2p_beginner_routing -v
```

Then run the repository's affected/full regression path required by the active
task contract.

The integration is not complete until the Logistics Shipment Workspace pilot
also receives runtime AppTest evidence and real-browser visual review at a
representative desktop and narrow/mobile viewport.

```text
P2P_PARALLEL_UIUX_SKILL=NO
P2P_INTEGRATION_TARGET=existing p2p-uiux
RUNTIME_CONTRACT_PRESERVE=YES
AUTO_MERGE=NO
```
