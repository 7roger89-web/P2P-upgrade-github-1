# P2P Character Forge Productization ISSUE 59 Actual Status

Title: P2P Character Forge Productization ISSUE 59
Date: 2026-09-02
Status: P2 Complete; Supervisor PASS; Owner Gate Pending
Companion plan: `docs/plans/2026-09-02-p2p-character-forge-productization-01/2026-09-02-p2p-character-forge-productization-01-plan.md`
Companion evidence: `docs/plans/2026-09-02-p2p-character-forge-productization-01/2026-09-02-p2p-character-forge-productization-01-evidence.md`
Companion benchmark: `docs/plans/2026-09-02-p2p-character-forge-productization-01/2026-09-02-p2p-character-forge-productization-01-benchmark.md`

## Purpose

This is the living current-state record for ISSUE=59. P0 classifies the exact
canonical source, existing MPFB2 route, runtime evidence, and the missing
productization seam before implementation. Later slices must append refresh rows
and update only affected classifications.

## Scope

Target scope:

- One beginner-facing facade over `game.character.generate`.
- Deterministic request normalization and recipe projection.
- Existing adapter binding, concise receipt, focused tests, and one real smoke.

Out of scope:

- New capability identity, router/selection system, NLP, UI, database, service,
  Game Truyen, upstream/runtime repair, exact height/age/hair/clothing systems,
  release, merge, deployment, or promotion.

## Relationship / Impact Evidence

| Unit / File / Surface | File Detail Evidence | Related File Count | Relationship Summary | Impact Note |
|-----------------------|----------------------|--------------------|----------------------|-------------|
| `p2p_capabilities/character_recipe.py` | `E0-P0A-GRAPH1` | 25 local relationships; 2 linked flows | Existing internal recipe validator/hash contract | medium scope warning; preserve-only |
| `p2p_capabilities/mpfb_adapter.py` | `E0-P0A-GRAPH2` | 80 local relationships; 3 linked flows | Existing plan, security, manifest, output, and execution boundary | high scope warning; preserve-only |
| `p2p_capabilities/mpfb_blender_entrypoint.py` | `E0-P0A-GRAPH3` | 49 local relationships; 5 linked flows | Existing Blender/MPFB lifecycle and output producer | medium scope warning; preserve-only |
| `p2p_capabilities/asset_provenance.py` | `E0-P0A-GRAPH4` | 17 local relationships; 1 linked flow | Existing rights/provenance validator | medium scope warning; preserve-only |
| `p2p_capabilities/glb_validator.py` | `E0-P0A-GRAPH4` | 21 local relationships; 1 linked flow | Existing GLB structural validator | medium scope warning; preserve-only |
| `p2p_capabilities/routing.py` | `E0-P0A-GRAPH5` | 4 local relationships; 0 linked flows | Existing single-router route classification | low scope warning; preserve-only |
| `p2p_capabilities/selection_request.py` | `E0-P0A-GRAPH5` | 126 local relationships; 1 linked flow | Existing provider-neutral selection contract | medium scope warning; preserve-only |
| `p2p_capabilities/windows_network_isolation.py` | `E0-P0A-GRAPH5` | 43 local relationships; 4 linked flows | Existing exact Windows firewall lifecycle | medium scope warning; preserve-only |
| `tests/test_p2p_game_truyen_mpfb_adapter_01.py` | `E0-P0A-GRAPH6` | 161 local relationships; critical file impact | Existing high-risk adapter test surface | do not expand; add separate focused test |
| `game.character.generate` registry entry | `E0-P0A-CAP1` | registry data | Existing identity and routing metadata | preserve; no duplicate |
| supplied MPFB2 runtime root | `E0-P0A-RUNTIME1` | external managed runtime | Blender/MPFB2/provisioning/output subject | inspect/validate-only |
| Game Truyen | `E0-P0A-SCOPE1` | external user project | Must remain untouched | do-not-touch |

## Status Rules

| Status | Meaning | Allowed next action |
|--------|---------|---------------------|
| `correct` | Already behaves as required. | Preserve. |
| `partial` | Some required behavior exists, but gaps remain. | Change only missing parts. |
| `wrong` | Current behavior or contract conflicts with the requirement. | Replace only with authority evidence. |
| `missing` / `unbound` | Required surface does not exist or is not wired. | Implement/bind the missing piece. |
| `fake-or-stub` | Demo/mock behavior is presented as real. | Remove or label honestly. |
| `blocked` | Authority or required evidence is unclear/unavailable. | Stop. |

## Current Status Matrix

| Unit | Current State | Required State | Status | Relationship Count | Evidence | Next Plan Decision |
|------|---------------|----------------|--------|--------------------|----------|--------------------|
| Canonical main/tree | Fresh remote main exactly matches expected SHA/tree | Exact expected base for Writer branch | correct | N/A | `E0-P0A-GIT1` | preserve; P1 allowed |
| Existing capability identity | `game.character.generate` already exists as `KNOWLEDGE_SOURCE`/`MODEL_ROUTABLE` with MPFB2 provenance | Reuse one identity and existing router | correct | registry data | `E0-P0A-CAP1` | preserve; no duplicate |
| Internal recipe contract | `p2p-character-recipe/1` validates verbose normalized MPFB inputs | Facade must produce it deterministically | correct | 25 local; 2 flows | `E0-P0A-GRAPH1`, `E0-P0A-CATALOG1` | preserve; call from P1-A |
| Beginner CharacterRequest | `character_forge.py` normalizes six supported fields, applies the explicit three-way support taxonomy, defaults, schema metadata, and rejects unknown/unsupported fields | Small JSON-shaped request with defaults and fail-closed unknown keys | correct/bound | 89 symbols; 130 local in new facade | `E1-P1A-SRC1`, `E1-P1A-SCHEMA1`, `E1-P1A-TAXONOMY1`, `E1-P1A-TEST1..3` | preserve; Supervisor re-review |
| CharacterRecipe product projection | Facade projects semantic gender/age-class/build into validated `p2p-character-recipe/1` with stable hash | Deterministic semantic projection with exact hash | correct/bound | new facade consumes existing recipe validator | `E1-P1A-SRC1`, `E1-P1A-TEST1..2` | preserve; P2 only |
| Existing MPFB2 adapter | Runtime plan/execution/security boundary exists and is proven | Facade must delegate without copy | correct | 80 local; 3 flows | `E0-P0A-GRAPH2`, `E0-P0A-RUNTIME1` | preserve-only; bind P1-B |
| Blender MPFB2 entrypoint | Real addon lifecycle, create, GameEngine rig/skin, export, provenance exist | Product facade must reuse it | correct | 49 local; 5 flows | `E0-P0A-GRAPH3`, `E0-P0A-HISTORY1` | preserve-only |
| Provenance model | Existing sidecar schema/hash/rights validation exists | Receipt must report its status/path without duplicating it | correct | 17 local; 1 flow | `E0-P0A-GRAPH4`, `E0-P0A-PROV1` | preserve-only |
| GLB validator | Existing structural validator passes current #56 artifact and handles optional skeleton | Receipt must report status; no weakening | correct | 21 local; 1 flow | `E0-P0A-GRAPH4`, `E0-P0A-RUNTIME1` | preserve-only |
| Router/selection | Existing single-router/provider-neutral machinery exists | No second router or selection agent | correct | 4 / 126 local | `E0-P0A-ROUTE1`, `E0-P0A-GRAPH5` | preserve-only |
| Beginner receipt | Facade returns validated `CharacterForgeReceipt` bound to output/provenance/status/hash fields | Validated concise `CharacterForgeReceipt` | correct/bound | new facade | `E1-P1B-SRC1`, `E1-P1B-TEST1..3` | preserve; P2 only |
| Exact height/age-in-years | Current facade/entrypoint does not bind meters or exact years | Explicit unsupported fail-closed classification | partial | entrypoint 49 local | `E0-P0A-ENTRY1`, `E0-P0A-MPFB1` | classify; do not expand |
| Hair/clothing customization | Recipe slots and core IDs exist but current entrypoint has no hair/clothing calls | Explicit unsupported/deferred classification; no false execution | partial | adapter/entrypoint | `E0-P0A-ENTRY1`, `E0-P0A-CATALOG1` | classify; do not expand |
| Windows isolation | Exact firewall lifecycle is existing and #56 passed | Reuse unchanged; cleanup PASS in product smoke | correct | 43 local; 4 flows | `E0-P0A-GRAPH5`, `E0-P0A-RUNTIME1` | preserve-only; validate P2 |
| Focused tests | Separate productization suite covers request, taxonomy, recipe, binding, receipt, fail-closed, cleanup, and injection boundaries; 12/12 pass | Separate focused behavior tests | correct | 12 focused tests; new file | `E1-P1A-TAXONOMY1`, `E1-P1A-TEST1..3`, `E1-P1B-TEST1..3` | preserve; Supervisor re-review |
| Provisioned runtime | Existing manifest/root/Blender/MPFB2 and #56 result are available | One fresh facade-driven run | correct | external | `E0-P0A-RUNTIME1` | validate P2; no reinstall |
| ISSUE=59 real product smoke | One facade-driven run reached real Blender/MPFB2, character creation, GameEngine rig, built-in skin, GLB, provenance, structural validation, and receipt | All required product flags PASS/YES exactly once | correct | 1 child; 1 GLB; 1 sidecar | `E2-P2A-RUN1`, `E2-P2A-ARTIFACT1`, `E2-P2B-ARTIFACT1` | preserve; Supervisor review |
| ISSUE=59 post-run cleanup | Facade removed managed recipe input; adapter closed isolation; post-run OS/root checks are clean | Zero residual Blender process/rule and unchanged provisioning root | correct | 0 processes; 0 rules | `E2-P2B-CLEAN1` | preserve; Supervisor review |
| Game Truyen | Not part of candidate surface | No reads/writes from productization | correct/preserve-only | external | `E0-P0A-SCOPE1` | do-not-touch |

## Status Refresh Log

| Refresh | Date | Repo Basis | Changed Scope | Status Changes | Evidence | Next Phase Update |
|---------|------|------------|----------------|----------------|----------|-------------------|
| R0 | 2026-09-02 | fresh remote/canonical clone, full SPEC/source/runtime inspection | ISSUE=59 baseline | initial classification: existing route correct; facade/receipt missing; cosmetic/height unsupported | `E0-P0A-GIT1..E0-P0A-SCOPE1` | P1-A may add only the new facade/schema/focused tests |
| R1 | 2026-09-02 | Writer candidate source/schema/tests plus refreshed Anvien capability-system graph and focused proof | P1-A/P1-B implementation | request/recipe/binding/receipt are correct/bound locally; 12/12 focused tests and compile pass; protected route remains preserve-only | `E1-P1A-SRC1..E1-P1-GRAPH1` | P2-A allowed: one real smoke after fresh runtime/output preflight |
| R2 | 2026-09-02 | One fresh facade smoke plus independent runtime/artifact/OS validation | P2-A/P2-B | all requested product flags PASS/YES; exact output/provenance hashes recorded; 0 residual Blender processes/rules; root hash unchanged; Game Truyen unchanged | `E2-P2A-BUILD1..E2-P2B-STOP1` | implementation PASS; create one independent Supervisor review |
| R3 | 2026-09-02 | Independent Supervisor review of candidate `8d338c0600d77b0f4fd4f790f6fa1f2422faebe8` | Supervisor review | REJECT limited to missing `SUPPORTED_DETERMINISTIC` taxonomy and stale status header; no runtime blocker; rejected evidence preserved | `reports/supervisor/rp_supervisor_260902_122647_by_gpt-5-codex_p2p-character-forge-productization-01.md` | create one descendant with minimum metadata/test/status correction; do not rerun smoke |
| R4 | 2026-09-02 | Descendant correction after R3; source/test/status bookkeeping only | Supervisor resubmission preparation | taxonomy now uses `SUPPORTED_DETERMINISTIC` for name/gender/age_class/build and `SUPPORTED_BY_SAFE_DEFAULT` for rig/output_format; status header current; focused tests 12/12 pass | `E1-P1A-TAXONOMY1`, `E1-P1A-TEST1..3` | fresh Supervisor review required on new exact subject |
| R5 | 2026-09-02 | Fresh independent Supervisor resubmission review of `40c8a2006fd50a6a72f2b426fae94e7615e5d299` / `a57d54ecb8894977a212499bc820ad5833838cd1` | Supervisor acceptance | PASS; taxonomy/status findings closed; runtime/artifact/isolation evidence accepted; no residual same-invariant gap | `E3-SUPERVISOR1` | stop at Owner Gate; PR remains unmerged |

## Phase Touch Map

| Unit / File / Surface | Plan-Relevant Relationship File | Relationship to Target | Plan Item | Touch Mode | Evidence | Constraint |
|-----------------------|---------------------------------|------------------------|-----------|------------|----------|------------|
| New `character_forge.py` | `character_recipe.py` | source contract consumer | P1-A/P1-B | edit | `E0-P0A-GRAPH1` | call existing validator; no copy |
| New request schema | `character.recipe.schema.json` | sibling schema authority | P1-A | edit | `E0-P0A-CATALOG1` | new request schema only; preserve recipe schema |
| New focused test module | existing adapter test | sibling behavior tests | P1-A/P1-B | edit new file | `E0-P0A-GRAPH6` | avoid critical test expansion |
| `mpfb_adapter.py` | `character_forge.py` | existing execution consumer | P1-B/P2 | preserve-only / validate-only | `E0-P0A-GRAPH2` | no adapter/security changes |
| `mpfb_blender_entrypoint.py` | `mpfb_adapter.py` | existing runtime producer | P2 | preserve-only / validate-only | `E0-P0A-GRAPH3` | no entrypoint changes |
| `asset_provenance.py` | `glb_validator.py` | existing output validation | P1-B/P2 | preserve-only / validate-only | `E0-P0A-GRAPH4` | reuse status, no duplicate validator |
| `routing.py` | registry entry | single router/registry | P0/P1 | inspect-only / preserve-only | `E0-P0A-ROUTE1` | no second router or registry identity |
| `selection_request.py` | routing surfaces | provider-neutral selection | P0/P1 | inspect-only / preserve-only | `E0-P0A-GRAPH5` | no selection framework |
| `windows_network_isolation.py` | `mpfb_adapter.py` | security lifecycle | P2 | preserve-only / validate-only | `E0-P0A-GRAPH5` | exact firewall mechanism unchanged |
| supplied runtime root | runtime manifest/result | external runtime subject | P2 | validate-only | `E0-P0A-RUNTIME1` | no reinstall/download/root repair |
| Game Truyen | none | forbidden user project | all | do-not-touch | `E0-P0A-SCOPE1` | no mutation or integration |

## Detailed Findings

### Existing capability and router

Current state:

The existing registry already binds MPFB2 provenance to
`game.character.generate`. The current router remains the only router, and
selection is provider-neutral. A second capability identity or route would
conflict with the capability SPEC and create duplicate ontology.

Required state:

```text
Reuse game.character.generate and expose a product facade behind it.
```

Evidence:

- `E0-P0A-CAP1`: exact registry identity and current route metadata.
- `E0-P0A-ROUTE1`: single-router source behavior.

Relationship and impact:

- Related file count: registry data plus routing/selection siblings.
- Relationship summary: existing metadata supplies discovery/readiness; it does
  not need to be changed for this bounded facade.
- Impact note: preserve-only.

Classification:

correct

Allowed next action:

Implement the product facade with `CAPABILITY_ID` equal to the existing identity.

Forbidden next action:

Do not add `game.character.forge`, a second router, a capability-specific
selection agent, or a new registry.

### Existing MPFB2 route

Current state:

The adapter and Blender entrypoint already perform the pinned, isolated route;
#56 current evidence proves a real child reached MPFB2 create, GameEngine
rig/skin, GLB export, provenance, and structural validation.

Required state:

```text
The new facade must delegate to the existing route unchanged.
```

Evidence:

- `E0-P0A-ADAPTER1`: adapter source boundary.
- `E0-P0A-ENTRY1`: entrypoint source boundary.
- `E0-P0A-RUNTIME1`: current runtime manifest and #56 result.

Relationship and impact:

- Related file count: adapter 80 local / 3 flows; entrypoint 49 local / 5 flows.
- Relationship summary: high-risk runtime chain with existing manifest, process,
  output, and security checks.
- Impact note: high/medium warning; no existing source edit is justified.

Classification:

correct

Allowed next action:

Bind the normalized recipe to the public adapter functions and report their
validated result.

Forbidden next action:

Do not copy adapter/validator/firewall logic, repair the runtime, or claim the
old Oak result is ISSUE=59 proof.

### Product facade and request/receipt

Current state:

No beginner request, deterministic semantic projection, runtime-owned binding,
or product receipt exists.

Required state:

```text
CharacterRequest -> CharacterRecipe -> existing MPFB2 adapter -> CharacterForgeReceipt
```

Evidence:

- `E0-P0A-ADAPTER1`: lower-level adapter currently has no beginner product seam.
- `E0-P0A-TEST1`: existing tests have no product facade coverage.

Relationship and impact:

- Related file count: new source surface; reused recipe/adapter contracts only.
- Relationship summary: one new facade can remain isolated from high-risk
  protected files.
- Impact note: missing/unbound; edit P1-A/P1-B.

Classification:

missing

Allowed next action:

Add only the new module/schema/focused tests, then bind to existing functions.

Forbidden next action:

Do not add a service, database, NLP parser, UI, or duplicate runtime.

### Unsupported fields

Current state:

The existing route controls normalized MPFB macro fields and fixed GameEngine
rig/skin. It does not execute physical meters, exact years, hair styling/color,
or clothing customization.

Required state:

```text
Unsupported material intent is rejected or explicitly deferred; it is never
reported as executed.
```

Evidence:

- `E0-P0A-ENTRY1`: current `_macro_detail_dict` and service calls.
- `E0-P0A-MPFB1`: pinned upstream macro/source behavior.

Relationship and impact:

- Related file count: entrypoint and existing internal recipe.
- Relationship summary: recipe includes slots for existing core bindings, but
  current producer does not make cosmetic calls.
- Impact note: partial; classify only, do not expand.

Classification:

partial

Allowed next action:

Document and test `NOT_CURRENTLY_SUPPORTED` fields, with fail-closed request
validation.

Forbidden next action:

Do not silently drop height/hair/clothing intent or claim visual customization.

## Next Phase Status Decisions

| Plan Item | Actual Status Finding | Required Status / Next-Action Update |
|-----------|-----------------------|--------------------------------------|
| P1-A | New facade/schema/tests implement and prove request normalization and deterministic recipe projection | complete; preserve new contract and proceed to P2 |
| P1-B | New facade delegates to existing adapter and validators and returns a validated receipt; 12/12 focused tests pass | complete; proceed to P2 without editing protected route |
| P2-A | One ISSUE=59 facade smoke completed with real Blender PID 21596 and all required product flags PASS/YES | complete; no second run |
| P2-B | Independent artifact, provenance, structural, process, firewall, root, cleanup, and no-retry checks PASS | complete; no rerun or repair |
| Supervisor | Fresh independent resubmission review PASS on corrected subject `40c8a2006fd50a6a72f2b426fae94e7615e5d299` / tree `a57d54ecb8894977a212499bc820ad5833838cd1`; no same-invariant gap remains | stop at Owner Gate; do not infer approval or merge |

## Implementation Gate

- [x] Target scope is listed in Current Status Matrix.
- [x] Each target unit has a status.
- [x] Each status has evidence IDs.
- [x] Each target file has relationship count evidence from `file-detail` when applicable.
- [x] Phase Touch Map lists plan-relevant relationship files that can affect the current phase.
- [x] Phase Touch Map defines touch mode for every plan-relevant relationship unit.
- [x] Correct parts are marked preserve-only.
- [x] Partial and missing parts have exact next actions.
- [x] No unresolved authority blocker affects P1.
- [x] Next phase status assumptions and work steps were updated from this status.
- [x] Status Refresh Log has an R0 baseline row.
- [x] If implementation has started, affected rows will be refreshed from latest evidence.
- [x] P1 request/recipe/binding/receipt rows were refreshed after focused proof.
- [x] P2 smoke/cleanup rows were refreshed after independent runtime proof.

## Final P0 Decision

- [ ] P0 actual-status incomplete. Implementation is blocked.
- [x] P0 complete. Next phase status, next action, or work steps must be updated before implementation.
- [ ] P0 complete. Target scope is preserve-only.
- [ ] P0 complete. Implementation is blocked by missing authority or evidence.

Decision note:

P0 is complete. The current canonical route and all proven boundaries are
preserve-only. The only missing implementation is the one beginner-facing
productization layer and receipt, with a separate focused test file. Physical
height, exact age-in-years, hair, and clothing customization are explicitly
unsupported by the current producer and will fail closed. P1 may proceed; P2 is
gated on focused proof and a fresh runtime preflight.

## P1/P2 Decision

P1 and P2 are complete with PASS evidence. The candidate adds one
beginner-facing facade over `game.character.generate`, not a second capability,
router, runner, validator, or service. The single real smoke used the
supported male/adult/slim request and produced one structurally valid rigged
and skinned GLB plus one provenance sidecar. Exact height, age-in-years, hair,
and clothing intent remain `NOT_CURRENTLY_SUPPORTED` and fail closed. The
implementation is ready for one independent Supervisor review; no Owner
approval or merge is inferred.

Supervisor closure: the fresh independent review for the corrected descendant
returned PASS. Technical readiness is complete; the workflow stops at
`OWNER_GATE`. This does not authorize merge, release, deployment, promotion,
or any additional runtime run.
