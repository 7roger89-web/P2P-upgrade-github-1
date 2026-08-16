# Coder Report: P2P Eval Helper Boundary Alignment

Status: READY FOR INDEPENDENT REVIEW

## Metadata

- Review scope: `P2P Eval Helper Boundary Alignment — Prerequisite for Real Context-Efficiency Benchmark`
- Authority: attached user Goal, repository `AGENTS.md`, plan/evidence/benchmark/actual-status ledgers.
- Invariant family: helper contract resolution and package/runtime role boundary.
- Git reference: unavailable; `anvien detect-changes --repo P2P-8.4.6-C-Codex-Edition-v4 --scope all --json` returned `Git diff failed: exit status 129`.
- Official baseline preserved: `.15` ZIP SHA-256 `af4d63a882dabfde20ac237574590ec584ee2944bc4cdc30b6a07bf7f681e195`.

## Invariant Family Map

- Source of truth: existing project-eval v2 helper contract in `scripts/p2p_eval.py`, package/manifest validators, installed runtime layout, and existing governance/evidence state.
- Primary surface: `scripts/p2p_workflow.py` helper discovery and bootstrap.
- Sibling surfaces checked: development `.p2p/system/scripts/p2p_eval.py` UI/UX helper, `scripts/doctor.py`, `.p2p/system/scripts/doctor.py`, `scripts/package_release.py`, `install.ps1`, `install.sh`, package manifests, focused tests, official `.15`, candidate `.16`, and isolated lifecycle fixtures.
- Forbidden legacy fallback: path order alone; incompatible UI/UX `p2p_eval.py`; implicit `.tmp`, quarantine, or preserved-snapshot helper sources.
- Verify matrix: direct bootstrap, incompatible-helper exclusion, transient-path exclusion, role-aware doctor, package verify, candidate package doctor, fresh install, upgrade, same-version reinstall, governance, Decision Trace, capability, secret scans, and full unit suite.

## Implementation

- `scripts/p2p_workflow.py`: added non-mutating `design --help` contract probing for `--goal-contract` and `--profile`; implicit transient helper paths are excluded; installed roots are role-bound to their canonical helper and cannot fall back to an ancestor development package; missing-helper diagnostics are explicit.
- `scripts/doctor.py`: added `auto/development/portable/installed` role semantics; development checks validate development-owned payload locations; portable checks remain strict and fail closed; explicit role mismatch is reported.
- `tests/test_p2p_workflow.py:42,48,53`: project-eval contract selection, transient path, and installed-root ancestor-fallback regression tests.
- `tests/test_p2p_doctor_roles.py:15,21`: development-role and explicit package-role mismatch tests.
- `governance/runtime-manifest.lock.json`: refreshed through the existing governance command after the source change.
- No evaluator, router, worker, scheduler, queue, second memory, Capsule, Knowledge Delta, provider, or AESTHETICA change was introduced.

## Sibling Surface Clearance

- Project eval v2 root helper: clear; existing CLI contract is selected.
- Installed UI/UX helper: clear; remains UI/UX-only and cannot satisfy project eval v2.
- Development doctor: clear; auto and explicit development checks pass.
- Portable doctor/package: clear; official `.15` and candidate `.16` verify and doctor pass.
- Installer: clear; fresh, upgrade, and same-version reinstall preserve the compatible installed helper.
- Temporary/source snapshot boundary: clear; implicit resolver discovery excludes transient paths and package verify has no forbidden transient paths.
- Prior proxy evidence: clear; preserved and labeled proxy-only.
- Residual unverified surfaces: none within the assigned helper/package/runtime invariant family.

## E2E Verification

```text
[PASS] Compiled: python -m py_compile scripts\p2p_workflow.py scripts\doctor.py
[PASS] Runtime happy path: focused workflow tests 7/7; development bootstrap returns project_eval REUSED and validation PASS
[PASS] Runtime edge path: focused doctor-role tests 2/2; --package against development root reports explicit role mismatch
[PASS] Full regression: python -m unittest discover -s tests -p 'test_*.py' -> 81/81
[PASS] Governance: runtime lock refresh and drift -> PASS
[PASS] Package: candidate .16 build/verify -> 398 content files, 399 checksums; official .15 verify -> 398/399
[PASS] Lifecycle: development, portable, fresh install, upgrade from .15, same-version reinstall
[PASS] Security scope: changed surfaces PASS; whole-repo findings remain a separate hygiene goal
```

## Boundary Decision

`REAL_AB_BENCHMARK_READY=YES` only for the unpromoted `.16` candidate boundary and isolated lifecycle infrastructure. It does not claim that the real worker/provider A/B benchmark ran, that quality is non-inferior, or that token/cache/cost telemetry is available. Official `.15` remains immutable and is not reclassified.

## Handoff

The implementation is complete and intentionally stops before the later real context-efficiency benchmark. Independent Supervisor Review must verify this report, the source, the plan ledgers, lifecycle evidence, and the unpromoted artifact before closure.

## Post-review correction

An independent source pass found that an installed fixture under `.tmp` could reject its canonical helper and discover the ancestor development helper. The resolver was tightened to recognize installed roots, keep their canonical helper first, and suppress ancestor package-root fallback. Focused tests now pass 7/7 and the full suite 81/81. The corrected immutable artifact is `P2P-8.4.7-C-Codex-Edition-v16-r2.zip`, package version `8.4.7-C-codex.16`, SHA-256 `410572d73aa06dadbd8fe1da068fe217eabeb7efc11cf35fc9576c750a4ee8cf`.
