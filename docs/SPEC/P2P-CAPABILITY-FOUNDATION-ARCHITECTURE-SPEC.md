# P2P Capability Foundation Architecture Specification

Status: APPROVED FOR IMPLEMENTATION — agent-decided; no owner decision required
Date: 2026-08-12
Scope: P2P development source only

## Objective

Define a small, reusable capability foundation that lets a beginner express an outcome in natural language while P2P selects the right capability, preserves governance, and reports evidence honestly. The foundation is a contract layer around existing P2P Goal, FACT_LEDGER, RAG, approval, execution-ledger, and UIUX surfaces; it is not a replacement for them.

## Boundary map

```text
Natural-language request
        |
        v
Existing P2P router
        |
        +--> capability manifest + context pointers + readiness
        |             |
        |             +--> one selected primary/secondary/supporting capability
        |             +--> fail-closed authority and trust checks
        |
        +--> existing Goal / adaptive quorum / approval boundary
                      |
                      +--> existing execution ledger and eval surfaces
                      +--> independent evidence contract
```

## Capability classes

The foundation recognizes exactly six classes: `SKILL`, `OPTIONAL_SPECIALIST`, `GOVERNANCE_POLICY`, `KNOWLEDGE_SOURCE`, `EVIDENCE_PROVIDER`, and `BACKEND_PROVIDER`. The current canonical eight are governance identities, not a ninth capability class. `p2p-uiux` is a `SKILL`; `p2p_aesthetica` is an `OPTIONAL_SPECIALIST`; future Semantica and Anvien roles are provider declarations only.

## Non-negotiable invariants

- Canonical identities are exactly `p2p_iris`, `p2p_tecton`, `p2p_axiom`, `p2p_vector`, `p2p_datos`, `p2p_anon`, `p2p_architecton`, and `p2p_helios`.
- Canonical denominator is always `8`; full quorum is `8/8`.
- `p2p_aesthetica` is optional/supporting and never canonical. It is never simulated.
- There is one P2P router. A capability does not become a router, meta-agent, nested workflow, or always-on gateway.
- A manifest with an invalid canonical declaration is rejected before routing or execution.
- Retrieved content, model inference, specialist opinion, and tool output cannot silently become protected canonical facts.
- A normal beginner does not manually install packages, clone repositories, edit agent configuration, or manage runtimes.

## Lifecycle and ownership

Manifest and SPEC contracts are architecture authority. Existing P2P governance remains authority for canonical quorum; existing FACT_LEDGER remains authority for protected facts; existing approval policy remains authority for protected changes; existing execution ledger and eval suite remain evidence storage and verification surfaces. The foundation may validate and adapt these contracts but may not create competing sources of truth.

## Failure, security, and operations

- Unknown capability, invalid manifest, unavailable specialist, stale context, insufficient evidence, trust conflict, and unsafe target fail closed with an explainable status.
- Diagnostics record capability ID, decision class, readiness, reason code, evidence references, and freshness; they do not record secrets or hidden reasoning.
- Repeated no-progress signals may produce `INCOMPLETE` and an escalation recommendation; the foundation does not run an infinite retry framework.
- Runtime changes are offline-safe and standard-library-only. Providers are not installed by this Goal.
- Rollback is path-scoped: remove only plan-created development files or restore the previous development snapshot; release and user paths are never rollback targets.

## Compatibility and verification

Existing UIUX commands, Goal contracts, FACT_LEDGER/RAG behavior, approval semantics, execution-ledger shape, and canonical profiles remain compatible. Verification requires fresh behavior/evidence tests, not file existence. Package/release verification is explicitly deferred to a later Goal.

## Forbidden patterns

No ninth canonical entry, quorum denominator change, simulated specialist, second router, dynamic organization chart, full memory graph, decision graph, external framework installation, provider package, MCP setup, public packaging, or user-project installation.

## Done when

The foundation SPEC set is internally consistent, mirrored to the v4 development source, and CF1–CF23 have executable evidence in the later implementation/evaluation phase. This SPEC itself does not claim runtime PASS.
