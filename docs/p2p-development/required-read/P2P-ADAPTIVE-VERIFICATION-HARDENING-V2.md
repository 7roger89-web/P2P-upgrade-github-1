# P2P REQUIRED POLICY — Adaptive Verification Hardening v2

**Owner decision:** ACCEPTED  
**Decision date:** 2026-08-21  
**Target:** Existing `P2P-FRAMEWORK-04 — QUALITY, EVIDENCE & LEARNING` adaptive-verification seam  
**New framework:** NO  
**Second orchestrator/router:** NO  
**Runtime implementation status:** NOT YET WIRED TO CANONICAL REPO  
**Promotion/release:** NO

## Canonical principle

> **RIGHT EVIDENCE, NOT MAXIMUM TEST COUNT.**

P2P verifies what the application actually owns, at the lowest verification layer capable of proving the acceptance requirement, and escalates only from evidence, affected surface, material risk, lifecycle stage, or explicit applicable NFRs.

## Hard rules

1. Test behavior the application owns; do not re-prove mature dependency guarantees by brute force.
2. Derive verification from goal + acceptance contract + affected surface + applicable FR/NFR + lifecycle stage.
3. Start with deterministic/static checks where applicable.
4. Run the smallest relevant targeted test before broader integration/regression.
5. Escalate scope only with an explicit justification/evidence edge.
6. `reasoning_effort` MUST NOT automatically widen `verification_scope`.
7. Full-suite execution is not a default task-level action; reserve broad suites for lifecycle gates where they materially increase confidence.
8. E2E, race, load, stress, soak, chaos, browser-money tests and high-cost performance tests require explicit applicability evidence.
9. NFRs require an `NFR_APPLICABILITY_GATE`; an aspirational/unbound NFR is not a hard gate.
10. An NFR whose scale assumption conflicts with project truth is `NOT_APPLICABLE` or `OWNER_REVIEW`, not silently mandatory.
11. Database/security/auth/permission/data-integrity/financial boundaries may justify deeper verification even for small diffs.
12. Unknown affected surface or unknown material NFR applicability fails closed; it does not trigger “run everything”.
13. Classify a test failure before changing implementation.
14. Failure taxonomy includes at least:
    - IMPLEMENTATION_DEFECT
    - TEST_DEFECT
    - ENVIRONMENT_DEFECT
    - FLAKY_TEST
    - DEPENDENCY_FAILURE
    - DATA_FIXTURE_DEFECT
    - RESOURCE_EXHAUSTION
    - TIMEOUT_POLICY_DEFECT
    - SPECIFICATION_CONFLICT
    - UNKNOWN_FAILURE
15. Never retry failures blindly.
16. Never weaken a valid test just to obtain GREEN.
17. TDD tests must derive from requirements/acceptance examples, not model-invented behavior.
18. Every spawned test/runtime process must be accounted for and safely cleaned up if P2P owns it.
19. Never kill unrelated processes not owned by the active execution.
20. Stop verification when the acceptance contract is proven and no unresolved material regression remains.
21. Goal Pass != Promotion.

## Verification ladder

- `L0_STATIC`: lint / format / type / compile / schema/static checks.
- `L1_TARGETED`: smallest unit or focused behavior test proving the changed requirement.
- `L2_COMPONENT`: affected component/subsystem.
- `L3_INTEGRATION`: relevant system boundary only.
- `L4_E2E`: materially affected critical user journey only.
- `L5_NFR_SYSTEM`: security/race/load/stress/performance/soak/chaos only when applicable.
- `L6_RELEASE`: broad/full regression and release-certification gates.

A task does not climb automatically to L6.

## NFR Applicability Contract

Each NFR should carry:
- `nfr_id`
- `requirement`
- `source`
- `applicability`: APPLICABLE | NOT_APPLICABLE | UNKNOWN | OWNER_REVIEW
- `project_truth_evidence`
- `scale_assumption`
- `verification_layer`
- `cost_class`
- `hard_gate`
- `reason`

`UNKNOWN` must not silently become a hard gate or silently disappear.

## Verification-plan inputs

- goal/acceptance contract
- affected surface
- mutation class
- risk class
- project profile
- lifecycle stage
- applicable FRs/NFRs
- available test/eval inventory
- resource budget
- test-history/flakiness evidence
- execution environment
- reasoning effort (informational only; not a scope multiplier)

## Verification-plan outputs

- required checks in order
- explicitly skipped/deferred checks with reason
- escalation edges with evidence
- stop condition
- resource/cost class
- process ownership/cleanup contract
- failure-classification requirement
- release-gate handoff where relevant

## Owned-behavior examples

Bad: prove UUID v4 can never collide by spawning many workers.  
Good: prove the application's duplicate-key boundary fails safely and preserves business invariants.

Bad: prove PostgreSQL ACID guarantees.  
Good: prove the application's own transaction, rollback, retry/idempotency and business invariants at the integration seam.

## Non-goals

This policy MUST NOT:
- reduce valid safety/security/data-integrity testing merely to save quota;
- turn performance/security NFRs off globally;
- make test selection a new orchestrator;
- bypass FW04 quality verdict;
- change permissions;
- change release/promotion authority;
- mutate a project merely because a test is available;
- normalize flaky tests by blind retry.

## Relation to existing P2P

This is a hardening of existing FW04 adaptive verification, which already:
- builds a per-task Quality Contract;
- prefers deterministic evals;
- uses Code-Impact / affected-surface evidence;
- separates execution success from quality proof;
- can require independent verification for higher-risk work.

The v2 hardening adds **applicability, proportionality, lifecycle timing, failure classification, resource awareness, and process hygiene**.
