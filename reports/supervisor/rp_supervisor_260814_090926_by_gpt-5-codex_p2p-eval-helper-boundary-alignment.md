# Supervisor Report: P2P Eval Helper Boundary Alignment

Verdict: PASS

## Metadata

- Report file: `reports/supervisor/rp_supervisor_260814_090926_by_gpt-5-codex_p2p-eval-helper-boundary-alignment.md`
- Review time: `260814 090926 Asia/Saigon`
- Reviewer: `gpt-5-codex`
- Repo/project: `P2P-8.4.6-C-Codex-Edition-v4`
- Scope reviewed: final source state, plan/evidence/benchmark/actual-status ledgers, coder handoff, official `.15`, unpromoted `.16` and `.16-r2` candidates, and isolated lifecycle fixtures.
- Claim reviewed: the bounded P2P eval-helper and package/runtime boundary is deterministic, role-correct, fail-closed, lifecycle-verified, and ready for a later real context-efficiency benchmark without claiming that benchmark has run.
- Authority used: attached user Goal, repository `AGENTS.md`, existing project-eval v2 contract, package/installer contracts, runtime source, tests, and current command evidence.
- Related artifacts: coder report, four plan ledgers, official `.15` ZIP, candidate `.16` artifacts, lifecycle fixtures under repo-local `.tmp`.

## Executive Summary

- Problem: the development workflow selected the UI/UX-only `p2p_eval.py` for project-eval v2 `design`, and package doctor conflated development and portable roots.
- Decision: PASS. The final resolver probes the existing project-eval v2 contract, binds installed roots to their canonical helper, suppresses ancestor development fallback, excludes unrelated transient paths, and the doctor validates explicit filesystem roles without weakening portable checks.
- Required outcome: accepted for this bounded Goal. The real worker/provider A/B benchmark remains a separate later Goal.

## Source-Level Clearance Notes

- `scripts/p2p_workflow.py:298-365`: clear. Contract probing is non-mutating; installed roots use only their canonical `.p2p/system/scripts/p2p_eval.py`; non-installed roots retain role-appropriate candidates; unrelated transient/ancestor candidates are rejected.
- `scripts/doctor.py:119-134,504-550,697-728`: clear. Role inference distinguishes portable, development, installed, and unknown inputs; development checks use source-owned paths; explicit role mismatch is reported; portable checks remain strict.
- `tests/test_p2p_workflow.py:42-66`: clear. Direct tests cover project-eval contract selection, transient path handling, canonical installed-root selection, and ancestor fallback rejection.
- `tests/test_p2p_doctor_roles.py:15-31`: clear. Development role and explicit package-role mismatch are directly tested.
- `scripts/package_release.py`, `install.ps1`, `install.sh`, manifests: clear/preserve-only. Package and installer contracts were inspected and verified; no unrelated source edit was made.

## Evidence Checked

Passed:

- Fresh source inspection of the changed resolver, doctor role logic, and direct tests.
- Fresh Anvien analysis with `--skip-git`: 281 files, 10,743 nodes, 12,212 relationships; workflow detail 267 symbols/40 inbound/145 local/46 linked flows; doctor detail 104 symbols/3 inbound/74 local/13 linked flows; graph not stale.
- Focused workflow/doctor tests: 9/9 PASS.
- Full unit/regression suite: 81/81 PASS.
- Development doctor: `role=development`, `detected_role=development`, `ok=true`.
- Project-eval v2 suite validate/gate: PASS; 5 paired cases, no regressions.
- Preserved context-efficiency proxy suite validate/gate: PASS; 12 paired cases, deterministic contract proxy only.
- Governance runtime lock and drift: PASS.
- Native Decision Trace: 24/24 PASS; canonical 8/8 preserved.
- Capability doctor: PASS; canonical denominator 8, full quorum 8/8, Aesthetica optional/noncanonical.
- Changed-surface secret scans: PASS for `.p2p/system`, `scripts`, and candidate `.16` runtime.
- Official `.15` clean extraction verify/doctor: PASS; official ZIP SHA-256 unchanged.
- Current candidate `.16-r2` verify/portable doctor/secret scan: PASS; 398 content files and 399 checksum entries.
- Lifecycle A–E on current candidate: development, portable, fresh install, upgrade from official `.15`, and same-version reinstall all pass. The fresh installed workflow resolves the installed canonical helper; the upgrade reports `UPGRADE_FROM_8.4.7-C-codex.15`; reinstall reports `SAME_VERSION_REINSTALL` and preserves backup inventory.
- Proxy artifacts were preserved and remain explicitly marked `runtime_task_execution=false` and `quality_noninferiority=UNKNOWN`.

Failed / non-blocking:

- Whole-repo secret scan: FAIL with 7 existing/reference `github-token` matches in bundled documentation and repo-local source snapshots. Changed surfaces pass; cleanup is explicitly outside this Goal and was not suppressed.

Not run:

- Real model/provider/worker A/B execution, token/cache/cost telemetry, and quality non-inferiority benchmark: intentionally out of scope for this prerequisite Goal.
- Git commit/change diff: attempted through Anvien, which returned `Git diff failed: exit status 129` because this workspace has no usable Git repository baseline; no commit was claimed.

## Invariant Closure

- Affected invariant: project-eval helper contract and development/portable/installed package-runtime boundary.
- Sibling surfaces checked: root project-eval helper, development UI/UX helper, installed runtime helper, workflow bootstrap, doctor roles, package builder, manifests, both installers, official `.15`, current `.16-r2`, fresh/upgrade/reinstall fixtures, eval suite/gate, governance, capability, Decision Trace, and secret-scan boundaries.
- Prior blocker closure: the wrong UI/UX helper no longer satisfies `design`; development no longer produces false portable-payload failures; an installed fixture cannot fall back to its ancestor development helper.
- Residual unverified same-invariant surfaces: none for the accepted bounded scope.

## Overall Evaluation

The implementation is surgical and evidence-backed. It preserves one project-eval v2 source of truth, keeps UI/UX evaluation separate, preserves strict portable validation, does not add a router/agent/evaluator/memory/orchestration system, and does not alter official `.15`. The candidate boundary is ready for a separately authorized real benchmark, but no efficiency or quality claim is made here. PASS is limited to the stated prerequisite Goal.
