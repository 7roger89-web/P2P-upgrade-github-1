# Coder Report — P2P-SEC01 Security / Reverse Foundation + APKiD

Date: `2026-08-29`
Task: `P2P-SEC01`
Scope: smallest existing-control-plane security/reverse foundation and one
safe local APKiD proof adapter
Candidate: `D:\AI\P2P_dev\P2P-upgrade-github\.tmp\p2p-sec01-canonical`
Candidate implementation commit:
`1a2f458e795e1dd4018d7d77ee5a1ebca6d68bc1`
Candidate implementation tree:
`c8ad589195a7b37a9378e76cd8291d765ef2e472`
Candidate base SHA:
`b8d09fc7a0e4a91e75db7f10dc8cfaea007ba37a`
Candidate base tree:
`91012e41e67a956bbca311368dc51a45e8c0423b`

## Result

The scoped implementation is technically PASS and ready for an independent
Owner Gate. It extends the existing capability model with optional orthogonal
semantic-kind metadata, adds the requested security/reverse IDs to the same
registry, binds five security execution classes into the existing EFF01
orchestration policy, and adds a minimal hash-bound reverse evidence contract.

The APKiD adapter is local-only and safe-readonly: it requires an explicit
local `.apk`, probes only an already-installed executable, invokes an argument
list without shell expansion, parses supported findings, and returns honest
`UNAVAILABLE`, `UNKNOWN`, or `REJECTED` states. APKiD is not installed and no
real smoke was possible because the binary is unavailable locally.

No second registry, router, orchestrator, risk engine, truth store, or
verification framework was introduced. No external target, credential,
device/emulator, network, bypass, exploit, mutation, promotion, release,
deployment, or live activation occurred.

## Authority reconciliation

- Fresh official `origin/main`: `b8d09fc7a0e4a91e75db7f10dc8cfaea007ba37a`
- Fresh official tree: `91012e41e67a956bbca311368dc51a45e8c0423b`
- Root checkout: invalid `.git/HEAD`; preserved and not repaired.
- Existing canonical/runtime checkout: dirty; preserved and not used as the
  editable subject.
- SEC01 branch descends directly from the fresh official SHA.
- C41: existing pilot/baseline-release lineage, explicitly not this security
  subject.
- C42: existing framework/release disclosure and goal-closure boundary labels;
  no security/reverse subject.
- No C41/C42 identifier is reused.

## Implemented surface

- `.p2p/system/p2p_capabilities/model.py`
  - Preserves the authoritative six `TYPE` classes.
  - Adds optional validated `SEMANTIC_KIND`: `SKILL`, `TOOL`, `ADAPTER`,
    `VENDOR`, `EXTERNAL_RUNTIME`, `KNOWLEDGE_SOURCE`.
  - Keeps canonical identities and denominator at eight / `8/8`.
- `.p2p/system/p2p_capabilities/orchestration_policy.py`
  - Adds `execution_class`, `target_authorized`,
    `controlled_test_environment`, and `explicit_task_authority` to the
    existing `TaskProfile`.
  - Keeps the existing FAST/STANDARD/STRICT/CRITICAL lanes.
  - Active and offensive classes fail closed without required authority;
    destructive/intrusive is denied by default.
- `.p2p/system/p2p_capabilities/security_contract.py`
  - Provides the shared security evidence envelope, artifact identity, finding
    categories, and reverse `DECOMPILED_OUTPUT` vs
    `RECONSTRUCTED_SEMANTICS` contract.
  - Reconstruction requires evidence refs, backend identity, semantic label,
    confidence, and uncertainty; insufficient evidence is `UNKNOWN`.
  - Original source recovery is explicitly not claimed.
- `.p2p/system/p2p_capabilities/apkid_adapter.py`
  - Uses existing `BackendAdapterIdentity`/health conventions.
  - Provides `dependency_status`, `analyze`, and the adapter-pattern `execute`
    alias.
  - Normalizes APKiD packer, protector, compiler, and obfuscator lines.
  - Binds artifact SHA-256 and output SHA-256 evidence references.
- `capabilities.json`
  - Registry is valid at 39 unique entries: existing 27 plus the 12 requested
    security/reverse IDs.
  - APKiD is the one active `BACKEND_PROVIDER` / `ADAPTER` capability;
    future tools remain `DISCOVERED` or catalog-only.
- `manifest/external-sources.json`
  - Extends the existing external-source catalog with 10 Phase 1 entries.
  - Every entry is non-vendored, install-disabled, non-network, credential-free,
    and not executed.
- `__init__.py` exports the foundation contract and APKiD adapter through the
  existing package surface.

## Invariant Family Map

| Invariant family | Existing owner | SEC01 change | Evidence | Result |
|---|---|---|---|---|
| Capability class/schema | `model.py` / capability registry | Optional semantic metadata only | Registry load + SEC01 test | PASS |
| Routing | existing `routing.py` / UIUX router | Trigger metadata only | Single-router selection test | PASS |
| Orchestration/risk | `orchestration_policy.py` / EFF01 | Execution-class fields and gate | SEC01 + EFF01 tests | PASS |
| Evidence/trust | existing evidence/trust contracts | Minimal security/reverse result envelope | Reverse contract tests | PASS |
| Backend seam | `backend_contract.py` | APKiD uses identity/health conventions | Adapter tests | PASS |
| External-source policy | `manifest/external-sources.json` | Additive catalog only | Catalog assertions | PASS |
| Canonical quorum | existing canonical eight | No change | Registry result and foundation tests | PASS |
| Owner/promotion boundary | existing governance policy | Candidate remains unpromoted | Git history/status and plan | PASS |

## Siblings and adjacent surfaces checked

- Current capability model/registry and `routing.py` were inspected before
  editing; no duplicate ID or second router was found.
- Existing `backend_contract.py`, `backend_execution_bridge.py`, and vendor
  policy were inspected; APKiD does not create an adapter registry or provider
  installation path.
- Existing C18/EFF01 policy and its frozen adaptive matrix were inspected;
  new fields preserve all existing focused behavior.
- C41/C42 records were searched and classified as historical/non-security
  lineage; they were not used as IDs or authority.
- Release/v5/immutable baseline, user projects, invalid root Git metadata, and
  dirty canonical/runtime worktree were preserved.

## Fallback status

- No provider/tool fallback was used.
- No simulated APKiD success was used.
- The controlled fake runner exists only inside deterministic tests and cannot
  change the production/runtime dependency result.
- Real APKiD availability: `NOT_AVAILABLE`; no installation attempted.

## Focused validation

| Command / check | Result |
|---|---|
| `python -m unittest tests.test_p2p_sec01_security_reverse_apkid` | 8/8 PASS |
| `python -m unittest tests.test_p2p_capability_foundation` | 28/28 PASS |
| `python -m unittest tests.test_p2p_eff01_execution_efficiency tests.test_p2p_adaptive_orchestration` | 13/13 PASS |
| `python -m unittest tests.test_p2p_aesthetica_selective_routing` | 7/7 PASS |
| Registry JSON parse + `load_registry` | PASS; 39 unique entries |
| Static `compile()` of five changed Python modules | PASS |
| `git diff --check` | PASS |
| `Get-Command apkid` | `NOT_AVAILABLE`; no smoke/install |
| Broad repository regression | NOT RUN by explicit user ceiling |
| Anvien | NOT RUN by explicit user ceiling |

The fresh-main baseline foundation test had a pre-existing stale count
expectation (`16` while the current registry was already `27`). The focused
test was updated to the current 39-entry registry after the SEC01 behavior was
implemented; no unrelated registry consumer was changed.

## Test evidence by requirement

- Semantic-kind invalid value fails closed: PASS.
- All 12 requested IDs are present once: PASS.
- Existing router selects APKiD without a router-agent: PASS.
- Active class without target/environment authority: BLOCKED: PASS.
- Active class with both required flags: ALLOWED by policy: PASS.
- Offensive class without explicit task authority: BLOCKED: PASS.
- Destructive class with all flags: BLOCKED by default: PASS.
- Decompiled output and semantic reconstruction are distinct: PASS.
- Insufficient reconstruction evidence is `UNKNOWN`: PASS.
- Missing APKiD dependency is `UNAVAILABLE`, never `PASS`: PASS.
- Packer/protector/compiler/obfuscator normalization: PASS.
- Local APK hash/mtime preservation: PASS.
- Adapter-observed artifact mutation: `REJECTED`: PASS.

## Residual boundary

Scoped residual defects: none found in the allowed surface.

Explicitly unverified by scope and therefore not claimed:

- Real APKiD binary smoke, because it is not locally available.
- Apktool, JADX, bundletool, MobSF, Frida, Ghidra, native/managed candidate
  execution, emulator/device behavior, active/offensive testing, and network
  inspection.
- Full security stack, broad repository regression, package/release rebuild,
  host certification, Owner approval, promotion, release, deployment, and live
  activation.

## Candidate stop

The implementation candidate is technically ready for the separate Owner Gate.
`CANONICAL_PROMOTED=false`. No Owner approval was inferred or performed.
