# Supervisor Report: P2P-C14 Design Intelligence Release Readiness

Verdict: PASS

## Metadata

- Report file: `reports/supervisor/rp_supervisor_260815_083636_by_gpt-5-codex_p2p-c14-design-intelligence-release-readiness.md`
- Review time: `2026-08-15 08:36:36 +07:00`
- Reviewer: `gpt-5-codex`
- Repo/project: `P2P-8.4.6-C-Codex-Edition-v4`
- Scope reviewed: C14 integrated C10-C13 source, isolated `.19` candidate, package boundary, disposable lifecycle, installed runtime behavior, governance/security gates, and owner-approval boundary
- Claim reviewed: the integrated Design Intelligence development source is technically ready to present to the owner for release approval, without being promoted or claiming browser/UI-quality certification
- Authority used: current user request `P2P-C14`, repository `AGENTS.md`, C14 plan/evidence ledgers, C13 accepted development-source report, package/doctor/governance contracts, installed runtime behavior, and the hash-bound technical gate
- Related artifacts: candidate ZIP `.tmp/p2p-c14-final/P2P-8.4.7-C-Codex-Edition-v19.zip`; technical gate `.tmp/p2p-c14-final/gate-official15/technical-gate-report.json`; pending request `.tmp/p2p-c14-final/gate-official15/approval-request.json`

## Executive Summary

- Problem: C13 accepted the Design Intelligence source but did not prove portable release packaging, installed isolation, lifecycle safety, final version consistency, or full-root security classification.
- Decision: PASS for the bounded technical-readiness claim. The candidate is new, internally consistent, package-verified, lifecycle-tested, offline, provenance-locked, and still unpromoted.
- Required outcome: owner approval remains required; no approval command, promotion, publication, merge, or external mutation was performed.

## Source-Level Clearance Notes

- `.p2p/system/p2p_uiux/design_intelligence.py:58,223-257`: clear. The registry now requires a sibling `nui_registry.lock.json`, verifies the raw registry SHA, upstream revision, and graph SHA, and fails closed with explicit integrity errors. The existing planner, router, metadata-only loading, and render/evidence boundaries remain intact at lines `600-620`, `687-699`, and `705-730`.
- `.p2p/system/p2p_uiux/nui_registry.lock.json`: clear. The lock binds registry SHA `b1790ff1c5b793996cf2d57905b556d54fee2eb975cc2a0b0504c8a08eddd0d3`, upstream revision `46780cdd58e41bea8338b2d27269d339c95e28e7`, and graph SHA `c90185bdda45ccd8d86716d4b565d2ac33c99644e732329ad7d8949a6a8117c6`.
- `.p2p/system/p2p_uiux/router.py:158-250`: clear. The existing classifier remains the only router; non-UI requests keep `use_skill=false`, and UI requests add the Design Intelligence projection without creating a second router.
- `.p2p/system/p2p_capabilities/capabilities.json` and `.p2p/system/p2p.manifest.json`: clear. Canonical identities remain exactly eight, denominator `8`, full quorum `8/8`; Aesthetica is optional and excluded from the denominator.
- `tests/test_p2p_design_intelligence.py:51-60`: clear. The new regression test rejects a tampered registry provenance snapshot with `NUI_REGISTRY_FINGERPRINT_MISMATCH`.

## Evidence Checked

Passed:

- Fresh Anvien refresh after the source lock: root `355` files scanned, `36` parsed, `13,717` nodes, `15,570` relationships; `.p2p/system` `49` files scanned, `39` parsed, `7,229` nodes, `9,416` relationships. The edited Design Intelligence file was reviewed with prior file-detail/impact evidence: `122` symbols before the lock addition, `50` local relationships, `17` linked flows, and a CRITICAL blast-radius warning treated as a scope warning, not ignored.
- Focused Design Intelligence/Capability Foundation regression: `44/44` PASS. Full regression after the lock change: `175/175` PASS in `144.198s`.
- Final candidate package verify: `8.4.7-C-codex.19`, `406` content files, `407` checksum entries; artifact SHA-256 `3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8`.
- Portable package doctor, package secret scan, package governance drift, capability doctor, and UI/UX doctor: PASS. The candidate contains the provenance notice and registry lock and contains no `__pycache__`/`.pyc` payload.
- Candidate metadata inventory: root `VERSION`, manifest version, release-manifest version, runtime version, runtime manifest version, UI/UX module version, and `p2p-uiux` capability version all equal `8.4.7-C-codex.19`.
- Exact official `.15` rollback artifact verified independently: `D:\AI\P2P_dev\P2P-8.4.7-C-Codex-Edition-v15.zip`, size `2,385,951`, SHA-256 `af4d63a882dabfde20ac237574590ec584ee2944bc4cdc30b6a07bf7f681e195`.
- Final technical gate: `PASS`; drift `PASS`; project eval `PASS` with `5` cases, `2` trials per variant, P2P pass rate `1.0`, delta `0.0`, and `0` case regressions; RAG `NOT_APPLICABLE` because no RAG corpus/index/retrieval source changed. Subject and technical-report hashes are bound in the pending approval request.
- Final lifecycle: fresh install `FRESH_INSTALL` PASS; official `.15` to `.19` upgrade `UPGRADE_FROM_8.4.7-C-codex.15` PASS; same-version reinstall `SAME_VERSION_REINSTALL` PASS. The sentinel hash is unchanged, the upgrade creates one backup, and reinstall creates no additional backup; profile count remains `9`.
- Installed runtime matrix: registry `174` faculties, `13` kernels, `9` rules; Logistics-like route `44` activated metadata entries with `0` loaded faculty bodies; consumer/game route `37` with `0` loaded bodies; beginner request has no technical questions or permissions; non-UI database/webhook request keeps Design Intelligence dormant; all four render states remain truthful; completion without evidence is `UNKNOWN`, with no beauty score.
- Installed CLI help and real `design-intelligence` execution: PASS. Installed UI/UX drift: PASS. Installed runtime contains no development-checkout references and no runtime network surface (`http(s)`, urllib, requests, httpx, socket, subprocess) in the UI/UX payload.
- Provenance tamper checks: changing the registry snapshot returns `NUI_REGISTRY_FINGERPRINT_MISMATCH`; removing the sibling lock returns `NUI_REGISTRY_LOCK_MISSING`.

Failed / classified:

- Full-root canonical secret scan returns raw `FAIL` with exactly one finding: `tests/test_p2p_security_scan.py:20`, an intentional `ghp_12345678901234567890` fixture used to verify that real token-shaped values remain blocked. The test source confirms the fixture is intentional; the final candidate package excludes tests and its package secret scan is `PASS`. This is a known-safe test fixture, not a release credential.
- The bounded C14 workflow-helper retry did not produce a completion report: `plan` hung for roughly two minutes and `run` reached the `180s` bound while hashing the full repository in `project_snapshot()`. This is classified as a control-plane/state-heavy timeout and NON_RELEASE_BLOCKING because the canonical release gate is package/doctor/drift/eval/rollback/approval bound, not helper completion. The exact C09 blocked state was restored and guard tests passed.
- Anvien `detect-changes` returned `Git diff failed: exit status 129` for both root and `.p2p/system`; the workspace has no Git metadata. No commit or commit hash is claimed.

Not run:

- Real Logistics/App Game Truyen render, browser/Playwright, Docker, host identity observation, external provider execution, eight-thread live QUORUM, release promotion, and owner approval. These are explicitly outside this C14 technical-readiness claim or require the owner’s separate decision.

## Invariant Closure

- affected invariant: portable offline Design Intelligence release contract, provenance integrity, single-router/C10-C11-C12 authority boundaries, optional-specialist governance, no-body-preload behavior, render/evidence honesty, lifecycle preservation, and release approval binding.
- sibling surfaces checked: source loader/lock, registry/provenance notice, sole router, capability registry, C10 Decision Trace projection, C11 task projection, C12 execution projection, CLI, package builder/manifest/checksums, portable doctor, governance drift, capability/UIUX doctors, secret scans, installers, fresh/upgrade/reinstall roots, non-UI and beginner routes, render states, completion evaluator, eval suite, and approval request.
- residual unverified same-invariant surfaces: none within the bounded offline package/release scope. Browser visual quality and real product render remain declared limitations, not silently certified.

## Overall Evaluation

The source-level change is surgical and directly closes the discovered release-integrity gap without changing the Design Intelligence architecture. The candidate is ready for the owner’s explicit release decision, but it is not released. C09 remains BLOCKED, C08 remains DEFERRED, external projects remain untouched, and the approval request remains PENDING.
