# P2P GitHub Research Appendix

Status: `RECONCILED_RESEARCH_APPENDIX_V1`
Date: `2026-09-16`
Primary inbox source: repository-root `github research.txt`
Authority: subordinate to `P2P_SUPREME_OPERATING_LAW_V1`, `governance/research-adoption-ledger.json`, `governance/research-intake-ledger.json`, and durable implementation evidence on canonical `main`.

## Purpose

`github research.txt` is a discovery inbox, not an adoption ledger. It mixes current repositories, old summaries, project-specific tools, broad agent frameworks, security tooling, voice/video/UI tooling, and claims that may have changed upstream.

This appendix turns that inbox into a recoverable catalog and, critically, reconciles it against work P2P has already completed. Chat history is useful for finding candidate lineage, but **durable GitHub state wins** when chat memory and repository evidence disagree.

This file does not create a second router, capability registry, truth store, roadmap, or research-adoption authority. Candidate decisions below are guidance for the next bounded goal; existing canonical ledgers remain authoritative for adoption status.

## Status vocabulary

| Status | Meaning |
| --- | --- |
| `MERGED_IMPLEMENTED` | Useful pattern/capability has durable merged implementation in P2P main. |
| `IMPLEMENTED_DEFAULT_OFF` | Durable implementation exists but runtime use is opt-in or still requires a separate Owner/security/privacy gate. |
| `PILOT_ACTIVE_UNMERGED` | Bounded work exists on an active PR/pilot but is not canonical main. |
| `RESEARCH_ONLY` | Studied or retained as reference; no runtime dependency/adoption. |
| `DEFERRED` | Valuable, but current P2P has no proven gap justifying integration. |
| `REJECTED_AS_SECOND_AUTHORITY` | Useful ideas may be studied, but wholesale adoption would create a competing router/control plane/truth store. |
| `PROJECT_CANDIDATE` | Better suited to one P2P-managed project than P2P core. |
| `NEW_GAP` | Research surfaced a capability not yet durably covered by P2P. |

## A. Reconciliation: items already implemented or already decided

| Upstream / research item | Durable P2P state | Evidence | Do not redo |
| --- | --- | --- | --- |
| `robzilla1738/supergoal` | `MERGED_IMPLEMENTED` | PR #169 adopted bounded native `/goal`, whole-worktree evidence and contract replay; PR #170 transported it through installed runtime; PR #174 projected it into portable project instructions; PR #177 added deterministic auto-activation from durable GoalPlan/TaskPlan state. | Do not install Supergoal or create `.supergoal/` authority, fixed three-strike recovery, second roadmap/ledger/daemon. |
| `comet-ml/opik` | `IMPLEMENTED_DEFAULT_OFF` | PR #171 added metadata-only Hermes observer pinned to `opik==2.2.59`; PR #175 closed normal release/install distribution. Default remains OFF; real external telemetry still needs privacy/secret authority. | Do not build a second observer framework or self-host stack merely to repeat this work. |
| `getzep/graphiti` | `RESEARCH_ONLY` | PR #171 explicitly kept Graphiti R&D-only because Hindsight already occupies the optional memory lane and P2P durable truth remains authoritative. | Do not make Graphiti a project truth store without a separately proven native gap. |
| `zhaoxuya520/reverse-skill` | `MERGED_IMPLEMENTED` | PR #173 safely adopted methodology references into existing SEC01; P2P remains sole router/authority and upstream bootstrap/auto-install/offensive execution surfaces are excluded. PR #172 is an older superseded candidate path. | Do not create a second security router or implicit offensive execution path. |
| Repomix | `MERGED_IMPLEMENTED` | PR #153 introduced bounded context bridge; PR #159 completed opt-in Hermes essential stack with Repomix `1.18.0`, read-only repo mount, external output and bounded token budget. | Do not add another context packer authority. |
| TokScale | `MERGED_IMPLEMENTED` | PR #153 bounded JSON telemetry bridge; PR #158 certified Hermes `state.db` compatibility; PR #159 completed opt-in runtime shape with TokScale `4.16.0`, read-only volume and no public `submit`. | Telemetry is not billing/project truth. |
| Hermes Workspace | `IMPLEMENTED_DEFAULT_OFF` | PR #159 builds pinned Workspace `v2.3.0` from exact release commit, loopback-only. | Workspace UI/Swarm/Conductor does not become Control Tower authority. |
| Hindsight | `IMPLEMENTED_DEFAULT_OFF` | PR #158/159 established the safe profile; one-shot enable requires explicit opt-in + API key; `auto_retain=false`, `auto_recall=false`, `memory_mode=tools`. | Recall is not durable P2P truth. |
| Mission Control | `REJECTED_AS_SECOND_AUTHORITY` | PR #153/#159 explicitly reject a runtime service/control-plane role. | Do not introduce it as scheduler/task/memory/approval authority. |
| `AnnenkovLabs/girl-agent` | `MERGED_IMPLEMENTED` (clean-room concepts only) | PR #152 created Personal AI Behavior Harness V1 without copying restrictive upstream code/prompts; PR #162 integrated it into Hermes; PR #178 added bounded per-session adaptation. | Do not re-introduce relationship/hormone/presence simulation or autonomous memory authority. |
| `Kappaemme-git/codex-first-customer-finder-skill` | `PILOT_ACTIVE_UNMERGED` | PR #180 contains the Opportunity Lab validation pilot, pinned upstream adapter, evidence gate, shortlist and Owner-authorized outreach batch. | Do not build a duplicate lead-generation framework in P2P core. |
| Evidence-first / Uncle Bob acceptance idea | `MERGED_IMPLEMENTED` | PR #182 added `P2P_EVIDENCE_FIRST_VERIFICATION_V1` with proof-carrying change, scoped PASS claims and risk-proportional independent challenge. | Do not create a parallel verification framework. |

## B. Catalog by capability family

| Family | Examples present in `github research.txt` | P2P treatment |
| --- | --- | --- |
| Agent runtime / orchestration | DeerFlow, OctoMind, Council of High Intelligence, HanaAgent | Study patterns only unless a specific capability gap is proven; wholesale frameworks collide with P2P router/executor/state authority. |
| Memory / context | Graphiti, Supermemory, AgentMemory, DejaVu, Headroom, Taste Skill | Prefer current durable-state + bounded Hindsight lane. External memory can be non-authoritative retrieval only. |
| Code intelligence / structural evidence | `DeusData/codebase-memory-mcp`, Codex Complexity Optimizer, finding-unknowns | **Highest remaining P2P-core gap.** Use as optional evidence/support, never architecture or truth authority. |
| Observability / evaluation | Opik | Already implemented default-off. Extend only when a concrete evaluation need exists. |
| Skill ecosystems | SkillsGate, SF Skills, AutoSkills, BrowserAct skills, self-learning-skills, David Ondrej skills | Discovery/reference sources only; P2P capability/skill selection and Rule Assimilation remain authoritative. |
| Browser / web intelligence | Unbrowse, Wigolo, API Mega List, YouTube-to-Markdown | Candidate external providers; security/session boundaries first. |
| Sandbox / isolated execution | CubeSandbox | Defer until P2P proves a sandbox capacity/isolation gap that current providers cannot satisfy. |
| Security / reverse / OSINT | Reverse-Skill, Deep-eye, Android reverse skill, Reversecore MCP, Awesome AI Hacking Agents, T3MP3ST, SpiderFoot | Route through existing security execution classes; no capability grants from upstream content. |
| Video / deterministic assembly | HyperFrames, ToonCrafter, Huobao Drama, SupoClip, ai-video-generator-claude, Storyboard Reference Studio, Seedance skills | Project candidates, especially `p2p-video-lab`; not P2P control-plane capabilities. |
| Voice / audio | Moonshine, Supertonic, Confucius4-TTS, X-Voice, GPT-SoVITS, DotsTTS, Sokuji | Project/provider candidates; voice identity/privacy/consent boundaries apply. |
| Image / UI | Stable Diffusion WebUI Forge, Cult UI, Transitions.dev, cut-it-out, Best Designs on X, Recent Design, Fylm | Project-specific design/render sources; reuse before new UI infrastructure. |
| Education | GenLearn / Generative Recursive Education, HappySeeds, paper-proofreading workflows | Project candidates for Child Learning Lab. |
| Product / embedded assistants | CopilotKit, Noodl | Downstream application capability, not P2P core routing. |
| Data / vector infrastructure | RuVector, BigSet | Defer by default; introducing a new DB/search substrate requires a proven data/query gap and must not become second truth. |
| Domain workflows | AI Quant Researcher, job agents, first-customer finder | Standalone/project skills; evidence and consent boundaries vary by domain. |
| High-risk / bypass automation | account creators, signup bypass collections, jailbreak corpora | Research/security contexts only as permitted; never general automatic runtime capability. |

## C. Newly prioritized gaps after chat + durable-state reconciliation

### C1. Code intelligence as Evidence-First structural proof — `DO_IT`

Upstream reviewed: `DeusData/codebase-memory-mcp` release `v0.11.0`, target commit `8972ea69c6ad94b1ef1d4ffbf0a92d78d2db1798`, MIT.

Useful properties:

- Tree-sitter / hybrid semantic code graph and impact queries.
- One-shot `cli` mode can invoke MCP tools without starting/connecting to its standing coordination daemon.
- JSON output is suitable for a bounded P2P evidence adapter.

Upstream also contains surfaces P2P must **not** inherit automatically: installer-driven client mutation, auto-index/watch, standing coordination daemon, UI, shared graph artifact, and ADR persistence. Those are intentionally excluded from the P2P bridge.

Decision for this slice: expose only a small whitelist of **read-only query tools over an already-existing index**. No auto-install, no index creation, no configuration mutation, no daemon/watcher/UI, no ADR management. Returned graph facts are `NON_AUTHORITATIVE_STRUCTURAL_EVIDENCE` for `STRUCTURAL_PROOF`; source code/tests/authoritative project files still win.

### C2. Complexity Optimizer — `ADAPT_PRINCIPLE_ONLY` now

`Kappaemme-git/codex-complexity-optimizer` has a good safety shape: report-first, scanner findings are leads rather than proof, conservative optimization, focused tests and benchmarks when performance matters. P2P already has Evidence-First and anti-overengineering mechanisms, so installing another mandatory skill is not justified yet.

Retain the principle: when performance/complexity is material, `STRUCTURAL_PROOF` should identify the current pattern, expected complexity, proposed change, risk, and measurement needed. Do not chase every scanner warning.

### C3. Finding Unknowns — `ASSIMILATE_AS_PLANNING_HEURISTIC`

`bozhouDev/finding-unknowns-skills` emphasizes surfacing architecture-changing unknowns before implementation and explicitly says trivial work should skip ceremony. This is compatible with P2P's existing analytical-autonomy, fresh-evidence, prompt-alignment and anti-overengineering rules.

P2P heuristic:

```text
Before a non-trivial implementation, ask:
Which unresolved unknown, if guessed wrong, could materially change
architecture, authority, acceptance, data safety, or blast radius?
```

Only material unknowns justify extra discovery/prototype work. Do not turn this into a mandatory interview phase.

### C4. HyperFrames — `PROJECT_CANDIDATE`

Strong candidate for `p2p-video-lab` as deterministic HTML/CSS/JS + browser + FFmpeg assembly around generated assets, narration, captions and motion graphics. Keep it outside P2P core. A separate project pilot should prove Windows/runtime compatibility and output quality before adoption.

## D. Explicitly deferred/rejected wholesale imports

- **DeerFlow / OctoMind / broad multi-agent runtimes:** research architecture only. P2P already owns routing, task state, evidence and authority.
- **Graphiti / Supermemory as canonical memory:** deferred; would compete with durable project truth unless a narrower non-authoritative retrieval role is proven.
- **CubeSandbox infrastructure:** defer until isolation/capacity need is measured; prefer provider/thin-adapter use over owning a new cluster/control plane.
- **SkillsGate / AutoSkills as canonical registry:** reference/discovery only; no second capability registry.
- **Supergoal runtime:** already mined for selected patterns; do not install the upstream control plane.
- **Mission Control:** rejected as second control plane.

## E. Research execution rule for this appendix

When a future item from `github research.txt` is proposed:

1. Fresh-check upstream identity, license, maintenance and actual interface.
2. Reconcile against this appendix **and canonical P2P ledgers/PR evidence** before doing new research.
3. Ask `Không bị over engineering chứ?` and prefer `reuse -> external provider -> thin adapter -> fork only with evidence`.
4. Classify the useful unit as principle, skill, provider, project capability, evidence source, or infrastructure.
5. Never let an upstream router, memory, registry, telemetry system, skill catalog, or generated output become P2P authority by installation side effect.
6. Implement the smallest independently verifiable slice and attach Evidence-First proof.
7. Update the canonical research/adoption machinery when an Owner-selected capability advances status; this appendix is descriptive navigation, not a replacement ledger.

## F. Current development order

1. **Code intelligence structural-evidence bridge** — this appendix's first implementation slice.
2. Use that bridge on real cross-cutting P2P tasks; measure whether it materially reduces blind file traversal or improves impact/regression discovery.
3. Only if the measured evidence justifies it, evaluate a complexity scanner/skill as an optional provider.
4. Run HyperFrames as a separate Video Lab pilot, not a P2P core dependency.
5. Evaluate Unbrowse/Wigolo only when browser/search cost or reliability becomes a measured bottleneck.

`CATALOG_COMPLETE_ENOUGH_FOR_ACTION=YES`
`DUPLICATE_RESEARCH_SHOULD_BE_RECONCILED_FIRST=YES`
`NEXT_CORE_SLICE=CODE_INTELLIGENCE_STRUCTURAL_EVIDENCE`
