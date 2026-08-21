# C37 CP0 Evidence — Prompt Audit + Git Truth + Baseline

Retrieval date: 2026-08-18. Source spec: /home/ubuntu/upload/pasted_content_4.txt (1,827 lines, archived summary at /home/ubuntu/analysis/c37_spec.md).

## 1. Prompt integrity review

Full prompt read start-to-finish before any mutation. Internal audit findings:

- Contradictions: none material. The prompt contains two halves — core selection pipeline (lines 1-1549) and execution-topology/parallelism intelligence (lines 1550-1827). Both halves require only selection-FOUNDATION machinery plus deterministic topology classification concepts; no instruction forces live backend calls, swarm, or C38 work.
- Stale assumptions: none. Expected HEAD b2d93e4 was verified against Git truth (match, byte-equal).
- Vendor-routing risk check: prompt explicitly forbids provider branches in core, silent fallback, model roulette, and vendor-name collapse — no instruction reintroduces vendor routing.
- Automatic-fallback risk check: reselection rules require bounded attempts, new evidence, and UNKNOWN_MUTATION block — consistent with C36 loop guard; no fail-open semantics anywhere.
- Historical-certification-vs-current-eligibility: prompt requires current eligibility only — consistent with C35 eligibility semantics.
- Permission widening: explicitly forbidden ("permission never widens" is a PASS requirement).
- Identity collapse: ROLE != MODEL/PROVIDER/HARNESS/TARGET preserved explicitly.
- Candidate mutation: C35/C36 candidates must remain UNPROMOTED — no mutation allowed.
- Credentials: prompt explicitly forbids real credentials and live probing.
- C38 risk: prompt names C38 as next goal and forbids starting it — respected.
- MATERIAL_SCOPE_GATE: nothing in the prompt requires credentials, live benchmarking, daemons, ML routers, new DBs, permission bypass, auto-release, swarms, new council, or replacement of C34/C35/C36.

Result: **PROMPT_AUDIT_PASS**. Proceeded to mutation only after this gate.

## 2. Git truth

- Branch: p2p-c36-evidence-bound-context-efficiency — MATCHES.
- HEAD: b2d93e487cbb56bbd9503a00c4686ae237bcaf1f — MATCHES expected b2d93e4 (full SHA prefix).
- Remote `origin/p2p-c36-evidence-bound-context-efficiency` == local HEAD.
- Working tree: 0 modified/untracked files (git status --short empty).
- Base lineage confirmed: 64d4387 (C36 implementation) → 9dc0811 (C35R) → ... → 7c9cb58 (C35).

Result: **GIT_TRUTH_MATCH**. No STOP.

## 3. Baseline measurement at b2d93e4

Full pytest at recovered C36 HEAD (working tree clean):

- **30 failed / 835 passed / 19 skipped / 884 collected** (63.31s).
- Baseline failure identity list preserved: `/home/ubuntu/analysis/c37_baseline_failures.txt` (30 lines, sorted).
- Failure classes identical to C36 final regression (known pre-existing env/governance projection failures — development_control projections, onboarding hosts, task_state UNKNOWN identity, drift classification, eval trial pairs).

PASS requirement for C37 regression: NEW_UNEXPLAINED_FAILURES = 0, computed by exact identity diff of sorted failure lists (proven, not labeled).
