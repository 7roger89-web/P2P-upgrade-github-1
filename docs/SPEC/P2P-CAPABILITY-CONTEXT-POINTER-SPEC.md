# P2P Capability Context Pointer Specification

Status: APPROVED FOR IMPLEMENTATION — agent-decided; no owner decision required
Date: 2026-08-12
Parent: `P2P-CAPABILITY-FOUNDATION-ARCHITECTURE-SPEC.md`

## Purpose

Make progressive disclosure explicit. Core P2P knows that context exists, whether it is relevant, who is authoritative, which scope it covers, how fresh it is, and where it came from. It loads content only after routing establishes relevance.

## Pointer contract

Each pointer declares a stable reference, label, relevance/domain, authority class, allowed scope, freshness/expiry, provenance, content class, and load policy. The pointer is metadata; it is not permission and it is not automatically trusted instruction.

Allowed content classes distinguish `CONTENT`, `INSTRUCTION_AUTHORITY`, `EVIDENCE`, `SCHEMA`, and `UNKNOWN`. An `UNKNOWN` class is not executable and cannot grant authority.

## Progressive-disclosure rules

- Discovery loads pointer metadata only.
- Resolution loads the smallest relevant context set after scope and authority checks.
- Execution receives only resolved, fresh, permitted context and its provenance.
- Evidence records which pointers were used and their freshness at decision time.
- Unrelated skill references remain unloaded. Tiny tasks do not trigger a large context bundle.

## Authority rules

The pointer's authority is bounded by its source class and manifest contract. Project context may describe product vocabulary and constraints; it cannot redefine canonical quorum, grant tools, or approve protected changes. Retrieved documents are content unless separately validated as P2P instruction authority.

## Staleness and conflict

Expired, scope-mismatched, sensitivity-mismatched, or provenance-missing pointers are excluded and reported. Conflicting pointers do not merge silently; the result is `UNKNOWN` or `INCOMPLETE` with the conflict references. Fresh owner input can supersede project-local descriptive context only within the approval boundary.

## Security and operations

Pointer loading is offline-safe and path/scope validated. Diagnostics record pointer IDs and statuses, not content secrets. Pointer changes require affected eval/drift evidence. No vector database, full memory graph, or external retriever is required by this contract.

## Done when

Capability manifests can reference progressive context, route resolution can select only relevant fresh pointers, and tests prove that pointer content cannot grant permissions or bypass approval.
