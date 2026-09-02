# Supervisor Report: P2P Character Forge Productization ISSUE 59

Verdict: REJECT

## Metadata

- Report file: `reports/supervisor/rp_supervisor_260902_122500_by_gpt-5-codex_p2p-character-forge-productization-01.md`
- Review time: `2026-09-02 12:31:41 +07:00`
- Reviewer: `gpt-5-codex`
- Repo/project: `7roger89-web/P2P-upgrade-github-1`
- Review checkout: `D:\\AI\\P2P_dev\\worktrees\\p2p-issue-59-character-forge-productization-writer`
- Scope reviewed: exact candidate `8d338c0600d77b0f4fd4f790f6fa1f2422faebe8` / tree `8b0a8c870de305f302d5e2f9f3e3dd3104a45501`; base `0ee414147ae308ab1f6035d1e7776292752bd8da` / tree `f34719776bee67a731c4049b79165bd3deaa3074`
- Claim reviewed: ISSUE=59 is a complete, safe beginner-facing facade over the existing `game.character.generate` MPFB2 capability and is ready for Owner Gate.
- Authority used: current delegation, repo `AGENTS.md` and `.p2p/system/AGENTS.md`, ISSUE=59 plan/evidence/benchmark/actual-status, candidate source/schema/tests, existing adapter/entrypoint/provenance/GLB/firewall contracts, and the two supplied runtime logs.
- Related artifacts: coder report `reports/coder/rp_coder_260902_121330_by_gpt-5-codex_p2p-character-forge-productization-01.md`; runtime result and independent validation under `D:\\AI\\P2P_runtime\\mpfb2-runtime-01\\logs`.

## Executive Summary

- Problem: the implementation and real smoke largely prove the bounded MPFB2 path, but the exact candidate does not close its support-classification contract or maintain a clean exact-subject checkout.
- Decision: REJECT. `FIELD_SUPPORT` labels request-selected deterministic fields as safe-default-only, omits the deterministic classification category, and its focused assertions do not catch that. The actual-status header is also stale, and concurrent uncommitted source/test drift appeared in the review checkout.
- Required outcome: correct the classification and status bookkeeping in a new descendant, ensure the new exact subject is clean, and obtain a fresh independent Supervisor review. Do not rerun Blender solely for metadata/test correction unless the runtime path changes.

## Blocking Findings

### [MEDIUM] Support classification is incomplete and semantically misleading

File: `.p2p/system/p2p_capabilities/character_forge.py:34-70`

Issue: the facade exposes `FIELD_SUPPORT`, `SAFE_DEFAULT_FIELDS`, and
`UNSUPPORTED_DEFERRED_FIELDS` as part of its public contract. In the exact
reviewed commit, all six accepted fields are placed in
`SUPPORTED_BY_SAFE_DEFAULT`; fields whose caller values are explicitly
mapped into the recipe (`name`, `gender`, `age_class`, and `build`) are
not represented as deterministic support. `SUPPORTED_DETERMINISTIC` is absent
from the exact subject entirely.

Evidence: committed source lines 34-70 assign every supported field to
`SAFE_DEFAULT_FIELDS`/`SUPPORTED_BY_SAFE_DEFAULT`, while lines 232-258 map
caller-selected gender, age class, and build into the validated recipe. The
focused test at `tests/test_p2p_character_forge.py:107-128` asserts that
`SAFE_DEFAULT_FIELDS` equals all supported fields and never asserts an exact
support taxonomy or per-field classification.

Why this blocks acceptance: the request/recipe invariant is not accurately
closed. A consumer cannot distinguish a value that is deterministically
projected from a field that is merely fixed by a safe default. The published
facade contract is therefore incomplete even though the supported smoke request
is valid.

Fix direction: define one canonical classification for every request field;
classify request-mapped fields as `SUPPORTED_DETERMINISTIC`, retain only
fixed-only fields such as `rig` and `output_format` as
`SUPPORTED_BY_SAFE_DEFAULT`, keep unsupported material fields fail-closed, and
add exact focused assertions for the classification sets.

Re-review evidence required: new candidate HEAD/tree, source/schema/test diff,
focused suite PASS, and updated plan/status/evidence bookkeeping. Reuse the
existing runtime artifact only if the correction remains metadata/test-only and
leaves the execution recipe and runtime path unchanged.

### [MEDIUM] Actual-status header contradicts its own closure evidence

File: `docs/plans/2026-09-02-p2p-character-forge-productization-01/2026-09-02-p2p-character-forge-productization-01-actual-status.md:5`

Issue: the exact candidate says `Status: P1 Complete; P2 Pending`, while the
same file's R2 refresh, P2-A/P2-B rows, and P1/P2 decision say the smoke and
independent cleanup passed and the next action is Supervisor review.

Evidence: `actual-status.md:5`, its R2 row, P2 completion rows, and P1/P2
Decision section; `evidence.md` records P2 PASS and the runtime logs record
the same result.

Why this blocks acceptance: current status is part of the durable plan
contract. A contradictory top-level state prevents a clean closure/Owner-Gate
handoff and must not be inferred away from lower rows.

Fix direction: update the status header to a truthful state such as
`P2 Complete; Supervisor Pending` in a new descendant and refresh directly
affected closure references.

Re-review evidence required: fresh exact-subject status/diff inspection with no
contradictory active status.

### [HIGH] Exact reviewed checkout is no longer clean

File: `N/A` (checkout state)

Issue: the checkout was clean at initial binding, but during this review
`git status` showed uncommitted modifications to
`.p2p/system/p2p_capabilities/character_forge.py` and
`tests/test_p2p_character_forge.py`, plus another untracked Supervisor
report. Those changes are outside immutable candidate `8d338c...` and were not
created by this review.

Evidence: initial exact-subject status was clean; a later read-only status
reported `M` for both source/test files and `?? reports/supervisor/rp_supervisor_260902_122647_by_gpt-5-codex_p2p-character-forge-productization-01.md`.
The working-tree diff contains the classification/test edits described above.
The committed HEAD/tree remain the delegated values, but the checkout now
contains concurrent owner/agent work.

Why this blocks acceptance: a Supervisor must bind the verdict to an
unambiguous exact subject. A dirty checkout cannot be accepted as the current
candidate without owner reconciliation; the Supervisor does not revert or
clean owner data.

Fix direction: reconcile the concurrent changes outside this review, create a
new immutable descendant, and present a clean checkout for review. Do not
mutate the reviewed candidate in place.

Re-review evidence required: fresh `git status`, exact HEAD/tree, diff from the
specified base, and proof that the review subject is the only intended state.

## Source-Level Clearance Notes

- `.p2p/system/p2p_capabilities/character_forge.py:1-275`: blocked on support classification; request parsing, defaults, deterministic recipe mapping, and reuse of the existing recipe validator/hash are otherwise clear.
- `.p2p/system/p2p_capabilities/character_forge.py:278-306`: clear; runtime binding keeps runtime paths out of the beginner request and fixes MPFB2 relative locations.
- `.p2p/system/p2p_capabilities/character_forge.py:309-525`: clear for delegation; it calls the existing adapter plan/execution boundary, checks plan/output binding, reuses provenance validation, and adds no second runner, firewall, validator, or service.
- `docs/p2p-development/capability-catalog/game-asset-forge/character.request.schema.json:1-39`: clear for shape/defaults and `additionalProperties: false`; it does not repair the missing source classification taxonomy.
- `tests/test_p2p_character_forge.py:1-293`: relevant behavior coverage and 12 test methods are present, but the exact source/test subject lacks classification assertions; the review run did not complete.
- Existing protected surfaces `character_recipe.py`, `mpfb_adapter.py`, `mpfb_blender_entrypoint.py`, `asset_provenance.py`, `glb_validator.py`, `windows_network_isolation.py`, `routing.py`, `selection_request.py`, and `capabilities.json`: clear/preserved; no candidate diff entries.

## Evidence Checked

Passed:

- Exact Git binding: HEAD, candidate tree, base tree, and base ancestry match the delegated values.
- Candidate diff contains nine intended files; protected runtime/registry/router source groups are unchanged.
- Full repo `AGENTS.md`, `.p2p/system/AGENTS.md`, and the requested `supervisor/SKILL.md` were read before judgment.
- Existing Anvien index was read-only and bound to the exact candidate commit for `.p2p/system`; file detail reports the facade parsed with 89 symbols, 130 local relationships, 2 linked flows, and no inbound callers. This is topology evidence, not the verdict.
- Runtime result log was read without rerunning smoke: child PID 21596, return code 0, all required product flags PASS/YES, recipe SHA `7c4fe122da0ddf7569eaa45323037ee27414bcdac04330fcc4e5047f334a8c52`, and output SHA `4e974fb6c6861731f547e3ec3d69f18f01d7ed9073df6bd96bd8ededbde3ae97`.
- Independent validation log reports exactly two outputs, receipt/provenance/recipe-asset binding PASS, glTF 2.0, 55 reachable nodes, GameEngine/built-in weights, recipe input absent, and provisioning-root hash match.
- Physical read-only artifact checks matched the logged GLB SHA and output size; the sidecar matched character, recipe, GLB hash, four `mpfb2-core` assets, MPFB2 2.0.17, and `CORE_CC0_ONLY`. Blender stderr was empty and stdout contained addon identity/preference/register markers.
- Read-only Game Truyen check showed HEAD `354203ee7c23a2b349e81a0254b537da4d9c622f` and 55 pre-existing dirty entries; no candidate file references that project.
- The exact candidate contains no self-referential candidate HEAD/tree bookkeeping; only base/implementation identities are recorded in its plan/report artifacts.

Failed:

- Support classification is incomplete/misleading as described above.
- Top-level actual-status label is stale as described above.
- The review checkout became dirty with concurrent source/test/report changes, so its current filesystem state is not an unambiguous exact-subject checkout.

Not run:

- No Blender process, real smoke, retry, or runtime repair was run during this review, per explicit instruction.
- No production source/test/schema/runtime file was repaired, reverted, pushed, merged, released, deployed, or promoted by this review.
- The one attempted focused-suite command did not complete within the bounded wait and is not used as PASS evidence; the coder report's `12/12` claim remains indirect evidence only.
- No broad suite, browser/UI test, or unrelated subsystem validation was run.

## Invariant Closure

- affected invariant: beginner request support classification and durable plan status, with exact candidate identity/clean-checkout binding; runtime/recipe/provenance/output/isolation is otherwise closed for the supplied supported request.
- sibling surfaces checked: request schema, facade normalization/recipe projection, existing recipe validator, adapter plan/execution, Blender entrypoint, provenance, GLB validator, firewall lifecycle, capability registry/router, focused tests, runtime receipt/artifact, plan/evidence/benchmark/status, coder report, and Game Truyen boundary.
- residual unverified same-invariant surfaces: exact per-field classification semantics, contradictory top-level status, and clean exact-subject reconciliation. These prevent acceptance of the full claim; no new Blender/runtime blocker was inferred.

## Required Fix List For Resubmission

1. Add truthful `SUPPORTED_DETERMINISTIC` versus `SUPPORTED_BY_SAFE_DEFAULT` field classifications and exact focused assertions while preserving fail-closed unsupported/runtime/path/network behavior.
2. Change the active actual-status header and directly affected bookkeeping to the truthful post-smoke/Supervisor-pending state.
3. Reconcile the concurrent dirty checkout without Supervisor cleanup, create a new exact descendant subject, and provide fresh HEAD/tree/status/diff evidence.
4. Re-run only the focused suite as needed for the corrected source/test subject; do not rerun Blender unless the execution path or recipe contract changes.

## Overall Evaluation

Implementation quality and the real male/adult/slim runtime evidence are strong
for the bounded path: one capability identity is reused, the adapter, entrypoint,
provenance, GLB validator, and firewall are reused, unsupported material intent
fails closed, and Game Truyen was not touched. That is not sufficient for
acceptance. The exact candidate's support taxonomy is not closed, its durable
status is internally contradictory, and the review checkout is no longer clean.
Verdict is therefore REJECT, limited to these same-scope
contract/bookkeeping/subject-binding corrections; no Blender rerun is justified
by the current findings.
