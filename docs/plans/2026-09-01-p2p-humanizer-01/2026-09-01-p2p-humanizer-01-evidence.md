# P2P-HUMANIZER-01 Evidence Ledger

## Metadata

- Date: `2026-09-01`
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
  created under repo-local `.tmp/p2p-humanizer-01`; `git fetch origin main
  --prune` completed. Current `origin/main`/HEAD is commit
  `d80934bc0090ef0cc6770f8c7d09b7b4cd4670b7`, tree
  `b2d5d03bcb81058ae4be9fea525603d53ea28ee5`, with a clean worktree.
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

P1-B evidence remains pending. The following IDs are reserved by the plan:

- `E1-P1A-SRC1`: exact two-file vendor snapshot comparison.
- `E1-P1A-REG1`: manifest parse/provenance/contract metadata.
- `E1-P1A-HASH1`: snapshot and entrypoint hash binding.
- `E1-P1A-ROUTE1`: explicit route selection and metadata-only discovery.
- `E1-P1A-ROUTE2`: unrelated/empty request exclusion and no global default.
- `E1-P1B-TEST1..E1-P1B-TEST7`: focused A-G value/boundary cases.
- `E1-P1B-BUILD1`: compile/build-equivalent and nearest-boundary validation.
- `E1-P1B-DETECT1`: Anvien detect-changes immediately before the slice commit.

## E2 - P2 Evidence

Matching plan item(s): `P2-A`, `P2-B`, `P2-C`

- `E2-P2A-SUP1`: reserved for a new independent Supervisor review; not run by
  the Writer lane before handoff.
- `E2-P2C-PR1`: reserved for exact branch/PR/Issue #51 linkage and candidate
  head/tree binding.

## Closure Evidence

Writer closure evidence will contain the final focused results, branch/PR
identity, exact candidate SHA/tree, `git status`, detect-changes result, and
the explicit stop at `NEXT_STEP=INDEPENDENT_SUPERVISOR`. Merge, promotion, and
Owner approval execution are not part of this Writer handoff.
