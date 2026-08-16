# System Architect Report — P2P Native Decision Trace SPEC

Date: 2026-08-12  
Mode: Mode 1 / new architecture authority before implementation  
Recipient: Architect Review, then implementation lane

## Scope reviewed

This handoff covers the new native Decision Trace authority only. It does not
authorize runtime edits, release packaging, install/upgrade work, Semantica,
Anvien, a new specialist, or changes to existing project/user targets.

## Authority context

The current authority remains `AGENTS.md` plus the approved capability
foundation, execution/evidence, trust/data-instruction, routing/readiness,
optional-specialist, provider, project-domain, manifest, and test/eval SPECs.
The historical beginner certification explicitly records the WHY gap as
PARTIAL because Goal/report/ledger/evidence links are distributed and there is
no single native decision trace.

## Proposed authority

`docs/SPEC/P2P-DECISION-TRACE-SPEC.md` defines the smallest additive contract:

- the existing execution ledger remains the only durable event store;
- trace events reference, but do not replace, Goal, FACT_LEDGER, Live Specs,
  evidence, approval, policy, change, and artifact sources;
- material decisions are captured automatically; routine line-level activity
  is excluded;
- contradictions, supersession, temporal validity, missing references,
  beginner WHY, JSON/Markdown export, redaction, and minimal justified
  integrity are explicit;
- exactly eight canonical identities and `8/8` remain unchanged;
- Aesthetica is separate supporting/optional evidence and never authority;
- no graph database, daemon, MCP, external dependency, Semantica, second
  ledger, router, agent, or memory system is introduced;
- legacy projects remain compatible and historical absence is not backfilled.

## Architecture decisions

1. A structured trace event is an additive event in the existing execution
   ledger, not a competing ledger.
2. Query indexing is disposable and rebuilt from the source ledger; exports are
   derived, read-only artifacts.
3. Decision basis is a concise audit summary, never raw private deliberation or
   hidden reasoning.
4. Approval and canonical participation are evidence-linked and fail visibly
   to `UNKNOWN`/`PARTIAL` when proof is absent.
5. A native provider seam may be named for future compatibility, but no future
   provider is installed or executed in this Goal.

## Required architecture review questions

Architect Review should verify in SPEC language that:

- the new SPEC does not create a competing authority or lifecycle;
- the existing execution/evidence, trust, approval, and routing contracts are
  not weakened or duplicated;
- canonical eight/quorum and Aesthetica boundaries are explicit;
- source/fact/evidence/approval/change/artifact links are references rather
  than copied content;
- failure, partial history, temporal validity, redaction, and export safety
  are production-complete enough for implementation planning;
- no true owner decision or architecture-changing dependency remains open.

## Implementation handoff condition

Implementation may begin only after Architect Review records `PASS` (or after
its precise SPEC finding is resolved and a new immutable review report records
the updated verdict) and the SPEC status is changed to
`APPROVED FOR IMPLEMENTATION — agent-decided; no owner decision required`.

## Anvien and repository limitation

The target is not registered with Anvien and is not a Git worktree. Local source
inspection is the bounded fallback. Architecture authority is derived from
SPEC/AGENTS documents, not from an implementation graph. Commit reference is
`N/A` for this unpacked development source.
