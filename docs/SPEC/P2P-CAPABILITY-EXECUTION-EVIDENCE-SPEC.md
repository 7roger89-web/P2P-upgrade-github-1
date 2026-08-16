# P2P Capability Execution and Evidence Specification

Status: APPROVED FOR IMPLEMENTATION — agent-decided; no owner decision required
Date: 2026-08-12
Parent: `P2P-CAPABILITY-FOUNDATION-ARCHITECTURE-SPEC.md`

## Behavior kernel

Every capability follows four compact rules: `ASSUMPTION_DISCIPLINE`, `SIMPLICITY`, `SURGICAL_SCOPE`, and `VERIFIABLE_SUCCESS`. Trivial work remains lightweight. The kernel does not create an agent, provider, retry framework, or ceremony when the request does not need one.

## Independent done check

An agent's “done” statement is an input, not proof. The verification path is:

```text
DONE-WHEN -> required evidence -> fresh actual evidence
          -> independent check -> governance result
```

The check reuses the existing execution ledger, Goal/eval contracts, approval policy, drift checks, and FACT_LEDGER. It does not create a second certification system. A missing or stale required evidence item is `INCOMPLETE`; conflicting evidence is `CONTRADICTED`.

## Evidence contract

Each claim has exactly four externally inspectable fields:

- `CLAIM`: what is asserted.
- `REQUIRED_EVIDENCE`: the evidence needed to accept it.
- `ACTUAL_EVIDENCE`: fresh evidence observed, with source and timestamp/fingerprint.
- `STATUS`: `VERIFIED`, `INCOMPLETE`, `CONTRADICTED`, or `NOT_APPLICABLE`.

Text saying PASS without actual evidence is not proof. Evidence references must identify the artifact/ledger/test/output used; hidden reasoning is never evidence.

## Minimal no-progress detection

If repeated attempts show the same failure, same missing evidence, same blocker, or no material state change, the result becomes diagnostic/escalation rather than another retry. If the architecture cannot produce clean evidence, defer the claim or report `UNKNOWN`. No infinite loop framework is introduced.

## Approval and mutation

Routine compatible adaptations may proceed within the manifest authority. Material brand, navigation, architecture, destructive changes, fact writes, or protected project state changes cross the existing approval boundary. The capability cannot approve itself.

## Monitoring and rollback

Execution records selected capability, readiness snapshot, context pointers, evidence status, approval reference, and changed-scope fingerprint. Failed execution leaves the target unchanged where possible; rollback is limited to managed development/test artifacts and existing project lifecycle safeguards.

## Done when

The runtime can evaluate a capability claim independently against fresh evidence and existing governance, with honest incomplete/contradicted states and no duplicate certification or retry framework.
