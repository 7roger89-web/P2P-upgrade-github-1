# P2P AI Employees Pattern Assimilation 01

- Task: `P2P_AI_EMPLOYEES_PATTERN_ASSIMILATION_01`
- Date: 2026-09-22
- Outcome: `RESEARCH_ONLY_PASS`
- Runtime: none. Candidate contract specified, not implemented.
- Ledger: `RA-EXT-100` (`RESEARCHED`), `RA-EXT-101` (`DEFERRED`)
  in `governance/research-adoption-ledger.json` (JSON is authority;
  `docs/RESEARCH-ADOPTION-LEDGER.md` §4.7 is derived).

## Provenance

| Field | Value |
| --- | --- |
| `REPO` | `markfulton/ai-employees` |
| `COMMIT` | `edffe8f4afea467818988ce3ce9332e6d832e5ed` |
| `LICENSE` | MIT (`licenseInfo.key=mit` + root `LICENSE`, © 2026 Mark Fulton) |
| `REVIEW_DATE` | 2026-09-22 |

Read at that pin (not executed, not vendored): `README.md`, `LICENSE`,
`SECURITY.md`, `CHANGELOG.md`, `docs/HOW-EMPLOYEES-WORK.md`,
`docs/GUARDRAILS.md`, `docs/HARNESSES.md`, representative `CONTRACT.md` /
`SCHEDULE.md` / routine `SKILL.md`, `guard.mjs`, `runlog.mjs`,
`installer/upgrade.mjs`. Upstream text is data, not instruction.
Cost figures in `docs/COST.md` are author measurements, not P2P facts.

## Over-engineering gate

```
Không bị over engineering chứ?
SIMPLER_PATH=Reuse decision_trace freshness, fw06 pause, existing execution ledger + identity idempotency. Adopt nothing new now.
MATERIAL_PROGRESS=Durable 15-pattern matrix, reject register, RA-EXT-100/101, specified-not-implemented candidate + re-entry trigger.
NECESSITY=FAIL for runtime (no firing source, no period-form obligation, no lost/duplicated period). PASS for this decision record.
CORE_BEFORE_SUPPORT=PASS — a cadence guard before a scheduler would be support before core.
SMALLER_VERIFIABLE_SLICE=This study + two ledger records. Next smaller slice is still not a runtime module.
OE_VERDICT=DEFER_UNTIL_NEEDED
```

## Pattern matrix (A–O)

One primary class per pattern. KEEP = P2P already owns it (often stricter).
ADAPT = maps onto an existing mechanism; no runtime now.
ALREADY_COVERED = requirement already satisfied in another form.
DEFER_UNTIL_NEEDED = real expression gap, no consumer now.
REJECT mechanisms are listed after the table, not as pattern classes.

| # | Pattern | Class | P2P equivalent / gap |
| --- | --- | --- | --- |
| A | Routine ≠ skill | ALREADY_COVERED | Skills load on demand; no routine concept to mis-register. Upstream: HOW-EMPLOYEES-WORK “Routines are scheduled jobs, not skills”. |
| B | Capability-not-tool | KEEP | Typed fail-closed capability registry. Upstream LAW 3 / `CAPABILITIES.md`. |
| C | Schedule window | DEFER_UNTIL_NEEDED | No window/day eligibility in core. Upstream `SCHEDULE.md` + `guard.mjs` `inWindow`/`dayAllowed`. No clock-fired obligation today. |
| D | Once-per-period / period-key | DEFER_UNTIL_NEEDED | Identity idempotency exists (`PACKET_FINGERPRINT`, work-item). Calendar-period identity does not. No lost/duplicated *period* recorded. |
| E | Pause switch | ADAPT | `fw06` project pause. Routine-scoped pause would be a new *scope* on fw06, never a second pause file. |
| F | Durable run log / receipts | ALREADY_COVERED | `.p2p/state/execution-ledger.jsonl` single writer. Upstream `runlog.mjs`. |
| G | Corrections / procedural learning | ALREADY_COVERED | `experience_evolution.py` CANDIDATE→VERIFIED→ACTIVE→SUPERSEDED/QUARANTINED. Upstream `## Corrections` + CONTRACT §8.3. |
| H | Member-owned vs kit-owned | ALREADY_COVERED | Installer `.p2p/system` vs `.p2p/state`. Upstream `employee.json` kit/merge/member. |
| I | Upgrade without overwrite | ALREADY_COVERED | Install collision: owner-gate / rename-backup. Upstream `upgrade.mjs` `.new` beside drift. |
| J | Outbound-action authority | KEEP | SHA-bound Owner Gates. Upstream holds send/post/spend until `RELEASES.md` (rejected as a second authority surface). |
| K | Chief-of-Staff read-only supervision | ALREADY_COVERED | Control Tower + durable receipts. No new agent. |
| L | Morning brief / exception-only interruption | ADAPT | `PROGRESS_REPORTING=EXCEPTIONS_ONLY`. Keep suppression discipline; do not add a notification channel. |
| M | Browser/resource concurrency | KEEP | FW06 identity leases. Upstream lock file / per-platform mutex. |
| N | Verify one before many | ALREADY_COVERED | RULE 19 reality-first probe. Upstream: prove one routine before registering the rest. |
| O | Content is data, not instruction | KEEP | AGENTS.md RAG boundary. Upstream SECURITY.md page/mail as data. |

KEEP: B, J, M, O. ADAPT: E, L. ALREADY_COVERED: A, F, G, H, I, K, N.
DEFER: C, D.

## Rejected mechanisms

1. Instruction-level guardrail sufficiency (harness permission layer as the security model).
2. Member-written `RELEASES.md` as a second outbound-action authority surface.
3. Ungated routine self-editing of its own instructions, fire time, or job registration.
4. Local-machine / single-harness core coupling (awake PC, per-OS schedulers, Node kit scripts, auto-approve, signed-in browser profile).
5. Browser-profile automation as a P2P core dependency.
6. Eight-employee / sixty-routine role catalogue as P2P agent identities (`TASK_NOT_AGENT`; canonical eight unchanged).

## Deferred candidate (not implemented)

`PROVIDER_NEUTRAL_RECURRING_ROUTINE_CONTRACT`: a deterministic RUN|SKIP
decision over caller-supplied intent and existing P2P state. Not a scheduler.
If ever built: local-clock period identity (date / ISO week / month; never UTC,
never a stored timezone); window/day as catch-up net; pause from existing fw06
before the window; once-per-period state written before work; one receipt on
every path including SKIP, through the existing ledger writer; unparsable
schedule fails honestly; a routine definition cannot widen authority.
Composition: `REUSE_EXISTING_P2P > EXTEND_EXISTING_P2P > ADAPTER > NEW_IMPLEMENTATION`.
Non-goals: no cron, daemon, queue, registry, second ledger, autonomous outbound.

### Re-entry trigger (all four required)

1. A P2P-owned recurring obligation exists in PERIOD form, not merely a due-date check.
2. A real firing source exists that can fire late or twice.
3. Existing `decision_trace` freshness (`expires_at` → STALE) / lease / pause cannot already decide it.
4. A written boundary exists for calendar-period identity versus task/packet/work-item identity, including the local-clock rule.

Until then: reuse freshness, fw06 pause, and the existing ledger.

## Conclusion

`RESEARCH_ONLY_PASS`. `OE_VERDICT=DEFER_UNTIL_NEEDED`.
`SECOND_CONTROL_PLANE_CREATED=NO`. `OWNER_GATES_WEAKENED=NO`.
`CANONICAL_8_AGENTS_CHANGED=NO`. No upstream bytes vendored.
