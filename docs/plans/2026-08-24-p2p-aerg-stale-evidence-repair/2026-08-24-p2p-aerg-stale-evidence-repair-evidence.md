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
- `E1-P1B-SRC1`: production checkpoint `a10be51` changes only
  `.p2p/system/p2p_capabilities/aerg_engine.py`: aggregate freshness from the
  evaluated observation (`STALE` cannot be hidden by a stronger
  `CONTRADICTED` decision), and append `STALE` whenever the observation
  freshness derives as stale. No new state or subsystem was added.
- `E1-P1B-GREEN1`: fresh five-case probe passed exactly:
  `AGE_EXPIRED=STALE/INCOMPLETE/STALE`,
  `EXPLICIT_STALE=STALE/INCOMPLETE/STALE`,
  `STALE_CONTRADICTION=CONTRADICTED/CONTRADICTED/STALE`,
  `FRESH_VALID=SUPPORTED/VERIFIED/CURRENT`, and
  `QI_ACTUAL_STALE=QUALITY_UNKNOWN/checkpoint_false/STALE_EVIDENCE`.
- `E1-P1B-GREEN2`: focused AERG reconciliation ran `17` tests with `0`
  failures; the freshness-specific subset ran `5` with `0` failures.
- `E1-P1B-GREEN3`: compileall exited `0`. Pre-repair AERG SHA-256 was
  `B6B9E6750F3ABEA0975B3F888EBEC7C43D54337482262287322CB4C309A36C36`
  as recorded by the prior checkpoint; repaired AERG SHA-256 is
  `0B14D04B3326D88FC8DDB4EE5FD8F8C7C570F517A262749BEF5F25F196D1BE2F`.
  The serialization assertions were added in test checkpoint `5273133`.
- `E1-P1C-QI1`: actual repaired AERG output reaches existing QI as
  `decision=STALE`; QI returns `QUALITY_UNKNOWN`, includes `STALE_EVIDENCE`,
  and sets `checkpoint_allowed=False`. `quality_intelligence.py` is unchanged.
- `E1-P1C-FW1`: FW01 retains the existing post-execution AERG/QI seam;
  `test_checkpoint_quality_gate.py` ran `6` tests with exit `0` under the
  package-path invocation. `p2p_fw01_loop.py` is unchanged.

## E2 - P2 Evidence

Matching plan items: `P2-A`, `P2-B`.

- `E2-P2A-RUN1`: focused AERG `17/17`, freshness subset `5/5`, and preserved
  no-mutation assertion `1/1`, all exit `0`.
- `E2-P2A-RUN2`: reconstructed baseline A-Z `26/26` plus age-only and
  explicit-stale extensions `2/2`; total semantic coverage `28` cases.
- `E2-P2A-RUN3`: QI `44` passed, `1` skipped, `0` failed; actual stale QI
  boundary is `QUALITY_UNKNOWN`, `STALE_EVIDENCE`, checkpoint false.
- `E2-P2A-RUN4`: FW01 checkpoint/integration `6/6`, exit `0`.
- `E2-P2A-RUN5`: fresh five-case direct probe passed and compileall exited `0`.
- `E2-P2B-RUN1`: full capability suite `352` passed, `6` skipped, `0` failed;
  known ResourceWarnings remained non-failing.
- `E2-P2B-RUN2`: C43 regression plus RF01 orientation/packaging `18/18`, exit
  `0`.
- `E2-P2B-RUN3`: framework validator `52/59`, exit `1`, with the same seven
  inherited failures (`V01-schema-valid`, `V03-family-registered`,
  `V05-dep-integrity`, `V09-freshness-vocab`,
  `V06-charter-no-competitor-patterns`, `V12-origin-type-valid`, and
  `V20-pr-lineage-declared`); `NEW_FAILURE=0`.
- `E2-P2B-RUN4`: fresh Anvien scan exit `0`, `898` scanned, `164` parsed,
  `0` parse failures; final detect-changes reports `0` affected files and
  low risk, with only the known owner-dirty registry outside this lane.
- `E2-P2B-RUN5`: `.19` remains `PROMOTED_VERIFIED`, `.74` remains
  `SEALED_UNPROMOTED`, development status remains
  `ACTIVE_NONCANONICAL_NO_PROMOTION`, promotion remains blocked by the
  external private-GitHub host-protection limitation, and the independent
  REJECT report is unchanged.

## Closure Evidence

Repair checkpoints are `11c3e9e` (test-first red), `a10be51` (production
repair), and `5273133` (serialization assertions). Coder handoff report
`reports/coder/rp_coder_260824_174436_by_gpt-5-codex_p2p-aerg-stale-evidence-repair.md`
and the 2026-08-24 notes-log entry are complete. The terminal state is
`P2P_AERG_STALE_EVIDENCE_REPAIR_READY_FOR_SUPERVISOR_REVIEW`. Supervisor and
independent verification are explicitly not part of this plan.
