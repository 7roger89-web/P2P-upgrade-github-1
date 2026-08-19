# P2P-FW01 Bootstrap Recovery & Truth Reconciliation — Terminal Report

**GOAL_ID:** P2P-FW01 Bootstrap Recovery & Truth Reconciliation (Framework-01 lineage only)
**GOAL_TERMINAL_STATUS:** RECONCILED — contradiction mechanically resolved, failure class determined, design ported onto authoritative lineage
**AUTHORITATIVE_P2P_BRANCH:** `p2p-framework-01-autonomous-operating-loop` — `ad5c39d927d3034261ea3ade5fcdb06cd7af6b79`
**AUTHORITATIVE_FW01_RELEASE_COMMIT:** `a91e115a9cda0bf4aef2fb2b21c096b5a196adfd` (tag `p2p-8.4.7-C-codex.24-fw01-v1`, asset 520387867, SHA `eb396dc1…3d7d`, owner approval `P2P-APR-20260819T043000Z-fw01-promote-release`)
**AUTHORITATIVE_VALIDATOR_COUNT:** 78/78 PASS, 0 failed (`ad5c39d`; also 78/78 on `4156fa8`)
**FINAL_HEAD:** `073a10fd7ad3ddec0b302d6f77a82fedd3bd11ae` (local branch `p2p-fw01-bootstrap-reconciliation` off `ad5c39d` — **NOT pushed**)
**FAILURE_CLASS:** E — DOCTOR_PATH_RESOLUTION_BUG (contributing: D, package-layout mismatch)
**NEW_UNEXPLAINED_FAILURES:** 0 — every observed FAIL is machine-recorded and explained
**CONSTRAINTS OBSERVED:** no FRAMEWORK-02, no Canonical Council / Gate J, no project pushes, no re-mint, no C34 branch declared canonical, no history rewrite, no merge of C34 history, no artifact alteration.

## 1. Repository truth resolution

Inspection of all local/origin branches, PR #18/#19, the FW01 release tag, the Development Charter, `development-control.json`, and candidate/release records resolves the lineage question mechanically rather than by declaration.

| Field | Value |
| --- | --- |
| AUTHORITATIVE branch | `p2p-framework-01-autonomous-operating-loop` |
| AUTHORITATIVE HEAD | `ad5c39d927d3034261ea3ade5fcdb06cd7af6b79` |
| FW01 release commit | `a91e115a…` (tag `p2p-8.4.7-C-codex.24-fw01-v1`); finalize gates PASS at `4156fa8`; PROMOTE+RELEASE at `ad5c39d` |
| Validator | 78/78 PASS on `ad5c39d` and `4156fa8` |
| PR #18 | open, `p2p-framework-00-product-memory` (head `33aa50b`, base `p2p-c40-project-usable-release-pilot`) |
| PR #19 | open, `p2p-framework-01-autonomous-operating-loop` (head `ad5c39d`, base `p2p-framework-00-product-memory`) |

The `p2p-c34-real-backend-contract-validation` branch (C25–C34 lineage) predates the framework lineage and is **not** part of it; it is not declared canonical. It existed only as the head the previous session worked on.

## 2. C34 bootstrap commit classification

| Commit | Classification | Rationale |
| --- | --- | --- |
| `9fb9c1a` manifest + harness | REUSABLE | No equivalent exists in the FW01 branch; design survives against the authoritative tree and artifact |
| `b43d831` flat/nested artifact layout detection | REUSABLE | Genuine portable bug-fix found against the real artifact |
| `00fec85` preflight + doctor-status | REUSABLE_WITH_CORRECTION | Code valid and prediction correct; diagnosis reclassified (see §4) |
| `0ed9d69` roadmap FW01 row | STALE | Superseded by this reconciliation |
| `35ebc33` terminal report | STALE | Superseded by the reconciled verdict |

The reusable designs were **recreated** as new files on the authoritative lineage — no cherry-pick, no rebase, no merge of C34 history, no history rewrite.

## 3. Mechanical contradiction reproduction (artifact SHA `eb396dc1…3d7d`)

A genuinely clean workspace (`/tmp/fw01-repro`, no P2P-repo involvement) tested the published asset on two independent paths.

| Record | Value |
| --- | --- |
| CANONICAL_INSTALL_RC | **1** — `install.sh` fails at its doctor step: `"Live Specs technical preview report is missing"`; release marker NOT written (fail-closed, no half-install) |
| CANONICAL_DOCTOR_STATUS | rc 1, `RESULT: FAIL` (single failure: preview missing) |
| BOOTSTRAP_PREFLIGHT_RC | **1** — preflight correctly predicts the same defect |
| BOOTSTRAP_DOCTOR_STATUS | rc 1, `UNHEALTHY` |
| Lock file | `governance/live-specs.lock.json` — byte-identical in artifact and authoritative tree |
| `technical_report` | `/home/ubuntu/p2p-repo/docs/p2p-development/research/release-gates-20260818/technical-preview.json` (absolute dev path) |
| Path-resolution code | `scripts/p2p_governance.py` (~576): absolute reference used as-is, relative resolved against `governance/`; requires existence + `sha256` match + schema + **deterministic re-projection equality** |
| Package layout | flat: `governance/` (incl. rev-2 preview `e0fad269…`), `scripts/`, `.agents/`, `.codex/` references, `source/`, `runtime/`; install/doctor CWD = package root |

Decisive controlled test: placing the rev-3 preview file (authoritative tree `docs/p2p-development/research/release-gates-20260818/technical-preview.json`, hash `e96a1d5b…`, **matches the lock**) at the lock's absolute path made doctor **rc 0 PASS**; removing it made doctor **rc 1 FAIL** — all other state identical. The rev-3 preview is versioned in the repo tree but **not packaged**; the packaged rev-2 preview is a different document that can never satisfy the lock's hash or drift keys.

## 4. Real failure class and path semantics

**E — DOCTOR_PATH_RESOLUTION_BUG** (contributing: D). The canonical installer copies `governance/` verbatim without rebinding the lock's absolute `technical_report`/`approval_record` references; path resolution accepts absolute paths with no fallback; the release machinery did not relativize at mint. This is **not** A (payload is intact and self-consistent) and **not** B (the bootstrap preflight prediction was correct, not a false positive). The earlier C34 diagnosis "upstream mint defect" was an over-broad label for this same root cause. The authoritative FW01 pilot recorded doctor HEALTHY because its environment (a machine holding the P2P repo checkout) satisfied the absolute path — the pilot's "fresh project clones" were fresh-**project**, not fresh-**machine**.

Live-specs path semantics: `technical_report` is a **normative runtime dependency** of the lock-runtime gate — neither provenance-only, nor ignored, nor auto-relativized, nor remapped by the installer.

## 5. Entry contract classification

`ENTRY_CONTRACT_VERSION: codex-project-agents/1` is **not** an existing P2P schema in either repository (no match outside the bootstrap doc itself). It is reclassified as a **legacy compatibility alias**: it names the Codex-class host presentation surface, not a P2P authority. The bootstrap's actual authority (release SHA binding, manifest truth, harness determinism) remains provider-neutral, model-neutral, backend-neutral; the harness calls no provider-specific API. P2P bootstrap authority is provider-neutral. No redesign STOP required; the alias is documented in the ported manifest.

## 6. Project integration diffs

| Project | Proposed diff | Canonical remote HEAD | Valid? |
| --- | --- | --- | --- |
| Game Truyện | `b0e6deb5` (additive +1 manifest) | `354203ee7c23a2b349e81a0254b537da4d9c622f` (== commit base, remote unpushed and unchanged) | VALID |
| Gia Phả | `34345485` (additive +2 files; repo had no gitignore) | `130da38fd5a7dd51723dc36709f9bdac0d99ea11` (== commit base, remote unpushed and unchanged) | VALID |

Both bases are identical to the heads recorded in the authoritative `fw01-pilot-evidence.json`. No Supabase/RLS mutation in either diff. **Both remain proposals — still not pushed per gate.**

## 7. Authority migration result

Bootstrap design ported onto authoritative lineage as commit `073a10f` on local branch `p2p-fw01-bootstrap-reconciliation` (base `ad5c39d`): recreated `docs/p2p-development/P2P-PROJECT-BOOTSTRAP.md`, `scripts/p2p-bootstrap.sh`, and the reconciliation research record. No C34 parent linkage; no rewrite; no push.

## 8. Reconciliation test suite

| Test | Result |
| --- | --- |
| Validator (authoritative branch, 78 checks) | 78/78 PASS, 0 failed |
| `p2p_development_control.py validate` | PASS |
| Canonical installer on clean workspace | rc 1, fail-closed, no half-install |
| Canonical doctor (no preview) | rc 1 FAIL (preview missing) |
| Doctor **with** preview at lock path | rc 0 PASS |
| Bootstrap preflight | rc 1 — correct prediction |
| Negative fail-closed suite | 10/10 PASS (T3 re-verified in clean `env -i`: rc 3 as designed) |
| Determinism | PASS (identical runs) |
| Regression differential (C34 vs auth) | Validator byte-identical; harness identical; manifest differs only in alias classification + corrected class-E diagnosis (deliberate, documented) |
| Gitleaks (3 reconciled files) | no leaks |
| NEW_UNEXPLAINED_FAILURES | 0 |

## 9. Minimal release correction (owner-authorized, not minted here)

Install-time rebinding: the installer should re-point the installed lock's `technical_report`/`approval_record` to package-relative copies of the exact rev-3 documents and re-derive the lock deterministically; or package the rev-3 preview alongside `governance/` with the reference relativized. Impact if minted: one deterministic rebuild candidate, new tag/release, regression re-run on the new artifact only; the existing tag and its evidence remain historically accurate for the environment in which they were proven.

> **Disclosure (added 2026-08-19, self-contained patch track):** fresh-machine testing of the v1 artifact additionally exposed a second defect in the same release: the packaged `source/` layout does not match the frozen `source-inventory.json` baseline (152/152 files mismatched), the supplemental catalog fails its locked hash, and the EXT-0002 catalog snapshot hash differs. The v1 `doctor_canonical` gate passed at mint only against the staged source, so the published artifact is **not self-validating on a fresh machine** and its `EXTERNAL_DEV_PATH_DEPENDENCY` cannot be certified 0. Both defects are closed in candidate `p2p-8.4.7-C-codex.24-fw01-self-contained-patch-candidate-v2.zip` (SHA `2a42e815…9e61`), which achieves `CANONICAL_INSTALL=PASS` and `DOCTOR=HEALTHY` with `EXTERNAL_DEV_PATH_DEPENDENCY=0` on a genuinely fresh machine. The v1 release is not re-minted; it remains historically accurate for its proven environment and carries this disclosure.

## 10. Terminal verdict

**RECONCILED / E (DOCTOR_PATH_RESOLUTION_BUG).** The artifact is mechanically sound; the failure is a path-resolution design bug that makes doctor environment-contingent. The bootstrap design is REUSABLE and now lives on the authoritative lineage. Owner gates remain: push the GT/GP integration proposals, and authorize the release rebinding correction. The goal ends here — no FRAMEWORK-02, no push, no re-mint.
