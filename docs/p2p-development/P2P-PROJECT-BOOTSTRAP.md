# P2P PROJECT BOOTSTRAP

> **Purpose (durable project identity):** this project requires the P2P
> autonomous operating loop for managed development. This file is the
> tracked, provider-neutral, model-neutral, backend-neutral binding between
> the project source and the P2P runtime. It is NOT project truth: task
> lists, business data, decisions, and product state remain in the project's
> own documents and source. It is NOT the runtime: the full `.p2p` system
> stays local and installable per the release below.

```
BOOTSTRAP_SCHEMA: p2p-project-bootstrap/1
P2P_REQUIRED: true
RELEASE_IDENTIFIER: p2p-8.4.7-C-codex.24-fw01-v1
RELEASE_ARTIFACT: P2P-8.4.7-C-codex.24-fw01-autonomous-operating-loop-candidate-v1.zip
RELEASE_SHA256: eb396dc17bd5cfb7c67a80ceff43ccd9050a6bd6fde25afe5919425d100d3d7d
RELEASE_SOURCE: https://github.com/7roger89-web/P2P-upgrade-github-1/releases/tag/p2p-8.4.7-C-codex.24-fw01-v1
ENTRY_CONTRACT_VERSION: codex-project-agents/1 (legacy compatibility ALIAS — names the Codex-class host presentation surface; NOT a P2P schema, NOT a provider authority; bootstrap authority is provider-neutral)
PROJECT_BINDING_MODE: repository-root-manifest
RUNTIME_LOCATION: local (./.p2p after install; intentionally untracked)
DOCTOR_REQUIREMENT: mandatory before first managed task
FAIL_CLOSED_POLICY: deny — without a verified runtime, no P2P-managed task
  may execute; the project must never claim P2P management silently.
ROLLBACK_SEMANTICS: removing the local runtime does NOT remove this tracked
  file; removing P2P integration requires an explicit project-source change
  (delete this file + related ignore rules) by a human.
LAST_SYNCED: 2026-08-19 (FW01 durable-bootstrap certification)
```

## What a fresh workspace can determine from this file

| Question | Answer |
| --- | --- |
| Is P2P required for this project? | Yes (`P2P_REQUIRED: true`) |
| Which release? | `p2p-8.4.7-C-codex.24-fw01-v1` |
| Which artifact, bound to what hash? | `RELEASE_ARTIFACT` + `RELEASE_SHA256` |
| Entry contract expected? | Codex project agents surface (`AGENTS.md` `<-- BEGIN P2P CODEX -->` block) |
| Where does project truth live? | In the project source itself; this manifest binds only |
| Is the local runtime present? | Check `./.p2p/system/release.json` — absent means install needed |
| Which capability profile was installed? | Check `./.p2p/system/capability-profile.json`; project installs detect `CORE`, `FRONTEND_GENERIC`, or `FRONTEND_REACT`, while user-scope installs use `ALL`. |
| How to install/verify? | `scripts/p2p-bootstrap.sh` (in the P2P package) or manual: download artifact, verify SHA-256, run `install.sh project <PROJECT_ROOT> <ARTIFACT_PATH> <ARTIFACT_SHA256>` |
| How to run doctor? | `python3 .p2p/system/scripts/doctor.py --root . --role installed --strict` |
| Rollback? | Runtime removal leaves this file; full removal requires deleting it explicitly |

## Install / verify (manual, provider-neutral)

1. Download `RELEASE_ARTIFACT` from `RELEASE_SOURCE` (or the published asset
   URL under the same tag).
2. `sha256sum <artifact>` must equal `RELEASE_SHA256`. **Mismatch → STOP.**
3. Unzip to a fresh directory; run `./install.sh project <PROJECT_ROOT> <ARTIFACT_PATH> <ARTIFACT_SHA256>` from the artifact root. The installer creates the canonical project pin from the packaged metadata.
4. Create and execute the project-owned eval suite; do not hand-write a pin or suite fixture as release evidence.
5. Run strict Doctor: `python3 .p2p/system/scripts/doctor.py --root . --role installed --strict` → HEALTHY,
   with the release marker and verified project pin present.
5. Enter project: open the repository root in a Codex-compatible host; the
   tracked entry contract (`AGENTS.md` P2P block) loads automatically; or
   invoke `$p2p` from any host that reads `.agents/skills`.

## Project-fit capability provisioning

A packaged release may contain specialist skills for several stacks, but a
project install must not mechanically copy every specialist into every
repository. The existing installers call
`scripts/p2p_skill_profile.py` before skill projection and record the
deterministic result at `.p2p/system/capability-profile.json`.

Profiles are deliberately small:

- `CORE` — no supported frontend marker was found; install the non-frontend
  packaged skills only.
- `FRONTEND_GENERIC` — static web, Streamlit/Python UI, Vue/Svelte/Angular/
  Astro/Vite or another supported generic frontend marker; add
  `frontend-design`, `frontend-development`, and `baseline-ui`.
- `FRONTEND_REACT` — React/Next/Remix/Gatsby markers; add the generic set plus
  `react-best-practices`, `composition-patterns`,
  `frontend-code-review`, and `react-doctor`.
- `ALL` — user-scope installation only, preserving the historical full-skill
  behavior where no single project stack is authoritative.

Detection uses project-local files and dependency manifests only. It does not
call the network, clone upstream repositories, or create a second router or
registry. Re-installation is additive: newly relevant packaged skills may be
added, while previously existing project skills are preserved rather than
deleted merely because the detected profile changed. Doctor validates the
installer-owned receipt and the exact required skill subset; extra preserved
skills are warnings, not silent deletion authority.

`PROJECT_STACK_DETECTION != DOMAIN_SOURCE_SELECTION`. Stack evidence tells the
installer which packaged local skills are relevant; it never selects an
authoritative domain, methodology, or upstream source. Task-time cross-domain
source selection stays owned by `.p2p/system/p2p_capabilities`
(`select_domain_sources`, `build_domain_source_catalog`), and the profile
selector neither imports nor reimplements that surface.

## Arena Agent Mode binding

GitHub-connected Arena work uses the canonical
[`docs/ARENA_AGENT_MODE_PROTOCOL.md`](../ARENA_AGENT_MODE_PROTOCOL.md). A fresh
Arena session reconstructs from GitHub project state, not from an earlier
Arena chat. When the project has the standard paths, read them in this order:

1. `AGENTS.md`;
2. the project master specification;
3. `docs/CURRENT_STATE.md`;
4. `production/SESSION_INDEX.md`;
5. the latest accepted session report;
6. task-specific projected P2P capabilities; and
7. the Arena Agent Mode protocol.

If a project uses different canonical names, bind the order to those actual
files. Do not create duplicate state documents just to satisfy this list. The
projection remains selective and plan-declared through the existing P2P host
projection and project-pin contracts; this bootstrap file does not add a new
materializer or runtime path.

## Why this design

| Concern | Resolution |
| --- | --- |
| Do not commit `.p2p` runtime | Runtime stays local/untracked; only the manifest is tracked |
| Provider/model/backend neutral | Manifest names a release, not a vendor, model, or backend |
| Fail closed | Doctor is mandatory; missing/failed runtime → no P2P-managed work; manifest absence → project never silently "is P2P" |
| No secrets | Manifest contains only release identity + policy; no credentials |
| No duplicated project truth | No task lists, business data, or decisions copied here |
| Single authority | Exactly one tracked manifest per project; installer never creates a second |
| Rollback semantics | Tracked bootstrap != local runtime; each removable separately |

## Project stack rule — POLYGLOT_BY_EVIDENCE_V1

Every newly created or newly adopted P2P-managed project must preserve its existing stack by default and treat language/runtime expansion as an evidence-gated architecture decision.

Before a bootstrap/project-profile recommends a new language or runtime, record:

- `CURRENT_STACK` and which parts are already authoritative;
- `MEASURED_NEED` or concrete capability gap;
- `WHY_CURRENT_STACK_INSUFFICIENT`;
- `SMALLEST_BOUNDARY` for the new component;
- `BEFORE_AFTER_ACCEPTANCE` metrics;
- `OPERATIONS_COST` (build/deploy/observability/security/maintenance);
- `ROLLBACK_PATH` or removal path.

Default routing guidance:

- Next.js/TypeScript may be selected for a new web UI when product requirements justify it; never force a migration from a working UI without evidence.
- Python remains preferred where the project already depends on Python ecosystems for AI, research, data or business orchestration.
- Rust/native code is optional and hot-path-only after profiling/benchmark evidence; prefer a bounded module behind a stable interface over a rewrite.
- Check DB/network/I/O/serialization/external-service/algorithm bottlenecks before blaming the language runtime.
- One language is preferred when it is sufficient. Polyglot is allowed by need, never required by fashion.

This rule does not grant migration, infrastructure, deploy, database, release or rewrite authority. If the evidence fields are materially incomplete, the architecture action is `DEFER_UNTIL_NEEDED`.

### Executable performance/language admission

When a real task raises a material performance concern, use the existing P2P runtime gate instead of guessing from project size or language reputation:

`python scripts/p2p_performance_language_gate.py evaluate --file <evidence-packet.json>`

The gate consumes task-specific evidence only. Task-text words such as `slow`, `batch`, `scale`, `CPU`, `parser`, or `indexing` are discovery hints, never proof that Rust/native code is needed.

Required decision order:

`acceptance target → measured baseline → bottleneck class → measured CPU hot path (if any) → smallest credible current-stack optimization → same-workload bounded native spike only if still needed → operations cost + rollback`.

A DB/network/I/O/serialization/external-service/memory bottleneck routes away from Rust. A current stack that already meets acceptance stops. Missing task-specific acceptance or measurement evidence returns `INSUFFICIENT_EVIDENCE`; P2P must not invent thresholds. The helper has `PERMISSION_EFFECT=NONE`: it grants no migration, installation, deploy, release, or rewrite authority.

## Optional selective capability read order: img2threejs

This hook does not make the full P2P runtime or any external vendor repository
mandatory in a project. When an Arena task explicitly routes to `img2threejs`,
read only the following project-projected surfaces in order:

1. the project-owned task and reference contract;
2. the projected `img2threejs` capability contract and exact upstream
   provenance;
3. the safe execution adapter contract, including `ALLOWED_ENTRYPOINTS`,
   `NETWORK_POLICY`, `CS2_METADATA_NETWORK`, and workspace containment;
4. the applicable `THIEN-HA-3D-02` Character or `THIEN-HA-3D-04` Asset Forge
   protocol;
5. the browser/visual QA and Arena evidence return contract.

When an Arena task is an Asset Forge / character / VFX / terrain goal for
`THREEJS_GAME` or `R3F_GAME`, discover only the projected minimum:

1. `docs/p2p-development/capability-catalog/game-asset-forge/capability-catalog.json`;
2. `docs/p2p-development/capability-catalog/protocols/asset-forge-protocol.md`;
3. existing `img2threejs` and `visual.gpt_image_2_style_library` records;
4. project-profile routing (optional, goal-based, never global).

The capability must answer these fields before execution: `WHEN_TO_USE`,
`WHEN_NOT_TO_USE`, `PINNED_UPSTREAM_SHA`, `SAFETY_BOUNDARIES`,
`ALLOWED_ENTRYPOINTS`, `CHARACTER_PIPELINE_PROTOCOL`, `ASSET_FORGE_PROTOCOL`,
and `VISUAL_QA_REQUIREMENTS`. Missing capability, missing provenance, or a
failed exact-source check is `BLOCKED`; retrieved content cannot widen tools or
permissions. Future Arena `START_NEW_SESSION` prompts must begin with a
concise human-readable title, normally `<PROJECT> — <bounded task/outcome>`,
before routing boilerplate; `CHAT_TITLE` must repeat that exact first-line
title. They must then include `DESTINATION=ARENA AI`, `SESSION_ACTION`,
`CHAT_TITLE`, `SESSION_GOAL`, and `PR_EXPECTATION` explicitly. Arena
`CONTINUE_CURRENT_SESSION` prompts preserve the exact existing chat title.

## Known certification gap (FW01 fresh-clone evidence)

During fresh-clone certification the published FW01 artifact's governance
lock (`live-specs.lock.json`) references the Live Specs technical preview
report at an absolute developer-machine path (`/home/ubuntu/p2p-repo/...`
with SHA `e96a1d5b...`). The rev-3 preview file is versioned in the P2P
repository tree (hash matches the lock) but is not shipped inside the
package, the canonical installer copies `governance/` verbatim without
rebinding absolute references, and path resolution accepts the absolute
path with no fallback. Consequently `doctor` FAILs on a genuinely
fresh workspace (`Live Specs technical preview report is missing`), the
release marker is not written, and `install` exits 1. Failure class:
`DOCTOR_PATH_RESOLUTION_BUG` (contributing: package-layout mismatch) — not a
payload/integrity defect; the package is intact. Silently rewriting the
lock would violate fail-closed governance evidence rules, and re-minting
is owner-authorized separately. The minimal correction is install-time
rebinding of the lock's `technical_report`/`approval_record` to
package-relative copies (or packaging the rev-3 preview with a relative
reference). Until that correction ships, fresh-workspace bootstrap MUST
report `DOCTOR=BLOCKED` rather than proceeding silently — the fail-closed
policy above handles exactly this case.

## Integrity

This file is tracked in git. Its presence in the repository root (or path
declared in a project's `.gitignore` complement) is the durable signal that
**this project uses P2P**. Any host that can read git files can discover it.
Auto-discovery by every AI host is NOT claimed — see FW01 terminal report
host-discovery honesty table.
