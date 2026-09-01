# Impeccable design-quality capability boundary (P2P-IMPECCABLE-01)

`BACKLOG_ID=IMPECCABLE_01` · issue #44 · candidate, not promoted.

## What was integrated

| | |
|---|---|
| Upstream | `https://github.com/pbakaus/impeccable` |
| Commit | `94b7f34f6e27b95bc32d8284a671601ed6ac1b2a` |
| Tree | `604c0d2d5f0c1c6bd1f3bd1cbc06bef637e24139` |
| Version at pin | `3.6.1` (`package.json`) |
| Root license | Apache-2.0 (`LICENSE`), upstream `NOTICE.md` retained |
| Upstream file count at pin | 3542 |
| Vendored files | 23 (`.p2p/vendor/skill/pbakaus-impeccable-94b7f34`) |

## P2P capability

Registry record `ui.design_quality` in `.p2p/system/p2p_capabilities/capabilities.json`
(`TYPE=SKILL`, `STATUS=DISCOVERED`, `LOCAL_VENDOR_SNAPSHOT`, `load_mode=ON_DEMAND`).

Projected actions — a strict subset of the 23 discovered upstream commands:

| Action | Kind | Backed by |
|---|---|---|
| `ui.design_quality.critique` | advisory | `reference/critique.md` |
| `ui.design_quality.polish` | advisory | `reference/polish.md` |
| `ui.design_quality.bolder` | advisory | `reference/bolder.md` |
| `ui.design_quality.quieter` | advisory | `reference/quieter.md` |
| `ui.design_quality.layout` | advisory | `reference/layout.md` |
| `ui.design_quality.typeset` | advisory | `reference/typeset.md` |
| `ui.design_quality.deterministic_check` | executable | pinned offline detector engines |

Not projected: `init`, `onboard`, `document`, `extract`, `live`, `audit`, `adapt`,
`animate`, `clarify`, `colorize`, `craft`, `delight`, `distill`, `harden`,
`optimize`, `overdrive`, `shape` — each either duplicates an existing P2P surface
(`ui.design`, `ui.design_system`, `ui.frontend`, threejs-qa visual evidence,
governance/roadmap records) or requires install / hooks / browser-live session
state that this workstream refuses.

## Machinery reused (no new infrastructure)

- capability registry: `.p2p/system/p2p_capabilities/capabilities.json`
- vendor-skill discovery/load/readiness: `p2p_capabilities.vendor_skill`
- single router: `p2p_capabilities.routing` via `p2p_uiux/router.py`
- capability catalog + project-profile routing: `docs/p2p-development/capability-catalog/ui-game-threejs/*`
- provenance convention: `.p2p/vendor/provenance/*.json`
- research adoption ledger: `governance/research-adoption-ledger.json` (`RA-EXT-069`)

No second router, design system, orchestrator, database, daemon, scheduler or
global skill loader was created.

## Authority

```
UI/game implementation (P2P)
  -> ui.design_quality critique / check / polish  (advice + findings)
  -> deterministic design check                   (findings only)
  -> Supervisor
```

`REVIEW_AUTHORITY != IMPLEMENTATION_AUTHORITY`. P2P keeps routing, project scope,
execution permission, evidence, Owner Gates and release/promotion. The capability
never edits project source; `deterministic_check` reports and returns
`source_mutation: false`.

## Staged law

`AVAILABLE != LOADED != AUTHORIZED != EXECUTED`

- `availability()` — registry metadata only, `content_loaded: false`
- `load_vendor_skill()` — reads the entrypoint plus explicitly named references only
- `authorize()` — requires a named grant and re-verifies the snapshot tree hash
- `deterministic_check()` — refuses without that grant, refuses advisory actions,
  refuses targets outside the repository, and requires an explicit target list
  (there is no repository-wide default scan)

No profile receives `ui.design_quality` as a required capability; it is optional in
all five profiles and excluded from none.

## Deterministic detector

Host runner: `.p2p/system/p2p_capabilities/impeccable_detector_runner.mjs` (P2P code)
invoking only the two offline engines of the vendored detector. Node builtins only —
no model, no network, no browser, no install.

Engine modes are always disclosed:

- `REGEX_DEGRADED` — zero-dependency default; the durable, asserted baseline.
- `STATIC_HTML_FULL` — only when the optional upstream parser modules
  (`htmlparser2`, `css-select`, `css-tree`, `domutils`) happen to be resolvable.
  P2P does not install or vendor them. Reported, never assumed.

Bounded fixture `tests/fixtures/p2p-impeccable-design-quality/` (synthetic,
P2P-owned; no Game Truyện source touched):

| Engine mode | BEFORE | AFTER (minimum correction) |
|---|---|---|
| `REGEX_DEGRADED` | 6 findings / 6 categories | 0 |
| `STATIC_HTML_FULL` | 14 findings / 13 categories | 0 |

Baseline categories asserted in every mode: `gradient-text` (generic gradient),
`side-tab` (AI accent-stripe card pattern), `dark-glow` (decorative glow),
`monotonous-spacing` (spacing rhythm), `flat-type-hierarchy` and `overused-font`
(typography/readability). The enhanced mode additionally observed `nested-cards`,
`tiny-text`, `undersized-ui-text`, `tight-leading`, `low-contrast`, `gray-on-color`
and `ai-color-palette`.

Evidence: `governance/evidence/p2p-impeccable-01-deterministic-check.json`
(includes a repeat run per mode; findings byte-identical across repeats).

## Excluded upstream surface

`cli/`, `extension/`, `demos/`, `plugin/` hooks and the `.claude`/`.cursor`/`.gemini`/…
auto-activation wiring, `scripts/live-*`, `detector/browser/*`,
`detect-antipatterns-browser.js`, the puppeteer/browser/visual engines,
`tests/`, `bun.lock`, `skills-lock.json`, `.github/`, and every reference file not
bound to a projected action. No runtime, cache or live-session artifacts were imported.
