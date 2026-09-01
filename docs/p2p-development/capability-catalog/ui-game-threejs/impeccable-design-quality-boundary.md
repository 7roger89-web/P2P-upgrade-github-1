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
- `authorize()` — **mints** a grant on the existing portable execution contract
  (`p2p_capabilities.host_executor.PortableExecutionRequest`) and records its
  canonical fingerprint in this process' issuance set
- `deterministic_check()` — fails closed unless the grant was minted by that
  authority surface and every binding still validates; refuses advisory actions,
  refuses targets outside the repository, and requires an explicit target list
  (there is no repository-wide default scan)

### Authorization boundary (Control-Tower repair)

`AUTHORIZED` is neither caller-asserted data nor a self-minted binding. The law is:

```
AUTHORIZATION = existing verified P2P permission        (authority)
              + PortableExecutionRequest identity/binding (binding)
```

**Permission authority (existing surface, reused, not rebuilt).** The permission
decision is read from the durable task control plane: the task store at
`.p2p/state/task-state.json` and the existing C11 preflight evaluator
`p2p_capabilities.task_state.evaluate_task_preflight`. Before any executable grant
is minted, `authorize()` requires:

| Requirement | Source |
|---|---|
| an active task (`READY` / `ACTIVE`) | durable `.p2p/state/task-state.json` |
| the task declares `ui.design_quality` | `TaskRecord.required_capabilities` |
| the task declares the `READ` permission need | `TaskRecord.permission_needs` |
| its persisted preflight is `PASS` | `TaskRecord.last_preflight` (`p2p-task-preflight/1`) |
| the Owner-approved permission record | persisted `last_preflight.permission_state` |
| the gate still passes **now** | `evaluate_task_preflight()` re-run with live vendor readiness |

`granted_by` is a provenance **label only**. No value of `granted_by` — and no
caller-supplied permission input of any kind — can produce an executable grant:
without a durable, Owner-approved, PASS-preflight task the call fails closed with
`PERMISSION_AUTHORITY_STATE_MISSING` (or a more specific `PERMISSION_*` code).

**Binding (identity only).** Only after permission is verified is a
`PortableExecutionRequest` minted, bound to:

| Binding | Value |
|---|---|
| durable task identity | `task_id` / `goal_id` taken from the task store |
| verified permission decision | `context_refs = ("task-preflight:<task_id>:<sha256>",)` |
| capability identity | `required_capabilities = ("ui.design_quality",)` |
| exact executable action | `purpose = "ui.design_quality.deterministic_check"` |
| registry + manifest identity | `project_binding = registry:<registry_hash>:capability:<manifest.identity_hash>` |
| pinned vendor snapshot identity | `candidate_binding = vendor-snapshot:ui.design_quality:<snapshot_sha256>` |
| permission shape | `granted_permissions = ("READ",)`, `mutation_requested = false` |

The binding contract is never the authority; it proves *which* verified permission
and *which* pinned artifact an execution refers to.

**Two gates, the last one truly last.** `deterministic_check()` verifies the grant
early (before target resolution), and then again — manifest re-resolved, vendor root
re-resolved, `snapshot_tree_sha256` recomputed and matched against the canonical
declared hash, `validate_binding()` required to return `BOUND`, and the P2P
permission authority re-read and re-evaluated — **immediately before**
`subprocess.run`. Between that final verification and the launch there is no
filesystem work, no preflight work and no target work: only the argv list is
assembled. A vendor mutation or a permission revocation that lands after the early
gate is still caught, and **no subprocess is started**.

Proven fail-closed, with `subprocess.run` asserted un-called:

- forged mapping / self-consistent forgery → `AUTHORIZATION_*`
- caller-minted binding, no P2P permission → `PERMISSION_AUTHORITY_STATE_MISSING`
- arbitrary `granted_by` → no grant at all
- permission denied / rejected / unapproved → `PERMISSION_PREFLIGHT_*`
- permission binding swapped inside the request → `PERMISSION_AUTHORITY_DRIFT`
- permission revoked between authorization and launch → fail closed at the final gate
- vendor drift between preflight and launch → `VENDOR_SNAPSHOT_HASH_MISMATCH` / `VENDOR_SNAPSHOT_DRIFT`

No second permission system, authority plane, database, daemon, scheduler, token
service or cryptographic framework was introduced. The authority is the existing
task-state preflight; the binding is the existing portable execution contract; the
issuance set remains in-memory process state on top of both.

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
includes the verified permission authority (surface, task id, preflight status),
the permission binding, the minted authorization fingerprint and its bindings.
(includes a repeat run per mode; findings byte-identical across repeats).

## Excluded upstream surface

`cli/`, `extension/`, `demos/`, `plugin/` hooks and the `.claude`/`.cursor`/`.gemini`/…
auto-activation wiring, `scripts/live-*`, `detector/browser/*`,
`detect-antipatterns-browser.js`, the puppeteer/browser/visual engines,
`tests/`, `bun.lock`, `skills-lock.json`, `.github/`, and every reference file not
bound to a projected action. No runtime, cache or live-session artifacts were imported.
