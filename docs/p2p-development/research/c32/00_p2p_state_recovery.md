<!-- RESEARCH_ONLY / NON_CANONICAL / PROPOSAL / NOT_IMPLEMENTATION / NOT_PROMOTED -->

# P2P State Recovery — C32 (evidence-backed)

Recovered: 2026-08-17T07:30Z (sandbox), repo `7roger89-web/P2P-upgrade-github-1`, fresh clone, PAT verified (user 7roger89-web, pushable, repo PRIVATE).

## Git lineage (verified via git log --oneline)
- main = bda3e22 "Initial commit"
- p2p-c25-charter-ledger = 20867a4 (parent 666dd5e)
- p2p-c26-capability-provenance = 1739b72 (parent 20867a4)
- p2p-c27-real-host-certification = 32e002d (parent 1739b72)
- p2p-c28-secure-onboarding = 5f9bc6f (parent 32e002d)
- p2p-c29-goal-closure-integrity = 90df897 (parent 5f9bc6f)
- p2p-c30-composable-execution-target = 2eaceeb (parent 90df897)
- p2p-c31-live-host-certification = 40d9441 (parent 2eaceeb)
Stacked lineage …→C29→C30→C31 CONFIRMED. PRs on GitHub API: PR#1..#7 all OPEN, unmerged. PR #6 = C30 (base p2p-c29), PR #7 = C31 (base p2p-c30).

## Verified state claims (from branch heads + governance/development-control.json)
- C30 = PASS (machinery only): terminal report P2P-C30-terminal-report.md; status MACHINERY_FOUNDATION_READY / CANDIDATE_UNPROMOTED; candidate v24 (SHA 94b09b59...) UNPROMOTED. Implements p2p_execution_target.py, ET1–ET60 tests, fingerprint/drift, backend registry foundation, research intake doc docs/p2p-development/research/execution-target-pattern-research.md. No router, no autonomy, no second executor, no live execution.
- C31 = BLOCKED / OWNER_ACTION_REQUIRED (NOT PASS): commit 40d9441 "honest BLOCKED / OWNER_ACTION_REQUIRED". Evidence evidence/c31_live_probe.json: fresh zero-model-contact probe of Codex CLI 0.147.0 → AUTH_INVALID (HTTP 401 before model contact); Manus path AUTH_CONFIG_ABSENT. Terminal verdict BLOCKED. capability_status C31: BLOCKED / CERTIFICATION_BLOCKED_OWNER_ACTION_REQUIRED.
- Official baseline 8.4.7-C-codex.19 / SHA 3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8 — immutable, all lineage refs to .19.
- C30 candidate .24 = UNPROMOTED (confirmed in current_development on C31 branch head).
- No live-certified execution target (live_manus_adapter_certified: false); no router (automatic_host_routing_ready: false); no AutoPilot; no second executor.
- C29 closure: Goal C28 CONSISTENT at terminal time; explained C30-vs-C28 roadmap split semantics.
- Regression at C31 terminal: 644 passed; validator 65/65.
- Capability ledger: .p2p/system/p2p_capabilities (+ capability-index.json), fact-ledger.json, live-specs.json (schema p2p-codex-live-specs/2), governance/development-control.json (schema p2p-development-control/1).
- Durable surfaces recovered: governance/*, .p2p/system/* (AGENTS.md, CLAUDE.md, VERSION=8.4.7-C-codex.24 (C30 head), p2p.manifest.json, release.json, scripts), docs/p2p-development (CHARTER, current-roadmap.md, reports C25-C31), tests/* (30 suites), reports/candidates (v21-v24 zip candidates), update_*.py scripts per goal.
- PR lineage declared in development-control.json pr_lineage (c25→main, c26→c25, ... c31→c30).
- owner_action_required: C30 PASS; candidates UNPROMOTED; C27 reopen needs codex login or Manus connector; no goal auto-started.

## Key architecture vocabulary recovered from C30
- ExecutionTarget composition model; eligibility evaluation; fingerprint/drift; backend registry; provider-neutral intake (no router, no autonomy, no real execution).
- 8 canonical agents quorum 8/8: p2p_iris, p2p_tecton, p2p_axiom, p2p_vector, p2p_datos, p2p_anon, p2p_architecton, p2p_helios (aesthetica optional).
- Architectural invariants: project-state-is-not-chat-history (.p2p/state/project-status.json); deterministic-first checks; durable evidence trail; filesystem context offloading.
