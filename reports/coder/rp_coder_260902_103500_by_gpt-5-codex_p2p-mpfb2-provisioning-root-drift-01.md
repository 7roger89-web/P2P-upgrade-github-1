# Coder Report: P2P-MPFB2 provisioning root drift ISSUE 56

Date: 2026-09-02 10:35:00 +07:00
Role: `RUNTIME_RECONCILIATION_WRITER`
Repository: `7roger89-web/P2P-upgrade-github-1`
Issue: `56`
Workstream: `P2P-MPFB2-PROVISIONING-ROOT-DRIFT-01`
Canonical base: `e7c040d87dacf7b5cfee1e57536edc0b27f5768b`
Canonical tree: `9649785f0104259bac05b244a2162e2a7321657f`
Candidate branch: `workstream/p2p-mpfb2-provisioning-root-drift-01-candidate`
Implementation checkpoint: `79d9526b4401fdd6b0e76eef972ec6ec2186430d` / tree `8c22e067ce35e96ac6e59d93f36f372603be9393`
PR: not created; no external publication action was performed.

## Result

The MPFB2 provisioning-root mismatch is reconciled without reinstalling,
redownloading, overwriting the manifest, or changing the pinned MPFB2 subject.
The exact current delta was 526 added runtime-generated Python bytecode files
under immediate `__pycache__` directories. The bounded root hash now excludes
only that exact generated-file shape; all other regular files remain bound.

One real canonical continuation was executed against the existing Windows
runtime. It passed root integrity, firewall isolation, Blender spawn, MPFB2
addon initialization, HumanService creation, GameEngine rig/skin, GLB export,
provenance, structural GLB validation, and cleanup. No retry was run.

## Invariant Family Map

| Family | Authority / SSOT | Sibling surfaces checked | Result |
|---|---|---|---|
| Provisioning-root integrity | `mpfb_adapter.py:187-216`, `provisioning-manifest.json`, exact pinned archive | `build_execution_plan`, `execute_plan`, Blender entrypoint root check | Closed by one exact `__pycache__/*.pyc` predicate; manifest binding preserved |
| Pinned MPFB2 subject | MPFB2 `2.0.17`, release `80919fa4682335c41847f761a4d79dcad4124732`, archive SHA `9a1efbb7e42590a72404be35a2a71082dd6e5cd9472167f4a977d336e77e7d20` | all 2,810 archive paths and four manifest-bound CORE_CC0 assets | Byte-identical before and after the real run |
| Runtime/security lifecycle | existing `mpfb_blender_entrypoint.py` and `windows_network_isolation.py` | pre-spawn plan, exact Blender executable, firewall setup/enforcement/cleanup | Preserved; setup/enforcement/cleanup all PASS |
| Output/provenance | existing `asset_provenance.py`, `glb_validator.py`, recipe contract | Oak GLB, sidecar, independent validation | Structurally valid and provenance-valid; bytes/hash retained |
| Product immutability | user boundary | `D:\game-truyen-github` HEAD/status fingerprint | Unchanged; no Game Truyen access beyond read-only fingerprinting |

## Root Delta and Classification

Complete per-path delta, including all 526 paths, is recorded in:

- `.tmp/issue56-root-delta-20260902.json`

The comparison was between the current runtime `mpfb2` root and the existing
exact pinned archive. Results:

```text
CURRENT_ROOT_HASH=10ebf09a8b425f6e1081f9624ccf9365e471522b01527820e89d27b20de705bf
MANIFEST_ROOT_HASH=f6907ef03674ddc995e8b0fdd988e9a003cad61df0d4f707e2a7aaeda4d4e788
DELTA_PATH_COUNT=526
ADDED=526
MODIFIED=0
DELETED=0
RUNTIME_GENERATED=526
PINNED_SOURCE=0
PINNED_ASSET=0
MANIFEST_METADATA=0
UNKNOWN=0
```

Every delta path is `src/**/__pycache__/<name>.pyc`; no path was labeled cache
from its name alone. The archive recomputed to the manifest root hash exactly,
and its SHA-256 matched the runtime manifest's recorded archive SHA.

## Pinned Subject Protection

```text
MPFB2_VERSION=2.0.17
MPFB2_RELEASE_SHA=80919fa4682335c41847f761a4d79dcad4124732
MPFB2_RELEASE_TREE=189a1d6694515ecfbdc40067218c5024389b4e43
PINNED_SUBJECT_MUTATED=NO
PINNED_SOURCE_CHANGED=NO
PINNED_ASSETS_CHANGED=NO
```

The staged Git object proves the exact MPFB2 release commit/tree. The runtime
contains all 2,810 archive paths with equal bytes; each of the four CORE_CC0
asset hashes also matches the manifest. No pinned restoration and no manifest
rewrite were performed.

## Design Classification

```text
HASH_SCOPE_DEFECT=YES
RUNTIME_CLEANUP_DEFECT=NO
PINNED_RUNTIME_CORRUPTION=NO
ROOT_CAUSE=The root hash enumerated every regular file, including 526 Python bytecode products generated under __pycache__ after provisioning. Those files are absent from the exact pinned archive, so a legitimate MPFB2 load permanently changed the next preflight hash.
```

## Remediation

```text
REMEDIATION_TYPE=BOUNDED_SOURCE_FIX
SOURCE_FILES_CHANGED=.p2p/system/p2p_capabilities/mpfb_adapter.py; tests/test_p2p_game_truyen_mpfb_adapter_01.py
```

`hash_provisioned_root()` now skips only a file whose immediate parent is
`__pycache__` and whose suffix is exactly lowercase `.pyc`. The manifest file
is still excluded only through its explicit path argument. Unknown files inside
`__pycache__`, `.pyc` files outside `__pycache__`, source mutations, and asset
mutations remain hash/manifest failures.

No generic ignore pattern, disabled root hashing, cache manager, second
provisioning framework, firewall change, addon change, GLB validator change,
upstream change, Blender change, or Game Truyen change was made.

## Focused Verification

- `tests/test_p2p_game_truyen_mpfb_adapter_01.py:329-370` adds six direct boundary cases: pinned source mutation, pinned asset byte mutation, approved generated bytecode, unknown cache extra, outside-cache bytecode, and exact manifest-root binding.
- `python -m unittest tests.test_p2p_game_truyen_mpfb_adapter_01.AdapterBoundaryTests -v`: `22/22 PASS`.
- `python -m compileall -q .p2p/system/p2p_capabilities tests/test_p2p_game_truyen_mpfb_adapter_01.py`: PASS.
- `python -m compileall -q .p2p scripts tests`: exit 0; one unrelated pre-existing `SyntaxWarning` in `tests/test_p2p_live_certification.py` was not changed.
- `git diff --check`: PASS before checkpoint.
- Anvien capability-subtree file detail: 92 symbols, 80 local relationships, 3 linked flows, HIGH file risk.
- Anvien exact impact for `hash_provisioned_root`: HIGH; two same-file callers (`build_execution_plan`, `execute_plan`); the hidden cross-file entrypoint import remains an analyzer resolution gap and was checked directly in source.
- Fresh candidate detect-changes: exactly two changed implementation files, no affected process, with the test file's known HIGH topology warning.

The package doctor was run as a native package check with
`python -B scripts/doctor.py --package . --role development --json`. It
returned `ok=false` only for pre-existing package-wide `governance-drift`
entries; those entries are unrelated to ISSUE=56 and were not modified.

## Real Runtime Continuation

Exactly one run used the existing Windows runtime and candidate source
checkpoint. Runner: `.tmp/issue56-real-runner.py`.

```text
REAL_RUNTIME_EXECUTED=YES
REAL_BLENDER_CHILD_SPAWNED=YES
REAL_BLENDER_CHILD_PID=27548
FIREWALL_SEQUENCE_PASS=YES
MPFB_ADDON_INIT_PASS=YES
HUMAN_SERVICE_CREATE_HUMAN_PASS=YES
CHARACTER_CREATED=YES
RIG_AND_SKIN_PASS=YES
GLB_EXPORT_PASS=YES
PROVENANCE_VALIDATION=PASS
GLB_STRUCTURALLY_VALID=YES
FIREWALL_CLEANUP_PASS=YES
```

The child log contains the real addon markers
`MPFB_ADDON_IDENTITY_PRESENT=YES`, `MPFB_GET_PREFERENCE_PASS=YES`, and
`MPFB_REGISTER_PASS=YES`, then reaches the native GLB 2.0 export. The absence
of a child error plus the exported artifact and `GAMEENGINE` provenance bind
the HumanService create/rig/skin stages to the observable result.

Runtime result: `D:\AI\P2P_runtime\mpfb2-runtime-01\logs\p2p-issue56-root-drift-01-result.json`.
Child stdout: `D:\AI\P2P_runtime\mpfb2-runtime-01\logs\p2p-issue56-root-drift-01-stdout.log`.
Supervisor report: `reports/supervisor/rp_supervisor_260902_103800_by_gpt-5-codex_p2p-mpfb2-provisioning-root-drift-01.md`.

```text
OUTPUT_PATH=D:\AI\P2P_runtime\mpfb2-runtime-01\output\issue56-mpfb2\Oak.glb
OUTPUT_SHA256=5f96f86fbfd4cdc01201e767b0383807ac5e2a7a6365252aee568a91a949c0c4
OUTPUT_BYTES=9093808
PROVENANCE_PATH=D:\AI\P2P_runtime\mpfb2-runtime-01\output\issue56-mpfb2\Oak.asset-provenance.json
PROVENANCE_SHA256=d5d50b0bea9dfb096762e566211df4db62be1ed1f7bb47473919a5f9f672f7b7
PROVENANCE_BYTES=1488
```

The output directory contains exactly the two declared files. Independent
validation returned glTF `2.0`, character `Oak`, 55 reachable scene nodes,
`GAMEENGINE`, `MPFB_BUILT_IN_WEIGHTS`, and `STRUCTURALLY_VALID`; independent
provenance schema, recipe binding, CORE_CC0 binding, and GLB hash checks passed.

After the run, the root recomputed to the manifest hash with 526 generated
`.pyc` files still present, all pinned bytes remained equal, active Blender
processes were `0`, and `P2P-MPFB-DENY-*` rule matches were `0`.

Game Truyen before/after:

```text
GAME_TRUYEN_HEAD_UNCHANGED=True
GAME_TRUYEN_STATUS_UNCHANGED=True
GAME_TRUYEN_MUTATIONS=NO
```

## Legacy Fallback Status

No fallback was added. Root hashing does not consult `.gitignore`, broad cache
patterns, or arbitrary runtime state. It uses one exact generated-bytecode
predicate and retains fail-closed behavior for everything else.

## Residual Unverified Surfaces

None for ISSUE=56 root reconciliation and the requested one-run smoke. This
does not claim visual/Golden Character acceptance; that claim is outside this
workstream. The existing package-wide governance doctor drift remains an
out-of-scope repository condition.

## E2E Verification

```text
fresh canonical main + exact pinned archive
  -> complete 526-path delta and pinned-byte proof
  -> bounded hash predicate
  -> manifest root PASS with generated .pyc retained
  -> firewall setup/enforcement PASS
  -> real Blender child 27548
  -> MPFB addon identity/preference/register PASS
  -> HumanService create + GameEngine rig/skin
  -> Oak.glb + provenance sidecar
  -> independent GLB/provenance PASS
  -> firewall cleanup PASS / zero residual rules
```

## Terminal Status

```text
ISSUE=56
ROOT_INTEGRITY_RECONCILED=YES
OVER_ENGINEERING_CHECK=PASS
GAME_TRUYEN_MUTATIONS=NO
TERMINAL_VERDICT=P2P_MPFB2_RUNTIME_SMOKE_PASS
```
