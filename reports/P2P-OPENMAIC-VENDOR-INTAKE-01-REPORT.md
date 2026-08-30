# P2P-OPENMAIC-VENDOR-01 — Vendor Intake & Selective Capability Projection (Intake Only)

**Goal:** Add OpenMAIC to the canonical P2P vendor/capability system as a pinned, selectively projectable education/course-production vendor. Vendor intake only — no install, no runtime, no classroom generation, no downstream modification.

**Branch:** `arena/01a0550f-p2p-upgrade-github-1` · P2P baseline `1c9eea39ce6aa0b721d67fa6b7130918357eea4d` (tree `0fab3c59bd34094219693ca8ac5e7e80e2200723`).

**Compliance:** No `pnpm install` run. No OpenMAIC runtime started. No classroom generated. No downstream project modified. No vendor tree copied into P2P. No second vendor framework / orchestrator / provider registry / persistence layer / scheduler / governance ontology created.

---

## 1. Fresh upstream verification (NOT trusted from reference)

| Item | Value |
|---|---|
| Repository | https://github.com/THU-MAIC/OpenMAIC.git |
| Identity | OpenMAIC (Open Multi-Agent Interactive Classroom) |
| Default branch | `main` |
| **OPENMAIC_UPSTREAM_SHA** | `dfebbcf33f3a56064129903faeab70a9e4243146` |
| **OPENMAIC_UPSTREAM_TREE** | `bb8972cb6fa5e4d6c5a7eff6f2357e79bf930b45` |
| HEAD committed | 2026-08-29T19:48:04Z |
| **OPENMAIC_RELEASE** | `v1.0.0` (published 2026-08-27T13:13:53Z; tag commit `aa2bfb3c1d406c47100c6744d90e788abdf1f6d5`) |
| main vs tag | main is **8 commits ahead** of the v1.0.0 tag |
| **OPENMAIC_ROOT_LICENSE** | MIT (LICENSE, © 2026 THU-MAIC; GitHub license metadata = MIT) |

Method: `git ls-remote`, fresh `git clone --depth 1` (206 MB) with `rev-parse HEAD` / `HEAD^{tree}`, `gh repo view`, `gh api` (commit date, tag ref, compare `aa2bfb3...dfebbcf` → `ahead 8, behind 0`).

**The supplied reference values (`dfebbcf…` / `bb8972cb…`) were re-verified as still current upstream `main` — they were not blindly trusted.**

## 2. Third-party license boundaries (exact — no flattening)

| Boundary | License | Evidence |
|---|---|---|
| Root repo | MIT | `LICENSE` |
| `packages/@openmaic/{dsl,editor,generation,importer,renderer,storage}` | MIT | per-package `LICENSE` (© 2026 THU-MAIC) |
| `packages/mathml2omml` (v0.5.0, vendored from `fiduswriter/mathml2omml`) | **LGPL-3.0-or-later** | `packages/mathml2omml/LICENSE` (LGPLv3) + package.json |
| `packages/pptxgenjs` (v4.0.1, vendored from `gitbrent/PptxGenJS`) | MIT (third-party) | `packages/pptxgenjs/package.json` |
| `render-service`, `packages/docs` | UNSPECIFIED | no license field/file found — no MIT claim made |
| npm dependency tree | MIXED per-dependency | `pnpm-lock.yaml` (1,040,204 B) |
| `assets/` demo media (GIF/PNG/audio) | NOT_INDIVIDUALLY_AUDITED | repo MIT notice ≠ per-asset rights |

**THIRD_PARTY_LICENSE_BOUNDARIES** record is exact; upstream README itself declares the LGPL-3.0-or-later boundary of `packages/mathml2omml` and third-party MIT of `packages/pptxgenjs`.

## 3. Runtime / platform / architecture

- Node.js `>= 20.9.0` (engines), `.nvmrc` = 22; pnpm `10.28.0` (packageManager pin); README Node ≥ 20 / pnpm ≥ 10.
- Next.js 16 App Router (standalone outside Vercel), React 19, TS 5, Tailwind 4, LangGraph 1.1; Docker compose profiles (`server-persistence`, `video-export`); Vercel supported.
- Workspace: `packages/*` + `packages/@openmaic/*` (docs excluded); root postinstall builds `mathml2omml`, `pptxgenjs`, `@openmaic/*`; `build` runs `assert-vendor-maic-importer.mjs`.
- Architecture: `app/` (api: agent, stages, generate, generate-classroom, chat, pbl, parse-pdf, web-search, persistence ...), `lib/` (generation two-stage pipeline, LangGraph orchestration, playback state machine, action engine, ai/audio/media/export/persistence/web-search/pdf), `components/` (slide-renderer canvas editor, scene-renderers, workbench, whiteboard, chat, roundtable), `packages/@openmaic/*` SDK, `render-service/` (optional MP4), `skills/agent-runtime` (23 modules on disk; README says "20 built-in skills").
- Optional operator-installed deps: `ffmpeg`/`ffprobe`; Chromium + FFmpeg + Node 22 for render-service; local providers run separately.

## 4. Capability inventory (discovered)

**A. COURSE AUTHORING** — topic/document → course; curriculum planning (multi-lesson); two-stage lesson generation (outline → scene content); iterative agent workbench editing (validated atomic JSON-patch scene edits, page gen/duplicate/insert/delete/reorder, narration/deck editing, history, resume/steer).

**B. CLASSROOM** — AI teacher; AI classmates; real-time discussion (SSE) + roundtable debate; TTS narration (multi-provider + voice clone) and ASR; SVG whiteboard; playback engine with 28+ action types.

**C. LEARNING ARTIFACTS** — slides; quizzes (single/multi choice, short answer, real-time AI grading); interactive HTML simulations; PBL v2 (roles, milestones, deliverables); Deep Interactive Mode (3D visualization, simulations, mini-games, mind maps, online programming).

**D. MATERIAL INGESTION** — PDF/DOC/DOCX/PPT/PPTX/XLS/XLSX/TXT/MD/images (MIME registry); audio + transcription; video + timestamped transcripts/keyframes (local ffmpeg); web materials (search providers + trusted-URL fetch); PPTX import with layout preservation (uses `mathml2omml` for MathML→OMML conversion).

**E. EXPORT** — editable PPTX; interactive self-contained HTML; classroom ZIP (`.maic.zip`) + Resource Pack; offline/intranet playback with asset inlining (KaTeX, Three.js, Tailwind CDN, fonts, images as `data:` URIs); optional MP4 via render-service.

**F. STORAGE** — browser localStorage/IndexedDB default; optional embedded `/api/persistence` + PostgreSQL; asset bytes in PostgreSQL or S3; durable agent sessions (PostgreSQL-backed, opt-in server runtime).

**G. PROVIDER ROUTING** — verified at family level: OpenAI, Azure OpenAI, Anthropic, Amazon Bedrock, Google Gemini, DeepSeek, Qwen, Kimi, MiniMax, Grok (xAI), GLM (Zhipu), Doubao, Tencent Hunyuan/TokenHub, Xiaomi MiMo, OpenRouter, SiliconFlow, AtlasCloud, **Ollama (local)**, **Lemonade (local)**, any OpenAI-compatible API; plus image, video, TTS, ASR, web-search, and document-parsing provider families. The complete internal model/provider catalog is **not** duplicated into P2P.

## 5. Selective projection (canonical naming; small high-level surface)

| Capability ID | DISCOVERED | PROJECTABLE | EXECUTION_REGISTERED | EXECUTION_AUTHORIZED | RUNTIME_PROVEN |
|---|---|---|---|---|---|
| `education.course_generation` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `education.interactive_classroom` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `education.course_editing` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `education.quiz_assessment` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `education.interactive_simulation` | ✅ | ✅ | ❌ | ❌ | ❌ |
| `education.course_export` | ✅ | ✅ | ❌ | ❌ | ❌ |

All registered in `capabilities.json` as `TYPE=BACKEND_PROVIDER`, `SEMANTIC_KIND=EXTERNAL_RUNTIME`, `STATUS=DISCOVERED`, `mode=EXTERNAL_VENDOR_INTAKE_ONLY`, `execution_status=NOT_EXECUTED`, `integration_status=INTAKE_AUDITED_PROJECTABLE_PENDING_EXECUTION_REGISTRATION`, `owner_gate_status=PENDING_EXACT_SUBJECT_REVIEW`.

DEFERRED_CAPABILITIES: vendor-internal 20+/23 skill catalog; complete provider/model catalog; OpenClaw/ClawHub integration; MP4 render service; voice cloning/registration; learner analytics beyond quiz grading; per-asset rights review of demo media; P2P hosting of OpenMAIC.

## 6. Multi-agent authority boundary

**OPENMAIC_MULTI_AGENT_AUTHORITY = VENDOR_INTERNAL_ONLY.** OpenMAIC teacher/peer agents belong to education runtime semantics only. P2P retains Control Tower authority, Work Factory, capability routing, execution lanes, Supervisor, Owner Gate, Git/evidence truth, BackendExecutionBridge, ReturnPacket. No second orchestration/review authority.

## 7. Provider / cost classification

- **LOCAL** — Ollama, Lemonade (LLM/image/TTS/ASR), FunASR, VoxCPM2, ComfyUI, MinerU self-host, SearXNG, browser storage.
- **BYO_API** — all cloud LLM providers, cloud image/video/TTS/ASR/search providers, S3 bucket, PostgreSQL instance, AliDocMind/MinerU cloud. **API-backed generation is not free; it consumes the operator's provider credentials/quota.**
- **HOSTED** — upstream public demo `open.maic.chat` (third-party access-code hosted; not a P2P service; no P2P hosting commitment).
- **HYBRID** — OpenMAIC runtime: browser/local default + optional server persistence + operator-chosen cloud or local providers.

## 8. Persistence (verified)

- **DATABASE_REQUIRED_BY_DEFAULT = NO.** Confirmed: "OpenMAIC runs without a database by default" — browser storage (localStorage KV, IndexedDB documents/runtime/assets) is the zero-server default; `@openmaic/storage` README confirms "zero-server `clone-and-run` default".
- **OPTIONAL_PERSISTENCE** — pluggable seam: embedded HTTP persistence (`/api/persistence`), PostgreSQL-backed documents/runtime/assets/sessions/materials/skills (docker compose `server-persistence`), S3 asset bytes (sign URLs or redirect egress). Nuance: v1.0.0 **agent workbench durable sessions are opt-in and PostgreSQL-backed by design** (`OPENMAIC_AGENT_RUNTIME_ENABLED=true` + `DATABASE_URL`).
- P2P does **not** introduce a database merely because OpenMAIC supports one.

## 9. Bounded static security assessment (no penetration test)

- **Secrets:** server-side provider config only; credentials never reach the browser; `server-providers.yml` and `.env*` gitignored (only `.env.example` tracked); no committed API keys found; opt-in `ACCESS_CODE` HMAC-signed cookie auth; CSP `frame-ancestors 'self'` + X-Frame-Options SAMEORIGIN.
- **SSRF controls CONFIRMED:** `lib/server/ssrf-guard.ts` — hostname + DNS-pinned IP classification (private/link-local/loopback, IPv4/IPv6/mapped), strict-fetch path, redirect-safe, `ALLOW_LOCAL_NETWORKS=true` explicit weakener; bounded downloads (byte budgets + timeouts); web fetch surface origin-allow-listed + content-type allow-list.
- **Uploads:** MIME registry/normalization; size bounds (agent 50 MB default, video export 300 MB capped stream, voice clone 10 MB; 200 MB proxy body cap); provider capability checks; server-side extraction with lease fencing.
- **Generated HTML/interactive execution:** vendor-generated interactive HTML runs in the learner's browser; exported HTML is self-contained (CDN assets inlined). Containment/sandboxing review deferred to the future execution-registration gate.
- **Local provider execution:** operator-run services on operator hosts; OpenMAIC is a client, not a sandbox.
- **Dependency footprint:** 130 direct deps (+32 dev), pnpm-lock 1.04 MB; postinstall builds workspace packages; no runtime network credentials.

## 10. Do-not-duplicate compliance

Reused: `.p2p/vendor/provenance/` (pinned vendor mechanism), `manifest/external-sources.json` candidate index, `capabilities.json` canonical registry, `p2p-capability-catalog/1` catalog pattern, authority gates (Owner Gate), existing router/BackendExecutionBridge/ReturnPacket semantics. No new framework, ontology, provider registry, persistence layer, or scheduler was created.

## 11. Files changed

| File | Change |
|---|---|
| `.p2p/vendor/provenance/p2p-openmaic-intake-01.json` | NEW — pinned provenance + license boundaries + inventory + projection + authority + security assessment |
| `docs/p2p-development/capability-catalog/education-course/capability-catalog.json` | NEW — `p2p-capability-catalog/1` vendor intake catalog |
| `docs/p2p-development/capability-catalog/education-course/README.md` | NEW — intake narrative + boundaries |
| `.p2p/system/p2p_capabilities/capabilities.json` | 6 new `education.*` capabilities (65 → 71), all DISCOVERED |
| `manifest/external-sources.json` | NEW candidate `P2P-EXT-CANDIDATE-OPENMAIC-01` |
| `tests/test_p2p_openmaic_intake_01.py` | NEW — 5 focused intake/pin/license/projection tests (all PASS) |
| `tests/test_p2p_game_toolchain_02a.py`, `tests/test_p2p_visual_vendor_integration.py`, `tests/test_p2p_game_truyen_mpfb_adapter_01.py` | canonical registry count 65 → 71 (only) |

## 12. Focused checks

- Registry loads and validates with 71 capabilities (`load_registry` → `valid=True`), no duplicate IDs.
- NEW test file: 5/5 PASS.
- Vendor-skill discovery remains metadata-only and returns no content for the new vendor rows (they are not `LOCAL_VENDOR_SNAPSHOT`).
- Affected prior test files: failure set **identical** before/after (pre-existing branch drift, e.g., toolchain test's stale `CURRENT_MAIN_SHA` pin, unrelated to this workstream).
- Fresh-clone evidence: pinned commit/tree verified with `git rev-parse`; tag comparison via `gh api` (`ahead_by=8`).
- No install/runtime executed; no downstream projects touched.

## 13. RETURN

```
FRESH_P2P_MAIN_SHA=1c9eea39ce6aa0b721d67fa6b7130918357eea4d
FRESH_P2P_MAIN_TREE=0fab3c59bd34094219693ca8ac5e7e80e2200723
OPENMAIC_UPSTREAM_SHA=dfebbcf33f3a56064129903faeab70a9e4243146
OPENMAIC_UPSTREAM_TREE=bb8972cb6fa5e4d6c5a7eff6f2357e79bf930b45
OPENMAIC_RELEASE=v1.0.0 (main is 8 commits ahead of tag)
OPENMAIC_ROOT_LICENSE=MIT
THIRD_PARTY_LICENSE_BOUNDARIES=mathml2omml:LGPL-3.0-or-later; pptxgenjs:MIT(third-party); render-service:UNSPECIFIED; packages/docs:UNSPECIFIED; npm tree:MIXED; assets media:NOT_INDIVIDUALLY_AUDITED
VENDOR_CLASSIFICATION=MANAGED_VENDOR_CANDIDATE_INTAKE_ONLY (pinned, selectively projectable)
COURSE_CAPABILITIES_DISCOVERED=authoring(A), classroom(B), artifacts(C), ingestion(D), export(E), storage(F), provider routing(G) - all static/discovered
SELECTED_P2P_CAPABILITIES=education.course_generation, education.interactive_classroom, education.course_editing, education.quiz_assessment, education.interactive_simulation, education.course_export
DEFERRED_CAPABILITIES=vendor skill catalog; full provider/model catalog; OpenClaw; MP4 render service; voice cloning; learner analytics; demo-media asset rights; P2P hosting
PROVIDERS_VERIFIED=OpenAI, Azure OpenAI, Anthropic, Amazon Bedrock, Google Gemini, DeepSeek, Qwen, Kimi, MiniMax, Grok(xAI), GLM(Zhipu), Doubao, Tencent Hunyuan, Xiaomi MiMo, OpenRouter, SiliconFlow, AtlasCloud, Ollama, Lemonade, OpenAI-compatible + media/search/parse families
LOCAL_PROVIDER_ROUTE=Ollama, Lemonade, FunASR, VoxCPM2, ComfyUI, MinerU self-host, SearXNG, browser storage
CLOUD_PROVIDER_ROUTE=BYO_API cloud LLM/image/video/TTS/ASR/search/parse + S3 + PostgreSQL
DATABASE_REQUIRED_BY_DEFAULT=NO
OPTIONAL_PERSISTENCE=embedded /api/persistence + PostgreSQL + S3 asset bytes; durable agent sessions Postgres opt-in
EXPORT_FORMATS=editable PPTX; self-contained interactive HTML; classroom ZIP (.maic.zip)/Resource Pack; offline/intranet (inlined assets); optional MP4 via render-service
OPENMAIC_MULTI_AGENT_AUTHORITY=VENDOR_INTERNAL_ONLY
P2P_CORE_CODE_COPIED=NO
GLOBAL_ACTIVATION=NO
RUNTIME_INSTALLED=NO
CLASSROOM_GENERATED=NO
FILES_CHANGED=7 files (2 new + 5 modified; see section 11)
FOCUSED_CHECKS=registry valid 71; intake tests 5/5; vendor-skill discovery unchanged; pre-existing test failure set unchanged; fresh clone SHA/tree verified
CANDIDATE_SHA=<recorded after commit>
CANDIDATE_TREE=<recorded after commit>
PR_NUMBER=<recorded after PR creation>
RUNTIME_SMOKE_REQUIRED=YES (required before any EXECUTION_REGISTERED/EXECUTION_AUTHORIZED transition; NOT executed in this intake)
OWNER_ACTION_REQUIRED=YES (Owner Gate exact-subject review; approve/adjust the 6-capability projection before execution registration; note mathml2omml LGPL boundary)
OVER_ENGINEERING_CHECK=PASS (intake only; no new framework; reuse of existing vendor/capability mechanisms)
TERMINAL_VERDICT=INTAKE_COMPLETE_PROJECTABLE_NOT_ACTIVATED
EXECUTION_POLICY=MINIMUM_SUFFICIENT_WORK
CONTEXT_POLICY=MINIMUM_RELEVANT_CONTEXT
PROGRESS_REPORTING=EXCEPTIONS_ONLY
STOP_WHEN_EVIDENCE_SUFFICIENT=YES
```
