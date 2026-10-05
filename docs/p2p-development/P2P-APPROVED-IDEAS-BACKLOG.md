# P2P APPROVED IDEAS BACKLOG

Status: `DURABLE_BACKLOG_ONLY`

Purpose: preserve Owner-approved P2P improvement ideas so they are not lost across chats, compaction, account/session rotation, or Control Tower rotation.

This file is **not** an active implementation plan, runtime authority, release authority, or permission to mutate code. It must not override canonical specs, governance, Task State, the P2P Operations Notebook, or an exact active workstream. Items here become implementation work only when Control Tower explicitly opens a bounded workstream for them.

## Retrieval rule

- Default task retrieval should not load this file unless the task is planning the next P2P improvement, reconciling the approved backlog, or explicitly references one of the IDs below.
- An entry marked `PENDING` is a durable promise to revisit, not an instruction to execute immediately.
- When an entry is implemented, Control Tower must verify the exact PR head/tree and change the entry to `VERIFIED` or replace it with a pointer to the canonical implemented artifact.
- Existing vendor/capability candidates referenced here must keep their own current authority/status; this backlog does not promote, install, authorize, or merge them.
- Do not create parallel backlogs for the same ideas.

## Execution trigger

Current active platform workstream is `P2P-IMPECCABLE-01` / Issue #44. Before opening unrelated new platform work, Control Tower must inspect this backlog and any detailed recovery records referenced here.

---

## P2P_BEGINNER_NORTH_STAR_01 — Beginner-first final product goal

`STATUS=EXISTING_CANONICAL_INVARIANT`

P2P's final product is for a beginner Owner. Internal architecture may be sophisticated, but the Owner-facing workflow must stay simple: one clear action now, plain-language explanation, automatic recommendation/default routing, no Owner-as-agent-relay, technical bookkeeping hidden by default, and escalation only for genuine Owner Gates.

Durable prior evidence already exists in the canonical Operations Notebook / `P2P_BEGINNER_OPERATIONS_UX_V1`; this entry prevents the North Star from being diluted as the capability catalog grows.

```text
BEGINNER_FIRST=YES
ONE_ACTION_NOW=YES
EXPLAIN_SIMPLY=YES
AUTO_RECOMMEND_DEFAULT=YES
OWNER_MICRO_LOOP_SUPPRESSION=YES
TECHNICAL_BOOKKEEPING_HIDDEN_BY_DEFAULT=YES
REAL_OWNER_GATES_ONLY=YES
NO_OWNER_AS_AGENT_RELAY=YES
```

---

## CONTEXT_HYGIENE_01 — Context Hygiene and Plan Lifecycle

`STATUS=VERIFIED`

Canonical implementation: Issue #42 / merged PR #43.

```text
MERGE_COMMIT=c1e08dfe5d8730cf9b36d7f307ee4b0143fd1f2b
MERGE_TREE=18eba62a24814cdd37a2483473fbbf649ef58598
RULE_ASSIMILATION_ID=CONTEXT_HYGIENE_01
RULE_ASSIMILATION_STATUS=VERIFIED
```

Verified laws now include:

- `SESSION_CONTEXT != AUTHORITY`;
- default retrieval favors current active/canonical sources;
- historical/superseded/closed material is retained but excluded by default;
- explicit historical retrieval remains available;
- exact repository/workstream/subject + Git commit/tree/PR binding outranks text similarity;
- closed/superseded plans lose active authority;
- evidence stays non-instructional;
- `OWNER_MICRO_LOOP_SUPPRESSION` keeps directly induced repairs in the Writer loop while real Owner Gates remain intact;
- no second router/project manager/database/daemon/scheduler/memory graph was introduced.

---

## IMPECCABLE_01 — Design Quality and Anti-Generic UI Capability

`STATUS=ACTIVE`

Owner decision: accepted for P2P evaluation/integration. Active bounded workstream: Issue #44.

Upstream: `pbakaus/impeccable`.

Approved role: design-quality critique/polish/deterministic anti-generic checks beneath P2P routing and authority; no replacement of the existing UI/game implementation stack, no global activation, no second design system.

---

## FRONTEND_CHECKLIST_01 — Deterministic Front-End Verification Capability

`STATUS=PENDING`

Owner decision: accepted for future P2P evaluation/integration.

Upstream: `thedaviddias/Front-End-Checklist`.

Approved role: structured/deterministic frontend QA after implementation/design review, not creative UI authority. MCP is optional transport, not a required P2P dependency. No bulk loading of hundreds of rules into default context.

---

## SCIENTIFIC_SKILLS_REGISTRY_01 — Selective Scientific Agent Skills Source

`STATUS=PENDING`

Upstream: `K-Dense-AI/scientific-agent-skills`.

Treat as a discoverable external skill registry/source, never as a bulk import.

```text
SKILL_LIBRARY != DEFAULT_CONTEXT
AVAILABLE != LOADED
LOADED != AUTHORIZED
AUTHORIZED != EXECUTED
BULK_IMPORT=NO
```

---

## OPENMAIC_01 — Existing Education/Course Vendor Candidate

`STATUS=HOLD_EXISTING_CANDIDATE`

Existing P2P subject: PR #32 / `P2P-OPENMAIC-VENDOR-01` / upstream `THU-MAIC/OpenMAIC`.

Do not create a duplicate intake. Fresh-reconcile the existing candidate against current canonical main before continuation; preserve its license/security/vendor-authority boundaries; require runtime smoke before production-ready claims.

---

## OPENMONTAGE_01 — Existing Reference-Only Media Vendor Candidate

`STATUS=HOLD_EXISTING_CANDIDATE`

Existing P2P subject: PR #31 / `P2P-OPENMONTAGE-VENDOR-01` / upstream `calesthio/OpenMontage`.

AGPL-3.0, reference-only external runtime vendor intake. No install/runtime/render proof exists from that intake. Reconcile, do not restart.

---

## ORCA_01 — Existing Optional Native-Harness Assessment

`STATUS=EXISTING_DURABLE_WORK`

Existing P2P subject: merged PR #29 / `P2P-NATIVE-HARNESS-ORCA-FIT-01` / upstream `stablyai/orca`.

Durable conclusion: optional native-harness adapter only; no second orchestrator/control plane; Dely not required. Reconcile from existing work rather than repeating the architecture assessment.

---

## GOOSE_01 — Goose Execution-Harness / Agent-Host Evaluation

`STATUS=PENDING_RECONCILIATION`

Upstream: `aaif-goose/goose`.

Prior discussion existed but no Goose-specific durable P2P subject was found during recovery. Evaluate only as an optional execution-harness/host adapter or source of reusable execution mechanics; never as replacement P2P authority/orchestrator; no global install by default.

---

## CYBERSECURITY_SKILLS_REGISTRY_01 — Selective Cybersecurity Skills Source

`STATUS=PENDING_RECONCILIATION`

Upstream: `mukul975/Anthropic-Cybersecurity-Skills`.

Treat only as a selective external security skill source. `BULK_IMPORT=NO`, default context off, authorized scope required, high-risk actions fail closed.

---

## CLAUDE_SEO_LOGISTICS_01 — Selective Logistics SEO Capability

`STATUS=PENDING`

Owner-approved evaluation for public Logistics website/landing/content surfaces. Provider-neutral projection; no global install; preserve source observation + dependencies + failure check + leading-indicator contract. Do not apply SEO machinery to internal shipment/payment/database logic when irrelevant.

Detailed record: `docs/p2p-development/approved-ideas/CLAUDE-SEO-LOGISTICS-01.md`.

---

## MEDIA_VISUAL_BEGINNER_RECOVERY_01 — Pre-backlog media/visual recovery

`STATUS=DURABLE_RECOVERY_RECORDED`

Detailed record:

`docs/p2p-development/approved-ideas/MEDIA-VISUAL-BEGINNER-RECOVERY-01.md`

This record exists because several image/character/3D/video/voice decisions predated the durable backlog. It preserves/reconciles:

- `P2P_BEGINNER_NORTH_STAR_01` — beginner-first final product invariant;
- `GAME_ASSET_FORGE_01` — merged PR #24, canonical selective game-asset routing/gates;
- `IMG2THREEJS_01` — production-proven static 3D asset route, closed;
- `MPFB2_CHARACTER_FORGE_01` — canonical adapter/runtime boundary exists, real Blender/MPFB execution still not proven;
- `VISUAL_GPT_IMAGE_2_STYLE_LIBRARY_01` — existing durable image/style capability referenced by Asset Forge; reconcile, do not duplicate;
- `OPENMONTAGE_01` — existing media/video vendor candidate PR #31;
- `REAL_TIME_VOICE_CLONING_01` — recovered pre-backlog voice idea, `PENDING_RECONCILIATION` because no dedicated durable P2P subject was found;
- `WHITEBOARD_ANIMATION_01` — recovered external media skill path, `PENDING_RECONCILIATION` because no canonical P2P workstream was found in the recovery pass.

Media/visual law:

```text
REFERENCE_IS_TARGET
CAPABILITY_IS_ROUTE_NOT_AUTHORITY
AVAILABLE != LOADED != AUTHORIZED != EXECUTED
REAL_ASSET_REQUIRED_FOR_ASSET_CLAIM
PROJECT_RUNTIME_EVIDENCE_REQUIRED_FOR_INTEGRATION_CLAIM
VISUAL_COMPARISON_REQUIRED_FOR_VISUAL_SUCCESS_CLAIM
EXISTING_DURABLE_SUBJECT -> RECONCILE, DO_NOT_RESTART
```

---

## Cross-cutting capability law

```text
SKILL_LIBRARY != DEFAULT_CONTEXT
CAPABILITY_CATALOG != ACTIVE_CONTEXT
AVAILABLE != LOADED
LOADED != AUTHORIZED
AUTHORIZED != EXECUTED
EXISTING_DURABLE_SUBJECT -> RECONCILE, DO_NOT_RESTART
```

As P2P grows, routing must load the minimum relevant, authority-valid capability set for the current task. Large libraries, rule corpora, vendor catalogs, media pipelines, and historical candidates must not become default context merely because they exist.

## Backlog maintenance law

When the Owner and Control Tower explicitly accept another durable P2P improvement idea that is intentionally deferred, add it here with a unique ID, concise rationale, approved direction, execution trigger, and status. For pre-backlog history, perform a bounded durable-recovery pass before declaring an idea forgotten. Do not store speculative ideas that have not been accepted.
