# P2P Character Forge Productization ISSUE 59 Evidence Ledger

## Metadata

- Date: `2026-09-02`
- Plan: `docs/plans/2026-09-02-p2p-character-forge-productization-01/2026-09-02-p2p-character-forge-productization-01-plan.md`
- Evidence: `docs/plans/2026-09-02-p2p-character-forge-productization-01/2026-09-02-p2p-character-forge-productization-01-evidence.md`
- Benchmark: `docs/plans/2026-09-02-p2p-character-forge-productization-01/2026-09-02-p2p-character-forge-productization-01-benchmark.md`
- Actual status: `docs/plans/2026-09-02-p2p-character-forge-productization-01/2026-09-02-p2p-character-forge-productization-01-actual-status.md`

## Evidence Rules

This ledger records current source, runtime, test, graph, artifact, and review
evidence for ISSUE=59. Historical reports are evidence pointers only; current
candidate source and fresh runtime checks control the claim. A passing status
string without its source, command, artifact, or independent check is not proof.

### Evidence ID Naming

Evidence IDs are phase-scoped and stable:

```text
E<phase>-<item>-<kind><n>
```

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-GIT1`: A fresh `git fetch origin main` from the canonical remote
  resolved `origin/main` to
  `0ee414147ae308ab1f6035d1e7776292752bd8da`; `git rev-parse
  origin/main^{tree}` resolved to
  `f34719776bee67a731c4049b79165bd3deaa3074`. A clean direct clone was made
  at `D:\AI\P2P_dev\worktrees\p2p-issue-59-character-forge-productization-clean`
  and the Writer branch was created from that exact main. The supplied
  `D:\AI\P2P_dev\P2P-upgrade-github` directory was not a usable Git checkout
  and was not repaired; the existing canonical clone was dirty and was not
  modified.
- `E0-P0A-CAP1`: Current registry inspection shows exactly one existing
  capability identity for this lane: `game.character.generate`. It is the
  existing `KNOWLEDGE_SOURCE` / `MODEL_ROUTABLE` surface with MPFB2 provenance,
  `p2p-character-recipe/1`, `p2p-character-asset-provenance/1`, and
  `execution_authorized=false`. No new `character.forge` identity is warranted.
- `E0-P0A-SPEC1`: The full relevant capability SPEC cluster was read in the
  authority order available in `Docs/SPEC`: foundation architecture, manifest,
  routing/readiness, context pointers, execution/evidence, test/eval, and
  trust/data-instruction. The repository does not contain the referenced
  `SPEC-MAP.md`; the explicit relevant cluster was read in full and did not
  leave a conflicting authority for this bounded lane.
- `E0-P0A-CATALOG1`: The full game asset forge catalog, recipe schema,
  provenance schema, README, and asset-forge protocol were read. They require
  reuse of `game.character.generate`, offline MPFB2, `CORE_CC0_ONLY`, exact
  durable GLB/provenance outputs, and no second ontology/router.
- `E0-P0A-ADAPTER1`: Current `mpfb_adapter.py` validates the pinned manifest,
  root hash, core assets, recipe binding, shell-free allowlisted Blender argv,
  minimal environment, timeout/process-tree cleanup, exact output membership,
  and delegates structural validation to `glb_validator.py`. It exposes no
  beginner request or product receipt; this is the productization gap.
- `E0-P0A-ENTRY1`: Current `mpfb_blender_entrypoint.py` loads MPFB2 through the
  Blender 4.2 local extension repository and `addon_utils.enable`, then calls
  `HumanService.create_human`, `add_builtin_rig(..., "game_engine",
  import_weights=True)`, `set_character_skin(..., skin_type="GAMEENGINE")`,
  GLB export, and existing provenance. Its `_macro_detail_dict` passes gender,
  normalized age, weight, muscle, and uniform proportions, but not physical
  `height_m`, hair intent, or clothing customization.
- `E0-P0A-MPFB1`: Static inspection of the provisioned MPFB2 source confirms
  `HumanService.create_human` accepts a normalized macro dictionary and a
  numeric scale; `TargetService.get_default_macro_info_dict` uses normalized
  macro values; the pinned macro config exposes gender/age/muscle/weight/
  proportions/height classes. This proves only the current normalized fields,
  not an exact age-in-years or physical-meter contract.
- `E0-P0A-ROUTE1`: Current `routing.py` remains the single router and returns
  `p2p-capability-route/1`; current selection surfaces are generic and
  provider-neutral. No productization code needs a second route or selection
  agent.
- `E0-P0A-PROV1`: Current `asset_provenance.py` requires
  `p2p-character-asset-provenance/1`, `CORE_CC0_ONLY`, MPFB2 2.0.17,
  `GAMEENGINE`, `MPFB_BUILT_IN_WEIGHTS`, exact asset bindings, and hash-valid
  sidecar data. Current `glb_validator.py` enforces glTF 2.0, reachable mesh and
  skin, JOINTS_0/WEIGHTS_0, rooted skeleton policy, and resource binding.
- `E0-P0A-TEST1`: Existing focused tests cover the internal recipe, adapter,
  Blender entrypoint, provenance, GLB validation, firewall lifecycle, exact
  pinned manifest, and prior runtime boundary. They do not cover a beginner
  request, a product facade, or a `CharacterForgeReceipt`; a separate focused
  test file avoids changing the critical existing test file.
- `E0-P0A-RUNTIME1`: Current supplied runtime manifest records Blender 4.2.23,
  MPFB2 2.0.17, release SHA/tree, manifest root hash
  `f6907ef03674ddc995e8b0fdd988e9a003cad61df0d4f707e2a7aaeda4d4e788`, local
  extension loading, `CORE_CC0_ONLY`, and network deny. Current #56 result
  records exactly one prior real Oak run with child PID 27548, Blender/MPFB2
  addon and HumanService create/rig/skin/export pass, provenance and structural
  validation pass, firewall cleanup pass, and exactly two outputs. It is
  historical/reference evidence and does not substitute for the ISSUE=59
  facade smoke.
- `E0-P0A-HISTORY1`: Current canonical history includes the bounded adapter,
  addon lifecycle, optional skeleton validator, and provisioning-root drift
  closures. #52/#55/#56 reports explicitly separate their bounded claims from
  full productization. No new blocker is carried forward from the old
  `skeleton=null` or root-drift state.
- `E0-P0A-GRAPH1`: Fresh Anvien capability-system graph file detail for
  `p2p_capabilities/character_recipe.py`: 48 symbols, 25 local relationships,
  2 linked flows, 81 unresolved analyzer references, high file risk; file
  impact is medium with 12 impacted symbols and 1 linked process. This file is
  preserve-only for ISSUE=59.
- `E0-P0A-GRAPH2`: Fresh Anvien file detail for
  `p2p_capabilities/mpfb_adapter.py`: 93 symbols, 80 local relationships,
  3 linked flows, 304 unresolved references, high file risk; file impact is
  high with 17 impacted symbols and 1 linked process. This file is
  preserve-only for ISSUE=59.
- `E0-P0A-GRAPH3`: Fresh Anvien file detail for
  `p2p_capabilities/mpfb_blender_entrypoint.py`: 72 symbols, 49 local
  relationships, 5 linked flows, 269 unresolved references, medium file risk;
  file impact is medium with 14 impacted symbols and 1 linked process. This
  file is preserve-only for ISSUE=59.
- `E0-P0A-GRAPH4`: Fresh Anvien file detail for
  `p2p_capabilities/asset_provenance.py` and `glb_validator.py` records
  respectively 38/17/1 and 55/21/1 (symbols/local relationships/linked flows),
  with medium file risk; their file impacts are medium with 9 and 8 impacted
  symbols respectively. Both are preserve-only.
- `E0-P0A-GRAPH5`: Fresh Anvien file detail for routing, selection, and firewall
  siblings records routing 29 symbols/4 local/0 flows, selection request 54
  symbols/126 local/1 flow, registry JSON with no code symbols, and firewall
  isolation 44 symbols/43 local/4 flows. File impacts are low/medium/low/medium
  respectively for routing/selection/registry/firewall. These are
  preserve-only and do not need a second router or isolation implementation.
- `E0-P0A-GRAPH6`: Existing focused adapter test file has 154 symbols, 161 local
  relationships, 812 unresolved references, high file risk, and critical file
  impact across 55 impacted symbols. ISSUE=59 adds a new test module instead of
  expanding that critical surface.
- `E0-P0A-SCOPE1`: No Game Truyen source is in the candidate scope. The product
  facade will accept only a P2P-owned runtime binding and will not import,
  write, or integrate `D:\game-truyen-github`.

P0 decision: the existing MPFB2 capability is correct and preserve-only; the
beginner facade and receipt are missing/unbound; the supplied runtime is
available for one later run; no authority or same-scope blocker prevents the
bounded P1 implementation.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

- `E1-P1A-SRC1`: `character_forge.py` adds one deterministic facade module. It
  accepts only the six supported beginner fields, maps age/build to the
  existing normalized MPFB recipe, rejects unknown/runtime-control fields, and
  calls the existing recipe validator. No NLP, command construction, or
  second capability/router was added.
- `E1-P1A-SCHEMA1`: `character.request.schema.json` declares
  `p2p-character-request/1`, optional matching `schema` metadata, six beginner
  properties, `additionalProperties: false`, and the same safe defaults/const
  values as the module. The focused test checks exact property alignment.
- `E1-P1A-TEST1`: `PYTHONDONTWRITEBYTECODE=1 python -B -m unittest
  tests.test_p2p_character_forge -v` passed all 12 tests.
- `E1-P1A-TEST2`: the same focused run proves `{}` defaults, canonical request
  round-trip, semantic-order independence, and identical recipe SHA-256.
- `E1-P1A-TEST3`: the same focused run proves invalid height type/range,
  unsupported exact age/height/hair/clothing fields, runtime/path/command/
  network/manifest injection, FBX, and unrigged requests fail closed.
- `E1-P1B-SRC1`: `forge_character` passes only P2-owned fixed runtime context
  and `network_access=False` to `mpfb_adapter.build_execution_plan`, then
  delegates to `mpfb_adapter.execute_plan`; it reuses the existing provenance
  validator and GLB validation result. It checks the plan recipe/output
  binding before execution and does not copy adapter, process, firewall, or
  validator logic.
- `E1-P1B-TEST1`: the focused binding test observes the exact adapter keyword
  arguments, fixed MPFB2 relative paths, separate authorization, output shape,
  and generated recipe-input cleanup using a repo-local temporary workspace.
- `E1-P1B-TEST2`: receipt tests prove round-trip validation and reject wrong
  capability identity or structural status; the receipt binds character name,
  recipe SHA-256, GLB SHA-256, provenance path/status, rig/skin, runtime, and
  firewall cleanup statuses.
- `E1-P1B-TEST3`: the focused run proves unsupported input never reaches the
  adapter, missing execution authorization is rejected, output is not
  overwritten, and only the managed recipe input is removed.
- `E1-P1-GRAPH1`: refreshed capability-system Anvien evidence sees the new
  `character_forge.py` as 89 parsed symbols, 130 local relationships, 2 linked
  flows, and no inbound callers yet; file risk is a scope warning for a new
  surface, not a reason to touch the protected route. Staged change detection
  reports exactly 3 intended files and `changedFileRisk=low`.
- `E1-P1A-TAXONOMY1`: after the first Supervisor rejection, the descendant
  assigns the required categories exactly: `name`, `gender`, `age_class`, and
  `build` are `SUPPORTED_DETERMINISTIC`; `rig` and `output_format` are
  `SUPPORTED_BY_SAFE_DEFAULT`; the eight material fields remain
  `NOT_CURRENTLY_SUPPORTED`. The focused test asserts category membership and
  disjointness.

P1 decision: PASS. Both contract and binding/receipt are implemented in the
single coherent `character_forge.py` product seam; splitting that importable
facade into an incomplete intermediate module would add no safety. The
existing adapter, entrypoint, provenance, validator, firewall, registry, and
selection surfaces remain unchanged. P2 is now the only implementation phase.

## Supervisor Correction Record

The first independent review was intentionally preserved as
`reports/supervisor/rp_supervisor_260902_122647_by_gpt-5-codex_p2p-character-forge-productization-01.md`.
It returned `REJECT` for two same-scope issues: the support taxonomy did not
use `SUPPORTED_DETERMINISTIC`, and the actual-status header was stale. No
runtime or artifact failure was found. The current descendant corrects both,
does not modify the rejected candidate in place, and does not rerun Blender;
fresh Supervisor review remains required for the new exact subject.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

- `E2-P2A-BUILD1`: `PYTHONDONTWRITEBYTECODE=1 python -B -m compileall -q
  .p2p/system tests scripts` exited 0. It emitted only the existing
  `tests/test_p2p_live_certification.py:179` `SyntaxWarning`; no touched file
  is that warning's source.
- `E2-P2A-PREFLIGHT1`: fresh read-only preflight found Blender 4.2.23 present,
  MPFB2 `2.0.17`, commit `80919fa4682335c41847f761a4d79dcad4124732`, tree
  `189a1d6694515ecfbdc40067218c5024389b4e43`, provisioning root hash
  `f6907ef03674ddc995e8b0fdd988e9a003cad61df0d4f707e2a7aaeda4d4e788`
  matching, a new absent output target, zero Blender processes, and zero
  `P2P-MPFB-DENY-*` rules. The pre-existing Game Truyen worktree had 55 dirty
  entries and was not touched.
- `E2-P2A-RUN1`: the repo-local smoke helper called `forge_character` exactly
  once with `{name: Issue59, gender: male, age_class: adult, build: slim,
  rig: true, output_format: glb}`. Real Blender child PID `21596` returned 0;
  the result is recorded at
  `D:\AI\P2P_runtime\mpfb2-runtime-01\logs\p2p-issue59-character-forge-productization-01-result.json`.
  The child stdout contains `MPFB_ADDON_IDENTITY_PRESENT=YES`,
  `MPFB_GET_PREFERENCE_PASS=YES`, and `MPFB_REGISTER_PASS=YES`.
- `E2-P2A-ARTIFACT1`: the receipt reports capability
  `game.character.generate`, recipe SHA-256
  `7c4fe122da0ddf7569eaa45323037ee27414bcdac04330fcc4e5047f334a8c52`, output
  `D:\AI\P2P_runtime\mpfb2-runtime-01\output\p2p-character-forge-7c4fe122da0ddf75\Issue59.glb`,
  output SHA-256
  `4e974fb6c6861731f547e3ec3d69f18f01d7ed9073df6bd96bd8ededbde3ae97`, and
  sidecar
  `D:\AI\P2P_runtime\mpfb2-runtime-01\output\p2p-character-forge-7c4fe122da0ddf75\Issue59.asset-provenance.json`.
  All requested product flags are PASS/YES in the result record.
- `E2-P2B-ARTIFACT1`: an independent read-only validator rerun reported
  exactly two output files (`Issue59.glb` and
  `Issue59.asset-provenance.json`), GLB size `6372972` bytes, glTF `2.0`, 55
  scene-reachable nodes, `GAMEENGINE` rig, `MPFB_BUILT_IN_WEIGHTS` skinning,
  matching output hash, receipt validation PASS, provenance validation PASS,
  and recipe/asset binding PASS. The independent record is at
  `D:\AI\P2P_runtime\mpfb2-runtime-01\logs\p2p-issue59-character-forge-productization-01-independent-validation.json`.
- `E2-P2B-CLEAN1`: post-run OS check found zero Blender processes and zero
  `P2P-MPFB-DENY-*` rules; provisioning root hash still matches
  `f6907ef03674ddc995e8b0fdd988e9a003cad61df0d4f707e2a7aaeda4d4e788`; the
  managed recipe input is absent after facade cleanup.
- `E2-P2B-STOP1`: exactly one child PID, one GLB, one provenance sidecar, and
  one receipt record exist for ISSUE=59; no retry or second character was run.
  Ephemeral repo-local smoke helpers were removed after evidence capture.
  Game Truyen HEAD and dirty-entry count remained
  `354203ee7c23a2b349e81a0254b537da4d9c622f` and `55`.

P2 decision: PASS. The complete product route is proven once through the new
facade; independent artifact, provenance, structural, process, firewall, root,
and cleanup checks agree. The request did not contain exact height, age-years,
hair, or clothing intent because those fields are explicitly unsupported and
fail closed; the receipt makes no visual-customization claim.

## Closure Evidence

Pending. Final closure must include fresh Anvien detect-changes, focused
validation/build output, exact candidate commit/tree, one unmerged PR, and one
independent Supervisor report. A real smoke blocker must remain `BLOCKED`, not be
repaired under this workstream.
