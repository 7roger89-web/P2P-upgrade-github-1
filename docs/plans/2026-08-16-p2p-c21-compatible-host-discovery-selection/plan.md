# P2P-C21 Compatible Host Discovery & Selection Policy Foundation

## Goal
Implement the minimum missing coordinating layer that derives a bounded host requirement from the existing C20 portable request, evaluates known host profiles with deterministic hard gates, and selects the minimum sufficient compatible host without launching or routing execution.

## Scope
The editable surfaces are `.p2p/system/p2p_capabilities/host_selection.py`, its focused tests, package/runtime metadata only when required, governance provenance, and C21 evidence. C20 host-executor contracts, C18 orchestration policy, C19 context retrieval, C12/C15 execution semantics, canonical governance, and historical artifacts are preserve-only or inspect-only.

## Non-goals
Automatic cross-host launching, remote control, provider/model routing, background autonomy, swarm execution, cost optimization, account management, live vendor discovery, and promotion of the official baseline remain out of scope.

## Phases
- [ ] P0 Recovery and actual-status: recover governance, version, C20 state, source/test surfaces, and record discrepancies.
- [ ] P1 C21 implementation: add neutral requirement, discovery, availability, candidate, decision, deterministic gates, minimum-sufficient tie-break, and safe reselection seams.
- [ ] P2 Verification: run HS1-HS30 controlled tests, focused integration tests, full regression, governance/security/package checks, and detect-changes.
- [ ] P3 Closure: update durable roadmap with provenance, build a new immutable unpromoted candidate if package-affecting, and record final supervisor verdict.

## Acceptance
The implementation must produce explicit SELECTED, NO_COMPATIBLE_HOST, or HOST_EVIDENCE_INSUFFICIENT decisions; preserve UNKNOWN capability/availability semantics; never grant permission; preserve environment authority and partial-mutation freeze; remain brand/model/provider neutral; and require zero host-choice questions for the beginner path.

## Plan files
- `actual-status.md` records source-of-truth status and discrepancies.
- `evidence.md` records stable evidence IDs and commands.
- `benchmark.md` records measured counts, sizes, hashes, and timings only.
- `plan.md` is the execution checklist and acceptance boundary.
