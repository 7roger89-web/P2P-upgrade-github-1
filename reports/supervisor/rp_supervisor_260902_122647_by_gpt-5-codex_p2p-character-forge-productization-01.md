# Supervisor Report: P2P Character Forge Productization ISSUE 59

Verdict: REJECT

## Metadata

- Report file: `reports/supervisor/rp_supervisor_260902_122647_by_gpt-5-codex_p2p-character-forge-productization-01.md`
- Review time: `2026-09-02 12:26:47 +07:00`
- Reviewer: `gpt-5-codex`
- Repo/project: `7roger89-web/P2P-upgrade-github-1`
- Review checkout: `D:\AI\P2P_dev\worktrees\p2p-issue-59-character-forge-productization-writer`
- Scope reviewed: exact candidate `8d338c0600d77b0f4fd4f790f6fa1f2422faebe8` / tree `8b0a8c870de305f302d5e2f9f3e3dd3104a45501`
- Claim reviewed: ISSUE=59 is a complete beginner-facing productization of the existing `game.character.generate` MPFB2 route and is ready for Owner Gate.
- Authority used: current user delegation, repository `AGENTS.md`, ISSUE=59 plan/evidence, existing capability contracts, candidate source/tests/schema, runtime result, and independent artifact checks.
- Related artifacts: coder report `reports/coder/rp_coder_260902_121330_by_gpt-5-codex_p2p-character-forge-productization-01.md`; ISSUE=59 plan/evidence/benchmark/status; runtime result and independent validation under `D:\AI\P2P_runtime\mpfb2-runtime-01\logs`; prior ISSUE=55/56 Supervisor reports.

## Executive Summary

- Problem: the candidate correctly adds a deterministic facade and proves one real MPFB2 product run, but its required per-field support classification is not represented accurately.
- Decision: REJECT. The source defines the required classification vocabulary but assigns `SUPPORTED_BY_SAFE_DEFAULT` to every supported field and never emits `SUPPORTED_DETERMINISTIC`. This leaves an explicit user requirement unresolved even though the runtime artifact itself passes.
- Required outcome: correct the classification contract and its focused assertions/documentation, create a new exact candidate subject, and obtain a fresh Supervisor review. Do not rerun Blender solely for this metadata correction; any source/runtime behavior change would require fresh runtime evidence.

## Blocking Findings

### [MEDIUM] Required `SUPPORTED_DETERMINISTIC` classification is absent

File: `.p2p/system/p2p_capabilities/character_forge.py:56-70`

Issue: the user required every proposed request field to be classified as one
of `SUPPORTED_DETERMINISTIC`, `SUPPORTED_BY_SAFE_DEFAULT`, or
`NOT_CURRENTLY_SUPPORTED`. `FIELD_SUPPORT` contains only
`SUPPORTED_BY_SAFE_DEFAULT` for all six accepted fields (`name`, `gender`,
`age_class`, `build`, `rig`, `output_format`) and
`NOT_CURRENTLY_SUPPORTED` for the eight rejected fields. The required
`SUPPORTED_DETERMINISTIC` value is never used.

Evidence: direct source inspection at lines 56-70; `SAFE_DEFAULT_FIELDS` at
lines 37-44 also equals all six supported fields. The implementation at lines
173-186 accepts caller-selected `gender`, `age_class`, `build`, and `name`,
then lines 232-258 deterministically map those values into the existing recipe.
The current focused tests at `tests/test_p2p_character_forge.py:107-128`
check schema/default disjointness but do not assert the required classification
vocabulary or per-field assignments.

Why this blocks acceptance: this is a direct contract requirement, not a
cosmetic label. The current result cannot distinguish fields that are
deterministically mapped from fields that are merely fixed by safe defaults,
so the declared capability support matrix is incomplete/misleading.

Fix direction: define and document one canonical classification for the six
accepted fields. At minimum, fields whose caller value is mapped into the
recipe (`gender`, `age_class`, and `build`, and the chosen identity treatment
for `name`) must be represented as `SUPPORTED_DETERMINISTIC`; fixed-only
`rig`/`output_format` may remain `SUPPORTED_BY_SAFE_DEFAULT`. Keep the eight
unsupported material fields fail-closed. Add a focused test that asserts the
exact supported/default/unsupported sets and that the three vocabulary values
are used consistently.

Re-review evidence required: new candidate HEAD/tree, updated source/schema
and focused test diff, passing focused tests, and an updated productization
report/status ledger. The existing real artifact may be reused only as prior
runtime evidence if the correction is metadata/test-only and the runtime
route source/recipe contract is unchanged.

### [LOW] Top-level actual-status label is stale

File: `docs/plans/2026-09-02-p2p-character-forge-productization-01/2026-09-02-p2p-character-forge-productization-01-actual-status.md:5`

Issue: the file says `Status: P1 Complete; P2 Pending`, while its R2 row,
P2 rows, and appended P1/P2 decision say the real smoke and independent
cleanup passed. This is inconsistent closure bookkeeping.

Evidence: the same file's current-status rows and status refresh R2; the plan
marks P2-A and P2-B complete; `evidence.md` records a P2 PASS.

Why this blocks final closure: the repository rules require current status and
evidence to agree before the plan is closed. This should be corrected together
with the classification fix or explicitly changed to `P2 Complete; Supervisor
Pending` for the next exact subject.

## Source-Level Clearance Notes

- `.p2p/system/p2p_capabilities/character_forge.py:101-275`: **blocked only on the classification contract**. Request parsing is strict, schema metadata is checked, semantic age/build mappings are deterministic, and the existing `character_recipe.validate_recipe`/hash contract is reused. Unknown runtime controls and unsupported material intent fail closed.
- `.p2p/system/p2p_capabilities/character_forge.py:278-306`: clear. Runtime binding keeps Blender and MPFB2 paths out of the beginner request and fixes the internal MPFB2 relative paths.
- `.p2p/system/p2p_capabilities/character_forge.py:309-525`: clear. The facade delegates to existing `mpfb_adapter.build_execution_plan` and `execute_plan`, validates the plan/output binding, reuses provenance validation, and returns a status-bound receipt. No second runner, firewall, validator, or service is present.
- `docs/p2p-development/capability-catalog/game-asset-forge/character.request.schema.json:1-39`: clear for shape/defaults and `additionalProperties: false`; it does not independently encode the missing classification vocabulary, so source/tests must carry that contract.
- `tests/test_p2p_character_forge.py:50-289`: clear as focused behavioral coverage for defaults, determinism, fail-closed input, adapter binding, cleanup, and receipt validation; blocked only because it lacks an exact `FIELD_SUPPORT` classification assertion.
- Existing protected route groups: clear/preserved. `character_recipe.py`, `mpfb_adapter.py`, `mpfb_blender_entrypoint.py`, `asset_provenance.py`, `glb_validator.py`, `windows_network_isolation.py`, `routing.py`, `selection_request.py`, and `capabilities.json` have zero candidate diff entries.

## Evidence Checked

Passed:

- Exact checkout identity: `origin/main` resolves to
  `0ee414147ae308ab1f6035d1e7776292752bd8da`; its tree is
  `f34719776bee67a731c4049b79165bd3deaa3074`; that base is an ancestor of the
  reviewed candidate. Candidate HEAD/tree exactly match the delegated subject.
- Candidate worktree was clean before this report; candidate diff from the
  expected base contains nine intended files and zero changes to protected
  runtime/registry/router source groups.
- Full `AGENTS.md` (439 lines) and full `supervisor/SKILL.md` (316 lines) were
  read from the exact checkout/skill path.
- Fresh Anvien refresh of the exact checkout's `.p2p/system` graph: 158 files,
  149 parsed code files, 43,442 nodes, and 57,629 relationships. The new
  facade has 89 symbols, 130 local relationships, 2 linked flows, and no
  inbound callers; the high file-risk value is a scope warning, not accepted
  proof of safety. Relevant existing adapter/entrypoint/provenance/validator
  surfaces were also inspected.
- Focused command
  `PYTHONDONTWRITEBYTECODE=1 python -B -m unittest tests.test_p2p_character_forge -v`:
  `12/12 PASS`.
- Registry validation: `registry_valid=true`, exactly one matching
  `game.character.generate` entry, type `KNOWLEDGE_SOURCE`, invocation
  `MODEL_ROUTABLE`; no duplicate identity.
- Real result record was read, not rerun: child PID `21596`, return code 0,
  `REAL_BLENDER_CHILD_SPAWNED=YES`, `REAL_MPFB2_EXECUTED=YES`,
  `CHARACTER_CREATED=YES`, `RIG_PRESENT=YES`, `SKIN_PRESENT=YES`,
  `GLB_STRUCTURALLY_VALID=YES`, `PROVENANCE_VALIDATION=PASS`, and
  `FIREWALL_CLEANUP_PASS=YES`.
- Independent read-only artifact validation was rerun without Blender:
  receipt/provenance/recipe-asset binding PASS; glTF `2.0`; 55 reachable
  scene nodes; `GAMEENGINE`; `MPFB_BUILT_IN_WEIGHTS`; exactly
  `Issue59.glb` plus `Issue59.asset-provenance.json`; output SHA-256
  `4e974fb6c6861731f547e3ec3d69f18f01d7ed9073df6bd96bd8ededbde3ae97`.
- Post-run OS check: 0 Blender processes and 0 `P2P-MPFB-DENY-*` rules; the
  managed recipe input is absent; provisioning root hash remains the manifest
  hash `f6907ef03674ddc995e8b0fdd988e9a003cad61df0d4f707e2a7aaeda4d4e788`.
- Prior ISSUE=55/56 history was checked. The old optional-skeleton/root-drift
  blockers are closed for this artifact; no old runtime blocker was silently
  reused as ISSUE=59 proof.

Failed:

- Contract classification is incomplete as described in the blocking finding.
- Actual-status header is stale as described in the bookkeeping finding.

Not run:

- No Blender process or real smoke was run during this Supervisor review, as
  explicitly required.
- No source/test/schema/runtime repair, PR, push, merge, deployment, release,
  or promotion was performed.
- No broad repository suite, UI/browser test, or unrelated subsystem repair was
  run.

## Invariant Closure

- affected invariant: beginner request support classification and final plan
  closure metadata, in addition to the otherwise-closed runtime/product
  invariant.
- sibling surfaces checked: request schema, facade normalization/recipe
  projection, existing recipe contract, adapter plan/execution, Blender MPFB2
  entrypoint, provenance, GLB validator, firewall lifecycle, capability
  registry/router, focused tests, runtime receipt/artifact, prior blocker
  reports, and Game Truyen boundary.
- residual unverified same-invariant surfaces: exact per-field classification
  semantics and stale top-level status label; these prevent acceptance of the
  full claim but do not indicate a new Blender/runtime failure.

## Required Fix List For Resubmission

1. Correct `FIELD_SUPPORT`/default-set semantics to use the required
   `SUPPORTED_DETERMINISTIC` category and add exact focused assertions.
2. Update the plan/status/report bookkeeping to reflect `P2 Complete;
   Supervisor Pending` for the new subject.
3. Produce a new exact candidate HEAD/tree and request fresh Supervisor review;
   do not mutate the reviewed candidate in place.

## Overall Evaluation

The implementation quality and real runtime evidence are strong for the
bounded supported male/adult/slim route. It correctly avoids NLP, duplicate
frameworks, runtime-path input, cosmetic overclaiming, and Game Truyen
mutation. Nevertheless, Supervisor acceptance is all-or-nothing for the
declared contract: the explicit support taxonomy is not closed, and the status
ledger is internally stale. Verdict is therefore `REJECT`, limited to these
small same-scope corrections; no Blender rerun is justified by the current
finding.
