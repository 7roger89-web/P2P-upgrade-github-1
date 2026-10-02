# Roger UI/UX v1 — P2P design execution profile

Status: EXPERIMENTAL / UNPROMOTED
Source inspiration: evondev/evondevKit ui-ux workflow, adapted to P2P operating law.
Scope: product/app UI. This document is a thin execution profile, not a second P2P law.

## 1. Purpose

Make UI work start from the user's job and the existing product truth instead of immediately generating decoration.

Core loop:

```text
PROJECT TRUTH
  -> USER JOB
  -> INFORMATION PRIORITY
  -> REUSE
  -> LAYOUT DECISION
  -> IMPLEMENT
  -> RENDER
  -> VISUAL ACCEPTANCE
```

The profile MUST NOT override the current P2P Supreme Operating Law, task state, evidence authority, Owner Gates, or repository-local product requirements.

## 2. Router

Choose exactly one primary lane:

- BUILD: new screen or substantial new UI.
- REDESIGN: improve an existing screen while preserving product/business behavior unless the task explicitly changes it.
- AUDIT: inspect UI/UX and return evidence-backed findings; do not mutate product code without explicit execution authority.
- SYSTEM: tokens/components/design-system work when the task explicitly needs a reusable system.
- VISUAL_REGRESSION: refactor or implementation change where appearance/behavior must remain visually equivalent.

A request smaller than one screen (button, dropdown, spacing bug, single component) uses the closest lane but skips heavyweight brief/wireframe ceremony.

## 3. Mandatory preflight

Before proposing layout or editing UI:

1. Establish the actor's own valid P2P law context.
2. Read the task acceptance criteria and repository-local instructions.
3. Inspect the existing stack, tokens/theme, component library, relevant screen/component, and nearby product copy.
4. Search for an existing component before creating a new one.
5. Determine the existing visual language from evidence; do not impose this profile's aesthetic on an established product.
6. Determine the primary platform from task/repository evidence. Do not assume desktop merely because development happens on desktop.

Emit one compact UI audit receipt when useful:

```text
UI_AUDIT=<stack> | REUSE=<existing components/tokens> | STYLE=<observed style> | PRIMARY_VIEWPORT=<evidence-backed viewport>
```

Do not add ceremony when the information is already obvious and the task is tiny.

## 4. User-job contract

For each material screen, establish four facts before implementation:

- ARRIVE: why the user comes here.
- DECIDE: what information they compare or inspect.
- ACT: the primary action or next operational step.
- EXCEPTIONS: states that materially change the decision (late, blocked, missing, failed, empty, permission denied, etc.).

Derive these from repository/product evidence and the user's request. Do not invent personas, research findings, conversion metrics, or business rules.

Information used to DECIDE or ACT gets visual priority. Database availability is not a reason to display a field.

For operations-heavy products, attention and action outrank decoration.

## 5. Reuse law

Prefer, in order:

1. existing project component;
2. existing project token/theme;
3. existing project library primitive;
4. a new local component;
5. a new dependency only when existing choices cannot reasonably satisfy the task.

Do not install a UI dependency merely to avoid implementing a small ordinary component. New dependencies follow normal P2P authority and evidence rules.

Do not silently create a second Button, Avatar, Modal, Table, Badge, Input, Select, DatePicker, or equivalent when a suitable project implementation already exists.

## 6. Layout decision and Owner Gate

Do NOT require brief approval and wireframe approval for every screen.

Proceed autonomously when:
- the task and user job are clear;
- the layout choice is reversible;
- alternatives do not materially change workflow/business behavior;
- repository conventions strongly determine the answer.

Use an Owner Gate only when two or more plausible UX directions materially change workflow, information architecture, product behavior, irreversible design-system direction, or a subjective brand choice that cannot be resolved from evidence.

When a gate is necessary, present 2–3 structurally different options. Differences must be information architecture or interaction strategy, not cosmetic color swaps. State the tradeoff and evidence for each. Do not rank political-style; this rule concerns product design choices only.

If the user explicitly requests wireframes, create them before implementation. Otherwise a concise layout decision is enough.

## 7. Implementation constraints

- Preserve business logic when the task is visual-only.
- Preserve repository language/i18n conventions.
- Use real or representative product content, including long and empty cases.
- Do not hide operationally important exceptions behind decorative summary cards.
- Use semantic controls and accessible labels.
- Keep primary action hierarchy obvious; avoid multiple competing primary CTAs.
- Responsive behavior is part of the feature, not cleanup after desktop completion.
- Dense operational tables may remain dense when density serves scanning/comparison; hierarchy must still be clear.
- Journey/progress visuals orient the user; they do not become a dumping ground for every alert or action unless the user job requires it.

## 8. Required states

For material interactive surfaces, cover the states that apply:

- normal/data;
- loading;
- empty;
- error;
- disabled;
- permission/locked;
- selected/current;
- long text / constrained width;
- mobile or narrow viewport;
- domain-specific exception states derived from the user-job contract.

Do not fabricate a state solely to satisfy the checklist.

## 9. Visual acceptance

Implementation is not accepted merely because it compiles or tests pass.

Use the smallest available evidence path appropriate to the task:

1. render/run the real UI;
2. inspect the target viewport(s);
3. inspect narrow/mobile behavior when applicable;
4. check overflow, clipping, wrapped controls, broken hierarchy, focus/keyboard behavior, modal/popover containment, empty/error states, and representative long content;
5. compare against an approved reference/wireframe when one exists;
6. record evidence on the existing P2P task/PR/evidence surface.

Minimum common viewport set when the product has no stronger contract:
- narrow/mobile: 375px;
- tablet/intermediate when layout changes: 768px;
- desktop: 1280px or the repository's established target.

Add wider widths only when the screen meaningfully uses them. Do not run six widths by ritual.

VISUAL_PASS != BUSINESS_PASS.
TEST_PASS != VISUAL_PASS.

## 10. AUDIT lane

An audit must separate:
- observed fact;
- user impact;
- proposed change;
- confidence/evidence.

Prefer a small number of material findings over a cosmetic census. A screenshot alone is evidence of appearance, not proof of underlying behavior.

Do not mutate code in AUDIT lane unless the task explicitly authorizes implementation.

## 11. REDESIGN lane

Default: preserve product behavior and domain semantics. Improve hierarchy, navigation, density, responsive behavior, states, and component consistency.

If a proposed redesign changes workflow or business meaning, route that decision through the normal Owner Gate instead of smuggling it in as "UI cleanup."

## 12. SYSTEM lane

Use SYSTEM only when multiple screens/components genuinely need shared primitives or the task explicitly requests a design system.

Start with the smallest shared layer that removes real duplication:
- semantic tokens;
- typography/spacing scale already compatible with the product;
- core primitives actually used by current screens.

Do not build a component museum before a real screen needs it.

## 13. VISUAL_REGRESSION lane

Before refactor:
- capture current target states/viewports;
- identify intentionally preserved quirks versus known defects.

After refactor:
- compare the same states/viewports;
- treat unexplained visual change as a regression until justified.

## 14. Progressive disclosure

Keep the entry profile thin. Load extra references only for the active lane or component.

Recommended future references, created only when repeated evidence justifies them:
- responsive-and-density.md
- forms-and-validation.md
- tables-and-operations.md
- visual-audit.md
- design-system.md

Do not import a large external UI handbook wholesale. Promote only rules that repeatedly improve real P2P project outcomes.

## 15. Pilot and promotion gate

Pilot this profile on one real Logistics screen before making it cross-project default.

Promotion requires evidence that it:
- reduces duplicate components or avoidable redesign churn;
- improves visual acceptance at target viewports;
- does not add unnecessary Owner interruptions;
- does not weaken business/functional acceptance;
- remains materially smaller than the external source workflow.

Until then:
```text
ROGER_UI_UX_V1=EXPERIMENTAL
CROSS_PROJECT_DEFAULT=NO
```


## 16. Integration discovery — existing p2p-uiux wins

Fresh repository inspection found the existing project-owned `.agents/skills/p2p-uiux/SKILL.md`, runtime UI/UX routing, browser-evidence contract, installer semantics, and eval coverage.

Therefore this experiment MUST NOT create a second P2P UI/UX authority. The durable P2P path is to fold only proven pilot rules into the existing `p2p-uiux` skill:

- project/codebase audit before layout;
- ARRIVE / DECIDE / ACT / EXCEPTIONS user-job contract;
- BUILD / REDESIGN / AUDIT / SYSTEM / VISUAL_REGRESSION execution lanes;
- reuse-first component/dependency order;
- minimum necessary Owner Gate;
- operational attention > decoration patterns.

Preserve the existing `p2p-uiux` runtime-evidence contract, provider-neutral browser classification, read-only review safety, accessibility boundary, router primacy, and optional Aesthetica boundary.

A standalone `roger-ui-ux` package may exist as a portable user skill outside P2P. When a target project exposes a stronger project-owned UI/UX authority (especially P2P `p2p-uiux`), that authority wins and the portable skill is supplemental only.

```text
P2P_PARALLEL_UIUX_SKILL=NO
P2P_INTEGRATION_TARGET=existing p2p-uiux
PORTABLE_ROGER_UIUX=ALLOWED_AS_SUPPLEMENT_OUTSIDE_P2P
```
