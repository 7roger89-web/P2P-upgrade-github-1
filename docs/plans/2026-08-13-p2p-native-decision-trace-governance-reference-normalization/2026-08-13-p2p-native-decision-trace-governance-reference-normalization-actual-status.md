# P2P Native Decision Trace - Governance Reference Normalization Actual Status

Title: P2P Native Decision Trace - Governance Reference Normalization
Date: 2026-08-13
Status: COMPLETE / PASS
Companion plan: `docs/plans/2026-08-13-p2p-native-decision-trace-governance-reference-normalization/2026-08-13-p2p-native-decision-trace-governance-reference-normalization-plan.md`
Companion evidence: `docs/plans/2026-08-13-p2p-native-decision-trace-governance-reference-normalization/2026-08-13-p2p-native-decision-trace-governance-reference-normalization-evidence.md`
Companion benchmark: `docs/plans/2026-08-13-p2p-native-decision-trace-governance-reference-normalization/2026-08-13-p2p-native-decision-trace-governance-reference-normalization-benchmark.md`

## Scope

Target: Decision Trace POLICY_REFS capture normalization and governed-root
lookup, plus fresh/upgrade/reinstall/package/runtime evidence.

Out of scope: old .5 artifact, App Game Truyen, Logistics, real projects,
UIUX redesign, discovery, specialists, agents, providers, external
dependencies, graph/RDF/MCP, and unrelated trace fields.

## Relationship / Impact Evidence

| Unit | Evidence | Related count | Relationship | Impact |
|---|---|---:|---|---|
| scripts/p2p_workflow.py | E0-P0A-IMPACT1 | 4 listed; 143 local; 36 inbound | emitter/hotspot | inspect-only |
| .p2p/system/p2p_capabilities/decision_trace.py | E0-P0A-IMPACT1 | 1 indexed; runtime import unresolved | capture/resolver authority | edit P1-A |
| scripts/p2p_decision_trace.py | E0-P0A-IMPACT1 | 1 indexed | CLI wrapper | preserve |
| tests/test_p2p_decision_trace.py | E0-P0A-IMPACT1 | 3 local | behavior tests | edit P1-B |
| .5 ZIP | E0-P0A-BASE1 | n/a | immutable release | do-not-touch |

## Current Status Matrix

| Unit | Current state | Required state | Status | Evidence | Next action |
|---|---|---|---|---|---|
| .5 artifact | verified/immutable | exact preservation | correct | E0-P0A-BASE1 | preserve-only |
| workflow capture | emits two bare names | runtime canonicalizes input | partial | E0-P0A-EMIT1 | inspect-only |
| trace capture | stores bare policy refs | new refs are governance/... | correct | E1-P1A-NORM1 | P2 package |
| policy resolver | root-only fallback | exact governed-root resolution | correct | E1-P1A-NORM1 | P2 package |
| legacy trace query | readable but false missing | deterministic where target exists | correct | E1-P1A-COMPAT1 | P2 lifecycle |
| invalid refs | missing is honest | remain missing | correct | E1-P1B-NEG1 | P2 negative |
| package behavior | .5 carries defect | candidate resolves valid refs | partial | E0-P0A-BASE1 | P2 candidate |
| canonical governance | exactly 8, denominator 8 | unchanged | correct | E0-P0A-AUTH1 | preserve-only |
| Aesthetica | optional/noncanonical | unchanged/non-simulated | correct | E0-P0A-AUTH1 | preserve-only |
| user boundary | untouched | untouched | correct | E0-P0A-BOUNDARY1 | preserve-only |

## P2 Lifecycle Refresh

| Surface | Result | Evidence |
|---|---|---|
| Candidate artifact | `8.4.7-C-codex.6`, SHA-256 `b8689fb812a438f379fc1d84353f2e4e4c9c0c234c1e22539b2bc32fd15b8156`, 2,336,913 bytes, 399 ZIP members | E2-P2A-ARTIFACT1 |
| Package boundary | `PASS`; 0 forbidden/transient members | E2-P2A-DOCTOR1 |
| Fresh install / WHY | `PASS`; 11 resolved, valid policy refs present | E2-P2B-FRESH1 |
| Upgrade from `.5` | `PASS`; old ledger hash and trace count preserved; legacy refs resolve | E2-P2B-UPGRADE1 |
| Same-version reinstall | `PASS`; no ledger/policy/backup churn | E2-P2B-REINSTALL1 |
| Windows / WSL POSIX | `PASS` | E2-P2C-PORTNEG1 |
| Invalid reference | `PASS`; deliberate invalid remains `MISSING_REFERENCE` | E2-P2C-PORTNEG1 |
| Regression/security | `PASS`; 49 tests, DT1-DT24, UIUX DW1-DW18, doctor/drift/secret | E2-P2C-REGRESS1 |

## P2 Status Refresh

| Refresh | Date | Basis | Status changes | Evidence | Next update |
|---|---|---|---|---|---|
| R2 | 2026-08-13 | candidate package and lifecycle certification | package partial -> correct; fresh/upgrade/reinstall/POSIX/negative/security -> correct | E2-P2A-ARTIFACT1..E2-P2C-NEXT1 | independent P3 supervisor |
| R3 | 2026-08-13 | independent supervisor acceptance | all RN1-RN20 -> PASS; stop rule satisfied | E3-P3A-SUPERVISOR1..E3-P3A-CLOSE1 | stop |

## Invariant Family Map

Workflow capture -> native make_trace -> existing JSONL ledger -> query
resolver -> CLI/export/WHY -> package/install runtime -> lifecycle tests.

Forbidden fallback: arbitrary directory search, fuzzy basename matching,
absolute developer path, or rewriting historical traces.

## Phase Touch Map

| Unit | Relationship | Plan item | Touch mode | Constraint |
|---|---|---|---|---|
| native runtime | capture/resolver | P1-A | edit | POLICY_REFS only |
| workflow | emitter | P1-A | inspect-only | input shape preserved |
| CLI wrapper | loader | P1/P2 | preserve/validate | no duplicate runtime |
| tests | behavior | P1-B | edit | trigger -> query observable |
| governance files | targets | P1/P2 | validate-only | exact files only |
| .5/user projects | protected | all | do-not-touch | hash/boundary invariant |

## Status Refresh Log

| Refresh | Date | Basis | Status changes | Evidence | Next update |
|---|---|---|---|---|---|
| R0 | 2026-08-13 | baseline before implementation | capture partial; resolver wrong; boundaries correct | E0-P0A-AUTH1..E0-P0A-BOUNDARY1 | P1-A runtime; P1-B tests |
| R1 | 2026-08-13 | P1-A/P1-B focused verification | capture partial -> correct; resolver wrong -> correct; legacy partial -> correct; invalid untested -> correct | E1-P1A-NORM1..E1-P1B-SRC1 | P2 candidate/lifecycle |

## Detailed Finding

The two reported refs exist under `.p2p/system/governance`. The emitter passes
bare names; the resolver first checks catalog and then only `project-root / ref`.
The proven rule is:

```text
new policy refs: governance/<POSIX-relative-path>
legacy bare refs: exact aliases into .p2p/system/governance or governance
invalid/unsafe refs: MISSING_REFERENCE
```

## Final P0/P1 Decision

- [x] P0 complete; next phase was narrow and is now complete.
- [x] P1 complete; P2 package/lifecycle phase is unblocked.
- [x] P2 complete; P3 independent supervisor review is unblocked.
- [x] P3 complete; supervisor PASS and RN1-RN20 are closed.
- [ ] P0 blocked.

Decision note: the native POLICY_REFS rule is implemented and direct evidence
proves valid canonical/legacy resolution, honest invalid failure, Windows
separator handling, no path leak, and unchanged DT1-DT24/canonical safety.
Candidate `.6` lifecycle evidence proves fresh, upgrade, reinstall, WSL/POSIX,
package boundary, security, and regression acceptance. Supervisor closure is
complete; the Goal is closed under the stop rule. Exactly one residual-risk
recommendation remains: separately verify real Aesthetica execution identity
when real execution proof exists; do not simulate it.
