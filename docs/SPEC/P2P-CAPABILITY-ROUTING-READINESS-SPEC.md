# P2P Capability Routing and Readiness Specification

Status: APPROVED FOR IMPLEMENTATION — agent-decided; no owner decision required
Date: 2026-08-12
Parent: `P2P-CAPABILITY-FOUNDATION-ARCHITECTURE-SPEC.md`

## Single-router boundary

The existing P2P router remains the only routing surface. The foundation supplies registry data, trigger scoring, negative-trigger exclusion, readiness facts, and explainable decisions to that route. No router agent, meta-agent, nested workflow, or “invoke everything related” policy is introduced.

## Invocation classes

- `USER_REQUESTED`: the user names a capability or explicitly asks for its domain.
- `MODEL_ROUTABLE`: natural-language scope makes a capability the appropriate primary/secondary/supporting choice; beginners need not know capability names.
- `GOVERNANCE_MANDATED`: an existing governance or approval contract requires a policy/evidence capability.

## Route classifications

Every candidate is classified as exactly one of `PRIMARY`, `SECONDARY`, `SUPPORTING`, or `NOT_APPLICABLE`. The decision considers scope, project context, positive triggers, negative triggers, value, readiness, collision, ambiguity, cost, and approval impact. The route output includes the selected class, capability ID, reason code, readiness, evidence references, and alternatives rejected by a negative trigger or insufficient value.

The router selects the smallest useful set. A related capability is not invoked merely because it exists. A tiny cosmetic change may receive a lightweight decision; a broad UI/UX request may use `p2p-uiux` and a real Aesthetica specialist when value and readiness justify it.

## Collision and ambiguity

When multiple domains overlap, the router records the collision and selects the narrowest primary domain. A mobile readability/contrast request is UIUX-primary with accessibility-supporting reasoning; it does not create a new specialist. Backend/database wording is a negative trigger for Aesthetica. An unknown optional provider cannot block P2P core routing.

## Readiness states

Readiness states are distinct and monotonic only within one inspected snapshot:

1. `INSTALLED`: the managed capability source is present.
2. `DISCOVERED`: the registry can identify and parse it.
3. `ELIGIBLE`: request scope, negative triggers, authority, and prerequisites permit use.
4. `RESOLVED`: required context and dependencies are selected and fresh enough.
5. `EXECUTABLE`: the actual runtime/profile/entry path is available and validated.
6. `HEALTHY`: an execution/evidence check passed for the current snapshot.

Profile existence is not runtime proof. For Aesthetica, the required chain is `SOURCE EXISTS -> PACKAGE CONTAINS -> INSTALLER INSTALLS -> RUNTIME DISCOVERS -> PROFILE RESOLVES -> AGENT EXECUTES -> IDENTITY VERIFIED`. Missing evidence produces `PROFILE_UNAVAILABLE` or `INCOMPLETE`; it never simulates the specialist.

## Failure and logging

Unknown capability, stale context, invalid registry, unavailable execution, collision without evidence, and negative-trigger exclusion are explicit statuses. Route diagnostics are safe to log and contain no secrets. A route decision cannot mutate a project.

## Verification examples

The evaluation suite owns cases for UI design, backend query optimization, mobile readability, tiny padding, unknown provider, invalid canonical declaration, and beginner natural-language routing. This SPEC defines route semantics; the test SPEC defines expected results.

## Done when

One existing router emits explainable scoped decisions and readiness states, preserves the current UIUX CLI contract, excludes Aesthetica from backend routing, and never simulates an unavailable profile.
