# P2P Frontend Upstream Intake 01 — Curated Capability Pack

- Task: `P2P_FRONTEND_UPSTREAM_INTAKE_01`
- Date: 2026-09-18 (UTC)
- Branch: `arena/01a0b287-p2p-upgrade-github-1` (ONE branch → ONE PR)
- Scope: P2P CORE only. No real-project rollout, no release/promotion/deployment.
- Ledger batch: `RA-EXT-082 .. RA-EXT-091` in
  `governance/research-adoption-ledger.json`
  (projection: `docs/RESEARCH-ADOPTION-LEDGER.md` §4.4).
- Focused tests: `tests/test_p2p_frontend_upstream_intake_01.py` (§11 A–K).

Precedence rule for this intake: `COPY_AUTHORITATIVE_UPSTREAM_ARTIFACT` —
adopt upstream bytes verbatim wherever they are coherent; put every P2P
judgment in wrappers, adapters, routers, notices, and tests instead of
editing upstream bytes. Result: **zero** `COPY_WITH_MIN_PATCH` rows — every
adopted upstream byte in this pack is bit-identical to its pinned upstream
(verified by git blob/subtree SHA, §6). All P2P authoring lives in wrapper /
adapter / router / `UPSTREAM_NOTICES.md` files, which are P2P-owned and
honestly labeled as such.

## 1. Upstream pins and rights

| # | UPSTREAM_REPO | Pinned commit | Rights (observed) | Ledger | Outcome |
| --- | --- | --- | --- | --- | --- |
| 1 | `vercel-labs/agent-skills` | `063bee94c3f4df8453406c830b0a7df0f2860278` | MIT (per skill frontmatter, author `vercel`; no root LICENSE) | RA-EXT-082 | IMPLEMENTED — 2 units vendored |
| 2 | `PracticalSwan/agent-skills` | `ff6d12f61e8250dd1b988e101a482f6adc05c451` | MIT AND Apache-2.0 (rights files vendored) | RA-EXT-083 | IMPLEMENTED — design unit vendored |
| 3 | `DNM03/frontend-code-review` | `033d1c5d8bccc311fc3c4362690a482016651b96` | MIT © 2026 frontend-code-review contributors | RA-EXT-084 | IMPLEMENTED — review unit vendored |
| 4 | `ibelick/ui-skills` | `c5bcd86450b3582ba25204c622b9213b07464938` | MIT © 2026 Julien Thibeaut | RA-EXT-085 | IMPLEMENTED — baseline-ui vendored |
| 5 | `millionco/react-doctor` | `499a0208fca5c0422b713bdedf2b83fcc8e29d20` | Modified MIT License (custom) + agent-use notice | RA-EXT-086 | IMPLEMENTED — pinned EXTERNAL_TOOL adapter |
| 6 | `pbakaus/impeccable` | `f2c7051853848826aac2f4646581d62a732155ad` | Apache-2.0 | RA-EXT-087 | DEFERRED — nothing copied |
| 7 | `microsoft/skills` | `f7d8a83e55ab7bf125cb1134e892302c2344592e` | MIT | RA-EXT-088 | RESEARCHED — reference only |
| 8 | `emilkowalski/skills` | `85e8e2363b713506e1d5b6e07a0eb2da66be1bc3` | MIT © 2026 Emil Kowalski | RA-EXT-089 | IMPLEMENTED — 1 unit vendored |
| 9 | `vercel-labs/design-systems-to-agent-skills` | `0e541bc7a8eb8e86e6b1c93fac7cf21588d487da` | MIT | RA-EXT-090 | RESEARCHED — reference only |
| 10 | `TanStack/table` | `21d713fc4947d2a08cc2136bb055889a61412ded` | MIT | RA-EXT-091 | RESEARCHED — no bounded gap |

Related non-intake source evaluated and kept reference-only (§5.11):
`vercel-labs/web-interface-guidelines` (`command.md` on `main`).

## 2. What changed in P2P CORE

New skills (vendored verbatim + P2P notices file each):

- `.agents/skills/react-best-practices/` — Vercel React/Next.js performance
  rules (SKILL.md, AGENTS.md, metadata.json, 72 `rules/*.md`).
- `.agents/skills/composition-patterns/` — Vercel React composition patterns
  (SKILL.md, AGENTS.md, metadata.json, 10 `rules/*.md`).
- `.agents/skills/frontend-code-review/` — DNM03 review skill (SKILL.md,
  11 `references/*.md`, 2 `examples/*.md`).
- `.agents/skills/baseline-ui/` — ibelick anti-slop UI baseline (SKILL.md).

Reworked skills (P2P-authored, no upstream bytes except where noted):

- `.agents/skills/frontend-development/SKILL.md` — converted to a thin hub
  (82 lines): routes by intent, names the pack, and explicitly refuses to
  impose a generic stack. All one-project material removed: the legacy
  `resources/` (10 files: MUI v7 patterns, TanStack Router guide, project
  aliases, SuspenseLoader conventions, …) is deleted, and no project
  stack name survives in the hub.
- `.agents/skills/frontend-design/SKILL.md` — converted to a context-fit
  wrapper at the same path. The old universal BOLD/unforgettable/extreme
  rules are gone; the wrapper defines the p2p-uiux boundary, the mode
  router, project design-system precedence, and the runtime evidence
  contract. The normative workflow is the vendored upstream body
  `upstream-frontend-design-v2.md` plus `references/accessibility-checklist.md`
  and `scripts/contrast-checker.py`.

New adapter (P2P-authored, zero vendored bytes):

- `.agents/skills/react-doctor/SKILL.md` — pinned optional EXTERNAL_TOOL
  adapter over `react-doctor@0.9.14` (observed upstream commit above).

Extended skill (one vendored file + router row):

- `.agents/skills/UI-animation-design/find-animation-opportunities/` —
  Emil Kowalski restraint-first opportunity finder; router row added to the
  `UI-animation-design` SKILL.md.

Machinery integration (existing surfaces only):

- `scripts/package_release.py` — `RELEASE_SKILLS` += the 7 pack skills.
- `scripts/doctor.py` — `EXPECTED_SKILLS` += the 7 pack skills, plus
  `SKILL_NAME_ALIASES` for the three units whose frontmatter `name:` differs
  from the directory name (`vercel-react-best-practices`,
  `vercel-composition-patterns`, `frontend-dev-guidelines`); the name check
  accepts the alias set.
- `AGENTS.md` + root `CLAUDE.md` — skill tables += 5 rows each for the new
  units (`frontend-development`/`frontend-design` rows already existed).
  `.p2p/system/AGENTS.md` is anvien-managed and untouched.
- All three skill mirrors (`.agents/skills/`, `.claude/skills/`,
  `.p2p/system/.agents/skills/`) kept byte-identical; all three skill
  manifests regenerated for the 8 touched skills (§4).

## 3. Method and fetch honesty

The sandbox blocks the git protocol (`fatal: could not read Username`,
proxy-intercepted) and direct curl to `raw.githubusercontent.com`
(HTTP 000). Upstream inspection therefore ran over the GitHub REST API
(trees/blobs) and raw-file fetches through the available page-fetch
channel — every listing, blob SHA, and file content cited here was read
from the pinned commit, not from memory or from a moving branch.

Byte-identity verification is cryptographic, not visual:

- Single files: `git hash-object` locally vs the upstream blob SHA from
  the API. Equal SHA = bit-identical.
- Directories: `rules/`, `references/`, `examples/` subtree SHAs recomputed
  through a disposable git index vs the upstream tree SHA. Equal SHA =
  identical file set, names, modes, and bytes.
- Runtime smoke: the vendored `contrast-checker.py` (stdlib only) was
  executed locally: sample pair scores `12.92:1`, AAA pass.
- `react-doctor@0.9.14` CLI probes: `rules list` enumerates 906 rule
  entries; `--json` emits the versioned `JsonReport` wire format
  (`schemaVersion: 3`); the remote score API is unreachable offline
  (`score: null`). A full lint verdict was NOT obtainable in this sandbox
  (the oxlint worker is killed by SIGABRT/OOM) — recorded as an environment
  limitation, and the adapter requires the `complete` + coverage check
  instead of trusting exit output.

## 4. Standing decisions

- **BOLD bias fix (frontend-design).** The old skill universalized one loud
  aesthetic ("commit to a BOLD aesthetic direction", "NEVER converge on
  common choices", …). All four loud-universal rules are removed; the
  wrapper routes through context-fit modes and defers to p2p-uiux and the
  target project's own design system. Focused tests assert the markers are
  absent and the boundary markers present.
- **Thin hub (frontend-development).** 82 lines, no stack names, no
  `resources/`. Backend-only tasks load nothing; every UI intent routes to
  at most the skills it needs (progressive disclosure is asserted).
- **Notices travel with the units.** Each vendored unit carries an
  `UPSTREAM_NOTICES.md` (repo, pinned commit, upstream path, rights,
  taken/not-taken lists) so the packaged release artifact — which ships
  skill directories, not this report — stays license-honest. The four
  LICENSE-carrying cases reproduce the full MIT text; the Vercel units
  record the frontmatter MIT grant (no upstream LICENSE file exists).
- **React Doctor is a pinned tool, never authority.** Pin `0.9.14` only;
  `NEVER @latest`; `NEVER` fetch the remote triage playbook
  (`https://www.react.doctor/prompts/…` — full URL recorded here as
  evidence and deliberately absent from the skill so canonical behavior
  cannot depend on it); `score: null` ⇒ `SCORE_UNAVAILABLE`;
  `complete: false` ⇒ partial run, never a clean bill;
  `REACT_DOCTOR_UNAVAILABLE` downgrades without blocking.
- **No moving `main` in canonical behavior.** No skill file references a
  live remote prompt, a `@latest` install (outside NEVER prohibitions), or
  a fetch-fresh-`main` step. The focused tests scan every byte of all 8
  touched skills for the forbidden markers.
- **Manifest aggregate scheme (documented).** Anvien's original aggregate
  algorithm is opaque (no in-repo generator); per-file SHA-256 entries are
  the authoritative verification surface. Touched manifest entries
  recompute the aggregate deterministically from current per-file hashes
  (`sha256` over `path␊hash` lines, sorted) so manifests stay
  self-consistent. The scheme is asserted by test, not just described here.
- **Force-add discipline.** `.agents/` and `.claude/` are git-ignored by the
  anvien block in `.gitignore`, while the repo tracks skill files under
  them by force-add convention. Every new skill file in this change set
  must be (and was) committed with `git add -f`; a plain `git add -A`
  would silently drop the vendored units.

## 5. File-level adoption matrix

Verdicts: `COPY_AS_IS` (bit-identical; rename-on-landing allowed and
recorded), `COPY_WITH_MIN_PATCH` (none in this intake — stated explicitly so
the absence is auditable, not an oversight), `EXTERNAL_TOOL` (used, never
vendored), `REFERENCE_ONLY` (studied; kept as cited reference),
`DEFER` (selected direction, postponed with conditions), `REJECT`
(deliberately not adopted, rationale recorded). Every row names
UPSTREAM_REPO (pinned commit from §1), the upstream path, and the
P2P_TARGET (`—` = nothing landed in the tree).

### 5.1 vercel-labs/agent-skills (RA-EXT-082)

| UPSTREAM_REPO | UPSTREAM_PATH | VERDICT | P2P_TARGET | RATIONALE |
| --- | --- | --- | --- | --- |
| vercel-labs/agent-skills | `skills/composition-patterns/SKILL.md` | COPY_AS_IS | `composition-patterns/SKILL.md` | blob `d07025bf…` verified |
| vercel-labs/agent-skills | `skills/composition-patterns/AGENTS.md` | COPY_AS_IS | `composition-patterns/AGENTS.md` | blob `558bf9aa…` verified |
| vercel-labs/agent-skills | `skills/composition-patterns/metadata.json` | COPY_AS_IS | `composition-patterns/metadata.json` | blob `3470b744…` verified |
| vercel-labs/agent-skills | `skills/composition-patterns/rules/_sections.md` | COPY_AS_IS | `composition-patterns/rules/_sections.md` | blob verified |
| vercel-labs/agent-skills | `skills/composition-patterns/rules/_template.md` | COPY_AS_IS | `composition-patterns/rules/_template.md` | blob verified |
| vercel-labs/agent-skills | `skills/composition-patterns/rules/architecture-avoid-boolean-props.md` | COPY_AS_IS | `composition-patterns/rules/architecture-avoid-boolean-props.md` | blob verified |
| vercel-labs/agent-skills | `skills/composition-patterns/rules/architecture-compound-components.md` | COPY_AS_IS | `composition-patterns/rules/architecture-compound-components.md` | blob `e5e3043c…` verified |
| vercel-labs/agent-skills | `skills/composition-patterns/rules/patterns-children-over-render-props.md` | COPY_AS_IS | `composition-patterns/rules/patterns-children-over-render-props.md` | blob verified |
| vercel-labs/agent-skills | `skills/composition-patterns/rules/patterns-explicit-variants.md` | COPY_AS_IS | `composition-patterns/rules/patterns-explicit-variants.md` | blob verified |
| vercel-labs/agent-skills | `skills/composition-patterns/rules/react19-no-forwardref.md` | COPY_AS_IS | `composition-patterns/rules/react19-no-forwardref.md` | blob verified |
| vercel-labs/agent-skills | `skills/composition-patterns/rules/state-context-interface.md` | COPY_AS_IS | `composition-patterns/rules/state-context-interface.md` | blob verified |
| vercel-labs/agent-skills | `skills/composition-patterns/rules/state-decouple-implementation.md` | COPY_AS_IS | `composition-patterns/rules/state-decouple-implementation.md` | blob verified |
| vercel-labs/agent-skills | `skills/composition-patterns/rules/state-lift-state.md` | COPY_AS_IS | `composition-patterns/rules/state-lift-state.md` | blob verified |
| vercel-labs/agent-skills | `skills/composition-patterns/README.md` | REFERENCE_ONLY | — | history/marketing stays upstream; SKILL.md is the entrypoint |
| vercel-labs/agent-skills | `skills/react-best-practices/SKILL.md` | COPY_AS_IS | `react-best-practices/SKILL.md` | blob `237988de…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/AGENTS.md` | COPY_AS_IS | `react-best-practices/AGENTS.md` | blob `4e340a50…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/metadata.json` | COPY_AS_IS | `react-best-practices/metadata.json` | blob `3bec38b1…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/_sections.md` | COPY_AS_IS | `react-best-practices/rules/_sections.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/_template.md` | COPY_AS_IS | `react-best-practices/rules/_template.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/advanced-effect-event-deps.md` | COPY_AS_IS | `react-best-practices/rules/advanced-effect-event-deps.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/advanced-event-handler-refs.md` | COPY_AS_IS | `react-best-practices/rules/advanced-event-handler-refs.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/advanced-init-once.md` | COPY_AS_IS | `react-best-practices/rules/advanced-init-once.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/advanced-use-latest.md` | COPY_AS_IS | `react-best-practices/rules/advanced-use-latest.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/async-api-routes.md` | COPY_AS_IS | `react-best-practices/rules/async-api-routes.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/async-cheap-condition-before-await.md` | COPY_AS_IS | `react-best-practices/rules/async-cheap-condition-before-await.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/async-defer-await.md` | COPY_AS_IS | `react-best-practices/rules/async-defer-await.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/async-dependencies.md` | COPY_AS_IS | `react-best-practices/rules/async-dependencies.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/async-parallel.md` | COPY_AS_IS | `react-best-practices/rules/async-parallel.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/async-suspense-boundaries.md` | COPY_AS_IS | `react-best-practices/rules/async-suspense-boundaries.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/bundle-analyzable-paths.md` | COPY_AS_IS | `react-best-practices/rules/bundle-analyzable-paths.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/bundle-barrel-imports.md` | COPY_AS_IS | `react-best-practices/rules/bundle-barrel-imports.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/bundle-conditional.md` | COPY_AS_IS | `react-best-practices/rules/bundle-conditional.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/bundle-defer-third-party.md` | COPY_AS_IS | `react-best-practices/rules/bundle-defer-third-party.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/bundle-dynamic-imports.md` | COPY_AS_IS | `react-best-practices/rules/bundle-dynamic-imports.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/bundle-preload.md` | COPY_AS_IS | `react-best-practices/rules/bundle-preload.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/client-event-listeners.md` | COPY_AS_IS | `react-best-practices/rules/client-event-listeners.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/client-localstorage-schema.md` | COPY_AS_IS | `react-best-practices/rules/client-localstorage-schema.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/client-passive-event-listeners.md` | COPY_AS_IS | `react-best-practices/rules/client-passive-event-listeners.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/client-swr-dedup.md` | COPY_AS_IS | `react-best-practices/rules/client-swr-dedup.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/js-batch-dom-css.md` | COPY_AS_IS | `react-best-practices/rules/js-batch-dom-css.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/js-cache-function-results.md` | COPY_AS_IS | `react-best-practices/rules/js-cache-function-results.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/js-cache-property-access.md` | COPY_AS_IS | `react-best-practices/rules/js-cache-property-access.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/js-cache-storage.md` | COPY_AS_IS | `react-best-practices/rules/js-cache-storage.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/js-combine-iterations.md` | COPY_AS_IS | `react-best-practices/rules/js-combine-iterations.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/js-early-exit.md` | COPY_AS_IS | `react-best-practices/rules/js-early-exit.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/js-flatmap-filter.md` | COPY_AS_IS | `react-best-practices/rules/js-flatmap-filter.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/js-hoist-regexp.md` | COPY_AS_IS | `react-best-practices/rules/js-hoist-regexp.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/js-index-maps.md` | COPY_AS_IS | `react-best-practices/rules/js-index-maps.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/js-length-check-first.md` | COPY_AS_IS | `react-best-practices/rules/js-length-check-first.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/js-min-max-loop.md` | COPY_AS_IS | `react-best-practices/rules/js-min-max-loop.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/js-request-idle-callback.md` | COPY_AS_IS | `react-best-practices/rules/js-request-idle-callback.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/js-set-map-lookups.md` | COPY_AS_IS | `react-best-practices/rules/js-set-map-lookups.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/js-tosorted-immutable.md` | COPY_AS_IS | `react-best-practices/rules/js-tosorted-immutable.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/rendering-activity.md` | COPY_AS_IS | `react-best-practices/rules/rendering-activity.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/rendering-animate-svg-wrapper.md` | COPY_AS_IS | `react-best-practices/rules/rendering-animate-svg-wrapper.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/rendering-conditional-render.md` | COPY_AS_IS | `react-best-practices/rules/rendering-conditional-render.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/rendering-content-visibility.md` | COPY_AS_IS | `react-best-practices/rules/rendering-content-visibility.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/rendering-hoist-jsx.md` | COPY_AS_IS | `react-best-practices/rules/rendering-hoist-jsx.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/rendering-hydration-no-flicker.md` | COPY_AS_IS | `react-best-practices/rules/rendering-hydration-no-flicker.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/rendering-hydration-suppress-warning.md` | COPY_AS_IS | `react-best-practices/rules/rendering-hydration-suppress-warning.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/rendering-resource-hints.md` | COPY_AS_IS | `react-best-practices/rules/rendering-resource-hints.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/rendering-script-defer-async.md` | COPY_AS_IS | `react-best-practices/rules/rendering-script-defer-async.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/rendering-svg-precision.md` | COPY_AS_IS | `react-best-practices/rules/rendering-svg-precision.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/rendering-usetransition-loading.md` | COPY_AS_IS | `react-best-practices/rules/rendering-usetransition-loading.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/rerender-defer-reads.md` | COPY_AS_IS | `react-best-practices/rules/rerender-defer-reads.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/rerender-dependencies.md` | COPY_AS_IS | `react-best-practices/rules/rerender-dependencies.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/rerender-derived-state-no-effect.md` | COPY_AS_IS | `react-best-practices/rules/rerender-derived-state-no-effect.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/rerender-derived-state.md` | COPY_AS_IS | `react-best-practices/rules/rerender-derived-state.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/rerender-functional-setstate.md` | COPY_AS_IS | `react-best-practices/rules/rerender-functional-setstate.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/rerender-lazy-state-init.md` | COPY_AS_IS | `react-best-practices/rules/rerender-lazy-state-init.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/rerender-memo-with-default-value.md` | COPY_AS_IS | `react-best-practices/rules/rerender-memo-with-default-value.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/rerender-memo.md` | COPY_AS_IS | `react-best-practices/rules/rerender-memo.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/rerender-move-effect-to-event.md` | COPY_AS_IS | `react-best-practices/rules/rerender-move-effect-to-event.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/rerender-no-inline-components.md` | COPY_AS_IS | `react-best-practices/rules/rerender-no-inline-components.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/rerender-simple-expression-in-memo.md` | COPY_AS_IS | `react-best-practices/rules/rerender-simple-expression-in-memo.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/rerender-split-combined-hooks.md` | COPY_AS_IS | `react-best-practices/rules/rerender-split-combined-hooks.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/rerender-transitions.md` | COPY_AS_IS | `react-best-practices/rules/rerender-transitions.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/rerender-use-deferred-value.md` | COPY_AS_IS | `react-best-practices/rules/rerender-use-deferred-value.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/rerender-use-ref-transient-values.md` | COPY_AS_IS | `react-best-practices/rules/rerender-use-ref-transient-values.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/server-after-nonblocking.md` | COPY_AS_IS | `react-best-practices/rules/server-after-nonblocking.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/server-auth-actions.md` | COPY_AS_IS | `react-best-practices/rules/server-auth-actions.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/server-cache-lru.md` | COPY_AS_IS | `react-best-practices/rules/server-cache-lru.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/server-cache-react.md` | COPY_AS_IS | `react-best-practices/rules/server-cache-react.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/server-dedup-props.md` | COPY_AS_IS | `react-best-practices/rules/server-dedup-props.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/server-hoist-static-io.md` | COPY_AS_IS | `react-best-practices/rules/server-hoist-static-io.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/server-no-shared-module-state.md` | COPY_AS_IS | `react-best-practices/rules/server-no-shared-module-state.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/server-parallel-fetching.md` | COPY_AS_IS | `react-best-practices/rules/server-parallel-fetching.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/server-parallel-nested-fetching.md` | COPY_AS_IS | `react-best-practices/rules/server-parallel-nested-fetching.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/rules/server-serialization.md` | COPY_AS_IS | `react-best-practices/rules/server-serialization.md` | rules-subtree SHA `0af4bf7c…` verified |
| vercel-labs/agent-skills | `skills/react-best-practices/README.md` | REFERENCE_ONLY | — | history/marketing stays upstream; SKILL.md is the entrypoint |
| vercel-labs/agent-skills | `skills/deploy-to-vercel/` + `.zip` | REJECT | — | deploy-vendor-specific; out of intake scope |
| vercel-labs/agent-skills | `skills/react-native-skills/` | REJECT | — | native-platform-specific; out of intake scope |
| vercel-labs/agent-skills | `skills/react-view-transitions/` + `.zip` | REJECT | — | narrow API surface: no bounded gap beyond the animation router set |
| vercel-labs/agent-skills | `skills/vercel-cli-with-tokens/` + `.zip` | REJECT | — | vendor-CLI-specific; out of intake scope |
| vercel-labs/agent-skills | `skills/vercel-optimize/` | REJECT | — | vendor-platform-specific; out of intake scope |
| vercel-labs/agent-skills | `skills/web-design-guidelines/` + `.zip` | REJECT | — | overlaps the curated pack (frontend-design + baseline-ui + frontend-code-review) without a recheck basis for snapshotting a living checklist |
| vercel-labs/agent-skills | `skills/writing-guidelines/` | REJECT | — | prose-writing, not frontend capability; out of scope |
| vercel-labs/agent-skills | `skills/react-best-practices.zip` | REJECT | — | redundant with the unpacked vendored directory |
| vercel-labs/agent-skills | `AGENTS.md`, `CLAUDE.md`, `README.md`, `package.json`, `package-lock.json`, `skills.sh.json`, `scripts/`, `packages/`, `.github/` | REFERENCE_ONLY | — | repo scaffolding; reviewed at listing level, nothing transferable |

### 5.2 PracticalSwan/agent-skills (RA-EXT-083)

Reviewed surface: the `frontend-design/` subtree in full. The rest of the
monorepo (dozens of non-frontend skills) is out of scope: not reviewed,
not adopted, no claim made about it.

| UPSTREAM_REPO | UPSTREAM_PATH | VERDICT | P2P_TARGET | RATIONALE |
| --- | --- | --- | --- | --- |
| PracticalSwan/agent-skills | `frontend-design/SKILL.md` | COPY_AS_IS | `frontend-design/upstream-frontend-design-v2.md` | renamed on landing (wrapper keeps `SKILL.md`); blob `f78cdbd7…` verified bit-identical |
| PracticalSwan/agent-skills | `frontend-design/references/accessibility-checklist.md` | COPY_AS_IS | `frontend-design/references/accessibility-checklist.md` | blob `07eb3892…` verified |
| PracticalSwan/agent-skills | `frontend-design/scripts/contrast-checker.py` | COPY_AS_IS | `frontend-design/scripts/contrast-checker.py` | blob `8ca58130…` verified + smoke-tested 12.92:1 AAA |
| PracticalSwan/agent-skills | `frontend-design/LICENSE.txt` | COPY_AS_IS | `frontend-design/LICENSE.txt` | blob `ccb922cc…` verified (MIT) |
| PracticalSwan/agent-skills | `frontend-design/LICENSE-APACHE-2.0.txt` | COPY_AS_IS | `frontend-design/LICENSE-APACHE-2.0.txt` | blob `b20752a1…` verified |
| PracticalSwan/agent-skills | `frontend-design/LICENSE-GITHUB-MIT.txt` | COPY_AS_IS | `frontend-design/LICENSE-GITHUB-MIT.txt` | blob `28a50fa2…` verified |
| PracticalSwan/agent-skills | `frontend-design/THIRD_PARTY_NOTICES.md` | COPY_AS_IS | `frontend-design/THIRD_PARTY_NOTICES.md` | blob `39394373…` verified |
| PracticalSwan/agent-skills | `frontend-design/CHANGELOG.md` | REFERENCE_ONLY | — | version history stays upstream |
| PracticalSwan/agent-skills | `frontend-design/agents/openai.yaml` | REJECT | — | provider-specific binding; P2P core is provider-neutral |

### 5.3 DNM03/frontend-code-review (RA-EXT-084)

| UPSTREAM_REPO | UPSTREAM_PATH | VERDICT | P2P_TARGET | RATIONALE |
| --- | --- | --- | --- | --- |
| DNM03/frontend-code-review | `skills/frontend-code-review/SKILL.md` | COPY_AS_IS | `frontend-code-review/SKILL.md` | blob `147da06a…` verified |
| DNM03/frontend-code-review | `skills/frontend-code-review/references/checklist.md` | COPY_AS_IS | `frontend-code-review/references/checklist.md` | references-subtree SHA `efe911e5…` verified |
| DNM03/frontend-code-review | `skills/frontend-code-review/references/data-fetching.md` | COPY_AS_IS | `frontend-code-review/references/data-fetching.md` | references-subtree SHA verified |
| DNM03/frontend-code-review | `skills/frontend-code-review/references/frontend-security.md` | COPY_AS_IS | `frontend-code-review/references/frontend-security.md` | references-subtree SHA verified |
| DNM03/frontend-code-review | `skills/frontend-code-review/references/i18n.md` | COPY_AS_IS | `frontend-code-review/references/i18n.md` | references-subtree SHA verified |
| DNM03/frontend-code-review | `skills/frontend-code-review/references/nextjs-app-router.md` | COPY_AS_IS | `frontend-code-review/references/nextjs-app-router.md` | references-subtree SHA verified |
| DNM03/frontend-code-review | `skills/frontend-code-review/references/output-format.md` | COPY_AS_IS | `frontend-code-review/references/output-format.md` | blob `aea4b5a1…` + subtree verified |
| DNM03/frontend-code-review | `skills/frontend-code-review/references/performance-seo.md` | COPY_AS_IS | `frontend-code-review/references/performance-seo.md` | references-subtree SHA verified |
| DNM03/frontend-code-review | `skills/frontend-code-review/references/react.md` | COPY_AS_IS | `frontend-code-review/references/react.md` | references-subtree SHA verified |
| DNM03/frontend-code-review | `skills/frontend-code-review/references/sources.md` | COPY_AS_IS | `frontend-code-review/references/sources.md` | references-subtree SHA verified |
| DNM03/frontend-code-review | `skills/frontend-code-review/references/typescript.md` | COPY_AS_IS | `frontend-code-review/references/typescript.md` | references-subtree SHA verified |
| DNM03/frontend-code-review | `skills/frontend-code-review/references/ui-ux-accessibility.md` | COPY_AS_IS | `frontend-code-review/references/ui-ux-accessibility.md` | references-subtree SHA verified |
| DNM03/frontend-code-review | `skills/frontend-code-review/examples/good-review.md` | COPY_AS_IS | `frontend-code-review/examples/good-review.md` | blob `fe3cd5a2…` + examples-subtree `becd2952…` verified |
| DNM03/frontend-code-review | `skills/frontend-code-review/examples/bad-review.md` | COPY_AS_IS | `frontend-code-review/examples/bad-review.md` | blob `dc677caa…` + subtree verified |
| DNM03/frontend-code-review | `skills/frontend-code-review/agents/openai.yaml` | REJECT | — | provider-specific binding; P2P core is provider-neutral |
| DNM03/frontend-code-review | `evals/` (harness: rubric, 15 cases, answer keys, results) | REJECT | — | the upstream project's own eval harness stays upstream; P2P verifies with its own focused tests |
| DNM03/frontend-code-review | `README.md`, `LICENSE`, `.gitignore` | REFERENCE_ONLY | — | rights reproduced in `UPSTREAM_NOTICES.md` instead of vendoring the root files |
### 5.4 ibelick/ui-skills (RA-EXT-085)

| UPSTREAM_REPO | UPSTREAM_PATH | VERDICT | P2P_TARGET | RATIONALE |
| --- | --- | --- | --- | --- |
| ibelick/ui-skills | `skills/baseline-ui/SKILL.md` | COPY_AS_IS | `baseline-ui/SKILL.md` | single-file unit; blob `98477ee0…` verified |
| ibelick/ui-skills | `skills/create-design-md/` | REJECT | — | overlaps the frontend-design workflow without a bounded gap |
| ibelick/ui-skills | `skills/fixing-accessibility/` | REJECT | — | overlaps frontend-code-review + a11y checklist without a bounded gap |
| ibelick/ui-skills | `skills/fixing-metadata/` | REJECT | — | overlaps review references (SEO/metadata) without a bounded gap |
| ibelick/ui-skills | `skills/fixing-motion-performance/` | REJECT | — | overlaps the animation router set without a bounded gap |
| ibelick/ui-skills | `skills/improve-ui/` | REJECT | — | overlaps the curated pack without a bounded gap |
| ibelick/ui-skills | `skills/ui-skills-root/` | REJECT | — | meta-router; a competing-router smell — P2P keeps its own hub |
| ibelick/ui-skills | `bin/` (installer/CLI surface) | REJECT | — | no second installer; the existing skill/package/install machinery delivers |
| ibelick/ui-skills | `src/`, `public/`, `scripts/`, `tests/`, `astro.config.mjs`, `wrangler.jsonc`, `tsconfig.json`, `package.json`, `package-lock.json` | REJECT | — | marketing-site product surfaces and toolchain, not guidance |
| ibelick/ui-skills | `AGENTS.md`, `DESIGN.md`, `README.md`, `LICENSE`, dotfiles, `.github/`, `.vscode/` | REFERENCE_ONLY | — | repo scaffolding; rights reproduced in `UPSTREAM_NOTICES.md` |

### 5.5 millionco/react-doctor (RA-EXT-086)

Nothing vendored. The adapter is P2P-authored.

| UPSTREAM_REPO | UPSTREAM_PATH | VERDICT | P2P_TARGET | RATIONALE |
| --- | --- | --- | --- | --- |
| millionco/react-doctor | CLI `react-doctor@0.9.14` (npm) at commit `499a020…` | EXTERNAL_TOOL | `react-doctor/SKILL.md` (adapter) | pinned invocation only; tool is used, never vendored/wrapped/daemonized |
| millionco/react-doctor | `JsonReport` schema v3 (`diagnostics[]`, `projects[].complete`, `analyzedFileCount`, `summary.score`, `mode`) | EXTERNAL_TOOL | `react-doctor/SKILL.md` (reading contract) | adapter branches on `schemaVersion` and scopes every claim to mode + coverage |
| millionco/react-doctor | `react-doctor@latest` | REJECT | — | moving target; the pin is the only reproducible invocation |
| millionco/react-doctor | remote triage playbook (`https://www.react.doctor/prompts/…`) | REJECT | — | moving remote prompt dependency; URL recorded here as evidence, absent from the skill |
| millionco/react-doctor | remote score API (`score: null` offline) | EXTERNAL_TOOL | `react-doctor/SKILL.md` (`SCORE_UNAVAILABLE`) | null is recorded with reason, never treated as pass or fail |
| millionco/react-doctor | agent-use license notice | REFERENCE_ONLY | `react-doctor/SKILL.md` (disclosure section) | observed runtime behavior; disclosure, not an adoption filter |

### 5.6 pbakaus/impeccable (RA-EXT-087)

Nothing copied. Reviewed: root layout, `PRODUCT.md`, `skill/` layout.

| UPSTREAM_REPO | UPSTREAM_PATH | VERDICT | P2P_TARGET | RATIONALE |
| --- | --- | --- | --- | --- |
| pbakaus/impeccable | `skill/SKILL.src.md`, `skill/agents/`, `skill/reference/`, `skill/scripts/` (23 design commands) | DEFER | — | a second skill system is a competing-router smell; overlaps frontend-code-review + p2p-uiux without bounded-gap proof |
| pbakaus/impeccable | `cli/`, `extension/`, `browser-bundle/` (deterministic no-LLM detectors) | DEFER | — | selected future direction (deterministic UI anti-pattern detection); needs bounded-gap proof + Owner detector-tooling decision |
| pbakaus/impeccable | `PRODUCT.md`, `DESIGN.md`, `docs/` | REFERENCE_ONLY | — | product/design reference for the deferred direction |
| pbakaus/impeccable | per-harness root folders, `plugin/`, `cursor-plugin/`, `vscode/` (generated distributions) | REJECT | — | generated artifacts, not sources |
| pbakaus/impeccable | `crates/`, `site/`, `functions/`, `demos/`, `tests/`, `scripts/`, toolchain files | REJECT | — | product implementation; out of intake scope |

Re-entry conditions: (a) a bounded gap is proven against
frontend-code-review plus the p2p-uiux runtime evidence contract; (b) the
Owner decides the detector-tooling direction.

### 5.7 microsoft/skills (RA-EXT-088)

Nothing copied. Reviewed: root layout and `Agents.md` (principles through
the skill catalog; MCP-server sections out of scope and not reviewed).

| UPSTREAM_REPO | UPSTREAM_PATH | VERDICT | P2P_TARGET | RATIONALE |
| --- | --- | --- | --- | --- |
| microsoft/skills | `Agents.md` (§§ principles, skill packaging, catalog) | REFERENCE_ONLY | — | methodology reference: SKILL.md frontmatter packaging, progressive loading ("context rot" warning), surgical-change discipline |
| microsoft/skills | `tests/scenarios/` (acceptance-criteria + scenarios.yaml harness) | REFERENCE_ONLY | — | scenario-harness convention; consistent with this intake's focused-test pattern |
| microsoft/skills | `.github/skills/` (133 Azure service skills) | REJECT | — | Azure-service-specific; no frontend guidance in scope |
| microsoft/skills | npx installer, `.vscode/mcp.json`, `hooks/`, `.claude-plugin/`, `.opencode/` | REJECT | — | second installer/daemon/config-plane smells; P2P machinery already exists |
| microsoft/skills | `docs/`, `docs-site/`, `README.md`, `LICENSE`, `SECURITY.md`, `context7.json` | REFERENCE_ONLY | — | repo documentation; nothing transferable |
### 5.8 emilkowalski/skills (RA-EXT-089)

| UPSTREAM_REPO | UPSTREAM_PATH | VERDICT | P2P_TARGET | RATIONALE |
| --- | --- | --- | --- | --- |
| emilkowalski/skills | `skills/find-animation-opportunities/SKILL.md` | COPY_AS_IS | `UI-animation-design/find-animation-opportunities/SKILL.md` | blob `d3b030fb…` verified; router row added to the P2P router |
| emilkowalski/skills | `skills/animate/`, `skills/animate-expo/` | REFERENCE_ONLY | — | no bounded gap beyond the existing animation router set in this intake |
| emilkowalski/skills | `skills/ask-sonner/` | REFERENCE_ONLY | — | product-specific (toast library); out of scope |
| emilkowalski/skills | `skills/mobile-native/` | REFERENCE_ONLY | — | platform-specific; out of scope |
| emilkowalski/skills | `skills/pick-ui-library/`, `skills/prototype/` | REFERENCE_ONLY | — | no bounded gap beyond hub routing + frontend-design in this intake |
| emilkowalski/skills | `skills/write-swift/` | REFERENCE_ONLY | — | platform-specific; out of scope |
| emilkowalski/skills | `performance-cheatsheet.md` | REFERENCE_ONLY | — | overlaps react-best-practices without a bounded gap |
| emilkowalski/skills | `skills/animation-vocabulary/`, `skills/apple-design/`, `skills/emil-design-eng/`, `skills/improve-animations/`, `skills/review-animations/` | REFERENCE_ONLY | — | already present in `UI-animation-design` from earlier work; out of this intake's change set |
| emilkowalski/skills | `README.md`, `LICENSE`, dotfiles | REFERENCE_ONLY | — | repo documentation; rights reproduced in `UPSTREAM_NOTICES.md` |

### 5.9 vercel-labs/design-systems-to-agent-skills (RA-EXT-090)

Nothing copied. Reviewed: full `README.md` plus root layout.

| UPSTREAM_REPO | UPSTREAM_PATH | VERDICT | P2P_TARGET | RATIONALE |
| --- | --- | --- | --- | --- |
| vercel-labs/design-systems-to-agent-skills | `README.md` (6-stage pipeline: Interview → Extract → PRD → Generate → Assets → Verify) | REFERENCE_ONLY | — | methodology reference: verified-facts extraction, closed-PRD discipline, session-isolated stages, mechanical verify script |
| vercel-labs/design-systems-to-agent-skills | `commands/`, `docs/`, `example/`, `scripts/` | REFERENCE_ONLY | — | layout-reviewed; running the pipeline is project work, not P2P core content — no design-system source exists in this intake |
| vercel-labs/design-systems-to-agent-skills | `LICENSE` | REFERENCE_ONLY | — | MIT; nothing copied so no notices file required |

### 5.10 TanStack/table (RA-EXT-091)

Nothing copied. Reviewed: root layout and `AGENTS.md` (dependency-pin
notes — not transferable).

| UPSTREAM_REPO | UPSTREAM_PATH | VERDICT | P2P_TARGET | RATIONALE |
| --- | --- | --- | --- | --- |
| TanStack/table | `AGENTS.md`, root layout, `README.md`, `LICENSE` | REFERENCE_ONLY | — | provenance of the no-gap decision; a component library is not guidance |
| TanStack/table | `packages/` (library source) | REJECT | — | library code is not vendored into P2P core, ever |
| TanStack/table | `docs/`, `examples/` | REJECT | — | vendoring library docs would be a stale clone without a recheck mechanism |
| TanStack/table | `perf-*.md`, `_artifacts/`, toolchain files | REJECT | — | working notes and toolchain; nothing transferable |

Decision: no bounded P2P gap. P2P core ships no data-grid guidance by
design — the frontend-development hub routes project stacks to
project-installed docs and never imposes a generic stack — and
review-time table concerns are already covered generically by the
frontend-code-review references.

### 5.11 Related non-intake source (no ledger record)

| UPSTREAM_REPO | UPSTREAM_PATH | VERDICT | P2P_TARGET | RATIONALE |
| --- | --- | --- | --- | --- |
| vercel-labs/web-interface-guidelines | `command.md` on `main` (~100 a11y/forms/motion/typography/i18n rules, terse `file:line` output contract) | REFERENCE_ONLY | — | fetched and read in full; rules overlap the curated pack (baseline-ui + PracticalSwan checklist + frontend-code-review) with no residual gap, and snapshotting a living `main` checklist adds a stale-clone burden without a recheck mechanism — so it stays a cited reference, never a moving runtime dependency |

## 6. Verification evidence

- Blob SHA matches (local `git hash-object` vs upstream API blob):
  `d07025bf…` + `558bf9aa…` + `3470b744…` (composition entrypoints),
  all 10 composition rule blobs, `237988de…` + `4e340a50…` + `3bec38b1…`
  (react-best-practices entrypoints), `f78cdbd7…` (PracticalSwan SKILL.md),
  `07eb3892…` (checklist), `8ca58130…` (contrast checker), all four
  PracticalSwan rights-file blobs, `147da06a…` (DNM03 SKILL.md),
  `aea4b5a1…` (output-format), `fe3cd5a2…` + `dc677caa…` (examples),
  `98477ee0…` (baseline-ui), `d3b030fb…` (find-animation-opportunities).
- Subtree SHA matches (disposable-index recomputation vs upstream tree):
  `react-best-practices/rules/` = `0af4bf7cbb25560321d127d270fd787875b8ea89`,
  `composition-patterns/rules/` = `30a98d7c7225fb0cc3f4b9fcc78381aa60c2498e`,
  `frontend-code-review/references/` = `efe911e5db549d2564680c12edfc6bd879c5ef2d`,
  `frontend-code-review/examples/` = `becd29521ea88c3ce1076d24e150a590a97ac198`.
- `contrast-checker.py` smoke: `12.92:1`, AAA pass on the sample pair.
- React Doctor probes at `0.9.14`: 906 rule entries; `schemaVersion: 3`;
  offline run yields `score: null` ("Score API unreachable"); full lint
  unverifiable in-sandbox (oxlint worker SIGABRT/OOM) — environment
  limitation, adapter hardened accordingly.
- Synthetic-project install proof (in-test, §7 D/E): `copy_selected` stages
  the release, the install contract copies every packaged
  `.agents/skills/*` into a synthetic project, and a repo-scoped executor
  (only the synthetic tree readable) discovers all 7 pack entrypoints with
  valid frontmatter; `doctor.check_skills` passes on the stage.
- Mirror discipline: canonical vs both mirrors byte-compared file by file
  in-test; manifests assert per-file SHA-256 equality plus the documented
  aggregate scheme for all 8 touched skills.

## 7. Test mapping (§11 A–K)

| §11 | Concern | Test class |
| --- | --- | --- |
| A | Hub is thin; project stack not universalized | `FrontendDevelopmentHubTests` |
| B | Vendored units complete (incl. animation opportunity finder) | `VendoredUnitTests` |
| C | Projection/mirror/manifest consistency | `ProjectionMirrorTests` |
| D | Release ships the pack; synthetic install receives nested refs | `PackageInstallProofTests` |
| E | Repo-scoped discovery; doctor validates packaged skills | `PackageInstallProofTests` |
| F | No parallel router/registry/package-manager/daemon | `NoParallelArchitectureTests` |
| G | No moving remote-`main` prompt dependency | `NoMovingRemotePromptTests` |
| H | React Doctor pinned, optional, honestly scoped | `ReactDoctorAdapterTests` |
| I | Backend-only routing stays clean; p2p-uiux untouched | `RoutingBoundaryTests` |
| J | Progressive disclosure markers | `RoutingBoundaryTests` |
| K | Ledger batch RA-EXT-082..091 durable + report matrix | `ResearchLedgerBatchTests` |
| §5A | BOLD-universal fix in frontend-design wrapper | `FrontendDesignWrapperTests` |

The suite is read-only except for disposable fixtures under `.tmp/` and
never executes external tools (no npx, no curl, no network).

## 8. Change-set surfaces and non-goals (kept)

Allowed surfaces (asserted by `NoParallelArchitectureTests` against both
the working tree and the branch diff): the 8 touched skill directories
across canonical + 2 mirrors (incl. the 3 skill manifests), `AGENTS.md`,
`CLAUDE.md`, `scripts/package_release.py`, `scripts/doctor.py`,
`governance/research-adoption-ledger.json`,
`docs/RESEARCH-ADOPTION-LEDGER.md`, this report, and the focused test.
No new `.py` module outside the two touched scripts and the test; no new
capability module; no router/registry/daemon/sync/installer smell in any
changed path. Non-goals kept: no real-project rollout, no release,
promotion, or deployment — this task ends at the PR.

## 9. Residual risks

- Vendored units drift from upstream by design (pins, not subscriptions).
  Re-intake is a deliberate future task with fresh pins and fresh blob
  verification — never silent syncing.
- Vercel units carry no upstream LICENSE file; the MIT grant lives in
  skill frontmatter. If upstream ever adds conflicting rights, the next
  intake must reconcile before copying.
- React Doctor's Modified-MIT agent-use notice may require written
  permission in some deployment contexts; the adapter records the notice
  and the applicability gate keeps every invocation deliberate and local.
