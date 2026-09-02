# P2P-HUMANIZER-01 Evidence Ledger

## Metadata

- Date: `2026-09-02`
- Plan: `docs/plans/2026-09-01-p2p-humanizer-01/2026-09-01-p2p-humanizer-01-plan.md`
- Evidence: `docs/plans/2026-09-01-p2p-humanizer-01/2026-09-01-p2p-humanizer-01-evidence.md`
- Benchmark: `docs/plans/2026-09-01-p2p-humanizer-01/2026-09-01-p2p-humanizer-01-benchmark.md`
- Actual status: `docs/plans/2026-09-01-p2p-humanizer-01/2026-09-01-p2p-humanizer-01-actual-status.md`

## Evidence Rules

The evidence file explains why the work is known to be correct.

It should contain:

- metadata and companion files;
- evidence rules or evidence template;
- evidence sections such as `E0`, `E1`, or sections by phase/task;
- user report or problem evidence;
- source inspection, codebase facts, and document facts;
- commands run and pass/fail result;
- impact or blast-radius evidence when code/graph behavior changes;
- implementation evidence: files changed and behavior changed;
- validation evidence: build, tests, e2e, screenshots, or traces;
- failures encountered and how they were handled;
- detect-changes before commit;
- commit hash and closure evidence.

Evidence can reference short metric traces, but long metric tables belong in the benchmark file.

### Evidence ID Naming

Use stable, phase-scoped evidence IDs so `plan.md`, `actual-status.md`, `benchmark.md`, and later agents can reference exact proof without ambiguity.

Format:

```text
E<phase>-<item>-<kind><n>
```

Rules:

- `E<phase>` matches the plan phase number: `E0` for `P0`, `E1` for `P1`, `E2` for `P2`, and so on.
- `<item>` matches the checklist item without the dash.
- `<kind>` is a short uppercase token meaningful in this plan.
- `<n>` is a 1-based sequence within that phase/item/kind.
- Do not reuse an evidence ID for different facts.
- Reference exact evidence IDs inside all companion documents.

Evidence sections follow the plan phases: `E0` for P0, `E1` for P1, and `E2` for P2.

## E0 - P0 Evidence

Matching plan item(s): `P0-A`

- `E0-P0A-GIT1`: Fresh clone of `7roger89-web/P2P-upgrade-github-1` was
  created under repo-local `.tmp/p2p-humanizer-01`; the initial
  `git fetch origin main --prune` bound `d80934bc...` and tree
  `b2d5d03b...` before implementation.
- `E0-P0A-REBASE1`: A second fresh remote check found unrelated upstream main
  delta PR #50 and advanced `origin/main` to commit
  `b65948b00ed2a8969fed70ab59f68b5d9b53858d`, tree
  `6553b9cb55990f66f6da5b2db83dc6f5ec7e393c`. The sole Writer branch was
  rebased onto that exact current main; merge-base now equals `b65948b...` and
  no Humanizer conflict occurred.
- `E0-P0A-UP1`: Detached upstream checkout is
  `https://github.com/blader/humanizer.git` at commit
  `e2e92e7b4b8229253ed5c8e81dc65463fdeddda5`, tree
  `b8a8804ed9210e539531fc26c2d84fdb603960f4`. Exact Git blob hashes are
  `SKILL.md` blob `c9c22422f822f07767ad1b6e79eedccbfe4e9f63` and `LICENSE`
  blob `625297fb778f32eb39d3a5b97e3e3b611b7304d6`; raw SHA-256 values are
  `14fc8a965b6e0a8dc100ba4dffeab55cb94bbac112abbde7e014d5c15a35c202` and
  `4ac4810254ab36d45419141aeb8e69bf50652cfafe5b2dab947d06d44e5cbf96`.
  `SKILL.md` declares version `2.11.2`; `LICENSE` is the MIT License.
- `E0-P0A-SPEC1`: The relevant approved capability, routing/readiness,
  context-pointer, trust/data-instruction, execution/evidence, provider, and
  host-projection specs were read in full. No `SPEC-MAP.md` exists in this
  checkout; the explicit SPEC cluster was used and the absence is recorded,
  not hidden.
- `E0-P0A-REG1`: Current registry has 67 records, exactly one
  `creative.copywriting` record, and no `creative.prose.humanize` record.
  Existing copywriting is advertising/double-semantic marketing-only with
  `LOCAL_VENDOR_SNAPSHOT` provenance and must be preserved rather than
  duplicated or broadened.
- `E0-P0A-ADAPTER1`: Existing `p2p_capabilities.vendor_skill` already owns
  metadata-only discovery, on-demand selected loading, canonical text hashing,
  snapshot hashing, safe relative paths, and no permission/network grant. Its
  behavior is generic for a no-reference Markdown snapshot; no adapter code is
  required by the requested scope.
- `E0-P0A-GRAPH1`: `anvien analyze --force` on the valid clone completed with
  1,109 scanned files, 199 parsed code files, 0 parse failures, and a current
  graph. Anvien does not resolve the hidden `.p2p` registry/adapter paths as
  file-detail targets in this graph. Existing test detail was available for
  `tests/test_p2p_vendor_skill_integration.py`: 41 symbols and 39 local
  relationships, risk `high`; this is a scope warning, not an edit ban.
- `E0-P0A-BASE1`: The nearest vendor/foundation/host/visual/game test batch
  ran 104 tests with 97 passing and 7 pre-existing failures: stale registry
  counts (`65`/`39` versus current `67`), stale visual route expectations for
  `ui.game_hud`/`ui.motion`, and an external-framework assertion against the
  already-present `img2threejs_adapter.py`. The focused existing vendor module
  itself passed 22/22. These failures predate Humanizer and are not silently
  reclassified as new regressions.
- `E0-P0A-SCOPE1`: Invariant family map is closed for planning: registry
  manifest + existing vendor loader + existing router + exact vendor snapshot
  + focused behavior fixtures. Forbidden alternate paths are second router,
  second engine, global activation, upstream execution, dependency install,
  and protected-content rewrite.

## E1 - P1 Evidence

Matching plan item(s): `P1-A`, `P1-B`

P1-A implementation evidence:

- `E1-P1A-SRC1`: The P2P vendor root contains exactly `SKILL.md` and
  `LICENSE`; byte comparison against the detached upstream checkout returned
  zero differences for both files.
- `E1-P1A-REG1`: Existing `load_registry` accepted 68 valid records with one
  `creative.copywriting` and one `creative.prose.humanize`; canonical
  identities remain eight and `full_quorum` remains `8/8`. The new record is
  `TYPE=SKILL`, `INVOCATION_CLASS=USER_REQUESTED`, `STATUS=ACTIVE`,
  `VERSION=2.11.2`, noncanonical, and non-optional.
- `E1-P1A-HASH1`: `snapshot_tree_sha256` returned
  `46249684a9dbb7f4a8b759f04178f0078dd3448ef5b77d203dbf7834d0c88607` and the
  loaded entrypoint returned the registry SHA-256
  `14fc8a965b6e0a8dc100ba4dffeab55cb94bbac112abbde7e014d5c15a35c202`.
  The vendored `LICENSE` canonical hash is
  `4ac4810254ab36d45419141aeb8e69bf50652cfafe5b2dab947d06d44e5cbf96`.
- `E1-P1A-ROUTE1`: Existing `discover_vendor_skills` selected exactly
  `creative.prose.humanize` for an explicit humanization request while
  returning `content_loaded=false`; `load_vendor_skill` then loaded only
  `SKILL.md` with `permission_grant=false` and `network_used=false`.
- `E1-P1A-ROUTE2`: The ordinary request `Write an article about natural
  prose.` did not select the new capability, and the no-dependency load probe
  returned `NOT_REQUIRED` without installation or network.
- `E1-P1A-FAIL1`: The first smoke command used a relative `Path('.')` parent
  and looked for the audit checkout in the wrong directory. The command was
  corrected to use `Path.cwd()`; the corrected P1-A smoke passed and no source
  was changed by the failed assertion.

P1-B implementation evidence:

- `E1-P1B-TEST1`: Case A passed in
  `tests/test_p2p_humanizer_integration.py`: the obvious AI-style fixture
  changes to a shorter natural sentence while preserving `dashboard`, `CSV
  files`, and `12 users`.
- `E1-P1B-TEST2`: Case B passed: unsupported facts/names/numbers/dates/quotes/
  citations and detector-evasion/bypass claims are prohibited by the manifest,
  and the loaded upstream prompt contains its no-fabrication rule.
- `E1-P1B-TEST3`: Case C passed: the supplied writer sample's `So` cadence is
  reflected in the expected output while the source facts remain present.
- `E1-P1B-TEST4`: Case D passed: the mixed Markdown fixture changes prose only;
  frontmatter, fenced code, URL targets, and the structured table are identical.
- `E1-P1B-TEST5`: Case E passed: technical fixture preserves inline command,
  SHA/commit/tree values, quoted evidence, and citation target exactly.
- `E1-P1B-TEST6`: Case F passed: empty, ordinary article, and unrelated
  PostgreSQL requests do not select or load the Humanizer capability; metadata
  reports `ON_DEMAND`.
- `E1-P1B-TEST7`: Case G passed: explicit
  `creative.prose.humanize` invocation selects only the new capability through
  the existing single router and loads only `SKILL.md` without permission or
  network flags.
- `E1-P1B-TEST8`: Exact snapshot/workflow and no-dependency boundary tests
  passed, bringing the direct module result to 9/9.
- `E1-P1B-GRAPH1`: After the focused test was added, Anvien file detail parsed
  `tests/test_p2p_humanizer_integration.py` with 33 symbols and 24 local
  relationships, risk `high`, stale `false`; file impact found no affected
  production files or flows. The high label is a scope warning for a test
  file, not evidence of a production blast radius.
- `E1-P1B-BUILD1`: `python -m compileall -q .p2p/system/p2p_capabilities
  scripts tests` exited 0 (one pre-existing SyntaxWarning in
  `test_p2p_live_certification.py`); nearest-boundary unittest batch
  `tests.test_p2p_humanizer_integration`, `tests.test_p2p_vendor_skill_integration`,
  and `tests.test_p2p_host_skill_projection` passed 61/61; `git diff --check`
  exited 0.
- `E1-P1B-GLOBAL1`: `python scripts/doctor.py --package . --role development
  --json` returned exit 1 because the current development checkout has a
  governance-drift report for unlocked/protected runtime files. This is a
  candidate-state governance signal, not a Humanizer route/load failure; the
  user requested no promotion or lock rebuild in this Writer lane.
- `E1-P1B-GLOBAL2`: The broad framework validator returned 52/59 with seven
  failures in existing ledger/charter/dependency/freshness/governance fields;
  none is a Humanizer capability/loader assertion. It is retained as a
  disclosed current-baseline limitation and excluded from focused PASS.
- `E1-P1B-RETRY1`: The first fixture run exposed an over-broad assertion that
  demanded upstream commit/tree values in a candidate-only technical fixture.
  Removing that unrelated expectation kept the acceptance boundary precise;
  the corrected focused module passed 9/9.
- `E1-P1B-DETECT1`: Staged `anvien detect-changes --scope all` after the graph
  refresh reported 14 changed files in the current slice, 5 affected files,
  overall risk `low`, and the focused test file as the only `high` file-risk
  warning. It reported no affected production files or execution flows; the
  registry/vendor production changes were already checkpointed in `2c85e855`.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`, `P2-C`

- `E2-P2A-SUP1`: reserved for a new independent Supervisor review; not run by
  the Writer lane before handoff.
- `E2-P2C-PR1`: Draft PR #53 is open at
  `https://github.com/7roger89-web/P2P-upgrade-github-1/pull/53`, links Issue
  #51 with `Refs #51`. The PR head/tree is intentionally fetched externally
  at review or promotion time; no moving candidate identity is committed.

## E3 - Reconciliation Evidence

- `E3-RECON1`: Fresh `git fetch origin main --prune` verified the current
  canonical main; fresh PR ref fetch verified the existing PR #53 head. Issue
  #51 is OPEN, PR #53 is the sole open Humanizer PR, and it remains draft/open.
- `E3-RECON2`: The old PR base was stale relative to current main. The
  existing Writer branch was reconciled with a non-rewriting
  `git merge --no-ff --no-edit origin/main`; no rebase, force-push, or merge to
  `main` was used.
- `E3-RECON3`: Candidate registry comparison against current main shows the
  five social IDs and `creative.copywriting` match current main exactly;
  `creative.prose.humanize` is the single additional ID.
- `E3-RECON4`: The direct Content Studio test assertion that required
  Humanizer to be absent was a stale cross-workstream assumption. It now
  permits the distinct registry ID; the social records, projections, and
  Voice Profile downstream wording were not edited.
- `E3-RECON5`: Current focused/adjacent suite
  `tests.test_p2p_humanizer_integration`,
  `tests.test_p2p_social_content_skills`,
  `tests.test_p2p_vendor_skill_integration`, and
  `tests.test_p2p_host_skill_projection` ran 73/73 PASS.
- `E3-RECON6`: The current candidate remains on one Writer branch and one
  draft PR. No global activation, second router, second registry, second
  runtime, promotion, or Owner approval execution was added.
- `E3-RECON7`: Moving PR head/tree claims were removed from committed
  Humanizer notes, plan evidence, and coder report. Current identity is a
  review-time external binding, not a self-referential evidence loop.
- `E3-RECON8`: Post-reconciliation Anvien refresh completed with 1,154 scanned
  files, 202 parsed code files, and 0 parse failures. File detail recorded the
  social test at 41 symbols/19 local relationships and the Humanizer test at
  33 symbols/24 local relationships; both file impacts reported 0 affected
  production files or flows. Compile sanity exited 0 and `git diff --check`
  passed.
- `E3-RECON9`: A final `anvien detect-changes --scope all` run is the only
  change-detection gate for the reconciliation cleanup commit; its result is
  terminal validation and is not written as a moving candidate SHA/tree claim.

## Closure Evidence

Final current base/candidate SHA/tree, branch status, and PR state are fetched
externally immediately before independent review. They are intentionally not
written back into this evidence file. The Writer lane stops after exactly one
independent Supervisor: PASS -> Owner Gate; REJECT -> genuine blocker. Merge
to `main`, promotion, and Owner approval execution remain unperformed.

Current Writer handoff binding: PR #53 remains draft/open and its current
head/tree are fetched externally when the exact review subject is bound.
