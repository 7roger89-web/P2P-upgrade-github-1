# P2P Provider Abstraction Specification

Status: APPROVED FOR IMPLEMENTATION — agent-decided; no owner decision required
Date: 2026-08-12
Parent: `P2P-CAPABILITY-FOUNDATION-ARCHITECTURE-SPEC.md`

## Purpose

Define future provider seams without installing or implementing providers in this Goal. Provider semantics may supply data or code intelligence; they must not leak into governance, routing authority, or canonical quorum semantics.

## Provider roles

- `P2P_PROVENANCE_PROVIDER`: possible implementations `P2P_NATIVE` or future `SEMANTICA`.
- `P2P_CODE_INTELLIGENCE_PROVIDER`: possible implementations `P2P_NATIVE` or future `ANVIEN`.

The foundation ships only the abstraction and a native offline-safe no-provider state. No Semantica/Anvien package, MCP, service, credential, network dependency, or index is created.

## Contract boundary

A provider declaration identifies role, implementation label, trust level, input scope, output schema, freshness, provenance, failure state, and evidence requirements. Provider output is data or proposed evidence. It cannot select the canonical quorum, grant permissions, approve facts, or change the router’s one-owner boundary.

## Trust levels

`PURE_DATA` may be consumed as untrusted data; `HOST_CODE` is subject to host execution/approval policy; `EXTERNAL_SERVICE` is untrusted and unavailable unless explicitly installed and verified by a future Goal. No trust level bypasses the data–instruction boundary.

## Failure and upgrade

Unknown provider, unavailable provider, stale response, schema mismatch, or credential failure is visible as `NOT_APPLICABLE`, `INCOMPLETE`, or `UNKNOWN` according to the claim. Core P2P remains usable. Future provider installation requires a separate approved Goal, provenance, security review, regression, rollback, and lifecycle evidence.

## Done when

The runtime can represent provider role/trust/output contracts and gracefully handle an unknown optional provider without adding a dependency or changing governance.
