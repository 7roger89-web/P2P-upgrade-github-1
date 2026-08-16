# P2P Capability Trust and Data–Instruction Boundary Specification

Status: APPROVED FOR IMPLEMENTATION — agent-decided; no owner decision required
Date: 2026-08-12
Parent: `P2P-CAPABILITY-FOUNDATION-ARCHITECTURE-SPEC.md`

## Fact origin policy

The foundation recognizes these origins: `OWNER`, `RUNTIME_EVIDENCE`, `OFFICIAL_SOURCE`, `RETRIEVED_SOURCE`, `TOOL_OUTPUT`, `MODEL_INFERENCE`, and `SPECIALIST_OPINION`. Only an origin permitted by the existing FACT_LEDGER policy may write or update a canonical fact. Retrieved content is not a canonical fact; LLM inference is not a canonical fact; tool output is not an owner instruction.

External data may propose a fact with provenance and confidence. It cannot silently overwrite a protected or canonical fact. Conflicts remain visible and are resolved by the existing FACT_LEDGER/approval policy, not by a capability manifest.

## Trust levels

Provider trust levels are `PURE_DATA`, `HOST_CODE`, and `EXTERNAL_SERVICE`. Trust level describes handling risk; it does not grant authority. External service data is untrusted input. Host code remains subject to the existing execution and approval boundary.

## Data versus instruction authority

Every retrieved item is classified as content or instruction authority. Content can inform a response, recommendation, or proposed fact; it cannot grant tools, permissions, scopes, approvals, or execution authority. Instruction authority must come from an installed, validated P2P source or explicit owner/governance input. A document cannot promote itself by containing imperative language.

## RAG compatibility

This contract reuses the existing RAG filters and boundary evaluations: project/tenant/version/sensitivity/source class, exact/paraphrase/cross-reference, unknown, injection, and authority-boundary cases. It does not redesign retrieval, add a memory graph, or require a new index.

## Failure behavior

Missing origin, invalid source class, injection-like authority claim, protected-fact conflict, or permission request in content yields `UNKNOWN`, `CONTRADICTED`, or `INCOMPLETE` as appropriate. The foundation fails closed for permission and fact writes while preserving content for review.

## Evidence and audit

Fact decisions record claim, origin, source/provenance, authority result, approval reference when needed, and resulting status. Logs are append-only through existing governance surfaces; secrets and hidden model reasoning are not stored.

## Done when

Tests prove that retrieved content cannot grant tools or permissions, external data cannot overwrite protected facts, and existing FACT_LEDGER/RAG behavior remains intact.
