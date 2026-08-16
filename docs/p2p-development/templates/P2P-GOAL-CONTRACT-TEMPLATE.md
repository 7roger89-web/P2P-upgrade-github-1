# P2P Goal Contract Template

> **Purpose.** A Goal Contract is a compact, durable document that a session uses to execute a bounded goal. It is derived from `governance/development-control.json` (roadmap, invariants, capability status) and `docs/p2p-development/capability-ledger/capability-index.json` (capability knowledge). It never duplicates them; it references them. A goal starts only when the **owner** prompts for it; goals are never auto-started.

---

## Goal Contract: P2P-CNN (replace CNN with goal number)

### 1. Identity
| Field | Value |
| --- | --- |
| Goal ID | `P2P-CNN` |
| Goal title | (one sentence, plain language) |
| Baseline at start | version + SHA-256 of official baseline from `development-control.json` |
| Working source version | source version string from `VERSION` |
| Opened by | owner prompt (record the exact request) |
| Date opened | ISO timestamp |

### 2. Truth recovery (do BEFORE any change)
- [ ] Load durable state from filesystem: `governance/development-control.json`, `VERSION`, `docs/p2p-development/` artifacts.
- [ ] VERIFY every value this goal needs against those files. **Durable evidence outranks the goal prompt.** If the prompt contradicts durable state, follow durable state and record the discrepancy.
- [ ] Record a recovery checkpoint (internal file, not a source of truth): what was found, what differs from expectations, what evidence already exists.

### 3. Purpose
One paragraph in plain language: what the beginner gains, and why this goal is needed now.

**One primary objective rule.** A goal has exactly one primary objective. It may have supporting criteria, but never two objectives competing for the session's focus. A session tempted to pursue a second objective must stop and open a new goal instead.

### 4. Scope (bounded)
- In scope: (numbered, specific)
- Out of scope: (numbered, explicit exclusions — defer items that need their own goal)
- Mutation boundary: list of paths this goal may change. Changes outside this boundary require owner approval.

### 5. Durable evidence contract (completion criteria)
Numbered criteria, each tied to a filesystem artifact (file, test result, hash, report). A criterion is met only when the artifact exists and passes deterministic verification. Example shapes:
- `CR1: tests/test_p2p_xxx.py passes in full regression with no new failures.`
- `CR2: capability-index.json validates against capability-ledger.schema.json.`
- `CR3: candidate zip SHA-256 recorded; verify stage of package_release.py reports PASS.`

### 6. Anti-goals (rejected patterns this goal must not introduce)
Reference `capability-index.json` records with status `REJECTED` that are adjacent (e.g., `SECOND_TASK_TRUTH_STORE`, `TASK_AS_AGENT`, `AUTO_PROMOTION_AFTER_GOAL_PASS`). Explicitly list each and the behavior to avoid.

### 7. Dependency and readiness check
For each foundation this goal consumes, cite the ledger record and its status. A goal must not claim a foundation whose status is `UNKNOWN` or not durably evidenced.

### 8. Evidence package (required at close)
- Pre-change baseline regression result (recovered by running, never assumed).
- Post-change regression result with classification of every failure: pre-existing / goal-introduced / environment.
- Candidate artifact: path, filename, SHA-256, `UNPROMOTED`.
- Supervisor report path (`reports/supervisor/`).
- Governance update: candidate record appended; `current_development` updated; promotion state **never** changed by the goal session itself.

### 9. Stop rule
The session stops when the evidence package is complete and delivered. It does **not** start the next goal, does **not** promote, and does **not** modify `current_development` beyond the candidate record.

### 10. Owner questions rule
Ask the owner only for genuine owner decisions (design choices, approvals). Never ask the owner to reconstruct technical progress; recover it from durable state.

---

*Template version 1 — created by P2P-C25. Extend only through a goal with evidence.*
