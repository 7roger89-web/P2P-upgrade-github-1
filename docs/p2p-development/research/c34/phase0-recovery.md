# C34 Phase 0 — Repository Recovery Notes

## Repository truth (verified)
- Repo: 7roger89-web/P2P-upgrade-github-1 (clone OK via PAT)
- Checked out branch: `p2p-c33-bounded-autopilot-core`, HEAD = `2a000e0` (matches expected C33 durable-closure head)
- Clean working tree, no untracked changes
- Stacked lineage intact: ... p2p-c29 / p2p-c30 (40d9441) / p2p-c31 (2eaceeb, BLOCKED) / p2p-c32 (835421d) / p2p-c33 (dbfa9e1 impl + 2a000e0 closure report commit)
- Baseline: 8.4.7-C-codex.19 PROMOTED_VERIFIED (confirmed in governance/development-control.json)
- Manifest: .p2p/system/p2p.manifest.json package_version 8.4.7-C-codex.24, canonical 8 agents confirmed, quorum 8/8

## C33 durable terminal report
- docs/p2p-development/research/c33/P2P-C33-terminal-report.md (301 lines), PASS / BOUNDED_AUTOPILOT_CORE_READY
- 11/11 scenario tests PASS (test_p2p_autopilot_scenarios.py)
- C33 declared candidate_policy output: NO (per scripts/p2p_goal_closure.py §18/§19) — consistent with lineage
- C33 runtime = `.p2p/system/p2p_capabilities/` (autopilot_*.py + fake_execution_backend.py)
- No .p2p/state/ directory exists (state families live elsewhere)

## C33 modules (.p2p/system/p2p_capabilities/)
autopilot_budget, autopilot_contract, autopilot_gate, autopilot_loop, autopilot_state,
autopilot_verifier, fake_execution_backend, bounded_delegation, foreground_execution,
decision_trace, evidence, orchestration_policy, parallel_execution, providers, routing,
task_state, host_executor, host_selection, isolation, live_execution, skill_standard,
specialist, context, domain, model, beginner, trust, capabilities.json, __init__.py

## C30/C20-C22 machinery locations
- tests/test_p2p_autopilot_scenarios.py, tests/test_p2p_autopilot_families.py
- C30 tests: scripts/show_et_errors.py, c30_recover_state.py, verify_package.py, fill_c30_candidate.py, build_c30_candidate.py, add_c30_invariants.py, update_governance_c30.py, update_ledger_c30.py
- C20 host_executor.py, C21 host_selection.py in p2p_capabilities

## Candidate policy (P0-A audit target)
- Authoritative checker: scripts/p2p_goal_closure.py, ChangeSignals.detect()
  - runtime = any(f.startswith(("scripts/", "source/")) and not .md)
  - governance = f.startswith("governance/")
  - release = f.startswith(("docs/p2p-development/templates/", "docs/p2p-development/P2P-DEVELOPMENT-CHARTER.md"))
- `.p2p/system/p2p_capabilities/*.py` are NOT matched by any rule → runtime_changed = False for C33's own changes
- C33 terminal report explicitly acknowledged this: "C33 deliberately stays on the `.p2p/system` capability surface to keep the machinery proveable without packaging ceremony" → policy was AWARE of the surface when C33 was decided
- Key question: is .p2p/system/p2p_capabilities executable runtime code under policy semantics? YES — imported at runtime by p2p_capability_doctor.py ("from p2p_capabilities import ..."). It IS runtime.
- Classification candidate: POLICY_BLIND_SPOT_CONFIRMED (checker excludes a real runtime surface) BUT the declared governance semantics at C33 decision time excluded it deliberately ("proveable without packaging ceremony"). → Need to check whether governance documents the intent. If ambiguous → POLICY_INTENT_AMBIGUOUS → OWNER_GATE.

## Governance references
- governance/development-control.json: current_development.development_goal = "C31" BLOCKED_TERMINAL, source_version 8.4.7-C-codex.24 ACTIVE_UNPROMOTED
- runtime-manifest.lock.json: protected-files SHA hashes (agents skills)
- manifest/source-inventory.json exists
