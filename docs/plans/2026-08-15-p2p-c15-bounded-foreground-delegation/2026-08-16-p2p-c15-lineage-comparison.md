# P2P-C15 Official `.19` versus Development `.15` Lineage Comparison

## Inputs

- Official ZIP: `D:\AI\P2P_dev\P2P-8.4.7-C-Codex-Edition-v19.zip`
- Official ZIP SHA-256:
  `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`
- Development tree: `D:\AI\P2P_dev\P2P-8.4.6-C-Codex-Edition-v4`
- Development version: `8.4.7-C-codex.15`

## Content-level comparison

The comparison used the package's real path mapping: `runtime/` to
`.p2p/system/`, UI/UX runtime script aliases, root scripts, manifests,
governance, docs, source, and root files.

- Official entries compared: `403`
- Byte-identical mapped entries: `390`
- Missing mapped entries: `0`
- Content mismatches: `13`

The 13 mismatches are:

- expected version/delta surfaces: `VERSION`, runtime `VERSION`,
  `p2p.manifest.json`, `p2p_uiux/__init__.py`, capability `VERSION`;
- additive C15/C16 wiring: capability exports, `doctor.py`,
  `package_release.py`, development-control references;
- generated/release metadata: package manifest, build report, checksum file,
  runtime lock, release notes.

Official `.19` does not contain `bounded_delegation.py` or
`p2p_delegation.py`. Shared C10-C12 runtime files are present and verified by
exact hash, but the development tree is not byte-identical or
provenance-equivalent to `.19`.

## Exact mismatch classification

| # | Mapped path | Classification | Integration decision |
|---:|---|---|---|
| 1 | `governance/runtime-manifest.lock.json` | generated lock drift from the development tree | preserve official `.19`; rebuild only through canonical release machinery |
| 2 | `manifest/build-report.json` | generated build metadata | preserve official `.19`; do not hand-edit |
| 3 | `manifest/package.json` | metadata plus development-control/C15 packaging references | conflict until canonical `.19` port is established |
| 4 | `manifest/sha256sums.txt` | generated checksum metadata | regenerate only after an accepted candidate exists |
| 5 | `RELEASE-NOTES.md` | release metadata | preserve official `.19`; no release operation in C15 |
| 6 | `runtime/p2p.manifest.json` | metadata/version surface | preserve official `.19` metadata |
| 7 | `runtime/p2p_capabilities/__init__.py` | intended additive C15 exports | ported in the temporary candidate only |
| 8 | `runtime/p2p_capabilities/capabilities.json` | metadata/version-only difference | preserve official `.19` capability metadata |
| 9 | `runtime/p2p_uiux/__init__.py` | metadata/version-only difference | preserve official `.19` Design Intelligence surface |
| 10 | `runtime/VERSION` | version metadata | preserve official `.19`; never use a string-only fix |
| 11 | `scripts/doctor.py` | intended C15 inventory/doctor wiring | ported in the temporary candidate only |
| 12 | `scripts/package_release.py` | intended C15 packaging wiring plus development-control dependency | unresolved conflict; candidate package build remains blocked |
| 13 | `VERSION` | version metadata | preserve official `.19`; never use a string-only fix |

The comparison remains `403 mapped / 390 exact / 13 mismatched / 0 missing`.
The official ZIP contains no `bounded_delegation.py` or `p2p_delegation.py`;
those are additive C15 delta files, not hidden `.19` content.

## Temporary candidate

A disposable candidate was assembled under:

`.tmp/p2p-c15-combined-candidate-20260816`

Base identity is the untouched official ZIP SHA-256
`3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`.
The controlled C15 delta inventory is:

- `runtime/p2p_capabilities/bounded_delegation.py`
- `scripts/p2p_delegation.py`
- `runtime/p2p_capabilities/__init__.py`
- `scripts/doctor.py`
- `scripts/package_release.py`

The candidate kept both VERSION files at official `.19`. Portable doctor PASS,
candidate runtime compile/import PASS, and a deterministic raw integration ZIP
was produced with SHA-256
`8e87369fb3f6427a239e87823562faf22e75525ab0ec40d5e399be1329ee3172`;
the sorted tree fingerprint is
`f165d7007cacae274a5f3a0e88125ab9011ad50c0ef599602e18c8050ecd4060`.
This is a temporary verification artifact, not a package release or promoted
candidate.

The canonical package builder was also run against the temporary candidate and
failed because the copied C15-era package-release surface requires
`p2p_development_control.py`, which is not present in official `.19`. The
development source builder independently remains blocked by the explicit
`.15 < .19` lineage guard. No governance file or version string was added to
silence either failure.

## Classification

`CANONICAL .19 + C15 DELTA = NOT_PROVEN`

This is stronger than “version string stale” but not evidence of a destructive
conflict in the shared C10-C12 files. The current development tree contains
real additive C15/C16 changes and release metadata drift. The existing package
lineage guard correctly rejects `.15 < .19` before packaging.

The combined candidate is useful for bounded doctor/import/regression checks,
but it is not canonical release-integrated: package construction and lineage
promotion remain blocked. The official ZIP was not modified.
