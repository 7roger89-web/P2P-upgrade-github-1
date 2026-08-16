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

*Template version 1 — created by P2P-C25. Extend only through a goal with evidence.*
