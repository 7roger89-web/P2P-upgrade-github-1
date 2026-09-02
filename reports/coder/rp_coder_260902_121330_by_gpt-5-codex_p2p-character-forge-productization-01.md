# Coder Report: P2P Character Forge Productization ISSUE 59

Date: 2026-09-02 12:13:30 +07:00
Role: `WRITER_AND_REAL_RUNTIME_EXECUTOR`
Repository: `7roger89-web/P2P-upgrade-github-1`
Issue: `59`
Workstream: `P2P-CHARACTER-FORGE-PRODUCTIZATION-01`
Canonical base: `0ee414147ae308ab1f6035d1e7776292752bd8da`
Canonical tree: `f34719776bee67a731c4049b79165bd3deaa3074`
Implementation checkpoint: `061f2a7bdcc50989140db81e6b7be7e5b757468e`
PR: not yet published; merge not performed.

## Result

PASS for the bounded productization claim. One new beginner-facing facade now
normalizes a small structured request, projects it into the existing
`p2p-character-recipe/1` contract, delegates to the existing
`game.character.generate` MPFB2 adapter, and returns a validated
`p2p-character-forge-receipt/1`. No second character framework, router,
process runner, validator, service, database, UI, or NLP parser was added.

The one real product smoke used a supported `male` / `adult` / `slim` request.
It produced one rigged and skinned GLB and one provenance sidecar through real
Blender and MPFB2. Exact physical height, age-in-years, hair intent, and
clothing intent are not executed by the current proven producer and therefore
fail closed; the product makes no visual-customization claim.

## Invariant Family Map

| Family | Authority / SSOT | Sibling surfaces checked | Result |
|---|---|---|---|
| Capability identity and routing | existing registry entry `game.character.generate`, existing single router | `capabilities.json`, `routing.py`, `selection_request.py`, game-asset catalog | One identity reused; registry/router/selection unchanged; no duplicate capability |
| Beginner request and recipe | new `character_forge.py`, new `character.request.schema.json`, existing `character_recipe.py` | recipe schema, MPFB2 macro source, existing recipe hash/validator | Six supported fields with deterministic defaults; semantic order does not change recipe or hash; unknown/runtime-control and unsupported material fields fail closed |
| MPFB2 execution and security | existing `mpfb_adapter.py`, `mpfb_blender_entrypoint.py`, `windows_network_isolation.py` | exact manifest, Blender command allowlist, PR50/PR54 boundaries, MPFB2 pin | Facade delegates only; no copied runner/firewall/entrypoint logic; `network_access=False` and fixed internal paths |
| Provenance and structure | existing `asset_provenance.py`, `glb_validator.py` | output sidecar, recipe/asset binding, GLB scene/skin checks | Receipt reports existing validation; independent rerun PASS; no validator weakening |
| Provisioning subject | supplied `runtime-manifest.json` and `mpfb2/provisioning-manifest.json` | MPFB2 version/release/tree, root hash, four CORE_CC0 assets | `2.0.17`, release `80919fa...`, tree `189a1d...`; root hash matched before/after; no reinstall/download/repair |
| Output and cleanup | facade-managed recipe input and adapter-owned output/isolation lifecycle | exact output directory, post-run process/firewall/root checks | Exactly two output files, managed recipe input absent, 0 Blender processes, 0 deny rules |
| Project isolation | user scope boundary | `D:\game-truyen-github` HEAD and dirty-entry fingerprint before/after | HEAD unchanged and dirty-entry count remained 55; no Game Truyen mutation |

## Source Changes

Product source files only:

- `.p2p/system/p2p_capabilities/character_forge.py`
- `docs/p2p-development/capability-catalog/game-asset-forge/character.request.schema.json`
- `tests/test_p2p_character_forge.py`

The plan/evidence/benchmark/status and this report are bookkeeping artifacts.
Existing adapter, entrypoint, provenance, GLB validator, firewall, registry,
selection, MPFB2 runtime, and Game Truyen files were not edited.

## Contract Classification

```text
PRODUCTIZATION_TYPE=BEGINNER_FACING_FACADE_OVER_EXISTING_CAPABILITY
EXISTING_CAPABILITY_ID=game.character.generate
REQUEST_SCHEMA=p2p-character-request/1
RECIPE_SCHEMA=p2p-character-recipe/1
RECEIPT_SCHEMA=p2p-character-forge-receipt/1
```

Supported request fields are `name`, `gender`, `age_class`, `build`, `rig`,
and `output_format`. Defaults are `Character`, `neutral`, `adult`, `default`,
`true`, and `glb`. The projection maps `young`/`adult`/`old` and
`default`/`slim`/`average`/`athletic` to the existing normalized MPFB macro
values and fixes GameEngine rigging, built-in weights, neutral proportions,
CORE_CC0 assets, and embedded GLB 2.0 output.

The following fields are classified `NOT_CURRENTLY_SUPPORTED` and are rejected
after deterministic shape validation: `height_m`, `age`, `age_years`, `hair`,
`hair_intent`, `hair_color`, `clothing`, and `clothing_intent`. Runtime paths,
commands, network settings, manifest hashes, and unknown keys are not request
fields and fail closed.

## Legacy Fallback / Anti-Fabrication Check

No fallback path exists. Natural-language interpretation remains above the
runtime boundary. The lower-level #56 Oak result was used only as prior
capability evidence; ISSUE=59 used a new recipe hash, new output directory,
new real child, and a new receipt. Unsupported cosmetic intent is not silently
dropped or reported as executed.

## Focused Verification

```text
PYTHONDONTWRITEBYTECODE=1 python -B -m unittest tests.test_p2p_character_forge -v
12/12 PASS

PYTHONDONTWRITEBYTECODE=1 python -B -m compileall -q .p2p/system tests scripts
exit 0; one existing SyntaxWarning at tests/test_p2p_live_certification.py:179

Anvien capability-system refresh + staged detect-changes
3 intended staged files; changedFileRisk=low
```

Focused tests cover defaults, request/schema alignment, deterministic
projection/hash, invalid type/range, unsupported material intent, runtime
injection, adapter binding, separate authorization, cleanup, receipt
round-trip, and malformed receipt rejection.

## Real Product Smoke

Exactly one facade call was executed against
`D:\AI\P2P_runtime\mpfb2-runtime-01`; no retry or second character was run.

```text
REQUEST={name:Issue59, gender:male, age_class:adult, build:slim, rig:true, output_format:glb}
REAL_BLENDER_CHILD_PID=21596
REAL_BLENDER_CHILD_SPAWNED=YES
REAL_MPFB2_EXECUTED=YES
CHARACTER_CREATED=YES
RIG_PRESENT=YES
SKIN_PRESENT=YES
GLB_STRUCTURALLY_VALID=YES
PROVENANCE_VALIDATION=PASS
FIREWALL_CLEANUP_PASS=YES
RUNTIME_STATUS=EXECUTED_AND_STRUCTURALLY_VALID
```

Receipt/result record:

`D:\AI\P2P_runtime\mpfb2-runtime-01\logs\p2p-issue59-character-forge-productization-01-result.json`

Normalized recipe SHA-256:

`7c4fe122da0ddf7569eaa45323037ee27414bcdac04330fcc4e5047f334a8c52`

Output:

```text
GLB=D:\AI\P2P_runtime\mpfb2-runtime-01\output\p2p-character-forge-7c4fe122da0ddf75\Issue59.glb
GLB_SHA256=4e974fb6c6861731f547e3ec3d69f18f01d7ed9073df6bd96bd8ededbde3ae97
GLB_BYTES=6372972
PROVENANCE=D:\AI\P2P_runtime\mpfb2-runtime-01\output\p2p-character-forge-7c4fe122da0ddf75\Issue59.asset-provenance.json
OUTPUT_MEMBERS=Issue59.glb,Issue59.asset-provenance.json
```

## Independent Post-Run Verification

The existing GLB validator and provenance validator were rerun independently
from the result record. They reported glTF 2.0, 55 scene-reachable nodes,
`GAMEENGINE`, `MPFB_BUILT_IN_WEIGHTS`, matching GLB hash, provenance PASS,
recipe/asset binding PASS, receipt validation PASS, and exactly two output
files. The independent record is:

`D:\AI\P2P_runtime\mpfb2-runtime-01\logs\p2p-issue59-character-forge-productization-01-independent-validation.json`

Post-run checks reported:

```text
BLENDER_PROCESSES_AFTER=0
P2P-MPFB-DENY-RULES_AFTER=0
PROVISIONING_ROOT_HASH_MATCH=YES
RECIPE_INPUT_ABSENT_AFTER_CLEANUP=YES
GAME_TRUYEN_HEAD_UNCHANGED=YES
GAME_TRUYEN_DIRTY_ENTRIES_BEFORE_AFTER=55/55
```

## E2E Boundary

```text
CharacterRequest
  -> normalize_character_request
  -> build_character_recipe + existing recipe validator/hash
  -> existing mpfb_adapter.build_execution_plan
  -> existing mpfb_adapter.execute_plan
  -> real Blender child / existing MPFB2 entrypoint
  -> HumanService create + GameEngine rig + built-in skin
  -> GLB + provenance sidecar
  -> existing structural/provenance validation
  -> isolation/process cleanup
  -> validated CharacterForgeReceipt
```

Residual same-invariant surfaces are none for the bounded claim. Exact height,
exact age-years, hair, clothing, UI, multiple characters, and integration with
other projects remain explicitly out of scope rather than unverified promises.

## Closure State

```text
REAL_PRODUCT_SMOKE=PASS
INDEPENDENT_ARTIFACT_AND_CLEANUP=PASS
GAME_TRUYEN_MUTATIONS=NO
OVER_ENGINEERING_CHECK=PASS
SUPERVISOR_VERDICT=PENDING
NEXT_STEP=INDEPENDENT_SUPERVISOR_REVIEW
```
