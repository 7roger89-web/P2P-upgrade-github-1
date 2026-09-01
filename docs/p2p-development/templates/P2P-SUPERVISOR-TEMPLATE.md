# P2P Supervisor Review Template

> **Purpose.** Every goal closes with an independent supervisor review stored in `reports/supervisor/`. The reviewer is an AI session that did not perform the goal's implementation work ("parent reviews worker artifacts" — superlearn principle). The review checks the evidence package against durable state and issues a verdict with reasoning. This file is the reusable template; each review is a separate file named `rp_supervisor_{date}_{time}_by_{reviewer}_{goal_id}.md`.

---

## Supervisor Review: {goal_id}

| Field | Value |
| --- | --- |
| Review ID | auto-generated |
| Goal reviewed | `P2P-CNN` |
| Reviewer | reviewer identity and date |
| Relationship | reviewer did NOT implement this goal (independence declaration) |

### Verifier
{reviewer identity, date, and a one-line declaration that the verifier independently re-ran the deterministic checks listed in section 1 rather than relying on the implementation session's report.}

### 1. Verification performed (list the actual checks, each with result)
- [ ] Governance record exists and matches claimed state (`development-control.json` candidate record).
- [ ] Candidate artifact exists at the recorded path; SHA-256 matches.
- [ ] `package_release.py verify` PASS on the candidate (or documented reason if not applicable).
- [ ] Regression baseline was recorded pre-change and post-change; every failure classified (pre-existing / goal-introduced / environment).
- [ ] No mutations outside the goal's stated mutation boundary (drift check against `runtime-manifest.lock.json` where applicable).
- [ ] Evidence contract criteria re-checked against the actual artifacts (rerun where deterministic).
- [ ] Charter/ledger/invariant consistency: new records comply with `capability-ledger.schema.json` and do not duplicate authority (`NO_SECOND_TRUTH_STORE`, `NO_COMPETING_ROUTER` checked).
- [ ] Anti-goals verified absent (rejected patterns referenced in the Goal Contract).
- [ ] **DECLARED_CAPABILITY_SCOPE**: every capability the goal touches is declared in the Goal Contract; no undeclared capability was promoted, verified, or re-statused.
- [ ] **ACTUAL_CAPABILITY_DELTA**: the Ledger Delta — Actual section of the Goal Contract lists exactly the deltas recorded, and no status change exists in the ledger that is absent from the delta section.
- [ ] **STATUS_EVIDENCE**: every `STATUS_CHANGED` delta cites a verifying artifact that exists and passes; no status relies on chat-only claims. `OWNER_ACCEPTS_CAPABILITY != CAPABILITY_IMPLEMENTED`: a capability with `origin_type: OWNER_ACCEPTED_PROPOSAL` must remain `PLANNED` unless a durable verification artifact justifies promotion.
- [ ] **PROVENANCE**: every changed record has `origin_refs` (no fabricated origins) and a valid `origin_type` enum value; `UNKNOWN` origin_type only with refs exactly `['origin_unknown_or_not_durably_recovered']`.
- [ ] **DEPENDENCY_VALIDITY**: every changed record's `dependencies` references valid ledger IDs, has no self-dependency, no invalid duplicates, and introduces no new cycle; a rejected or obsolete capability is not newly required without explicit documentation.
- [ ] **ROADMAP_SYNC**: roadmap impact declared in the Goal Contract matches the governance record; no orphaned `PLANNED`/`ACTIVE` capability without a roadmap presence, and no roadmap item referencing a capability absent from the ledger.
- [ ] **TERMINAL_STATE_CONSISTENCY**: the terminal verdict in the terminal report equals the roadmap item status and the `current`/`likely_next` values in governance (`PASS`→`DONE`, `BLOCKED`→`BLOCKED`, `FAIL`→`FAIL`); no silent divergence across roadmap, development-control, report, and supervisor verdict.
- [ ] **CANDIDATE_POLICY_COMPLIANCE**: the deterministic candidate policy was applied (`CANDIDATE_REQUIRED` declared in the contract); if `YES` and verdict `PASS`, the candidate record exists with a non-placeholder SHA-256, verify evidence, and `UNPROMOTED` status; if `NO`, no candidate record claims otherwise.
- [ ] **CAPABILITY_CLAIM_SEPARATION**: machinery capability statuses (evidence-based: `FOUNDATION_READY`, `PARTIAL`) are never conflated with goal roadmap statuses (`DONE`/`BLOCKED`), and no outcome capability is assigned a machinery-only status without real execution evidence.
- [ ] **DEVELOPMENT_CONTROL_SYNC**: `current_development`, `candidate_records`, provenance, and the capability ledger agree with the roadmap projection; no record references a state this goal did not durably change.
- [ ] **PR_LINEAGE_INTEGRITY**: this goal's branch contains the full ancestry of its parent branch (every prior merged-equivalent branch tip is an ancestor), and the pull-request base matches the declared parent branch; any retarget is reported to the Owner with no commit rewrite.
- [ ] **NO_UNDECLARED_CAPABILITY_PROMOTION**: no capability status rose to `VERIFIED_IMPLEMENTED` or `FOUNDATION_READY` without a Goal Contract that declared it in advance.

### 2. Discrepancies found
List every discrepancy between the claim and the evidence, however small. An empty list must be stated explicitly ("No discrepancies found").

### 3. Verdict
One of: **PASS** / **CONDITIONAL_PASS** (named conditions, owner-visible) / **FAIL**.
Justification in plain language, 3–8 sentences, tied to check results above.

### 4. Risk statement
What a future session or the owner should still be careful about, given this goal's evidence.

### 5. Promotion recommendation (informational only)
Supervisor may recommend promotion or not; **promotion itself is an owner approval event** and never executed by the session.

---

*Template version 3 — extended by P2P-C29 (terminal-state consistency, candidate policy compliance, capability claim separation, development-control sync, PR lineage integrity) and by P2P-C26 (provenance, dependency, and ledger-delta checks). Extend only through a goal with evidence.*
