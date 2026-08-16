# Coder Report: P2P reusable release packaging

## Scope

Finalize the current verified development tree as the next reusable package,
`8.4.6-C-codex.5`, without changing the already-PASS Goal subsystem or replacing
any existing governance, Eval, RAG, Approval, Drift, Quorum, or Ledger authority.

## Invariant Family Map

| Family | Authority / SSOT | Sibling surfaces checked | Forbidden fallback | Verification |
|---|---|---|---|---|
| Release identity | `VERSION`, `manifest/package.json`, `manifest/build-report.json` | `docs/AI-HANDOFF.md`, release notes, package manifest | inventing a second version scheme or changing immutable `8.4.6-C` baseline | metadata consistency and final manifest |
| Distributable boundary | `scripts/package_release.py` allowlist and release manifest | package wrappers, doctor-required paths, runtime lock, source inventory | archiving the development root or shipping `.tmp`, reports, plans, scratch, project state | extracted verify, ZIP exclusion scan, SHA-256 inventory |
| Install classification | package `VERSION` plus `.p2p/system/release.json` | PowerShell installer, shell installer, backup paths, doctor invocation | guessing upgrade state or overwriting project templates | fresh, `.4 -> .5`, same-version fixture assertions |
| Project-state preservation | project `.p2p` state outside `.p2p/system` | FACT/Live fixture state, evals, policy, approvals, ledger, CAPSULE, status, Goal, trusted evidence | replacing project state with package governance/templates | before/after file-hash snapshots and no duplicate governance assertions |
| Existing governance/runtime | existing FACT_LEDGER, Live Specs, Eval, RAG, Approval, Drift, Quorum, Ledger, doctor | installed system scripts/governance and workflow entrypoints | introducing a parallel control system or hardening Goal again | package doctor, drift, 19-test regression suite, installed workflow |

## Source-level implementation

- `VERSION`, `manifest/package.json`, `manifest/build-report.json`: advanced the
  existing `.4` convention to `.5` and aligned release metadata.
- `RELEASE-NOTES.md`, `BAT-DAU.md`, and `docs/AI-HANDOFF.md`: added the concise
  reusable-release handoff and beginner three-step natural-language entry path.
- `scripts/package_release.py`: added the explicit runtime/package allowlist,
  exclusions, release manifest, content hashes, checksum inventory, extracted
  verification, package doctor gate, and package drift gate.
- `scripts/package.ps1` and `scripts/package.sh`: delegate to the shared builder
  and refuse implicit whole-tree archives.
- `install.ps1` and `install.sh`: read package identity, classify fresh,
  already-initialized, legacy, upgrade, and same-version installs, preserve
  project state, keep system backups, and write a marker only after doctor PASS.
- `governance/drift-policy.json`: excludes development plan/report paths from the
  protected runtime lock so they can remain outside the reusable release.
- `tests/test_p2p_release_packaging.py`: safe ZIP, fresh, upgrade, reinstall,
  state-preservation, evidence-reuse, doctor, and drift acceptance coverage.

Legacy fallback status: no alternate Goal or governance subsystem was added; all
existing P2P runtime authorities remain the source of truth.

## Verification

- Final artifact: `D:\AI\P2P_dev\P2P-8.4.6-C-Codex-Edition-v5.zip`.
- Package version: `8.4.6-C-codex.5`.
- Artifact SHA-256: `0c5db0f90480c4668db9bf1c2a7226e86b039bc10281e93619e193ea6e0be44b`.
- Artifact size: `2,217,368` bytes; release content `342` files; checksums `343`.
- Archive manifest/checksum/exclusion test: PASS; `344` archive entries, no
  forbidden development/project paths, no `.pyc`/`.pyo`, no Logistics-specific
  state, and no suspicious credential filenames/content.
- Extracted release verification: PASS; `package_release.py verify`.
- Extracted package doctor: PASS; 22 skills, eight agents, source inventory,
  manifests, and governance checks all pass.
- Extracted package drift: PASS; no failures or warnings.
- Windows PowerShell fixture: fresh install, exact beginner request, `.4 -> .5`
  upgrade, same-version reinstall, state hashes, duplicate checks, doctor, and
  drift: PASS.
- WSL/Bash fixture: fresh `install.sh`, package doctor, and installed drift: PASS.
- Regression suite: `19/19 PASS` (13 Goal, 4 existing workflow, 2 release tests).
- Goal subsystem: preserve-only; no Goal implementation changes were made.
- Real project-quality eval and live eight-agent host quorum are not claimed;
  fixtures are deterministic packaging/install evidence only.

## Scope and closure notes

- Anvien registration/query/detect-changes was attempted; the target package path
  is not registered, so local source, artifact, installer, doctor, drift, and test
  evidence is the documented fallback.
- The package has no `.git` metadata; no repository was initialized and no commit
  or external publication is claimed.
- No project migration was introduced: project state is preserved in place, while
  reusable system files are backed up and replaced. A future schema migration must
  be explicit and separately validated rather than inferred by this installer.
