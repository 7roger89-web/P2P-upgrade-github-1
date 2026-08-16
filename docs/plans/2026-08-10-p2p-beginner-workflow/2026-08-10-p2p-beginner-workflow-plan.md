# P2P beginner workflow Plan

## Metadata

- Date: `2026-08-10`
- Status: `complete; supervisor-pass`
- Plan: `docs/plans/2026-08-10-p2p-beginner-workflow/2026-08-10-p2p-beginner-workflow-plan.md`
- Evidence: `docs/plans/2026-08-10-p2p-beginner-workflow/2026-08-10-p2p-beginner-workflow-evidence.md`
- Benchmark: `docs/plans/2026-08-10-p2p-beginner-workflow/2026-08-10-p2p-beginner-workflow-benchmark.md`
- Actual status: `docs/plans/2026-08-10-p2p-beginner-workflow/2026-08-10-p2p-beginner-workflow-actual-status.md`

## Goal

Upgrade the canonical P2P Codex Edition with a single reusable project workflow that turns a natural-language request into a bounded Goal Contract, initializes only missing project state, selects the smallest useful named-agent team, reuses valid evidence, stops at PASS/BLOCKED/REJECT, persists a compact status/capsule and execution ledger, and reports completion in beginner-friendly language.

## Rules

- Preserve the immutable `source/8.4.6-C/` 152-file baseline.
- Reuse FACT_LEDGER, Live Specs, Drift Gate, Approval Gate, project eval v2, RAG checks, and existing CAPSULE state instead of creating parallel governance systems.
- Keep global workflow logic in the package and project facts/state under the target project's `.p2p/` directory.
- Ordinary tasks must not invoke the full eight-agent quorum unless the goal or policy explicitly requires it.
- Existing valid suites and PASS evidence are authoritative until relevant protected inputs change or evidence expires.
- Every long-running run has bounded work, explicit completion criteria, out-of-scope boundaries, and terminal-state rules.
- No implementation starts until P0 actual status and the invariant-family map are recorded.

## Problem

The package has strong governance primitives and named agents, but the main entry skill still expects the user or coordinator to assemble the goal contract, project initialization, eval design, quorum size, evidence reuse, and final report manually. The missing behavior is orchestration and reuse around the existing controls.

## Scope boundary

Editable:

- `scripts/p2p_workflow.py` as the single reusable orchestration helper.
- Existing `scripts/p2p_eval.py` for project-specific suite design and reuse.
- Existing P2P entry, scope, eval, capsule, quorum, and state guidance.
- Install/doctor/manifest metadata needed to distribute and validate the helper.
- Safe synthetic fixtures and direct behavior tests.
- This plan and evidence artifacts.

Preserve-only:

- `source/8.4.6-C/` and its 152-file inventory.
- Existing FACT_LEDGER, Live Specs, approval records, schemas, named agent TOMLs, and quorum role definitions except for routing guidance.

Out of scope:

- Replacing or duplicating FACT_LEDGER, Live Specs, RAG, Drift, Approval, project eval, or Execution Ledger semantics.
- Changes to application code in unrelated projects.
- Enabling PXPIPE, hooks, network, connectors, downloads, or external communication.
- Releasing or publishing the package.

## Invariant family map

| Family | Authority / SSOT | Sibling surfaces | Forbidden fallback | Verification |
|---|---|---|---|---|
| Bounded goal and stop | `scripts/p2p_workflow.py`, main P2P skill | scope guidance, reports, ledger, status | vague/open-ended goal or optional work after PASS | goal, run, terminal-state tests |
| Project initialization and reuse | installed `.p2p/` state plus package governance templates | installer, doctor, eval helper, capsule/status | overwriting valid policy/suite/evidence | new/existing fixtures |
| Adaptive agent routing | eight `.codex/agents/*.toml` identities and quorum role docs | main skill, quorum skill, execution ledger | simulated/generic identity or silent full quorum | selection matrix tests |
| Project-specific eval | `scripts/p2p_eval.py`, `governance/eval-suite.schema.json` | project suite, fixtures, eval gate | generic placeholder suite or regeneration of valid suite | design/validate/reuse tests |
| Governance evidence continuity | existing governance helpers and runtime lock | doctor, installer, drift, report, ledger | new parallel gates or stale evidence after input change | package/installed doctors and drift |

## Requirements and technical direction

- `p2p_workflow.py` provides `inspect`, `goal`, `bootstrap`, `plan`, `run`, `report`, and `acceptance` commands.
- Goal contracts include objective, verified/unknown assumptions, measurable mandatory criteria, constraints, protected actions, validation requirements, stop rules, out-of-scope items, residual risks, bounded work plan, and agent selection.
- Bootstrap creates only missing project profile, policy, eval suite/fixtures, status, trusted-evidence store, and execution-ledger location; valid artifacts are reused.
- Evidence reuse is fingerprint-based and control-scoped; changed files map to affected controls only.
- `scripts/p2p_eval.py design` creates a minimal five-case project-specific v2 suite with positive, negative/adversarial, regression, completion, and reuse/boundary cases; it returns `REUSED` for a valid existing suite.
- Normal reporting is compact; detailed JSON remains in `.p2p/state/reports/` and `.p2p/state/execution-ledger.jsonl`.
- Acceptance tests use safe local fixtures and deterministic readiness checks; they do not claim a real project eval or eight-agent runtime proof.

## Acceptance criteria

- [ ] Natural-language request becomes a measurable bounded Goal Contract with explicit success criteria, constraints, and STOP rules.
- [ ] New-project bootstrap initializes required project state without manual coding.
- [ ] Adaptive routing selects 1-2 agents for small work, 3-4 for medium work, larger only when justified, and never silently lowers explicit quorum.
- [ ] Project-specific eval suite is generated minimally; valid existing suites are reused.
- [ ] PASS evidence is reused when protected inputs are unchanged; unrelated discoveries remain OUT OF SCOPE/BACKLOG.
- [ ] PASS stops the run; BLOCKED names exactly one decision/action; REJECT is reserved for unsafe/invalid outcomes.
- [ ] Beginner report hides implementation diary while audit evidence persists.
- [ ] Status/capsule resumes from authoritative references without full re-audit.
- [ ] Existing FACT_LEDGER, Live Specs, Drift, Approval, Eval, RAG, and Ledger gates remain usable.
- [ ] Package doctor, installed/fresh-fixture doctor, drift validation, and existing regression checks pass.
- [ ] Eight named agents remain valid and ordinary fixtures do not use full quorum.
- [ ] New and existing safe fixtures demonstrate bootstrap, bounded Goal, eval initialization/validation, selective verification, evidence reuse, and final report.

## Phases

- [x] P0-A: classify current package reality and confirm the invariant-family map.
  - Goal: prove what already works and identify only missing orchestration surfaces.
  - Work steps: inspect package instructions, skills, helpers, schemas, installer, doctor, manifest, and baseline gates; record Anvien availability and local fallback evidence.
  - Implementation gate: actual-status matrix has evidence IDs and every editable surface has a touch mode.
  - Acceptance: P0 status is complete and downstream work reflects the findings.
- [x] P1-A: implement the bounded workflow helper and eval design/reuse.
  - Goal: make one natural-language request produce durable goal/bootstrap/plan/ledger/status artifacts.
  - Work steps: add the helper; extend eval design; add scoped evidence fingerprints, terminal states, reports, and safe update planning; write direct unit/behavior tests.
  - Implementation gate: no existing valid artifact is overwritten and all writes are project-local/atomic.
  - Acceptance: new/existing workflow tests pass and the helper never selects full quorum for ordinary small work.
- [x] P1-B: wire the existing P2P entry guidance and distribution checks.
  - Goal: make the capability discoverable through the normal `$p2p` entry and installers.
  - Work steps: update main/scope/eval/capsule/quorum guidance, installer script lists, doctor helper checks, package metadata, and runtime lock.
  - Implementation gate: only existing governance paths are referenced; no duplicate gate is introduced.
  - Acceptance: package doctor and static installer checks pass.
- [x] P2-A: run new/existing acceptance fixtures and all affected gates.
  - Goal: demonstrate complete bounded workflow and selective evidence reuse.
  - Work steps: run direct tests, acceptance command, package doctor, a fresh installed fixture doctor, package and installed drift, and relevant eval validation; capture outputs in evidence.
  - Implementation gate: fixture results distinguish deterministic workflow proof from real project quality claims.
  - Acceptance: both fixture verdicts are PASS and no optional lane starts after PASS.
- [x] Pn-A: supervisor acceptance loop.
  - Goal: independently verify the final artifact and evidence against this plan.
  - Work steps: read supervisor instructions, inspect final files and reports, rerun targeted checks, and correct only evidenced failures.
  - Implementation gate: all planned phases are complete or explicitly blocked.
  - Acceptance: supervisor passes or records a real blocker; no unsupported PASS claim is made.
- [x] Pn-B: close evidence and final status.
  - Goal: refresh actual status, benchmark, evidence, and final report.
  - Work steps: record final commands/results, update package runtime lock after the last protected change, verify no BOM/placeholder/dead artifact, and report the final verdict.
  - Implementation gate: all completion criteria have evidence IDs.
  - Acceptance: final report contains only the requested verdict/checklist/capabilities/fixture/gate/risk sections.

## Risk notes

- The package is an unpacked distribution rather than a Git worktree; commit checkpoints cannot be created without changing package scope. This will be reported, not hidden.
- A real eight-thread runtime quorum and real project eval trials require the Codex host/project; synthetic acceptance proves orchestration only.
- Existing live-governance dates and hashes are protected. Any runtime-lock or drift mismatch must be repaired before acceptance.
