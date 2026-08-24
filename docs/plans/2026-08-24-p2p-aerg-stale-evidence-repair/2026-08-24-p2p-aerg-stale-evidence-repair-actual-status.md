# P2P AERG Expired-Evidence Fail-Closed Repair Actual Status

Title: P2P AERG Expired-Evidence Fail-Closed Repair
Date: 2026-08-24
Status: P3 Complete / P2P_AERG_STALE_EVIDENCE_REPAIR_READY_FOR_SUPERVISOR_REVIEW
Companion plan: `Docs/plans/2026-08-24-p2p-aerg-stale-evidence-repair/2026-08-24-p2p-aerg-stale-evidence-repair-plan.md`
Companion evidence: `Docs/plans/2026-08-24-p2p-aerg-stale-evidence-repair/2026-08-24-p2p-aerg-stale-evidence-repair-evidence.md`
Companion benchmark: `Docs/plans/2026-08-24-p2p-aerg-stale-evidence-repair/2026-08-24-p2p-aerg-stale-evidence-repair-benchmark.md`

## Purpose

This is the P2 current-state classification after the narrow production repair
and fresh regressions. It supersedes no earlier plan or report; it records only
this repair lane.

## Scope

Target scope:

- AERG freshness decision aggregation and direct regression tests.

Out of scope:

- QI/FW01 source, governance, release, deployment, host, Owner authority,
  `.19`, `.74`, CPT01-R2, RF01, C43, and the prior REJECT report.

## Relationship / Impact Evidence

- Fresh post-repair `anvien analyze --force`: exit 0; `898` files scanned,
  `164` parsed code files, `0` parse failures.
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
| `aerg_engine.py` freshness aggregation | correct / fail-closed | edited surgically | `E1-P1B-SRC1`, `E1-P1B-GREEN1` | preserve exact precedence and serialization |
| AERG age-only freshness test | passing discriminator | preserve test | `E1-P1B-GREEN2`, `E2-P2A-RUN1` | retain exact `STALE` assertions |
| AERG explicit stale test | passing discriminator | preserve test | `E1-P1B-GREEN2`, `E2-P2A-RUN1` | retain exact `STALE` assertions |
| AERG serialized stale result | correct / fail-closed | preserve test | `5273133`, `E2-P2A-RUN1` | do not normalize to `VERIFIED/CURRENT` |
| AERG no-mutation/claim preservation | correct | preserve-only | `E0-P0A-CLOSED1`, `E2-P2A-RUN1` | do not reopen |
| QI stale mapping | bound-correct | inspect-only | `E1-P1C-QI1`, `E2-P2A-RUN3` | no QI source edit |
| FW01 post-execution AERG seam | bound-correct | inspect-only | `E1-P1C-FW1`, `E2-P2A-RUN4` | no FW01 source edit |
| Capability ledger record | correct foundation status | preserve-only | `E0-P0A-LEDGER1` | no status promotion |
| `.19/.74/promotion.allowed` | correct protected state | preserve-only | `E0-P0A-AUTH1` | no governance mutation |
| Prior independent REJECT report | correct historical evidence | preserve-only | `E0-P0A-REJECT1` | never rewrite |

## P2 Decision

The confirmed stale-evidence semantic defect is repaired in production at
`a10be51`, with serialization coverage added at `5273133`. Fresh focused,
integration, full-capability, C43/RF01, compile, graph, and protected-state
checks show `NEW_FAILURE=0` relative to the known inherited framework
validator debt. QI and FW01 required no source changes. The next bounded slice
is P3 evidence handoff; no Supervisor, independent verification, promotion,
release, deployment, or new Goal is authorized here.

## Status Refresh Log

| Date | Transition | Evidence | Consequence |
| --- | --- | --- | --- |
| 2026-08-24 | baseline -> P0 Complete | `E0-P0A-SRC1..E0-P0A-REJECT1` | begin test-first stale repair only |
| 2026-08-24 | P0 Complete -> P1-A Red Checkpoint | `E1-P1A-RED1..E1-P1A-RED2` | commit tests before production edit; proceed to minimal P1-B fix |
| 2026-08-24 | P1-A Red Checkpoint -> P1-B Repair | `E1-P1B-SRC1..E1-P1B-GREEN3` | `a10be51` closes stale decision and outward freshness semantics |
| 2026-08-24 | P1-B Repair -> P2 Complete | `E1-P1C-QI1..E2-P2B-RUN5` | fresh regressions pass; inherited validator debt remains explicit |
| 2026-08-24 | P2 Complete -> P3 Complete | coder report and notes log | stop at `P2P_AERG_STALE_EVIDENCE_REPAIR_READY_FOR_SUPERVISOR_REVIEW`; no review or promotion action |
