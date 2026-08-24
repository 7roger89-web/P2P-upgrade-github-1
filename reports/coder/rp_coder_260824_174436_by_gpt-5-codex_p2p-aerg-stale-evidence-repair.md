# Coder Report — P2P AERG Stale-Evidence Fail-Closed Repair

## Verdict

`P2P_AERG_STALE_EVIDENCE_REPAIR_READY_FOR_SUPERVISOR_REVIEW`

Classification:

`PRODUCTION_SEMANTIC_DEFECT_REPAIR`

Specific defect class:

`STALE_EVIDENCE_FAIL_CLOSED_DEFECT`

This is a bounded development-plane repair handoff. No Supervisor review,
independent verification, Owner approval, promotion, release, deployment,
host-protection change, or new Goal was performed in this lane.

## Exact subject and checkpoint binding

- Repository/worktree:
  `D:\AI\P2P_dev\P2P-upgrade-github\.tmp\p2p-post74-development-01`
- Branch: `codex/p2p-post74-development-01`
- Current HEAD: `5273133`
- Test-first red checkpoint: `11c3e9e`
- Production repair checkpoint: `a10be51`
- Serialization assertion checkpoint: `5273133`
- Prior independent REJECT report commit:
  `430c47d868da084771afc9fbae039f4d4dda637a`
- Prior independent report remains historical and unchanged.

The production subject is the current AERG implementation at `a10be51` with
the serialized-result assertions at `5273133`. The later evidence/report
surfaces are bound to the same worktree and current HEAD.

## Confirmed root cause

Before repair, `aerg_engine.py` derived `freshness=STALE` and retained
`EVIDENCE_EXPIRED` or `EVIDENCE_NOT_CURRENT`, but did not append a `STALE`
decision for those freshness paths. The observation therefore fell through to
`SUPPORTED`, and the outward result could be `VERIFIED/CURRENT`. At aggregate
level, a stronger `CONTRADICTED` decision also hid the observation's stale
freshness because result freshness was derived only from decision labels.

The independent pre-repair behavior was reproduced before editing:

```text
EXPIRED_BY_TIME decision=SUPPORTED status=VERIFIED freshness=CURRENT reasons=['EVIDENCE_EXPIRED']
EXPLICIT_STALE decision=SUPPORTED status=VERIFIED freshness=CURRENT reasons=['EVIDENCE_NOT_CURRENT']
QI actual expired result=QUALITY_VERIFIED checkpoint_allowed=True
```

## Invariant Family Map

| Invariant family | Authority/source | Repair or preservation | Fresh proof |
|---|---|---|---|
| Freshness decision | AERG engine | Age-expired and explicit stale freshness now append `STALE` | `E1-P1B-SRC1`, `E1-P1B-GREEN1`, `E2-P2A-RUN1` |
| Outward status/serialization | `AERGResult` construction and `to_dict()` | Stale result is `INCOMPLETE/STALE`; no `VERIFIED/CURRENT` normalization | `5273133`, `E2-P2A-RUN1` |
| Contradiction precedence | Existing AERG aggregation | `CONTRADICTED` still wins; stale freshness remains visible | `E1-P1B-GREEN1` |
| Fresh happy path | Existing AERG contract | Current mechanically valid evidence remains `SUPPORTED/VERIFIED/CURRENT` | `E1-P1B-GREEN1` |
| QI boundary | Existing `quality_intelligence.py` mapping | No source edit; actual stale AERG maps to `QUALITY_UNKNOWN/STALE_EVIDENCE`, checkpoint false | `E1-P1C-QI1`, `E2-P2A-RUN3` |
| FW01 seam | Existing `p2p_fw01_loop.py` post-execution path | No source edit; existing seam carries the repaired bounded result | `E1-P1C-FW1`, `E2-P2A-RUN4` |
| No-mutation and claim provenance | Existing AERG tests/model contract | Preserve exact `NO MUTATION CLAIM + OBSERVED MUTATION = CONTRADICTED`, claim, evidence, and flags | `E0-P0A-CLOSED1`, `E2-P2A-RUN1` |
| Provider/live/fixture/authority boundaries | Existing AERG/QI/full capability contracts | No provider branch, self-verification, fixture/live, or authority relaxation | `E2-P2A-RUN1`, `E2-P2B-RUN1` |
| Governance and release boundary | Governance records and protected artifacts | Preserve-only; no promotion/release/deployment mutation | `E2-P2B-RUN5` |

## Implemented scope

### Production

Only `.p2p/system/p2p_capabilities/aerg_engine.py` changed in production:

- At line `174`, aggregate result freshness now considers the evaluated
  observation freshness, so stale freshness remains `STALE` even when decision
  precedence returns `CONTRADICTED`.
- At lines `294-295`, any derived `freshness == "STALE"` appends the `STALE`
  decision before existing contradiction/subject/stale/insufficient
  aggregation.

This is the smallest correction to the existing state model. No new state
machine, subsystem, queue, persistence layer, router, scheduler, QI rewrite,
or FW01 redesign was introduced.

### Tests and evidence

The test file
`.p2p/system/p2p_capabilities/tests/test_aerg_reconciliation.py` now contains
exact discriminators for:

1. age-only expiry;
2. explicit `freshness="STALE"` metadata;
3. stale plus contradiction precedence;
4. fresh valid evidence;
5. actual stale AERG through the existing QI boundary; and
6. serialized `AERGResult.to_dict()` decision/status/freshness fields.

The current A-Z matrix remains an honest `26/26` baseline. The two uncovered
stale dimensions are reported as explicit additional falsification cases, so
the reconstructed semantic coverage is `26` baseline cases plus `2` stale
extensions, `28` total—not a falsely reported `26/26` total.

## Test-first proof

Before production editing, commit `11c3e9e` added the five discriminating
cases and the QI boundary assertion. The pre-repair run was:

```text
py -X utf8 -m unittest discover -s .p2p/system/p2p_capabilities/tests -p 'test_aerg_reconciliation.py'
Ran 17 tests
FAILED (failures=4)
```

The four failures were the expected stale decision/freshness/QI failures; the
fresh happy path and existing cases remained passing. Production source was
untouched at that checkpoint. This red result is retained in
`E1-P1A-RED1..E1-P1A-RED2`.

## Fresh repair evidence

The direct five-case probe after `a10be51` produced:

```text
AGE_EXPIRED STALE INCOMPLETE STALE ['EVIDENCE_EXPIRED']
EXPLICIT_STALE STALE INCOMPLETE STALE ['EVIDENCE_NOT_CURRENT']
STALE_CONTRADICTION CONTRADICTED CONTRADICTED STALE CONTRADICTED ['EVIDENCE_EXPIRED', 'EXIT_CODE_CONTRADICTS_PASS']
FRESH_VALID SUPPORTED VERIFIED CURRENT []
QI_ACTUAL_STALE QUALITY_UNKNOWN False ['STALE_EVIDENCE']
P1B_FIVE_CASE_PROBE_PASS
```

The actual stale AERG result was passed through the existing QI function; no
crafted replacement result was used.

## Fresh regression results

| Check | Result | Classification |
|---|---:|---|
| Focused AERG reconciliation | `17 passed, 0 failed` | `NEW_FAILURE=0` |
| Freshness-specific subset | `5 passed, 0 failed` | stale discriminators closed |
| Reconstructed A-Z | `26/26` | baseline preserved |
| Additional stale extensions | `2/2` | age-only and explicit stale |
| Total reconstructed semantic cases | `28` pass | actual coverage reported honestly |
| QualityIntelligence | `44 passed, 1 skipped, 0 failed` | existing boundary preserved |
| FW01 checkpoint/integration | `6 passed, 0 failed` | existing seam preserved |
| Full capability suite | `352 passed, 6 skipped, 0 failed` | five added tests; no new failure |
| C43 + RF01 orientation/packaging | `18 passed, 0 failed` | regression pass |
| Python compile boundary | exit `0` | no syntax regression |
| Framework validator | `52/59`, exit `1` | same seven inherited failures; not introduced |

The full capability run emitted the pre-existing bounded-documentation
`ResourceWarning` messages only; they did not become test failures.

The seven framework-validator failures remain:

`V01-schema-valid`, `V03-family-registered`, `V05-dep-integrity`,
`V09-freshness-vocab`, `V06-charter-no-competitor-patterns`,
`V12-origin-type-valid`, and `V20-pr-lineage-declared`.

## E2E verification template

- Build/compile: `py -X utf8 -m compileall -q .p2p/system/p2p_capabilities`
  exited `0`.
- Runtime surface: offline in-memory Python capability runtime; no browser,
  Docker, database, or product UI surface applies.
- Happy path: fresh mechanically valid evidence returned
  `SUPPORTED/VERIFIED/CURRENT`.
- Age-expiry edge: expired observation returned `STALE/INCOMPLETE/STALE` with
  `EVIDENCE_EXPIRED`.
- Explicit metadata edge: `freshness=STALE` returned
  `STALE/INCOMPLETE/STALE` with `EVIDENCE_NOT_CURRENT`.
- Precedence edge: stale plus exit-code contradiction returned
  `CONTRADICTED/CONTRADICTED/STALE`.
- Integration edge: actual stale AERG result returned QI
  `QUALITY_UNKNOWN/STALE_EVIDENCE/checkpoint_allowed=False`.
- Preservation edge: no-mutation contradiction, claim/provenance, provider
  neutrality, live/fixture/mock, authority, and capability flags remained
  covered by the focused/full suites.

## Source hashes and unchanged siblings

| Path | SHA-256 |
|---|---|
| `.p2p/system/p2p_capabilities/aerg_model.py` | `60500940266BC08DE151FF1BBFCB1B2541E5B3700BC841435A12D5CBDC533B61` |
| `.p2p/system/p2p_capabilities/aerg_engine.py` before repair | `B6B9E6750F3ABEA0975B3F888EBEC7C43D54337482262287322CB4C309A36C36` |
| `.p2p/system/p2p_capabilities/aerg_engine.py` after repair | `0B14D04B3326D88FC8DDB4EE5FD8F8C7C570F517A262749BEF5F25F196D1BE2F` |
| `.p2p/system/p2p_capabilities/quality_intelligence.py` | `4A2DFCFDEC0959C9F416045D9E9F8F9D2DCFFDBF1996E10C7EDB8D96EAE47702` |
| `.p2p/system/p2p_capabilities/p2p_fw01_loop.py` | `97EF5FB0F86D27440F5BE500420296CFFB461EB7E5660E183B75D0685FB91AC1` |
| `.p2p/system/p2p_capabilities/tests/test_aerg_reconciliation.py` | `EF79D8429C2C01A8B8C4B91B1CD25E41174191FF4B7A7105BB72EEE1A20DCBA8` |
| `docs/p2p-development/capability-ledger/capability-index.json` | `2B1AEC43B53A7A0B320C81A7BDA2574C42F22412C5B2FA5B7B73318D4B3C262D` |

The diff from the prior implementation checkpoint `fc1b9dc` to HEAD changes
only the AERG engine in the protected production quartet; QI, FW01, and the
provider-neutral model remain unchanged. The prior independent REJECT report
has no diff from `430c47d` to HEAD.

## Graph and impact boundary

Fresh `anvien analyze --force` exited `0` with `898` files scanned, `164`
parsed code files, `0` parse failures, `37,493` graph nodes, and `43,308`
relationships. `detect-changes --scope all` reported `0` affected files and
low changed-file risk. The hidden `.p2p/system` file projection returned
`not_found` for file-detail/impact, so that limitation is disclosed rather
than turned into a false no-impact claim; direct source, diff, test, and
runtime evidence are authoritative for this hidden surface.

## Protected state and residual boundaries

- Official `.19` remains `PROMOTED_VERIFIED`, artifact SHA-256
  `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`.
- Development `.74` remains `SEALED_UNPROMOTED`, artifact SHA-256
  `2b82dea10695abb1c99253be1205728335a114df42cececde2fcca5c1727fd12`.
- Development status remains `ACTIVE_NONCANONICAL_NO_PROMOTION`.
- `promotion.allowed=false` remains blocked by the external GitHub private
  repository host-protection limitation.
- CPT01-R2, RF01, C43, governance, Owner authority, release/deployment
  helpers, host state, and the prior independent REJECT evidence were not
  changed.
- Existing unrelated dirty owner files and untracked C43/RF01 evidence were
  preserved and not staged.

Deliberately unperformed actions are not hidden as technical gaps: Supervisor
review, independent verification, Owner approval, promotion, release,
deployment, and a next Goal remain outside this coder lane.

## Handoff and stop boundary

The narrow production semantic defect is repaired and fresh development-plane
evidence is complete. The exact terminal handoff is:

`P2P_AERG_STALE_EVIDENCE_REPAIR_READY_FOR_SUPERVISOR_REVIEW`

Stop here. A later Supervisor review must independently verify this exact
subject and must not be interpreted as promotion, release, deployment, host
certification, or Owner approval.
