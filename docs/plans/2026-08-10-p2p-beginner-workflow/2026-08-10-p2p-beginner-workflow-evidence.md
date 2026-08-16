# P2P beginner workflow Evidence Ledger

## Metadata

- Date: `2026-08-10`
- Plan: `docs/plans/2026-08-10-p2p-beginner-workflow/2026-08-10-p2p-beginner-workflow-plan.md`
- Evidence: `docs/plans/2026-08-10-p2p-beginner-workflow/2026-08-10-p2p-beginner-workflow-evidence.md`
- Benchmark: `docs/plans/2026-08-10-p2p-beginner-workflow/2026-08-10-p2p-beginner-workflow-benchmark.md`
- Actual status: `docs/plans/2026-08-10-p2p-beginner-workflow/2026-08-10-p2p-beginner-workflow-actual-status.md`

## Evidence rules

- Evidence IDs are stable and phase-scoped.
- Command output is recorded by result and stored in repo-local `.tmp/` when redirected.
- Synthetic acceptance evidence proves workflow behavior only; it is not a real project quality benchmark or real eight-thread quorum proof.
- Final protected-runtime lock and drift evidence must be refreshed after the last runtime file change.

## E0 - P0 Evidence

Matching plan item: `P0-A`.

- `E0-P0A-SRC1`: local inventory found 22 P2P skills, eight custom-agent TOMLs, existing P2P state/eval/quorum/capsule guidance, and no reusable goal/bootstrap/evidence-reuse orchestrator.
- `E0-P0A-GATE1`: `python scripts/doctor.py --package .` returned PASS for package structure, 152/152 immutable source files, source hashes, conversion targets, governance drift, and eight named agent profiles.
- `E0-P0A-ANV1`: Anvien `list_repos` showed only the unrelated `app_game_truyen` repository; target path queries returned `repository path is not registered`. Local file inspection is the documented fallback.
- `E0-P0A-BASE1`: package is an unpacked directory without `.git`; no commit checkpoint can be created without changing scope.

## E1 - P1 Evidence

Matching plan items: `P1-A`, `P1-B`.

- `E1-P1A-CODE1`: `scripts/p2p_workflow.py` implements inspect/Goal Contract/bootstrap/adaptive-agent selection/scope guard/evidence reuse/selective update/terminal state/persistent status/capsule/ledger/report commands. It keeps exact named agent IDs and records that no real quorum was invoked by the local helper.
- `E1-P1A-CODE2`: `scripts/p2p_eval.py design` creates a bounded project-specific suite for a new project and reuses a valid existing suite without overwriting it. The generated cases cover positive, negative, regression, completion, and reuse/boundary behavior.
- `E1-P1A-TEST1`: `python -m unittest discover -s tests -p 'test_*.py' -v` passed all four workflow tests, including bounded team selection, explicit full-quorum selection, new-project bootstrap, and existing-project selective reuse.
- `E1-P1A-ACCEPT1`: `python scripts/p2p_workflow.py acceptance --package .` passed the safe deterministic new-project and existing-project fixtures. The existing-project fixture detected only `app.py`, reused unrelated evidence, reran only affected project controls, used fewer than eight agents, and stopped at PASS.
- `E1-P1B-DIST1`: main P2P entry guidance, scope/eval/capsule/quorum guidance, installers, doctor checks, and package manifest were wired to the one helper. The canonical counts remain 22 skills, eight named agents, and 152 immutable source files.
- `E1-P1B-ENC1`: changed text/runtime files were checked for UTF-8 readability and placeholder markers; the helper explicitly configures UTF-8 stdout/stderr for Windows installed runs.
- `E1-P1B-INSTALL1`: fresh installed-fixture smoke validation on `.tmp/fresh-installed-project-3` passed installer lock, installed doctor, and installed acceptance. A final fresh install is recorded in E2 after the last lock refresh.

## E2 - P2 Evidence

Matching plan item: `P2-A`.

- `E2-P2A-LOCK1`: `python scripts/p2p_governance.py lock-runtime --root . --governance governance --reason "User-authorized bounded P2P workflow upgrade"` returned PASS with 178 protected files and two virtual hashes.
- `E2-P2A-PACKAGE1`: `python scripts/doctor.py --package .` returned PASS. It verified 22 skills, eight named agents, the helper distribution, governance continuity, source 152/152, source hashes, conversion targets, and package manifest.
- `E2-P2A-DRIFT1`: `python scripts/p2p_governance.py drift --root . --governance governance` returned PASS with no failures or warnings after the final lock refresh.
- `E2-P2A-FRESH1`: fresh install in `.tmp/fresh-installed-project-5` returned installer PASS with a 156-file installed lock; explicit installed doctor returned PASS with the expected release-readiness WARN because no real project eval suite was supplied.
- `E2-P2A-WORKFLOW1`: the installed helper in `.tmp/fresh-installed-project-5` ran `run --acceptance` and returned PASS with the five Vietnamese beginner-report sections, including `CÓ GÌ CHƯA XONG: Không.` and `ANH CÓ CẦN LÀM GÌ KHÔNG?: Không.`.
- `E2-P2A-ANV1`: supervisor re-queried Anvien; only unrelated `app_game_truyen` is indexed and the target package path is not registered. Local source inspection, tests, doctor, installer, and drift are the evidence fallback for this unpacked package.

## Closure evidence

- `CLOSE-SUPERVISOR1`: independent supervisor report `reports/supervisor/rp_supervisor_260810_160715_by_gpt-5-codex_p2p-beginner-workflow.md` returned PASS after source inspection, fresh compile/unit/acceptance/doctor/drift checks, fresh installation, and invariant-closure review.
- `CLOSE-LOCK1`: final closure refresh must keep `governance/runtime-manifest.lock.json` generated by `lock-runtime`; the final lock command passed with 178 protected files and two virtual hashes, and the post-report drift check passed.
- `CLOSE-GIT1`: package root has no `.git` metadata, so no commit hash exists. No Git repository was initialized because that would expand scope beyond the requested package upgrade.
- `CLOSE-SCOPE1`: no application project was changed; synthetic fixtures prove orchestration only. Real project-quality eval trials and live eight-agent runtime proof remain explicit environment-dependent risks, not hidden claims.
