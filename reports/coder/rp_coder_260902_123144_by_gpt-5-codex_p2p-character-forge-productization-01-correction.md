# Coder Report: ISSUE 59 Supervisor Correction

Date: 2026-09-02 12:31:44 +07:00
Role: `WRITER_AND_REAL_RUNTIME_EXECUTOR`
Repository: `7roger89-web/P2P-upgrade-github-1`
Issue: `59`
Workstream: `P2P-CHARACTER-FORGE-PRODUCTIZATION-01`
Rejected subject: `8d338c0600d77b0f4fd4f790f6fa1f2422faebe8`
Rejected subject tree: `8b0a8c870de305f302d5e2f9f3e3dd3104a45501`
Canonical base: `0ee414147ae308ab1f6035d1e7776292752bd8da`
Canonical tree: `f34719776bee67a731c4049b79165bd3deaa3074`

## Correction Result

The first independent Supervisor review returned `REJECT` for two bounded
bookkeeping/contract issues, both preserved in the rejected report:

1. `FIELD_SUPPORT` did not use the required `SUPPORTED_DETERMINISTIC`
   category.
2. The actual-status header still said `P1 Complete; P2 Pending` after P2 had
   passed.

The new descendant correction assigns `name`, `gender`, `age_class`, and
`build` to `SUPPORTED_DETERMINISTIC`; assigns fixed-only `rig` and
`output_format` to `SUPPORTED_BY_SAFE_DEFAULT`; and keeps the eight material
fields `NOT_CURRENTLY_SUPPORTED`. Focused assertions cover the exact disjoint
sets and all three vocabulary values. The actual-status header now says
`P2 Complete; Supervisor Re-review Pending` and records the first rejection and
the correction separately.

No production route, runtime, artifact, or security behavior changed. The
previous single real smoke remains valid because the corrected fields are
metadata/test/status only and the MPFB2 recipe, adapter, entrypoint,
provenance, GLB validator, firewall lifecycle, and generated artifact are
unchanged. No Blender rerun is authorized or needed.

## Invariant Family Map

| Family | Correction authority | Sibling surfaces checked | Result |
|---|---|---|---|
| Request support taxonomy | user-required three-way classification; `character_forge.py` constants | request schema, normalized request tests, actual-status/evidence | Exact supported/default/unsupported sets are now explicit and disjoint |
| Deterministic recipe | existing `p2p-character-recipe/1` and prior PASS smoke | recipe hash, runtime result, provenance binding | Unchanged; prior recipe SHA and output evidence remain valid |
| MPFB2/security | existing adapter, entrypoint, PR50/PR54 isolation | candidate diff and prior independent cleanup proof | Unchanged; no rerun needed |
| Status/evidence closure | planner templates and Supervisor finding | plan, evidence, benchmark, actual-status, rejected report | Header and refresh log now agree; rejected evidence preserved |

## Focused Verification

```text
PYTHONDONTWRITEBYTECODE=1 python -B -m unittest tests.test_p2p_character_forge -v
12/12 PASS

PYTHONDONTWRITEBYTECODE=1 python -B -m compileall -q .p2p/system/p2p_capabilities/character_forge.py tests/test_p2p_character_forge.py
PASS

git diff --check
PASS
```

The test module now verifies:

```text
SUPPORTED_DETERMINISTIC={name,gender,age_class,build}
SUPPORTED_BY_SAFE_DEFAULT={rig,output_format}
NOT_CURRENTLY_SUPPORTED={height_m,age,age_years,hair,hair_intent,hair_color,clothing,clothing_intent}
```

## Scope and Runtime Boundary

The correction is one descendant of the rejected candidate and contains no
second framework or in-place rewrite. It does not change the supported real
request (`Issue59`, male, adult, slim, rigged GLB), normalized recipe hash
`7c4fe122da0ddf7569eaa45323037ee27414bcdac04330fcc4e5047f334a8c52`, GLB
SHA-256 `4e974fb6c6861731f547e3ec3d69f18f01d7ed9073df6bd96bd8ededbde3ae97`,
or the independent output/provenance/cleanup evidence. Exactly one real smoke
has been executed for this workstream; no second run was made.

Game Truyen remains untouched: its pre/post HEAD was
`354203ee7c23a2b349e81a0254b537da4d9c622f` and its dirty-entry fingerprint was
55 before and after the smoke.

## State

```text
SUPERVISOR_REVIEW_1=REJECT (preserved)
CORRECTION_SCOPE=taxonomy + status bookkeeping + focused assertions
REAL_RUNTIME_RERUN=NO (not needed)
NEW_SUPERVISOR_REVIEW=REQUIRED
```
