# DesignArena Execution Playbook — P2P

Status: REUSABLE EXECUTION GUIDANCE
Applies from: 2026-09-20
Authority: subordinate to `P2P_SUPREME_OPERATING_LAW_V1`
Purpose: route product/frontend work through the DesignArena surface that best matches the bounded goal without turning DesignArena into a new P2P control plane.

## 1. Core principle

DesignArena is a replaceable execution surface inside the P2P product fast loop. It is not architecture authority, methodology authority, release authority, or a second orchestrator.

Use the smallest arena that matches the work:

```text
OWNER OUTCOME
→ MINIMUM PRODUCT TRUTH
→ CHOOSE DESIGNARENA SURFACE
→ BUILD REPRESENTATIVE VERTICAL SLICE
→ RENDER / INTERACT / COMPARE
→ LOCK THE WINNING PRODUCT REFERENCE
→ INTEGRATE INTO DURABLE PROJECT
→ VERIFY
→ STOP
```

P2P remains responsible for task contract, scope, evidence, durable state, Owner Gates, executor routing, and acceptance.

## 2. Current capability snapshot

Fresh official DesignArena/Arena documentation checked on 2026-09-20 shows:

- **Web Apps**: multi-file React frontend work with file tools, shell, web/media tools, and Vercel preview/deploy.
- **Full-Stack**: Web Apps capability plus `propose_plan` and Supabase database/auth/storage tools.
- **UI Component**: specialized component design/evaluation surface.
- **Data Visualization**: specialized visualization surface; its agentic tool set reuses Web Apps tooling.
- **Image-to-App**: image-driven implementation surface; its agentic tool set reuses Web Apps tooling.
- **Agent Mode + GitHub**: repo sandbox, diff review, checks, commit/push, and one pull request per chat session at the current documented capability.

Current official references:
- https://www.designarena.ai/methodology/agentic-harness
- https://help.arena.ai/articles/5701270322-arena-how-to-code-arena
- https://help.arena.ai/articles/1655691990-how-to-use-coding-in-agent-mode
- https://help.arena.ai/articles/5432423882-how-to-use-agent-mode
- https://notes.designarena.ai/fullstack-arena-methodology/

This is a dated capability snapshot, not an eternal product guarantee. Fresh official capability state wins when later behavior changes.

## 3. Arena routing matrix

| Goal | Preferred surface | Why |
|---|---|---|
| Product shell / multi-page frontend / responsive workflow | **Web Apps** | Multi-file frontend without forcing database architecture |
| One difficult reusable widget | **UI Component** | Compare several implementations of the same bounded component |
| Timeline, comparison matrix, lineage, dense analytical display | **Data Visualization** | Optimize information geometry and interaction |
| A strong visual reference already exists as an image | **Image-to-App** | Rebuild against a fixed fidelity target |
| Persistent CRUD/auth/storage is part of acceptance | **Full-Stack** | Supabase-backed stack is native to this arena |
| Durable integration into an existing GitHub repo | **Agent Mode + GitHub** | Branch/diff/check/PR workflow |

Default rule:

```text
FRONTEND_PRODUCT_WITHOUT_REQUIRED_PERSISTENCE => WEB_APPS_FIRST
DATABASE_OR_AUTH_REQUIRED_BY_TASK_CONTRACT => FULL_STACK
EXISTING_REPO_INTEGRATION => AGENT_MODE_GITHUB
```

Do not choose Full-Stack merely because an app is called “full app”. If database/auth/storage are not required by acceptance, introducing Supabase first is normally `DEFER_UNTIL_NEEDED`.

## 4. Tournament pattern

Use DesignArena as a competition surface, not as a single-model oracle.

For a meaningful design decision:

1. Give competing models the same bounded product contract.
2. Keep critical facts, target user, language, layout constraints, responsive requirements, and acceptance invariant identical.
3. Preview both candidates before voting.
4. Test interaction, not only screenshot beauty.
5. Select the winner by:
   - domain/task correctness;
   - usability and visual hierarchy;
   - responsive quality;
   - state completeness;
   - compatibility with real data/schema;
   - absence of fabricated functionality.
6. Preserve the winning product reference before expanding scope.

A beautiful preview with broken interaction, impossible data requirements, or wrong product semantics is not a winner.

## 5. Vertical-slice rule

Build by complete user workflow, not by horizontal technical layers.

Preferred:

```text
ONE MODULE
→ real input contract
→ domain presentation
→ interactions
→ loading/error/empty states
→ mobile
→ representative data
→ rendered verification
→ durable integration
```

Avoid:

```text
all UI first
→ all APIs later
→ all engines later
→ responsive at the end
```

The second pattern creates large integration debt and weakens evidence.

## 6. Reuse-first UI rule

Before designing a domain/module from scratch:

1. inspect the authoritative engine/data schema;
2. inspect any existing frontend/component already paired with that engine;
3. identify what can be reused or wrapped;
4. rebuild only the missing or unusable presentation layer.

```text
EXISTING_AUTHORITATIVE_COMPONENT
→ PROVE_REUSE_OR_UNUSABILITY
→ ONLY THEN CONSIDER_REPLACEMENT
```

Frontend must not recalculate domain facts that already belong to an engine unless the task contract explicitly makes that calculation frontend authority.

## 7. Prompt contract for DesignArena

A strong initial prompt should contain only the task delta needed for the current slice:

- target user and primary workflow;
- one-sentence visual thesis;
- exact user-visible language;
- real data/schema constraints;
- required geometry/information hierarchy;
- desktop and mobile behavior;
- key interaction states;
- explicit anti-patterns;
- acceptance and rendered proof;
- stop condition.

Do not spend prompt budget repeating the whole project history when durable project files already carry it.

For long projects, preserve a small durable contract in the project repository and tell later DesignArena tasks to read it before changing established decisions.

## 8. Language contract

Every product task must explicitly state the user-visible language policy.

For strict single-language products, scope the requirement across:

- navigation;
- form labels;
- buttons;
- chart labels;
- interpretation/explanation prose;
- errors;
- warnings;
- empty states;
- tooltips;
- help;
- exports/reports;
- generated user-facing text.

Machine identifiers that cannot be translated without losing identity (repository names, commit SHA, URLs, filenames, protocol keys) may remain unchanged only inside clearly technical/developer surfaces when the project contract allows it.

Do not assume interface localization is enough when generated interpretation remains in another language.

## 9. Full-Stack plan review

When Full-Stack is actually selected, inspect the proposed plan before execution.

Reject or remove steps that introduce:

- database persistence not required by the bounded outcome;
- authentication not required by the bounded outcome;
- generic CRUD unrelated to the primary workflow;
- deployment before representative local/product behavior is proven;
- schema design that silently becomes product architecture authority.

Use the plan step field to restore the real task contract before implementation.

## 10. Image-to-App tactic

Use Image-to-App after a visual winner exists and fidelity is materially valuable.

Pattern:

```text
WINNING_RENDER
→ capture representative screenshot
→ Image-to-App implementation attempt
→ compare fidelity + interaction
→ keep only if materially better
```

Do not use this as mandatory ceremony. Skip it when the Web Apps winner is already implementable and accepted.

## 11. Agent Mode integration

For durable repo work:

- connect the intended GitHub repository;
- use one bounded branch/PR per session under the current one-PR-per-chat limitation;
- ask for preview when visual verification is part of acceptance;
- inspect diff and checks before merge;
- push all required changes before the PR is closed/merged because the current documented session may not push afterward;
- keep GitHub as durable checkpoint.

If the DesignArena winner exists only as preview code, transport it through a supported, lossless route that obeys Supreme Law artifact-transport rules.

## 12. Evidence and acceptance

DesignArena self-report is not acceptance evidence.

Use the evidence class required by the product task:

- visual claim → rendered view;
- responsive claim → representative mobile/desktop render;
- interaction claim → real interaction path;
- repo integration claim → durable branch/PR/head;
- persistence claim → actual write/read proof;
- engine/schema compatibility → representative real payload.

Do not promote mock/preview evidence into live/runtime/production proof.

## 13. Trick adoption rule

Useful tricks discovered during real work may update this playbook only when they materially improve outcome, recovery, fidelity, or effort.

Discuss the observation first and classify it:

```text
ONE-OFF QUIRK
REPEATABLE USEFUL TRICK
CURRENT PRODUCT CAPABILITY CHANGE
MATERIAL FAILURE MODE
```

Do not create a new framework, registry, benchmark system, or mandatory ritual around a one-off observation.

Fresh official product behavior overrides stale tricks.

## 14. OE gate

Before adding a DesignArena stage, ask exactly:

`Không bị over engineering chứ?`

Evaluate:
- SIMPLER_PATH
- MATERIAL_PROGRESS
- NECESSITY
- CORE_BEFORE_SUPPORT
- SMALLER_VERIFIABLE_SLICE

If a UI Component battle, Image-to-App pass, Full-Stack backend, second redesign, or extra reviewer does not materially improve acceptance, return `SKIP_IT` or `DEFER_UNTIL_NEEDED`.

## 15. Portable project pattern

For a new P2P project using DesignArena:

```text
1. establish language + visual + product contract
2. Web Apps shell/vertical slice
3. use UI Component/Data Visualization only for genuinely difficult surfaces
4. lock the winner
5. integrate through GitHub-capable lane
6. verify representative real workflow
7. repeat by module only when needed
8. add Full-Stack persistence only when acceptance requires it
```

This playbook guides executor choice; it does not replace project-specific architecture, product truth, or the Supreme Law.
