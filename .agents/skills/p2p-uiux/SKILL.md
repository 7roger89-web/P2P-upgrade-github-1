---
name: p2p-uiux
description: >-
  Reusable P2P UI/UX workflow for concrete existing or proposed interface
  outcomes: product context, user needs, screens, flows, navigation, usability,
  responsive behavior, accessibility, Design System, Contract, evidence, and
  Design Drift. Use it first for beginner wording such as “this looks messy”,
  “users cannot find the button”, or “I want the app easier to use”; do not use
  it for pure product ideation or backend work.
version: 8.4.7-C-codex.15
---

# p2p-uiux

Use this skill first when the requested outcome is a concrete existing or
proposed interface or user experience: interfaces, screens, flows, navigation,
interaction design, responsive behavior, typography, color, component
language, accessibility, and UI/UX review. Beginner language, uncertainty
about design, or the word “idea” does not change that primary route. Skip it
for pure product/feature ideation with no concrete interface outcome, and for
pure backend, data, infrastructure, or other non-visual work.

## First-decision handoff

The primary dispatcher must record
`INITIAL_PLANNING_CLASSIFICATION: UIUX` before selecting this skill whenever
the requested outcome is a concrete interface or user-experience change. The
later `FINAL_ROUTING_CLASSIFICATION` is a separate record produced after the
capability route is evaluated. Do not accept a prior `$p2p-idea` selection as a
normal intermediate step for these requests; generic beginner uncertainty is
not stronger evidence than the concrete UI/UX outcome.

## Routing boundary

- `p2p-uiux` is primary when the deliverable is to make a screen, flow,
  navigation, layout, interaction, accessibility behavior, responsive/mobile
  experience, readability, or visual direction better.
- `$p2p-idea` is primary when the deliverable is product or feature discovery
  before a concrete interface outcome exists. A UI mention in that context is
  secondary only.
- In a mixed request, choose the primary route from the deliverable and record
  the other concern as secondary. Do not use keyword-only routing.
- A trivial padding, color, spacing, or button-size adjustment is still a
  direct UIUX task and normally does not need `p2p_aesthetica`.

## Workflow

`Product Context -> User/Persona -> UX Objectives -> Information Architecture -> Design Direction -> Design System -> Component Rules -> Implementation Constraints -> Accessibility -> Verification -> Design Drift`

Start by naming the product type, primary user, user need, primary flow, platform/stack, constraints, and what “done” means. Use the local adapter to propose a direction. Keep the chain explicit:

`USER NEED -> UX PRINCIPLE -> DESIGN DECISION -> IMPLEMENTATION CONSEQUENCE`

Do not hardcode a generic visual style. Adapt the design principle to the project technology. Record unknown stacks as adaptation notes rather than forcing React/Tailwind assumptions.

## Design System and Contract

For a substantial UI/UX scope, create a Design Contract and a project-owned `.p2p/design/MASTER_DESIGN_SYSTEM.md` plus its machine-readable companion. A small change may use the lightweight contract mode. Never silently replace an approved Design System. Material changes to brand, visual identity, primary navigation, core tokens, hierarchy, interaction philosophy, or accessibility baseline require owner approval.

## Accessibility

Always consider contrast, readable typography, visible focus, keyboard behavior when applicable, target size, reduced motion, semantic hierarchy, form labels/errors, color-independent meaning, and responsive reading. Emit `NEEDS_EVIDENCE` when verification has not been supplied. Never claim WCAG conformance from a recommendation alone.

## Specialist boundary

`p2p_aesthetica` is a real optional supporting specialist. The bounded certification supports automatic eligibility only for a material `ACCESSIBILITY_HEAVY` or `DENSE_WORKFLOW_FORM` problem. It is not canonical and is never included in the 8-agent denominator. Eligibility is conditional, not mandatory; capability readiness, bounded scope, and fallback rules still apply.

## Native specialist handoff

For a material UI/UX request, first keep p2p-uiux as the primary route. Generic
dashboard, story/game, mobile consumer, ecommerce, responsive-only,
design-system-only, visual-polish, and small-cosmetic work remain p2p-uiux-only
by default. When the existing router marks `ACCESSIBILITY_HEAVY` or
`DENSE_WORKFLOW_FORM` eligible and the real optional profile plus supported
native execution path are available, ask the current native coordinator to
perform the bounded specialist review and wait for completion. Do not manually
spawn, infer identity from child prose, or simulate the specialist. Accept
identity only from the existing official host receipt with exact
`agent_type p2p_aesthetica`. If the profile, native path, or receipt is
unavailable or unverifiable, continue with the normal verified p2p-uiux path
and report the fallback.

## Commands

From the installed project system directory or development source:

```text
python scripts/p2p_router.py route --request "Design a logistics dashboard for dispatchers"
python scripts/p2p_uiux.py recommend --input request.json
python scripts/p2p_uiux.py design-system --input request.json --project . --approve --approved-by owner
python scripts/p2p_uiux.py contract --input request.json --project . --scope large
python scripts/p2p_uiux.py drift --baseline .p2p/design/MASTER_DESIGN_SYSTEM.json --candidate candidate.json
python scripts/p2p_uiux.py a11y --file .p2p/design/MASTER_DESIGN_SYSTEM.json
```

The upstream reference is pinned in `references/UPSTREAM-UI-UX-PRO-MAX-PROVENANCE.md`; this skill does not fetch or install upstream at runtime.
