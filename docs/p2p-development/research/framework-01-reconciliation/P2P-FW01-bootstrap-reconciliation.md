# P2P-FW01 Bootstrap Recovery & Truth Reconciliation

*Reconciliation goal only. No FRAMEWORK-02, no Canonical Council / Gate J, no project pushes, no re-mint, no history rewrite.*

## 1. Authoritative lineage (repository evidence)

Inspection of all local/origin branches, PR #18/#19, the release tag, the charter, development-control, and candidate/release records resolves the lineage question mechanically. The later P2P development lineage that completed FRAMEWORK-00/FRAMEWORK-01, release readiness, promotion, and release is authoritative.

| Field | Value |
| --- | --- |
| AUTHORITATIVE_P2P_BRANCH | `p2p-framework-01-autonomous-operating-loop` |
| AUTHORITATIVE_P2P_HEAD | `ad5c39d927d3034261ea3ade5fcdb06cd7af6b79` |
| AUTHORITATIVE_FW01_RELEASE_COMMIT | `a91e115a9cda0bf4aef2fb2b21c096b5a196adfd` (tag `p2p-8.4.7-C-codex.24-fw01-v1`; finalize gates PASS on `4156fa8`; owner PROMOTE+RELEASE at `ad5c39d`, approval `P2P-APR-20260819T043000Z-fw01-promote-release`, asset 520387867) |
| AUTHORITATIVE_VALIDATOR_COUNT | 78/78 (0 failed) on `ad5c39d`; `4156fa8` also 78/78 |
| PR #18 | open, `p2p-framework-00-product-memory` (head `33aa50b`), base `p2p-c40-project-usable-release-pilot` |
| PR #19 | open, `p2p-framework-01-autonomous-operating-loop` (head `ad5c39d`), base `p2p-framework-00-product-memory` |

The `p2p-c34-real-backend-contract-validation` branch (C25–C34 lineage) predates and is **not** part of the framework lineage; the bootstrap work was performed there only because that branch was the head the previous session worked on, not because it is canonical. It is not declared canonical.

## 2. Classification of the C34 bootstrap commits

| Commit | Classification | Rationale |
| --- | --- | --- |
| `9fb9c1a` (canonical manifest + harness) | REUSABLE | No equivalent exists in the FW01 branch; design survives against the authoritative tree and artifact (manifest schema `p2p-project-bootstrap/1`; harness paths match the released asset layout) |
| `b43d831` (flat/nested artifact layout detection) | REUSABLE | Genuine bug-fix discovered while testing the real artifact; portable |
| `00fec85` (preflight detection of the preview-path defect, doctor-status) | REUSABLE_WITH_CORRECTION | The preflight correctly predicted the failure; its "upstream mint defect" label is reclassified (see §4) — the code remains valid, the diagnosis is corrected |
| `0ed9d69` (roadmap FW01 row) | STALE | Written against the C34-local view; superseded by this reconciliation |
| `35ebc33` (terminal report PARTIAL/mint-defect) | STALE | Terminal verdict based on the pre-reconciliation diagnosis; superseded by the reconciled verdict below |

Cherry-pick was not used. The reusable designs were recreated as new files on the authoritative lineage (copy of content, no C34 parent linkage), preserving both histories. The C34 branch history was not rewritten and nothing was merged from it.

## 3. Artifact contradiction — mechanical reproduction (SHA `eb396dc1…3d7d`)

A genuinely clean workspace (`/tmp/fw01-repro`, no P2P repo involvement) was used with the same published asset, tested on two paths separately.

| Record | Value |
| --- | --- |
| CANONICAL_INSTALL_RC | **1** — `install.sh` fails because its doctor step fails (`"Live Specs technical preview report is missing"`); release marker NOT written (fail-closed, no half-install) |
| CANONICAL_DOCTOR_STATUS | rc 1, `RESULT: FAIL`, single failure: preview missing |
| BOOTSTRAP_PREFLIGHT_RC | **1** — harness preflight (lock inspection before install) reports the same preview-missing defect |
| BOOTSTRAP_DOCTOR_STATUS | rc 1, `UNHEALTHY` |
| Lock file used | `governance/live-specs.lock.json` (both artifact and authoritative tree are byte-identical) |
| Preview field | `technical_report: /home/ubuntu/p2p-repo/docs/p2p-development/research/release-gates-20260818/technical-preview.json` (absolute) |
| Path-resolution code | `scripts/p2p_governance.py` (~line 576): absolute reference used as-is; relative reference resolved against `governance/`; requires existence, `sha256` match, schema match, and **deterministic re-projection equality** against the installed package's own `fact-ledger.json` |
| Package layout | flat: `governance/` (incl. `live-specs-preview-report.json` = rev 2 Aug-09 snapshot, SHA `e0fad269…`), `scripts/`, `.agents/`, `.codex/` references, `source/`, `runtime/` |
| Install/doctor CWD | package root; project root passed via `--root` |

Decisive controlled test: placing the **rev-3 preview file** (authoritative tree `docs/p2p-development/research/release-gates-20260818/technical-preview.json`, SHA `e96a1d5b…`, hash matches the lock) at the lock's absolute path made doctor **rc 0 PASS**; removing it made doctor **rc 1 FAIL**. All other state identical. The preview file is versioned in the authoritative tree and matches the lock; the packaged preview is a different (older) document that can never satisfy the lock's hash or drift keys.

## 4. Real failure class

**E — DOCTOR_PATH_RESOLUTION_BUG** (contributing: D, PACKAGE_LAYOUT_INTERPRETATION_MISMATCH).

The canonical installer + canonical doctor **do** reproduce the failure on a clean workspace, so this is not merely a C34 semantics artifact; but it is not a payload/integrity defect (A) either — the package is intact and self-consistent. The bug: the released lock embeds a mint-time absolute dev-machine path for `technical_report` (and `approval_record`), the canonical installer copies `governance/` verbatim without rebinding those references to package-relative copies, and path resolution accepts the absolute path with no fallback. The authoritative FW01 pilot recorded doctor HEALTHY because its environment (the machine holding the P2P repo checkout) satisfied the absolute path — the pilot's "fresh project clones" were fresh-project but **not** fresh-machine-isolated. The earlier C34 report's "upstream mint defect" label was an over-broad diagnosis of this same root cause; the corrected diagnosis is E. The prior bootstrap-harness BLOCKED report was a correct prediction, not a false positive (not B).

Live-specs path semantics answer: the `technical_report` field is a **normative runtime dependency** of the lock-runtime gate — it is neither provenance-only, nor ignored, nor automatically relativized at install, nor remapped by the canonical installer.

## 5. Entry contract provider-neutrality

`ENTRY_CONTRACT_VERSION: codex-project-agents/1` in the bootstrap manifest is **not** an existing P2P schema (no match in either repository outside the bootstrap doc itself). It is classified as a **legacy compatibility alias**: it names the host presentation surface a Codex-compatible agent uses to load the project entry contract, not a P2P authority. The bootstrap's actual authority (release SHA binding, manifest truth, harness determinism) is provider/model/backend neutral, and the harness does not call any Codex-specific API. P2P bootstrap authority remains provider-neutral. No redesign STOP required; the alias is documented as such in the reconciled manifest header.

## 6. Project integration diffs

| Project | Proposed diff | Remote HEAD check | Status |
| --- | --- | --- | --- |
| Game Truyện | `b0e6deb5` (additive +1 manifest, no source mutation) | Base `354203ee` == origin HEAD; remote unpushed, unchanged | Diff still VALID against canonical remote HEAD |
| Gia Phả | `34345485` (additive +2 files; repo had no gitignore) | Base `130da38f` == origin HEAD; remote unpushed, unchanged | Diff still VALID against canonical remote HEAD |

Both bases are identical to the heads recorded as baselines in the authoritative `fw01-pilot-evidence.json`. No Supabase/RLS mutation in either diff. Both remain proposals only — still not pushed per the gate.

## 7. Authority migration

The bootstrap design remains valid, so it has been ported onto the authoritative lineage as **new commits on a local branch** (`p2p-fw01-bootstrap-reconciliation` off `ad5c39d`): recreated manifest `docs/p2p-development/P2P-PROJECT-BOOTSTRAP.md`, harness `scripts/p2p-bootstrap.sh`, and this reconciliation record. No C34 history merged; no rebase of C34 commits; no history rewrite; no artifact alteration; no new release published. The FW01 design docs (framework docs) remain authoritative; the bootstrap design supplements them.

## 8. Minimal release correction (no re-mint in this goal)

Install-time or mint-time rebinding: the canonical installer should, at install, re-point the installed lock's `technical_report` and `approval_record` to **package-relative copies** of the exact documents (rev-3 preview, approval record) and re-derive the lock deterministically — or the release machinery should package the rev-3 preview alongside `governance/` with the lock's absolute reference relativized. Impact if minted: one deterministic rebuild candidate, new tag/release, regression re-run on the new artifact only; existing tag `p2p-8.4.7-C-codex.24-fw01-v1` and its evidence remain historically accurate for the environment in which they were proven. Owner authorizes separately.
