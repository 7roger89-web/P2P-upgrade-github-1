# P2P canonical lineage repair authority model

This record is append-only for `P2P-CANONICAL-LINEAGE-REPAIR-01`. The
canonical authority is `origin/main`, and its `.19` official baseline remains
official until a later independent owner promotion.

The successor branch keeps these authorities separate:

- `governance/development-control.json`: official baseline state, development
  lineage, and historical reconciliation.
- `manifest/package.json`: candidate package identity.
- `.p2p/system/p2p_capabilities/capabilities.json`: capability registry only;
  it is not a package-version authority.
- Candidate archive metadata: distribution manifest, source binding, artifact
  identity, inventory, and checksum set.

Project-context logical surfaces are intentionally honest:

| Surface | Status |
|---|---|
| PROJECT_IDENTITY | DERIVED |
| PRODUCT_MODEL | PROPOSED or DERIVED from project pin |
| PROJECT_CONSTITUTION | PROPOSED unless an authoritative project supplies one |
| PROJECT_MAP | DERIVED and durable only after explicit save |
| ARCHITECTURE_MAP | PROPOSED unless present in project context |
| UI_LAYOUT_MAP | PROPOSED or NOT_IMPLEMENTED |
| DATA_MAP | PROPOSED or NOT_IMPLEMENTED |
| DECISION_LEDGER | DERIVED/read-only projection |
| PROJECT_CONSTRAINTS | DERIVED or UNKNOWN |
| GOAL_GRAPH | PROPOSED or UNKNOWN |
| PROJECT_CONTEXT_FINGERPRINT | DERIVED |

`PROJECT_CONTEXT_READY` never grants execution permission. The runtime gate
requires a durable fresh project map, an explicit mutation intent, and a
permission grant. A missing or stale map, or a denied permission, blocks
mutation; read-only bootstrap discovery remains allowed.

The Manus boundary remains provider-neutral:

`P2P control plane -> ExecutionTarget -> Manus adapter/backend -> external
result -> P2P receipt/verifier/checkpoint`.

The recovered native council status is honest: supported through
backend-attested internal members with raw member results and per-member
failure support; per-member external IDs and P2P direct child control are not
exposed/supported. A P2P council adapter is feasible, not an externally
observable eight-member Manus council.
