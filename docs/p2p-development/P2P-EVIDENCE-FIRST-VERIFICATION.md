# P2P Evidence-First Verification

Status: `CANONICAL_VERIFICATION_PROFILE_V1`
Authority: subordinate to `P2P_SUPREME_OPERATING_LAW_V1`; this profile refines existing evidence, completion, risk-proportional execution, and independent-verification rules. It creates no second truth store, router, executor, permission system, promotion authority, or parallel Supreme Law.

## Core contract

```text
P2P_EVIDENCE_FIRST_VERIFICATION_V1=ACTIVE
AGENT_CLAIM_IS_NOT_EVIDENCE=YES
TEST_PASS_PROVES_ONLY_CHALLENGED_BEHAVIOR=YES
OUTPUT_PASS != ACCEPTANCE_PROVEN
GOAL_PASS != PROMOTION
DO_NOT_ASK_THE_AGENT_TO_BE_RIGHT; REQUIRE_THE_CHANGE_TO_PROVE_IT_IS_RIGHT
```

A worker's statement that work is correct, complete, safe, merged, deployed, or production-ready is never sufficient evidence by itself. A passing test proves only the behavior, boundary, environment, and data that test actually challenged. Coverage proves execution reach, not semantic correctness. Static checks prove only their own class of properties. A reviewer must reason from the strongest independent evidence available for the actual claim.

The objective is not to eliminate code inspection. It is to make manual inspection targeted and risk-driven instead of the default acceptance mechanism. Architecture boundaries, auth/security-sensitive code, data migrations, irreversible behavior, canonical governance changes, and other high-impact surfaces may still require direct independent review.

## Proof-carrying change

Every non-trivial implementation or repair must leave a compact evidence packet sufficient for a fresh reviewer to determine what was changed, what was actually challenged, and what remains unproven.

Minimum packet fields:

```text
INTENT
  approved requirement / observable outcome

BEHAVIOR_PROOF
  acceptance scenario(s)
  representative real-path check where applicable
  observed result

REGRESSION_PROOF
  focused regression checks
  relevant broader checks when risk requires them

TEST_QUALITY_PROOF
  why the checks can fail when behavior is wrong
  mutation / adversarial / negative / property evidence when required by lane

STRUCTURAL_PROOF
  architecture / dependency / complexity / duplication checks when relevant

ENVIRONMENT_PROOF
  build / runtime / browser / API / integration / deployment-health evidence when the claim crosses those boundaries

RISK_PROOF
  auth / secrets / security / data / migration / destructive / external-side-effect evidence when relevant

PROVENANCE
  repository
  base SHA
  head SHA
  changed paths
  exact commands or automated checks
  evidence artifact references

VERDICT
  PROVEN | INCOMPLETE | FAILED
  unproven claims / blockers if any
```

The packet may be represented by existing P2P evidence/report artifacts; do not create a second evidence store merely to match this shape. Reuse the current task state, evidence files, PR checks, logs, screenshots, reports, or return packets as appropriate.

## Independence rule

For `FAST`, deterministic self-verification may be sufficient when the change is local, reversible, acceptance is clear, and the nearest-boundary check actually challenges the changed behavior.

For higher lanes, do not let one worker's self-authored implementation plus self-authored tests plus self-declared PASS become the only acceptance authority. Independence can be provided by an existing deterministic oracle, separately authored acceptance contract, mutation/adversarial challenge, real-path QA, independent reviewer, or another existing P2P verifier. Use the smallest independent mechanism sufficient for the risk; do not spawn reviewers decoratively.

## Risk-lane verification contract

This profile reuses the canonical execution lanes already produced by P2P orchestration policy: `FAST`, `STANDARD`, `STRICT`, `CRITICAL`. It does not create a second risk classifier.

| Lane | Minimum evidence expectation |
| --- | --- |
| `FAST` | nearest-boundary deterministic check; focused regression if behavior changed; real-path smoke when the claim crosses a runtime/UI/API boundary |
| `STANDARD` | FAST evidence + explicit acceptance scenario(s) + relevant regression checks + evidence that changed behavior is actually exercised |
| `STRICT` | STANDARD evidence + independent challenge of changed behavioral surface (mutation, adversarial/negative/property test, or equivalent) + integration/E2E where applicable + structural review for cross-cutting architecture |
| `CRITICAL` | STRICT evidence + independent reviewer/verifier + explicit security/data/migration/destructive checks as applicable + representative real-path/production-like verification before any readiness claim; Owner Gates remain unchanged |

Mutation testing is not a universal ritual. Prefer changed-surface or targeted mutation when it gives decision-useful evidence. A surviving mutant is a signal that the current tests may not distinguish correct from incorrect behavior; either strengthen the checks or record a specific justified survivor. If mutation adds no material information for the changed surface, use the equivalent smallest adversarial challenge and state why.

## Real-path rule

A unit or integration suite cannot prove a claim that crosses an environment it never exercised. Examples:

- UI behavior claim -> exercise the real rendered interaction path when practical.
- API integration claim -> exercise the actual request/response boundary or a faithful contract harness.
- deployment-health claim -> verify the deployed target, not only the build artifact.
- connector/provider claim -> verify the relevant authenticated provider surface when the task depends on it.
- data migration claim -> verify representative source-to-destination behavior, invariants, and rollback/recovery expectations.

If the real path cannot be exercised, downgrade the verdict to the strongest truthful claim (`INCOMPLETE`, `UNVERIFIED_RUNTIME`, or the existing canonical equivalent). Never upgrade a lower-boundary PASS into a higher-boundary claim.

## Test-quality rule

A high coverage percentage is supportive evidence, not acceptance authority. Prefer checks that would observably fail under a plausible wrong implementation. For behavioral changes, at least one of the following should normally be present at `STANDARD` or above when applicable:

- acceptance example with an observable expected result;
- negative or boundary case;
- property/invariant check;
- mutation/adversarial challenge;
- regression that reproduces the previously failing behavior;
- real-path comparison against an authoritative source/oracle.

Do not chase arbitrary numeric coverage or mutation thresholds unless the project already has an approved threshold. The question is whether the evidence can distinguish the important wrong behavior from the intended behavior.

## Structural integrity rule

Passing behavior tests does not excuse architecture drift. When a change crosses modules, introduces a dependency, duplicates domain rules, changes a schema, or moves authority boundaries, verify the relevant structural constraint. Prefer existing linters, dependency rules, architecture tests, schemas, type checks, or narrow independent review. Do not add a new architecture framework merely to satisfy this profile.

## Stop rule

When the evidence packet proves the bounded acceptance at the required risk lane and no unresolved blocker or Owner Gate remains, stop. Do not add broad mutation campaigns, full-repository benchmarks, extra reviewers, observability, abstractions, or refactors merely to make the packet look impressive.

If evidence is insufficient, report exactly which claim remains unproven and run the smallest next check or repair that can close that gap.
