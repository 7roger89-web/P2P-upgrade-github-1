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

Current priority remains the already-active P2P/img2threejs completion chain. After the current bounded workstream reaches its safe terminal point, Control Tower must inspect this backlog before inventing unrelated new platform work.

---

## CONTEXT_HYGIENE_01 — Context Hygiene and Plan Lifecycle

`STATUS=PENDING`

Owner decision: accepted for future P2P development.

### Problem

Long-lived repositories and long AI sessions accumulate obsolete plans, specs, assumptions, failed approaches, and historical evidence. Semantic retrieval can select an old but textually relevant plan, and session compaction can preserve stale assumptions or lose important current details. File timestamps alone do not establish authority.

### Approved direction

Use authority-aware lifecycle and retrieval instead of blind deletion or moving all planning to another service.

```text
ACTIVE_TASK_PLANS        -> GitHub Issues / active workstream state
CANONICAL_SPECS          -> repository canonical surfaces
EVIDENCE                 -> durable, non-instructional evidence
HISTORICAL/SUPERSEDED    -> retained for audit, excluded from default retrieval
```

### Required laws

1. `SESSION_CONTEXT != AUTHORITY`.
2. Default retrieval is `ACTIVE_ONLY_RETRIEVAL` plus required canonical specs.
3. Historical/superseded plans are not loaded by default; history is opt-in when the task actually needs it.
4. Active task identity must bind to the durable workstream and exact Git/GitHub subject where applicable (`repository + workstream + SHA/tree/PR`).
5. After merge/closure, an active plan loses active authority.
6. Durable knowledge discovered by a completed task should be synthesized into the correct canonical spec/governance surface; the old task plan remains historical evidence.
7. Evidence is durable but does not become instruction authority merely because it is relevant text.
8. `NO_BLIND_DELETE_AFTER_MERGE`: do not delete useful history solely to make the repo look clean.
9. New execution sessions should load minimum relevant active context rather than replaying full old chat history.
10. Worktree/parallel-agent execution is allowed only for dependency-independent, low-conflict work; worktrees solve filesystem isolation, not semantic dependency.

### Preferred implementation constraint

Use existing GitHub Issues + PRs + P2P Task State/router/governance surfaces first.

```text
LINEAR_REQUIRED=NO
NEW_PROJECT_MANAGER_REQUIRED=NO
NEW_DATABASE_REQUIRED=NO
NEW_DAEMON_REQUIRED=NO
```

Linear or another external project manager may be evaluated later as a planning projection if there is a real product-management need, but it must not become a second conflicting technical authority by default.

### Acceptance direction for future bounded workstream

A future implementation should prove at minimum:

- active/canonical material is retrieved by default;
- superseded/historical plans are excluded by default;
- explicit historical queries can still retrieve preserved evidence;
- closed task plans cannot silently regain active authority;
- exact workstream/SHA binding wins over text similarity;
- no duplicate router, memory graph, project manager, daemon, or scheduler is introduced;
- existing Operations Notebook / Task State / governance authority remains intact.

### Assimilation gate

```text
RULE_ASSIMILATION_ID=CONTEXT_HYGIENE_01
RULE_ASSIMILATION_STATUS=PENDING
```

To become `VERIFIED`:

1. a future Writer task explicitly lists `CONTEXT_HYGIENE_01` as a deliverable;
2. Writer reports the exact canonical artifacts changed and `RULE_ASSIMILATED=YES`;
3. independent verification passes on the exact candidate head/tree;
4. canonical merge/promotion follows the normal Owner Gate.

---

## IMPECCABLE_01 — Design Quality and Anti-Generic UI Capability

`STATUS=PENDING`

Owner decision: accepted for future P2P evaluation/integration.

Upstream: `pbakaus/impeccable`.

Observed upstream shape at acceptance time: one design skill, 23 commands, browser/live iteration, and 61 deterministic detector rules; Apache-2.0 at repository root.

### Approved role

Use Impeccable as a **design-quality capability**, not as a replacement for P2P's UI/game implementation stack.

Target routing model:

```text
P2P UI ROUTER
  -> implementation capability
  -> Impeccable design critique/polish/shape/layout/typeset/bolder/quieter
  -> deterministic anti-generic-design checks
  -> browser visual evidence
  -> Supervisor
```

### Constraints

- Do not bulk-copy its working/runtime artifacts into canonical project state.
- Preserve the distinction between ephemeral live/cache/screenshots and durable design truth/evidence.
- Prefer selective adapter/skill projection over importing a second design framework.
- Evaluate hooks/browser-live surfaces under P2P trust and provenance rules before activation.
- No global activation by default.

### Future acceptance direction

Prove on a bounded UI/game surface that Impeccable adds measurable design-quality value without replacing existing P2P routing, visual QA, Storybook, Motion, Three.js/R3F, or design-system capabilities.

---

## FRONTEND_CHECKLIST_01 — Deterministic Front-End Verification Capability

`STATUS=PENDING`

Owner decision: accepted for future P2P evaluation/integration.

Upstream: `thedaviddias/Front-End-Checklist`.

Observed upstream shape at acceptance time: 385 English rules across 11 categories and 11 MCP tools; skills are also provided. Repository documentation states MIT licensing.

### Approved role

Use Front-End Checklist primarily as a **verification corpus/tooling capability**, not as a creative UI generator.

Target routing model:

```text
UI implementation
  -> design/visual review
  -> Front-End Checklist deterministic/structured QA
  -> browser/runtime evidence
  -> Supervisor
```

Expected domains include HTML, CSS, JavaScript, performance, accessibility, SEO, security, images, testing, privacy, and i18n.

### Constraints

- MCP is a transport option, not a mandatory P2P dependency.
- Prefer rule lookup/audit adapters over copying hundreds of rules into default prompts/context.
- Highest-confidence and risk-relevant findings first; do not force every rule on every task.
- No second governance/checklist authority: P2P remains the authority router and release gate.

### Future acceptance direction

Prove selective audits against real frontend code and/or browser surfaces, with deterministic reproducibility where possible and no context bloat.

---

## SCIENTIFIC_SKILLS_REGISTRY_01 — Selective Scientific Agent Skills Source

`STATUS=PENDING`

Owner decision: accepted as a future external capability/skill source; bulk import explicitly rejected.

Upstream: `K-Dense-AI/scientific-agent-skills`.

Observed upstream shape at acceptance time: README advertised 163 skills and 100+ scientific databases while repository metadata advertised 165 skills, demonstrating upstream metadata drift; MIT root license; weekly incremental security scanning with periodic full rescans.

### Approved role

Treat the repository as a **discoverable external skill registry/source** for science/research tasks.

Required routing model:

```text
science/research task
  -> search relevant external skills
  -> shortlist minimum relevant set (normally 1-3)
  -> provenance/license/security review
  -> explicit capability binding
  -> execute only if authorized
```

### Required laws

```text
SKILL_LIBRARY != DEFAULT_CONTEXT
AVAILABLE != LOADED
LOADED != AUTHORIZED
AUTHORIZED != EXECUTED
BULK_IMPORT=NO
```

- Do not hard-code a global skill count as authority.
- Do not install the whole repository merely because it is available.
- Preserve per-skill security/provenance review and minimum-relevant-context routing.
- High-stakes scientific/medical/regulatory skills require their own domain-specific safety and verification boundaries.

### Future acceptance direction

Implement registry/discovery semantics before importing any individual skill. Validate selective discovery, provenance, security metadata, and explicit execution authorization.

---

## OPENMAIC_01 — Existing Education/Course Vendor Candidate

`STATUS=HOLD_EXISTING_CANDIDATE`

Owner reminder: **do not forget OpenMAIC; do not duplicate its workstream.**

Existing P2P subject:

```text
PR=32
WORKSTREAM=P2P-OPENMAIC-VENDOR-01
UPSTREAM=THU-MAIC/OpenMAIC
CURRENT_PR_STATE=OPEN_NOT_MERGED
CANDIDATE_HEAD_SHA=befd1ed085c72ecb2b32b30c6b96957fad2217cb
UPSTREAM_SHA=dfebbcf33f3a56064129903faeab70a9e4243146
UPSTREAM_TREE=bb8972cb6fa5e4d6c5a7eff6f2357e79bf930b45
ROOT_LICENSE=MIT
```

Known boundary from PR32: LGPL-3.0-or-later boundary in `packages/mathml2omml`, third-party MIT in `packages/pptxgenjs`, and unspecified-license areas noted for `render-service` / `packages/docs` at intake time.

### Existing discovered capability projection

PR32 proposed six DISCOVERED/PROJECTABLE capabilities:

- `education.course_generation`
- `education.interactive_classroom`
- `education.course_editing`
- `education.quiz_assessment`
- `education.interactive_simulation`
- `education.course_export`

They remain **not execution-registered, not execution-authorized, and not runtime-proven** by this backlog entry.

### Approved continuation rule

- Do not create a second OpenMAIC intake PR/workstream.
- Before any continuation, fresh-reconcile PR32 against current canonical main because its base is stale relative to current development.
- Recheck upstream pin/license boundaries/security before promotion or runtime activation.
- Preserve `OPENMAIC_MULTI_AGENT_AUTHORITY=VENDOR_INTERNAL_ONLY` unless explicitly re-evaluated.
- Runtime smoke is required before any production-ready claim.

---

## OPENMONTAGE_01 — Existing Reference-Only Media Vendor Candidate

`STATUS=HOLD_EXISTING_CANDIDATE`

Owner reminder recovered from pre-backlog work: preserve the existing OpenMontage intake; do not restart it from chat memory.

Existing P2P subject:

```text
PR=31
WORKSTREAM=P2P-OPENMONTAGE-VENDOR-01
UPSTREAM=calesthio/OpenMontage
CURRENT_PR_STATE=OPEN_NOT_MERGED
CANDIDATE_HEAD_SHA=653b2ee3cf3ca5e325a6fb53620f9768070e347b
UPSTREAM_SHA=cd9f3c1f03368be87b140af494914b8ee4e3c7a4
UPSTREAM_TREE=6cd1961d552dd9d2bcfba990b80ac06edfe4b061
ROOT_LICENSE=AGPL-3.0
CLASSIFICATION=REFERENCE_ONLY_EXTERNAL_RUNTIME_VENDOR
```

PR31 recorded seven `DISCOVERED` reference-only projections (`media.openmontage` plus documentary/explainer/composition/audio/sourcing/quality). They were not installed, eligible, executable, or runtime-proven.

### Continuation rule

- Do not create a duplicate OpenMontage intake.
- Fresh-reconcile PR31 against current canonical main before any continuation; its intake base is historical/stale.
- Preserve the AGPL fail-closed boundary; no source vendoring/copying into P2P merely to make integration convenient.
- Commercial compatibility/clearance remains unproven until explicitly assessed.
- Any later runtime/render path requires a separate bounded authorization and runtime smoke.

---

## ORCA_01 — Existing Optional Native-Harness Assessment

`STATUS=EXISTING_DURABLE_WORK`

Existing P2P subject:

```text
PR=29
WORKSTREAM=P2P-NATIVE-HARNESS-ORCA-FIT-01
UPSTREAM=stablyai/orca
PR_STATE=MERGED
MERGE_COMMIT=d7d3b5d95f5bb6dae2daf50055ca5fbeb02bf8bd
FINAL_ASSESSMENT_HEAD=78f647409dc4111d760bdb20b020e767b079960f
```

The durable assessment concluded that Orca fits only as an **optional native-harness execution adapter** beneath the canonical P2P Work Factory. It explicitly rejected a second orchestrator/authority plane, rejected Dely as a required control plane, and identified the minimum seam as reusing existing backend-adapter/return-packet surfaces rather than inventing a new WorkItem ontology.

Known durable boundary:

```text
ORCA_OPTIONAL_ONLY=YES
Dely_REQUIRED=NO
SECOND_ORCHESTRATOR=NO
RA_EXT_011_IDENTITY=UNVERIFIED
```

### Continuation rule

- Do not repeat the architecture-fit assessment from scratch.
- Reconcile from the merged PR29 outcome and current canonical main.
- If value remains after current priorities, the next legitimate step is a separate bounded read-only/native-harness probe rather than automatic install or activation.
- Keep Orca adapter status honest until runtime evidence exists; architecture compatibility is not live certification.

---

## GOOSE_01 — Goose Execution-Harness / Agent-Host Evaluation

`STATUS=PENDING_RECONCILIATION`

Upstream: `aaif-goose/goose`.

Durable-recovery finding: prior discussion existed, but no Goose-specific P2P PR or repository record was found during this backlog reconciliation. Therefore Goose was at real risk of being lost across chat/session rotation.

Observed upstream at recovery time: open-source extensible AI agent, Rust implementation, Apache-2.0, with MCP/ACP-oriented integration surfaces and an execution model that can install, execute, edit, and test using different LLMs.

### Approved preservation direction

Do **not** install Goose merely because it is popular or capable. Future work should first compare it against capabilities P2P already has through the provider-neutral runtime, Work Factory, Codex/Manus/Hermes paths, and Orca assessment.

Potential value to evaluate:

- optional execution-harness/host adapter;
- MCP/ACP interoperability concepts;
- reusable tool/extension/session patterns;
- any execution mechanics that reduce host-specific code without displacing P2P governance.

### Constraints

```text
SECOND_ORCHESTRATOR=NO
P2P_AUTHORITY_REPLACEMENT=NO
GLOBAL_INSTALL_BY_DEFAULT=NO
RUNTIME_PROVEN=NO
```

Open a bounded research/fit workstream before any install, adapter registration, or live execution claim. Pin upstream SHA/tree/license at that time rather than treating this backlog entry as a freshness authority.

---

## CYBERSECURITY_SKILLS_REGISTRY_01 — Selective Cybersecurity Skills Source

`STATUS=PENDING_RECONCILIATION`

Upstream: `mukul975/Anthropic-Cybersecurity-Skills`.

Durable-recovery finding: no matching P2P PR or repository record was found during this backlog reconciliation, so this pre-backlog idea was also at risk of being forgotten.

Observed upstream at recovery time: repository metadata advertises a large Agent Skills corpus for cybersecurity, mapped across multiple security frameworks (including MITRE ATT&CK, NIST CSF, MITRE ATLAS, D3FEND and AI-risk/fraud frameworks), Apache-2.0, and compatibility with common coding-agent hosts.

### Approved preservation direction

Treat this only as a **selective external security skill registry/source**, never as a blanket offensive-security capability and never as default context.

Required routing model:

```text
security task
  -> classify authorized scope and defensive/offensive risk
  -> search minimum relevant skills
  -> provenance/license/security review
  -> select only required skill(s)
  -> explicit execution authorization and sandbox boundary
  -> evidence + Supervisor
```

### Required laws

```text
BULK_IMPORT=NO
DEFAULT_CONTEXT=NO
AUTO_EXECUTE_SECURITY_SKILLS=NO
AUTHORIZED_SCOPE_REQUIRED=YES
HIGH_RISK_ACTIONS_FAIL_CLOSED=YES
```

The future evaluation must distinguish harmless review/hardening/reference use from intrusive or dual-use execution. Availability of a skill is never permission to run it.

---

## Cross-cutting capability law accepted with these entries

```text
SKILL_LIBRARY != DEFAULT_CONTEXT
CAPABILITY_CATALOG != ACTIVE_CONTEXT
AVAILABLE != LOADED
LOADED != AUTHORIZED
AUTHORIZED != EXECUTED
EXISTING_DURABLE_SUBJECT -> RECONCILE, DO_NOT_RESTART
```

As P2P grows, routing must load the **minimum relevant, authority-valid capability set** for the current task. Large libraries, rule corpora, vendor catalogs, and historical candidates must not become default context merely because they exist.

---

## Backlog maintenance law

When the Owner and Control Tower explicitly accept another durable P2P improvement idea that is intentionally deferred, add it here with a unique ID, concise rationale, approved direction, execution trigger, and status. Do not store speculative ideas that have not been accepted.
