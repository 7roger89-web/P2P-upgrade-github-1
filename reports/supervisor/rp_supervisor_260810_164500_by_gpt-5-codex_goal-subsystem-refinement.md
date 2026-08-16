# Supervisor Report: P2P Goal subsystem refinement

## Verdict

`PASS`

The focused Goal refinement satisfies the attached acceptance scope. No residual
Goal invariant gap was found within the package and safe-fixture scope, and no
duplicate governance or Goal subsystem was introduced.

## Authority and scope

- User authority: attached request `Perform one FINAL focused refinement of the P2P Goal subsystem...`.
- Required scope: Goal eligibility, oracle-backed Goal Contract/Linter, item classes,
  work type, bounded exploration, iteration/mutation discipline, terminal behavior,
  capsule/status continuity, beginner routing, ten safe cases, and existing-gate regression.
- Preserve-only surfaces: existing bootstrap, Eval, FACT_LEDGER, Live Specs,
  Approval, Drift, adaptive quorum, Execution Ledger, doctor, and immutable source baseline.
- Anvien was attempted for target repository evidence but the package path is not registered;
  local source, tests, installer, acceptance, doctor, drift, and lock evidence are the declared fallback.
- The package has no `.git` metadata. No repository was initialized and no checkpoint commit is claimed.

## Source and invariant review

Reviewed `scripts/p2p_workflow.py`, the five affected P2P guidance/state surfaces,
`manifest/package.json`, focused tests, existing workflow tests, and the coder report.

- Eligibility emits exactly `DIRECT TASK`, `PLAN FIRST`, `GOAL`, or `SEPARATE GOALS`.
- Ambiguous/open-ended input routes to bounded `PLAN FIRST`; independent objectives are separated.
- Goal Contracts persist one primary objective, authoritative context, constraints,
  out-of-scope boundary, protected decisions, STOP conditions, evidence reuse rule,
  work-item classes, work type, exploration policy, failed approaches, mutation records,
  iteration discipline, and structured verification oracles.
- The Goal Linter fails closed when a mandatory criterion lacks an oracle or contains
  placeholder oracle text.
- Exploration is one primary lane, at most one alternative after primary failure/evidence,
  and no speculative third lane; failures are appended to the Execution Ledger.
- PASS is terminal; post-PASS approach recording returns `PASS_STOPPED`.
- BLOCKED returns one decision/action and optional backlog is not a blocker.
- Capsules and project status expose eligibility, mandatory/PASS criteria, reusable evidence,
  bottleneck, work type, active lane, failures, backlog, approval, and terminal state.
- Existing P2P control paths remain consumed rather than reimplemented.

## Verification evidence

- Syntax: final in-memory AST parse PASS for the changed Python sources; prior coder
  `py_compile` evidence also PASS.
- Tests: `python -m unittest discover -s tests -p 'test_*.py'` — `17/17 PASS`.
  This includes 13 focused Goal tests and 4 existing workflow regression tests.
- Acceptance: `python scripts/p2p_workflow.py acceptance --package .` — `PASS`.
  All 10 Goal cases PASS, and new-project/existing-project workflow fixtures PASS.
- Fresh install: installed helper doctor PASS; installed vague-request `classify` returns
  `PLAN FIRST`; installed acceptance `run` returns PASS and stops after PASS.
- Package doctor: `python scripts/doctor.py --package .` — PASS; 22 skills, eight named
  agents, 152/152 source baseline, helper distribution, manifest, and governance checks PASS.
- Drift: `python scripts/p2p_governance.py drift --root . --governance governance` — PASS;
  failures `[]`, warnings `[]`.
- Protected-runtime lock: `lock-runtime` — PASS; `182` protected files, `2` virtual hashes.
  Final lock SHA-256: `3F0A05D5193BB521A568A3DEA97037F1FAE33B2295791539A87EF7FAD170E09F`.
- Docker/Playwright: not applicable; this is a Python CLI/state-only subsystem.
- Real project-quality eval and live eight-thread runtime: not claimed; safe fixtures only.

## Verification note

An initial broad `compileall` check generated `__pycache__` directories inside the
fixtures, and the fixture-copy tests correctly exposed that generated directory as
an invalid source entry. Those generated caches were quarantined under `.tmp/`; the
fixtures were restored to their original source shape, and the final syntax/test gates
were rerun successfully without compiling into fixture directories. This was a test
environment artifact, not a Goal implementation failure.

## Changed runtime surfaces

- `scripts/p2p_workflow.py`
- `.agents/skills/p2p/SKILL.md`
- `.agents/skills/p2p/references/state-schema.md`
- `.agents/skills/p2p-capsule/SKILL.md`
- `.agents/skills/p2p-scope/SKILL.md`
- `manifest/package.json`
- `tests/test_p2p_goal_subsystem.py`

Plan/evidence/benchmark/status files and coder/supervisor reports are audit artifacts;
no unrelated application or governance implementation was changed.

## Acceptance closure

The ten required cases are all PASS: vague request → PLAN FIRST; clear long-running
request → GOAL; open backlog → bounded PLAN FIRST; unrelated discovery → OUT OF SCOPE;
failed primary → one alternative then BLOCKED; deterministic run → TOOL-BOUND; unchanged
PASS evidence → reuse; PASS → stop; genuine business choice → one BLOCKED decision; and
mid-Goal unrelated input → NEW OBJECTIVE / SEPARATE GOALS.

No further Goal hardening is justified by the current evidence.
