# P2P AERG Expired-Evidence Fail-Closed Repair Actual Status

Title: P2P AERG Expired-Evidence Fail-Closed Repair
Date: 2026-08-24
Status: P1-A Red Checkpoint
Companion plan: `Docs/plans/2026-08-24-p2p-aerg-stale-evidence-repair/2026-08-24-p2p-aerg-stale-evidence-repair-plan.md`
Companion evidence: `Docs/plans/2026-08-24-p2p-aerg-stale-evidence-repair/2026-08-24-p2p-aerg-stale-evidence-repair-evidence.md`
Companion benchmark: `Docs/plans/2026-08-24-p2p-aerg-stale-evidence-repair/2026-08-24-p2p-aerg-stale-evidence-repair-benchmark.md`

## Purpose

This is the P1-A current-state classification before the narrow production
edit. It supersedes no earlier plan or report; it records only this repair lane.

## Scope

Target scope:

- AERG freshness decision aggregation and direct regression tests.

Out of scope:

- QI/FW01 source, governance, release, deployment, host, Owner authority,
  `.19`, `.74`, CPT01-R2, RF01, C43, and the prior REJECT report.

## Relationship / Impact Evidence

- Fresh `anvien analyze --force`: exit 0; `894` files scanned, `164` parsed
  code files, `0` parse failures.
- `anvien file-detail` and `anvien impact` for the hidden
  `.p2p/system/p2p_capabilities/aerg_engine.py` path report `not_found`; this
  is a tooling limitation, not evidence of no relationships.
- Direct source inspection and runtime probes are therefore required for the
  hidden capability surface.
- Existing owner worktree modifications and untracked C43/RF01 evidence are
  preserve-only.

## Current Status Matrix

| Surface | Status | Touch mode | Evidence | Plan consequence |
| --- | --- | --- | --- | --- |
| `aerg_engine.py` freshness aggregation | wrong / partial | editable, surgical | `E0-P0A-SRC1`, `E0-P0A-PROBE1` | P1-B must derive `STALE` decision |
| AERG age-only freshness test | explicit failing discriminator | editable test | `E1-P1A-RED1` | P1-B must make it pass |
| AERG explicit stale test | explicit failing discriminator | editable test | `E1-P1A-RED1` | P1-B must make it pass |
| AERG no-mutation/claim preservation | correct | preserve-only | `E0-P0A-CLOSED1` | do not reopen; rerun after fix |
| QI stale mapping | bound-correct | inspect-only | `E0-P0A-QI1` | no QI source edit expected |
| FW01 post-execution AERG seam | bound-correct | inspect-only | `E0-P0A-FW1` | no FW01 source edit expected |
| Capability ledger record | correct foundation status | preserve-only | `E0-P0A-LEDGER1` | no status promotion |
| `.19/.74/promotion.allowed` | correct protected state | preserve-only | `E0-P0A-AUTH1` | no governance mutation |
| Prior independent REJECT report | correct historical evidence | preserve-only | `E0-P0A-REJECT1` | never rewrite |

## P1-A Decision

P1-A is complete as an intentional red checkpoint. The five new assertions
were added without production edits; `17` focused tests ran and `4` newly added
stale assertions failed against the confirmed pre-repair behavior. The next
executable slice is P1-B: append the minimal `STALE` decision derivation.

## Status Refresh Log

| Date | Transition | Evidence | Consequence |
| --- | --- | --- | --- |
| 2026-08-24 | baseline -> P0 Complete | `E0-P0A-SRC1..E0-P0A-REJECT1` | begin test-first stale repair only |
| 2026-08-24 | P0 Complete -> P1-A Red Checkpoint | `E1-P1A-RED1..E1-P1A-RED2` | commit tests before production edit; proceed to minimal P1-B fix |
