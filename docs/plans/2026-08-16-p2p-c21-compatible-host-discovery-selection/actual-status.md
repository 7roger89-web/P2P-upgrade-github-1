# Actual Status — P2P-C21

## Durable recovery

The authoritative Windows source is `D:\AI\P2P_dev\P2P-8.4.6-C-Codex-Edition-v4`. It is a release/source package and has no `.git` directory. `governance/development-control.json` records official baseline `8.4.7-C-codex.19` as `PROMOTED_VERIFIED / IMMUTABLE`; C20 is preserved as DONE/PASS and unpromoted historical evidence. C08 remains DEFERRED and C09 remains BLOCKED / EVENT_EVIDENCE_UNAVAILABLE.

## Status matrix

| Surface | Status | Result |
|---|---|---|
| C20 HostCapabilityProfile | correct | Reused without semantic weakening |
| C20 PortableExecutionRequest | correct | Source for bounded requirement derivation |
| C20 evaluate_host_preflight | correct | Reused as per-profile hard gate |
| C20 selector | partial before C21 | C21 now supplies deterministic multi-host policy without replacing C20 |
| HostRequirementProfile | correct | Implemented and request-derived |
| Host discovery record | correct | Explicit records only; provenance and freshness retained |
| Availability states | correct | KNOWN_AVAILABLE, KNOWN_UNAVAILABLE, UNKNOWN |
| Minimum-sufficient selector | correct | Deterministic hard gates and stable tie-break |
| Portable handoff | correct | Reuses C20 handoff; no launcher |
| Safe reselection | correct | Only before execution/possible mutation |
| Decision Trace integration | correct | Structured reason codes; no hidden chain-of-thought |
| Governance / lineage | correct | C21 DONE/PASS and candidate UNPROMOTED |
| Git commit lifecycle | blocked | Supplied source package has no `.git` |

## Scope boundary

No automatic cross-host launching, remote control, provider/model routing, background monitor, worker pool, swarm expansion, cost optimizer, account manager, or live Manus adapter was added.
