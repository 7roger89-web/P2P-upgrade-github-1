# P2P AERG Expired-Evidence Fail-Closed Repair Evidence Ledger

## Metadata

- Date: `2026-08-24`
- Plan: `Docs/plans/2026-08-24-p2p-aerg-stale-evidence-repair/2026-08-24-p2p-aerg-stale-evidence-repair-plan.md`
- Evidence: `Docs/plans/2026-08-24-p2p-aerg-stale-evidence-repair/2026-08-24-p2p-aerg-stale-evidence-repair-evidence.md`
- Benchmark: `Docs/plans/2026-08-24-p2p-aerg-stale-evidence-repair/2026-08-24-p2p-aerg-stale-evidence-repair-benchmark.md`
- Actual status: `Docs/plans/2026-08-24-p2p-aerg-stale-evidence-repair/2026-08-24-p2p-aerg-stale-evidence-repair-actual-status.md`

## Evidence Rules

- Fresh source and runtime evidence outrank prior reports.
- Hidden `.p2p/system` Anvien gaps are disclosed, not converted to PASS.
- A failing pre-repair test is intentional P1-A evidence, not a final result.
- Evidence must distinguish implementation, test, QI, FW01, governance, and
  owner-authority boundaries.

## E0 - P0 Evidence

Matching plan item: `P0-A`.

- `E0-P0A-SRC1`: current `aerg_engine.py:284-293` records stale reasons/state
  without appending `STALE`; `:442-451` falls through to `SUPPORTED`.
- `E0-P0A-PROBE1`: fresh pre-repair probes return `SUPPORTED/VERIFIED/CURRENT`
  for both age-expired and explicit-stale observations.
- `E0-P0A-QI1`: actual expired AERG input reaches QI as
  `QUALITY_VERIFIED/checkpoint_allowed=True`; direct crafted `STALE` mapping is
  otherwise `QUALITY_UNKNOWN/STALE_EVIDENCE`.
- `E0-P0A-TEST1`: current tests contain default observed time and stale-by-source
  case C, but no age-only or explicit-stale case.
- `E0-P0A-CLOSED1`: existing no-mutation test asserts exact contradiction,
  reason, and claim preservation; prior invariant is preserve-only.
- `E0-P0A-FW1`: FW01 evaluates AERG after `self.loop.step()` through the
  existing QI seam; no source edit is expected.
- `E0-P0A-LEDGER1`: current record is `AI_EXECUTION_RELIABILITY_GUARD` with
  `FOUNDATION_READY`, and explicitly remains development-plane only.
- `E0-P0A-AUTH1`: `.19` is `PROMOTED_VERIFIED`, `.74` is
  `SEALED_UNPROMOTED`, and `promotion.allowed=false`.
- `E0-P0A-REJECT1`: independent REJECT report remains unchanged and historical.
- `E0-P0A-GRAPH1`: Anvien refreshed successfully; hidden AERG source file
  detail/impact is `not_found`, so direct evidence is required.

## E1 - P1 Evidence

Matching plan items: `P1-A`, `P1-B`, `P1-C`.

- `E1-P1A-RED1`: command
  `py -X utf8 -m unittest discover -s .p2p/system/p2p_capabilities/tests -p
  'test_aerg_reconciliation.py'` ran `17` tests with exit `1`; the age-only
  and explicit-stale assertions each received `decision=SUPPORTED` instead of
  `STALE`.
- `E1-P1A-RED2`: the same red run showed the stale-plus-contradiction case
  retained `decision=CONTRADICTED` but serialized `freshness=CURRENT`, and the
  actual stale-to-QI boundary first received `decision=SUPPORTED`. The fresh
  happy path passed. Overall: `4` failures, all newly added discriminators;
  the prior cases passed. The edited test SHA-256 is
  `C3D462E985516387E8E57B91D69D52E83D253D4D5C8B3E83F5CD2BA055EE8187`.
- `E1-P1B-SRC1`: pending minimal production diff.
- `E1-P1B-GREEN1`: pending repaired five-case direct probe.
- `E1-P1B-GREEN2`: pending focused repaired AERG/freshness tests.
- `E1-P1B-GREEN3`: pending compile and source/hash boundary.
- `E1-P1C-QI1`: pending actual repaired AERG result through QI.
- `E1-P1C-FW1`: pending FW01 seam and closed-invariant regression.

## E2 - P2 Evidence

Matching plan items: `P2-A`, `P2-B`.

- `E2-P2A-RUN1..E2-P2A-RUN5`: pending focused behavior, reconstructed A-Z,
  QI, FW01, and no-mutation outputs.
- `E2-P2B-RUN1..E2-P2B-RUN5`: pending full capability, C43, RF01, compile,
  validator classification, and protected-state checks.

## Closure Evidence

Pending until the repair checkpoint and coder handoff report exist. Supervisor
and independent verification are explicitly not part of this plan.
