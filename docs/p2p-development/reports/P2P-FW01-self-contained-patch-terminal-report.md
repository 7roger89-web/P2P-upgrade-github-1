# P2P-FW01 Self-Contained Release Patch — Terminal Report

**Goal ID:** FW01 (self-contained release patch track)
**Date:** 2026-08-19
**Verdict:** PATCH_MINTED / HEALTHY_ON_FRESH_MACHINE / UNPROMOTED
**Failure class resolved:** E (DOCTOR_PATH_RESOLUTION_BUG) + package-layout inventory defect
**Closure gate:** OWNER_PATCH_RELEASE_GATE (open)
**Lineage:** branch `p2p-framework-01-autonomous-operating-loop` @ HEAD `56e99ca` (local, not pushed)

## 1. Objective

Make the FW01 release **self-contained**: a genuinely fresh machine (no development paths, no P2P source checkout) must achieve `CANONICAL_INSTALL=PASS` and `DOCTOR=HEALTHY` from the packaged artifact alone, with `EXTERNAL_DEV_PATH_DEPENDENCY=0`. The fix is implemented **in the mint machinery** (not post-hoc rewrites of the artifact), preserves fail-closed semantics, and produces exactly **one unpromoted candidate** via the canonical candidate policy — never re-minting or replacing the existing tag `p2p-8.4.7-C-codex.24-fw01-v1` or its evidence.

## 2. Root causes verified (mechanically, on clean workspaces)

The v1 artifact failed `doctor` on fresh machines for two independent mint-machine defects, both reproduced and diagnosed by machine:

1. **Path resolution (class E, from the reconciliation track).** The release mint machine's lock (`governance/live-specs.lock.json`) recorded `technical_report` as an absolute path on the mint machine (`/home/ubuntu/p2p-repo/.../technical-preview.json`, SHA `e96a1d5b…`). The rev-3 preview exists in the authoritative tree but **was not packaged**; the canonical installer copies `governance/` verbatim with no rebinding and no fallback. Decisive test: presence of the preview at the lock path is the single difference between `doctor` rc 0 and rc 1.
2. **Package-layout inventory defect (new).** The packaged `source/` files do not match the frozen baseline `source-inventory.json` (152/152 mismatched), the supplemental catalog fails its locked hash, and the EXT-0002 catalog snapshot hash differs — so even after fixing (1), the stock `doctor` still failed three checks on the stock artifact. This defect exists **in the original mint artifact itself**; the mint-time `doctor_canonical` gate passed only because it ran against the staged source (which matched at mint time) and the inventory/regeneration was never re-derived against the actually packaged layout.

## 3. Fix implemented (mint machinery, `scripts/fw01_patch_mint.py`, inserted into `scripts/package_release.py` build flow)

| # | Fix | Property |
|---|-----|----------|
| 1 | Stage the rev-3 technical preview into `governance/release-evidence/technical-preview.json` and rebuild the live-specs lock via `build-live` with `--as-of` from the existing lock — the lock already relativizes references when the preview sits under `governance/` | Relative refs, SHA-bound (lock references file hash), deterministic rebuild |
| 2 | Regenerate `source-inventory.json` and `source/supplemental-checksums.json` against the actually packaged files | Closes the inventory/catalog defects |
| 3 | `doctor.py` supplemental check reads the mint-written `governance/supplemental-checksums.json` when present (fail-closed legacy fallback) | No weakened lock-runtime semantics; schema-bound |
| 4 | Drift policy: longest-prefix scope matching in `scan_volatile` + `docs/` prefix scope classified `P` (host-project evidence); `package.json` also scoped | Host-project source docs can no longer be misflagged as unledgered P2P volatile claims |
| 5 | Runtime portability: `.p2p/system/p2p_capabilities/p2p_fw01_live.py` key resolution is env-first with auto-detected evidence dir (same honest-gate behavior) | Removes the one genuine runtime dev-path dependency |
| 6 | Zip entry mtime normalization in `package_release.py` | Deterministic artifact bytes per build |
| 7 | Harness `scripts/p2p-bootstrap.sh`: restore executable bits on installed runtime scripts after zip extraction (zip strips +x; previously misread as corrupt runtime) | Correctness of fresh-clone certification |

All fixes are fail-closed: nothing silently proceeds when a precondition is unmet; nothing in `lock-runtime` semantics was weakened.

## 4. Candidate

Exactly **one** candidate, minted through the canonical machinery on the authoritative branch:

`P2P-8.4.7-C-codex.24-fw01-self-contained-patch-candidate-v2.zip` — SHA-256
`2a42e815ca44fbecce4d8f35a641529e8cad028f07dccc5800bae00e3f509e61`
Status: **UNPROMOTED**. The existing v1 tag/release is untouched. Promotion awaits OWNER_PATCH_RELEASE_GATE.

## 5. Fresh-machine proof (v2 artifact)

On a genuinely fresh workspace (`env -i`, `HOME` only, no `/home/ubuntu/p2p-repo`, no env overrides except the certification asset URL): `CANONICAL_INSTALL=PASS`, `DOCTOR=HEALTHY` (all checks including `installed-foundation` 8/8, decision trace bound), `EXTERNAL_DEV_PATH_DEPENDENCY=0`. The four remaining absolute-path-bearing files (two approval records, `development-control.json`, the packaged preview) are hash-bound governance content whose absolute paths are narrative provenance, never runtime-resolved; they are classified and excluded from the runtime dependency count, recorded honestly in evidence.

## 6. Fresh-clone certification (GT + GP, candidate v2)

Both projects were certified with the proposed integration manifests rebound to the v2 candidate (certification-run local binding; production binding awaits the owner gate): real fresh clone via `file://`, discover → verify SHA (`RELEASE_SHA_BINDING=VERIFIED`) → install → `DOCTOR=HEALTHY` → idempotent reinstall → runtime rollback with manifest preserved → reinstall. GP: mutation audit `0` tracked changes, Supabase present, no RLS migration touched. GT: the only tracked change is `AGENTS.md`, which the canonical installer **deliberately merges/rewrites** as the native-entry contract surface; the merge repaired the pre-existing mojibake double-encoding in GT's AGENTS.md and normalized one quote — installer-owned surface, disclosed, not suppressed. No push to any project repository.

## 7. Validation gates

| Gate | Result |
|------|--------|
| Negative fail-closed suite (v2) | **10/10 PASS** — includes T7: the v1 artifact remains BLOCKED (rc 7), proving the correction only ships with v2 |
| Determinism | Identical install output bytes across runs |
| Fresh-machine simulation | PASS, `EXTERNAL_DEV_PATH_DEPENDENCY=0` |
| Validator (authoritative branch, incl. new files) | **78/78 PASS** |
| `p2p_development_control.py validate` | PASS |
| gitleaks (fw01_patch_mint.py, p2p-bootstrap.sh, p2p_governance.py scan region) | no leaks |
| Regression differential vs P2P-C34 branch | Only intended diffs: exec-bit restore (bootstrap), prefix scope (governance), diagnosis→resolution text (manifest) |
| Candidate verification | SHA/integrity verified; relative refs confirmed; zero runtime dev-path deps |
| **NEW_UNEXPLAINED_FAILURES** | **0** |

## 8. Terminal verdict

**PATCH_MINTED / HEALTHY_ON_FRESH_MACHINE / UNPROMOTED.** The self-contained patch candidate v2 closes both v1 mint defects mechanically, is verified self-contained on a genuinely fresh machine, certified on both target projects, and passes every gate. The decision to publish the tag/release and bind production manifests rests with the owner at the OWNER_PATCH_RELEASE_GATE; the goal ends here — no FRAMEWORK-02, no push, no promotion.
