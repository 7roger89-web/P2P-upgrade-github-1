# RF01 Coder Report

Date: 2026-08-24
Goal: RF01 — README-FIRST PROJECT ORIENTATION + DEVELOPMENT FRAMEWORK REVISION
Branch: `codex/p2p-post74-development-01`
Worktree: `.tmp/p2p-post74-development-01`
Base closure: `54d15cb02b04a0fea35fb7d2fd0af1fd564bb264`
Current subject: `e00bdc7571483bc0daf0a9794bbd2db249e1e8ee`

Required disclaimer: Implemented against sealed .74 NONCANONICAL DEVELOPMENT BASE. Official canonical baseline remains .19. Release/promotion authority remains deferred due to external GitHub private repository host-protection limitation.

## Result

RF01 is implemented at the scoped development-plane level. The root README is
an explicit orientation projection, the managed-block updater is deterministic
and fail-closed, the existing framework/governance surfaces record the product
and assurance loops, and the existing package/install lists expose the README
and helper without adding automatic README mutation.

Terminal recommendation: `P2P_RF01_PASS_FOR_INDEPENDENT_REVIEW_HANDOFF`.
This is not a release, promotion, deployment, canonical, or independent
certification claim.

## Implementation slices

- `579a711643415fee87647be278cc40fe098e35f0` — README, orientation helper,
  and seven focused behavior tests.
- `be7ff403903d9668e0a370b5b07adc74ffe1713f` — development charter,
  product architecture, roadmap projection, and additive `development_plane`.
- `e00bdc7571483bc0daf0a9794bbd2db249e1e8ee` — package/install bindings,
  static preservation tests, and refreshed RF01 ledgers.

## Invariant family map

| Invariant family | Bound surface | Evidence/result |
|---|---|---|
| Projection is not authority | `README.md`, `scripts/p2p_orientation.py` | Caller supplies content; helper never invents approval, host, promotion, or canonical state. PASS. |
| Owner content preservation | Managed marker replacement and append path | LF/CRLF fixtures, ambiguity rejection, exact outside-slice preservation, and idempotence. PASS. |
| Existing authority remains singular | `governance/development-control.json` | `development_plane` is the only added top-level key; `current_development` is unchanged. PASS. |
| Product vs assurance separation | charter, product architecture, roadmap | Product Fast Loop and Assurance/Release Loop are explicit; no second router, daemon, memory graph, or certification system added. PASS. |
| Package/install availability | `scripts/package_release.py`, `install.ps1`, `install.sh` | README/helper are listed; both installers copy only the helper; static scan finds zero README write paths. PASS. |
| Noncanonical/promotion boundary | README, governance, reports | `.19` remains official; `.74` remains sealed/unpromoted; host limitation and no-promotion state are explicit. PASS. |

## Verification evidence

- Focused orientation and packaging suite: 9/9 PASS.
- `p2p_development_control.py validate`: PASS.
- Python compile with BOM-aware tokenizer: PASS.
- PowerShell AST parse: PASS.
- LF-normalized `bash -n install.sh`: PASS. The Windows working copy has
  `core.autocrlf=true`; raw `bash -n` on CRLF bytes is therefore not treated
  as a source-syntax failure.
- README deep links: all eight referenced local paths exist.
- Fresh Anvien graph after the implementation commit: 872 files scanned, 163
  parsed code files, 0 failures, 37,029 nodes, 42,804 relationships.
- P1-C detect-changes: eight staged files, zero affected processes, overall
  LOW risk; package builder impact was reviewed separately as HIGH and kept
  list-only.
- No release ZIP, install execution, host mutation, promotion, merge, publish,
  or C43 execution occurred.

## Known inherited blockers

The full legacy framework validator and charter suite remain blocked by the
parent baseline, not by RF01 changes. At parent `f92264b`, capability record
index 175 already uses legacy `id` instead of required `capability_id`; the
ledger also contains `SHIPPED` outside the allowed vocabulary, and
`current-roadmap.md` says 159 records while the ledger contains 176. The final
charter run is 32 passed / 8 failed for these same conditions. RF01 does not
repair that unrelated ledger because doing so would broaden the task and alter
historical authority.

The external GitHub private-repository host-protection limitation remains
`EXTERNAL_HOST_CAPABILITY_LIMITATION`; it blocks promotion authority, not the
scoped RF01 implementation.

## Forbidden actions respected

The sealed `.74` ZIP and candidate branch were not edited, the official `.19`
baseline was not changed, no release candidate was built, no installer was
run, no GitHub plan/visibility or host rule was changed, and C43 was not
started.
