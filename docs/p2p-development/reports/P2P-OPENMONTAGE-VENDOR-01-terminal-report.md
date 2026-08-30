# P2P-OPENMONTAGE-VENDOR-01 — TERMINAL REPORT

**WORKSTREAM:** P2P-OPENMONTAGE-VENDOR-01
**ACTION:** VENDOR_INTAKE_AND_SELECTIVE_CAPABILITY_PROJECTION
**STATUS:** **COMPLETE — VENDOR INTAKE ONLY (no install, no execution, no render)**
**UPSTREAM:** https://github.com/calesthio/OpenMontage
**BRANCH:** `arena/01a05508-p2p-upgrade-github-1`

---

## RETURN BLOCK (authoritative values)

| Field | Value |
|---|---|
| `FRESH_P2P_MAIN_SHA` | `1c9eea39ce6aa0b721d67fa6b7130918357eea4d` |
| `FRESH_P2P_MAIN_TREE` | `0fab3c59bd34094219693ca8ac5e7e80e2200723` |
| `OPENMONTAGE_UPSTREAM_SHA` | `cd9f3c1f03368be87b140af494914b8ee4e3c7a4` |
| `OPENMONTAGE_UPSTREAM_TREE` | `6cd1961d552dd9d2bcfba990b80ac06edfe4b061` |
| `OPENMONTAGE_LICENSE` | `AGPL-3.0` (verified: full AGPLv3 LICENSE text + GitHub API `license.spdx_id = AGPL-3.0`) |
| `VENDOR_CLASSIFICATION` | `REFERENCE_ONLY_EXTERNAL_RUNTIME_VENDOR` — canonical registry mode `PINNED_REFERENCE_ADAPTER`, semantic kind `EXTERNAL_RUNTIME`, dependency mode `EXTERNAL_RUNTIME_NOT_INSTALLED` (all existing P2P vocabulary; no new framework) |
| `LICENSE_BOUNDARY` | `HARD_VENDOR_BOUNDARY_CONCERN` — AGPL-3.0; fail closed to reference-only; no upstream source or license text copied into P2P; commercial clearance `NOT_ASSESSED` (no legal claim beyond license text) |
| `PIPELINES_DISCOVERED` | 13 manifests (12 production: animated-explainer, animation, avatar-spokesperson, character-animation, cinematic, clip-factory, documentary-montage, hybrid, localization-dub, podcast-repurpose, screen-demo, talking-head; + framework-smoke internal) |
| `TOOLS_DISCOVERED` | 153 tool modules across tools/video(40), tools/audio(21), tools/graphics(23), tools/analysis(15), tools/avatar(5), tools/subtitle(2), tools/character(2), tools/capture(3), tools/enhancement(7), tools/publishers(1), tools/_comfyui(3), tools/_kling(8), + registry/cost/atlas modules; 157 skill markdown files; 20 artifact schemas; 6 tool schemas |
| `PROVIDERS_DISCOVERED` | 23 documented provider-to-tool rows (Pexels, Pixabay, Unsplash, Archive.org, NASA, Wikimedia, Piper, Remotion, HyperFrames, FFmpeg, Google, OpenAI, ElevenLabs, fish.audio, Azure, fal.ai, Atlas Cloud, Kling Official, Volcengine Ark, MiniMax, xAI, Runway, Higgsfield, HeyGen, Suno, Tencent Hunyuan, ComfyUI Partner Nodes, Modal, local GPU, local diffusion) |
| `ZERO_PAID_KEY_ROUTE` | documentary-montage: Archive.org/NASA/Wikimedia (no key) + Pexels/Pixabay/Unsplash (free keys) + Piper TTS + Remotion/HyperFrames/FFmpeg + built-in subtitles + ffprobe/audio QA. Verified statically (README zero-keys table; `docs/PROVIDERS.md` statements `'archive.org, nasa, and wikimedia work without API keys'`, Piper `'no API key, no cost, no network'`) |
| `LOCAL_GPU_ROUTE` | not projected; upstream supports it (`make install-gpu`: WAN 2.1/2.2, Hunyuan 1.5, CogVideo, LTX-2, local diffusion, ComfyUI local) — 6–24GB VRAM, requires owner-gated envelope before any P2P projection |
| `PAID_API_ROUTE` | not projected; ~23 env-var keyed providers; upstream HAS cost reporting (`tools/cost_tracker.py` estimate/reserve/reconcile → `cost_log.json`; budget `observe|warn|cap`; per-action approval; `schemas/artifacts/cost_log.schema.json`) |
| `SELECTED_P2P_CAPABILITIES` | `media.openmontage`, `media.openmontage.documentary`, `media.openmontage.explainer`, `media.openmontage.composition`, `media.openmontage.audio`, `media.openmontage.sourcing`, `media.openmontage.quality` — 7 records, all `STATUS=DISCOVERED`, all fail-closed (INSTALLED=false, ELIGIBLE=false, EXECUTABLE=false) |
| `DEFERRED_CAPABILITIES` | `media.openmontage.generation` (PAID_API/LOCAL_GPU), `media.openmontage.avatar` (PAID_API/local repo), `media.openmontage.screen_demo`, `media.openmontage.cinematic`, `media.openmontage.clip_factory`, `media.openmontage.podcast_repurpose`, `media.openmontage.hybrid`, `media.openmontage.localization_dub`, `media.openmontage.enhancement` |
| `P2P_CORE_CODE_COPIED` | **NO** |
| `GLOBAL_ACTIVATION` | **NO** |
| `RUNTIME_INSTALLED` | **NO** |
| `VIDEO_RENDERED` | **NO** |
| `FILES_CHANGED` | see below |
| `FOCUSED_CHECKS` | registry validation (valid, 72 records), fail-closed routing probe (OpenMontage requests → DISCOVERED only, never selected), new focused unittest suite 6/6 PASS, JSON schema-ish parsing of all three artifacts; pre-existing unrelated test failures NOT touched (baseline stale, verified before change) |
| `CANDIDATE_SHA` | filled at commit time (see §Git) |
| `CANDIDATE_TREE` | filled at commit time (see §Git) |
| `PR_NUMBER` | filled after push (see §Git) |
| `RUNTIME_SMOKE_REQUIRED` | **YES** — before any future execution path (isolated OpenMontage runtime owner-gated envelope); NOT required for intake |
| `OWNER_ACTION_REQUIRED` | **YES** — owner gate before (a) any runtime invocation/execution registration, (b) any paid-provider or API-key path, (c) any local-GPU/model-download path; no owner decision requested for this intake |
| `OVER_ENGINEERING_CHECK` | PASS — one provenance JSON, one catalog JSON, 7 registry records, minimal fail-closed readiness wiring in the existing single router, 1 focused test file, 1 report; no new registry/scheduler/orchestrator/provenance store/ontology |
| `TERMINAL_VERDICT` | **INTAKE COMPLETE — REFERENCE_ONLY_EXTERNAL_RUNTIME_VENDOR REGISTERED (DISCOVERED), ZERO EXECUTION, FAIL_CLOSED** |

---

## 1. UPSTREAM VERIFICATION (fresh read)

Method: GitHub API metadata + `git ls-remote` + shallow clone at `cd9f3c1f03368be87b140af494914b8ee4e3c7a4` (no install, no execution). Facts recorded in `.p2p/vendor/provenance/openmontage-vendor-01.json`.

| Item | Evidence |
|---|---|
| Repository | `calesthio/OpenMontage`, default branch `main`, not archived, `pushed_at=2026-08-22` |
| Commit / tree | `cd9f3c1…` / `6cd1961d552dd9d2bcfba990b80ac06edfe4b061` |
| License | AGPL-3.0 (LICENSE = full AGPLv3 text) |
| Architecture | agent-first: pipeline YAML manifests + Markdown director skills + 153 tool modules + scored 7-dimension provider selection; no code orchestrator (host AI agent is orchestrator) |
| Runtime reqs | Python 3.10+, Node 18+ (Remotion) / 22+ (HyperFrames), FFmpeg; `make setup` = pip + npm + piper-tts + npx hyperframes cache-warm; GPU stack optional |
| Platforms | macOS, Linux, Windows (documented PowerShell path), self-hosted cloud GPU (Modal) |
| Outputs | `projects/<project-id>/renders/final.mp4` (env-overridable root), checkpoints, Backlot board |
| Quality gates | pre-compose validation (delivery promise, slideshow risk), post-render self-review (ffprobe, frame sampling, audio levels, subtitle checks), human approval gates |
| Cost reporting | present (cost tracker + budget observe/warn/cap + per-action approval + cost_log artifact) |

## 2. LICENSE BOUNDARY — DECISION

OpenMontage is **AGPL-3.0**. This is a hard vendor-boundary concern: P2P core must not casually import/adapt/snapshot OpenMontage implementation code (network copyleft). Therefore:

- **No source snapshot** (`LOCAL_VENDOR_SNAPSHOT` explicitly rejected).
- **Reference-only pin** under the existing canonical `PINNED_REFERENCE_ADAPTER` mode (same vocabulary `p2p-uiux` already uses), with `SEMANTIC_KIND=EXTERNAL_RUNTIME` and `dependency_mode=EXTERNAL_RUNTIME_NOT_INSTALLED` (same vocabulary `img2threejs`/`game.majid…` use).
- Upstream copyright/LICENSE/provenance/commit/tree preserved by reference (URL + hash), not by copy.
- No license-compatibility claim is made; `commercial_clearance: NOT_ASSESSED`. Fail-closed classification = reference-only external runtime vendor.

## 3. CAPABILITY PROJECTION (selective)

Registered in the **existing single registry** (`.p2p/system/p2p_capabilities/capabilities.json`, now 72 records; canonical quorum set unchanged) and projected in `docs/p2p-development/capability-catalog/openmontage-vendor/capability-catalog.json`. Per-group lifecycle (canonical status/readiness is authoritative; the five requested states are annotations, no new enum):

| Capability | DISCOVERED | PROJECTABLE | EXECUTION_REGISTERED | EXECUTION_AUTHORIZED | RUNTIME_PROVEN | Runtime class |
|---|---|---|---|---|---|---|
| media.openmontage | ✔ | ✔ | ✘ | ✘ | ✘ | HYBRID (umbrella) |
| media.openmontage.documentary | ✔ | ✔ | ✘ | ✘ | ✘ | LOCAL_FREE + FREE_KEY |
| media.openmontage.explainer | ✔ | ✔ | ✘ | ✘ | ✘ | LOCAL_FREE (+paid optional) |
| media.openmontage.composition | ✔ | ✔ | ✘ | ✘ | ✘ | LOCAL_FREE |
| media.openmontage.audio | ✔ | ✔ | ✘ | ✘ | ✘ | LOCAL_FREE (+free-tier/paid) |
| media.openmontage.sourcing | ✔ | ✔ | ✘ | ✘ | ✘ | LOCAL_FREE + FREE_KEY |
| media.openmontage.quality | ✔ | ✔ | ✘ | ✘ | ✘ | LOCAL_FREE |

Not registered (deferred, documented in catalog): image/video generation, avatar/talking-head/lip-sync, screen-demo/cinematic/clip-factory/podcast-repurpose/hybrid/localization-dub pipelines, enhancement.

## 4. ROUTING / READINESS (fail-closed wiring)

`vendor_skill.py` now recognises `PINNED_REFERENCE_ADAPTER` + `EXTERNAL_RUNTIME_NOT_INSTALLED` + no-entrypoint records as **reference-only external runtime vendors**: discovery returns metadata only (no content read, no file access), and readiness is forced to `INSTALLED=false, DISCOVERED=true, ELIGIBLE=false, RESOLVED=false, EXECUTABLE=false, HEALTHY=false` with reasons `EXTERNAL_RUNTIME_NOT_INSTALLED / REFERENCE_ONLY_ADAPTER / NO_P2P_EXECUTION_REGISTRATION / NO_EXECUTION_AUTHORIZATION / RUNTIME_PROVEN_FALSE`. Verified: OpenMontage requests surface all 7 records as DISCOVERED/NOT_APPLICABLE and are **never selected**; existing routes (whiteboard, Three.js, etc.) unchanged. No second router/scheduler/orchestrator/provenance store was created.

## 5. SECURITY / RESOURCE ASSESSMENT (static surface only)

- Install footprint: large (Python requirements + optional pip extras + Node/Remotion + HyperFrames via npx + FFmpeg + optional GPU stack).
- Subprocess: 50 invocations across 23 files. Network: 67 files with HTTP clients. Downloads: 99 files reference download surfaces.
- API keys: dotenv-based, 23+ env vars, no hardcoded keys found in scanned source, `.env` ignored.
- Arbitrary command/code surface: **high** — 12/13 pipeline manifests set `extensions.custom_scripts=true`/`custom_skills=true` (agentic by design) → any future runtime invocation must be sandboxed/isolated.
- Output paths: configurable (projects root, env-overridable); contained by design but not P2P-governed.
- Provider fallback: scored selector with documented fall-through; budget cap + per-action approval for paid tools.
- GPU/disk: NVIDIA CUDA, 6–24GB VRAM by model, multi-GB weights; repo clone ~161MB (mostly demo MP4s).
- No broad security research performed; no CVE claims.

## 6. P2P INTEGRATION (reused, not duplicated)

Existing vendor registry/catalog → `capabilities.json` + `capability-catalog/*`; provenance → `.p2p/vendor/provenance/`; selective routing → existing `TRIGGERS`/`NEGATIVE_TRIGGERS` + single router; evidence/ReturnPacket → P2P-owned (no OpenMontage-specific evidence schema). OpenMontage's pipeline/orchestration concepts are NOT imported; P2P retains Control Tower, Work Factory, risk lanes, capability routing, ReturnPacket, Supervisor, Owner Gate.

## 7. FILES CHANGED

| File | Change |
|---|---|
| `.p2p/system/p2p_capabilities/capabilities.json` | +7 DISCOVERED reference-only vendor records (72 total) |
| `.p2p/system/p2p_capabilities/vendor_skill.py` | reference-only external runtime vendor discovery + fail-closed readiness wiring |
| `.p2p/vendor/provenance/openmontage-vendor-01.json` | intake/provenance record (pin, license, classification, security, no-execution evidence) |
| `docs/p2p-development/capability-catalog/openmontage-vendor/capability-catalog.json` | selective projection catalog (groups, exact upstream tools, lifecycle, deferred, routes) |
| `docs/p2p-development/reports/P2P-OPENMONTAGE-VENDOR-01-terminal-report.md` | this report |
| `tests/test_p2p_openmontage_vendor_01.py` | focused offline test suite (6 tests) |
| `tests/test_p2p_game_toolchain_02a.py` / `tests/test_p2p_visual_vendor_integration.py` | capability-count assertions 65 → 72 (both files already failing on unrelated stale pins; count kept honest) |

## 8. EXECUTION POLICY / VERDICT

`EXECUTION_POLICY=MINIMUM_SUFFICIENT_WORK` honored: no upstream sources vendored, no adapters executed, no installs, no renders, no keys, no downstream mutation. `STOP_WHEN_EVIDENCE_SUFFICIENT=YES`. **Terminal verdict: intake complete; OpenMontage is registered as an isolated, pinned, selectively projectable, reference-only external video-production vendor. Owner gate remains required for any future runtime/execution/paid/GPU authorization.**
