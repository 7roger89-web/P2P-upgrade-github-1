# P2P-C09 Supported Generic Host Identity and Route Observation Boundary Evidence Ledger

## Metadata

- Date: `2026-08-14`
- Plan: `docs/plans/2026-08-14-p2p-c09-host-identity-boundary/2026-08-14-p2p-c09-host-identity-boundary-plan.md`
- Evidence: `docs/plans/2026-08-14-p2p-c09-host-identity-boundary/2026-08-14-p2p-c09-host-identity-boundary-evidence.md`
- Benchmark: `docs/plans/2026-08-14-p2p-c09-host-identity-boundary/2026-08-14-p2p-c09-host-identity-boundary-benchmark.md`
- Actual status: `docs/plans/2026-08-14-p2p-c09-host-identity-boundary/2026-08-14-p2p-c09-host-identity-boundary-actual-status.md`

## Evidence Rules

The evidence file explains why the work is known to be correct.

- Evidence IDs are stable and phase-scoped.
- Source inspection precedes tests and completion claims.
- Anvien graph evidence is refreshed before graph queries; high/critical risk is recorded as a scope warning.
- Live claims require a fresh official host receipt, output capture, request/context/artifact binding, and `runtime_task_execution=true`.
- Proxy, child prose, prompt labels, and requested profile are not host identity proof.
- C08 scored execution is explicitly not evidence for this Goal and must remain at zero.
- Long measurements belong in the companion benchmark ledger; pass/fail command evidence stays here.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-SRC1`: Frozen C08 router observation maps all C1-C12: C1/C4/C5/C8-C12 standard/non-UI, C6 `p2p-uiux` primary without AESTHETICA, C7 `p2p-uiux` plus AESTHETICA eligibility, and C2/C3 lexical UI ambiguity disclosed without routing redesign.
- `E0-P0A-SPEC1`: Approved capability SPEC cluster states that `p2p-uiux` is `SKILL`, AESTHETICA is optional/noncanonical, the existing router remains singular, execution evidence reuses the existing ledger, and missing/stale/conflicting evidence fails closed.
- `E0-P0A-HOOK1`: Current hook `.p2p/system/scripts/p2p_host_identity_hook.py` records official lifecycle fields into the existing JSONL ledger, but currently accepts any non-empty `agent_type`; `.codex/config.toml` matches only `^p2p_aesthetica$`.
- `E0-P0A-LIVE1`: Current `.p2p/system/p2p_capabilities/live_execution.py` requires a fresh official receipt matching `requested_execution.profile` before setting `runtime_task_execution=true`, but has no logical route/capability fields and does not classify identity mismatch separately.
- `E0-P0A-REG1`: Current capability registry contains exactly eight canonical identities, `p2p-uiux` as `SKILL`, and `p2p_aesthetica` as optional/noncanonical.
- `E0-P0A-C07-1`: Existing C07 Supervisor report accepts the blocked C08 result because only fresh AESTHETICA identity receipts were available; it explicitly requires a separate Goal for non-AESTHETICA host coverage and preserves C08 treatment.
- `E0-P0A-GRAPH1`: Fresh `p2p-system` Anvien file-detail: hook has 29 symbols, 17 local relationships, 8 linked flows, 125 unresolved references, risk HIGH; live boundary has 100 symbols, 78 local relationships, 11 linked flows, 344 unresolved references, risk HIGH; router has 43 symbols, 6 local relationships, 2 linked flows, 75 unresolved references, risk HIGH. All three are parsed and not stale.
- `E0-P0A-IMPACT1`: Fresh Anvien upstream impact for hook is one affected file/7 impacted symbols, three affected process hits, file blast-radius risk LOW; source-level scope warning remains HIGH because the hook is the identity authority.
- `E0-P0A-IMPACT2`: Fresh Anvien upstream impact for live boundary is one affected file/28 impacted symbols, four affected process hits, file blast-radius risk LOW; edits remain surgical and must preserve context/artifact/proxy invariants.
- `E0-P0A-IMPACT3`: Fresh Anvien upstream impact for router is one affected file/3 impacted symbols, one affected process hit, file blast-radius risk LOW; router is preserve-only for this Goal.
- `E0-P0A-ART1`: Official `.15` SHA-256 is `af4d63a882dabfde20ac237574590ec584ee2944bc4cdc30b6a07bf7f681e195`; current `.16-r2` and `.17` are preserve-only per the user request and C07 evidence.
- `E0-P0A-GIT1`: Repository has no `.git`; prior C07 evidence records Anvien `detect-changes`/Git diff as unavailable and makes no commit claim. This Goal must repeat that honesty.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`, `P1-C`

- `E1-P1A-HOOK1`: PASS. The existing hook now has explicit canonical-eight, optional Aesthetica, and supported `default` sets; unknown types and secret-like known values are ignored without a receipt. Exact Aesthetica compatibility remains green, and all eight canonical identities plus `default` are covered by direct tests.
- `E1-P1A-CONFIG1`: PASS. `.codex/config.toml` uses the exact explicit matcher `^(?:default|p2p_(?:iris|tecton|axiom|vector|datos|anon|architecton|helios|aesthetica))$`; no wildcard and no `p2p-uiux` profile were added.
- `E1-P1B-ROUTE1`: PASS. `p2p-route-host-observation/1` is validated and persisted through the existing request/receipt path. Top-level receipt fields now separate logical route/capability from requested profile, observed host type/class, session/turn, host execution ID, and identity authority. Historical callers receive a backward-compatible legacy route value.
- `E1-P1B-FAILCLOSED1`: PASS. Direct tests cover missing/unreadable host evidence, stale receipts, wrong session/turn, identity mismatch, unknown requested profile, proxy non-promotion, tampered requests, recursive delegation, secret output, and output/receipt isolation. Missing ledger/read failures now classify as `HOST_EVIDENCE_CAPTURE_FAILURE`; wrong requested/observed type classifies as `HOST_IDENTITY_MISMATCH`.
- `E1-P1C-IDENTITYTEST1`: PASS. Focused hook/live suite is 24/24; router, capability, context, and beginner regression is 54/54. No routing function, profile registry, canonical denominator, permission, or proxy policy changed.
- `E1-P1C-LIVETEST1`: PASS for the synthetic/direct boundary contract only. The suite asserts `runtime_task_execution` and receipt bindings when a valid official receipt fixture is supplied; it does not substitute for the real-host proof, which remains separately blocked in E2.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`

- `E2-P2A-NONUI1`: BLOCKED. Real default worker `019fff22-023e-70b1-adb1-cf3f8a00ce29` completed the bounded read-only probe, but the existing official ledger gained no matching `default` `SubagentStart` receipt. No live proof was accepted.
- `E2-P2A-NORMALUI1`: BLOCKED by the same host boundary. Router inspection remains PASS for `p2p-uiux` primary with `call_aesthetica=false`, but no real default receipt exists to bind a normal-UI live execution.
- `E2-P2B-A11Y1`: NOT RUN as a fresh C09 probe. Historical C07 Aesthetica evidence remains valid and unchanged, but it cannot substitute for the requested C09 route/receipt proof.
- `E2-P2B-CANONICAL1`: BLOCKED. Real `p2p_iris` worker `019fff25-73a3-7ab0-9794-b345391ef12c` completed its bounded read-only probe, but the existing official ledger gained no matching canonical receipt. No identity was inferred from the worker’s label or prose.
- `E2-HOST-BLOCKER1`: The ledger contained 18 valid official host receipts before and after both probes, all `p2p_aesthetica`; no current `default` or `p2p_iris` receipt was present. This is the single mandatory live-evidence blocker. The host hook’s direct synthetic path is tested, but current host `SubagentStart` emission/config activation is not observable for these worker types.

## E3 - P3 Evidence

Matching plan item(s): `P3-A`, `P3-B`

- `E3-P3A-REGRESSION1`: PASS for all executable gates. Full repository suite is 111/111 in 257.196 seconds; focused and affected suites are green; package/lifecycle is 2/2; candidate package verify, package doctor, capability doctor, UI/UX doctor, and governance drift all PASS. C08 scored trials remain zero.
- `E3-P3A-PACKAGE1`: PASS. New unpromoted candidate `D:/AI/P2P_dev/P2P-8.4.7-C-Codex-Edition-v18.zip` is 399 content files / 400 checksums with SHA-256 `5dd547319a4d5ed0d529017d2514470c81e9456d4c448c7820b4adc9868f02c8`. Protected `.15`, `.16-r2`, and `.17` hashes were rechecked unchanged.
- `E3-P3B-SUPERVISOR1`: BLOCKED/REJECTED for route-wide readiness because the mandatory fresh generic/default and canonical official receipts are absent; the independent review is recorded in `reports/supervisor/`.
- `E3-P3B-CLOSURE1`: BLOCKED. The implementation, regression, and package work is complete, but the Goal cannot claim `SUPPORTED_ROUTE_WIDE_HOST_IDENTITY_READY` until the host emits fresh official receipts for the supported generic/default and canonical custom probes. The persisted P2P terminal report is `.p2p/state/reports/run-20260814-075236-p2p-c09-implement-an.json` (`BLOCKED`). No C08 rerun or scoring occurred.

## Closure Evidence

The terminal state is `BLOCKED` at the real host-evidence boundary. Production
behavior is implemented and locally/package validated; the current host did
not emit the required fresh official identities for the two real probes. C08
scored-trial evidence remains absent, and no benchmark quality, efficiency,
token, cost, or non-inferiority claim is made.
