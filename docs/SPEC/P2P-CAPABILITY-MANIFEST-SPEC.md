# P2P Capability Manifest Specification

Status: APPROVED FOR IMPLEMENTATION — agent-decided; no owner decision required
Date: 2026-08-12
Parent: `P2P-CAPABILITY-FOUNDATION-ARCHITECTURE-SPEC.md`

## Purpose

Provide the smallest reusable declaration needed to discover, route, authorize, and verify a capability. Metadata is limited to fields that affect one of those decisions.

## Allowed classes

`TYPE` MUST be one of `SKILL`, `OPTIONAL_SPECIALIST`, `GOVERNANCE_POLICY`, `KNOWLEDGE_SOURCE`, `EVIDENCE_PROVIDER`, or `BACKEND_PROVIDER`.

## Required manifest fields

| Field | Contract |
|---|---|
| `CAPABILITY_ID` | Stable lowercase identity; unique within the registry. |
| `TYPE` | One allowed class. |
| `DESCRIPTION` | Plain-language outcome/domain description. |
| `TRIGGERS` | Positive natural-language or governance signals. |
| `NEGATIVE_TRIGGERS` | Signals that exclude routing or invocation. |
| `INVOCATION_CLASS` | `USER_REQUESTED`, `MODEL_ROUTABLE`, or `GOVERNANCE_MANDATED`. |
| `CANONICAL_QUORUM_MEMBER` | Boolean; true only for one exact canonical governance identity. |
| `OPTIONAL_SPECIALIST` | Boolean; true only for an optional specialist. |
| `AUTHORITY` | Allowed decision/evidence boundary. |
| `PROHIBITED_ACTIONS` | Explicit out-of-scope actions. |
| `REQUIRES` | Capability or readiness prerequisites. |
| `CONTEXT_POINTERS` | References to relevant progressive-disclosure context. |
| `APPROVAL_BOUNDARY` | Changes requiring owner approval. |
| `EVIDENCE_CONTRACT` | Required claim/evidence/status shape. |
| `TRUST_LEVEL` | `PURE_DATA`, `HOST_CODE`, or `EXTERNAL_SERVICE`. |
| `UPSTREAM_PROVENANCE` | Source, version/pin, license, verification, and recheck metadata when applicable. |
| `VERSION` | Capability contract version. |
| `STATUS` | `ACTIVE`, `DISCOVERED`, `DEFERRED`, or `RETIRED`. |

No unused or decorative metadata is required. A field may be omitted only when the registry schema explicitly supplies a safe default; required routing, authority, and evidence fields may not be omitted.

## Canonical safety

Default `CANONICAL_QUORUM_MEMBER` is false. The only declarations allowed to set it true are the eight canonical governance identities. A manifest is invalid if it marks Aesthetica true, names an unknown canonical identity, duplicates an identity, declares a ninth identity, or makes the denominator anything other than 8. Invalid manifests are rejected before registry publication.

`OPTIONAL_SPECIALIST` defaults false. A declaration with both canonical and optional true is invalid. Aesthetica MUST declare `TYPE=OPTIONAL_SPECIALIST`, `OPTIONAL_SPECIALIST=true`, and `CANONICAL_QUORUM_MEMBER=false`.

## Authority and evidence

`AUTHORITY`, `PROHIBITED_ACTIONS`, `APPROVAL_BOUNDARY`, and `EVIDENCE_CONTRACT` are declarative boundaries, not permissions. A manifest cannot grant tools, write access, owner authority, or a quorum vote. A retrieved manifest is data until validated against the installed registry.

## Validation and operations

Validation reports stable reason codes for missing field, invalid enum, duplicate ID, invalid canonical declaration, unsafe trust level, missing provenance, or contradictory authority. The registry records the manifest hash and validation time. It does not phone home or install dependencies. A changed manifest requires a fresh validation and affected evaluation; it does not silently alter existing project state.

## Done when

The runtime can load a minimal registry containing the canonical governance identities, `p2p-uiux`, and the real optional Aesthetica declaration; invalid canonical variants fail closed; unknown optional declarations remain non-fatal to core P2P.
