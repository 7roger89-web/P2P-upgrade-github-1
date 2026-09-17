# P2P EXTERNAL CAPABILITY ASSIMILATION 20260917-01 — TERMINAL REPORT

Ten external repositories assessed; selective assimilation under the core
decision law `REUSE_EXISTING_P2P > EXTEND_EXISTING_P2P > ADAPTER >
EXTERNAL_TOOL > NEW_IMPLEMENTATION`.

```
TASK_ID: P2P_EXTERNAL_CAPABILITY_ASSIMILATION_20260917_01
TASK_TERMINAL_STATUS: COMPLETE_ASSESSED_SELECTIVE_ASSIMILATION
LAW_SOURCE_READ: docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md (P2P_SUPREME_OPERATING_LAW_V1, RULE_ASSIMILATION_GATE_V1) + docs/ARENA_AGENT_MODE_PROTOCOL.md + AGENTS.md (fresh main 1a7ff5278acc16ca7e28516dc67ae036a01ce4ac)
ASSESSED_REPOS: 10
ASSIMILATED: 1 mechanism cluster (interaction-polish mechanics -> existing UI-taste-skill redesign-skill)
IMPLEMENTED_CHANGES: redesign-skill Interaction Polish Gate (3 synced copies + 3 manifest per-file hash updates) + research-adoption-ledger records RA-EXT-072..081 + md projection section + this report + focused test
NEW_INFRASTRUCTURE_CREATED: NO
PARALLEL_ROUTER_CREATED: NO
PARALLEL_CAPABILITY_REGISTRY_CREATED: NO
SECOND_OPERATING_LAYER_INSTALLED: NO
OWNER_CODEX_CONFIG_TOUCHED: NO
SECRETS_OR_DEPLOY_OR_RELEASE: NO
```

## 1. Assessment method

Every repository was cloned at a pinned commit and assessed from source
(code/docs/tests), not from README claims. Each claim below is labeled
VERIFIED FACT (observed in source), INFERENCE, or UPSTREAM CLAIM NOT
INDEPENDENTLY VERIFIED.

| # | Repository | Observed commit | License (verified) | Real capability |
| --- | --- | --- | --- | --- |
| 1 | jakubkrehel/make-interfaces-feel-better | `35545ea` | MIT | VERIFIED FACT: 19-principle interaction-polish skill + structured review output format (SKILL.md + 5 reference files) |
| 2 | pgrundev/pgbot | `08882b5` | Apache-2.0 | VERIFIED FACT: Go read-only Postgres diagnostics, versioned `--json` contract 1.2.0 + JSON Schema, stdio MCP server with deterministic tools; beta (UPSTREAM CLAIM: finding accuracy) |
| 3 | rlaope/oh-my-hermes | `964ddc1` | MIT | VERIFIED FACT: large Python operating layer over Hermes Agent (workflows, typed artifacts, orchestration patterns, worktree guidance) |
| 4 | vercel-labs/fx | `a1e3265` | Apache-2.0 | VERIFIED FACT: Zig native coding-agent CLI with ACP server mode, MCP, skills; self-declared experimental |
| 5 | MDX-Tom/gpt-instruct | `0ad8ec5` | MIT | VERIFIED FACT: Codex prompt versioning + A/B/C gates + isolated eval runs + regression corpus + failure attribution |
| 6 | larashero3-dotcom/lieflat-less-ai-tone | `27d2923` | MIT | VERIFIED FACT: contrastive corpus study (629 articles / 2.83M chars) + whitelist-only Chinese rewriting skill; UPSTREAM CLAIM NOT INDEPENDENTLY VERIFIED: corpus composition |
| 7 | lynote-ai/humanize-text | `51eb2bb` | MIT | VERIFIED FACT: 4-hop LLM+translation rewrite pipeline (zh→ja→fi→en) |
| 8 | TencentCloud/Octop | `ae65fe4` | MIT | VERIFIED FACT: self-hosted multi-user multi-agent assistant platform (single-process control plane, MCP/OAuth connectors, ACP) |
| 9 | danny-avila/LibreChat | `12d7890` | MIT | VERIFIED FACT: multi-provider chat platform (api/client/docker surfaces) |
| 10 | zjwzcx/Awesome-Astra-Embodied-AI | `6777fc8` | none (rights-unspecified) | VERIFIED FACT: README+assets catalog of embodied-AI demos; no executable code |

## 2. What P2P already had (duplication gate results)

Before any addition, the existing surfaces were searched: capability ledger
(176 capabilities), skill catalog, MCP surfaces, evaluation machinery,
research ledgers.

- **Worktree/session isolation** — already SHIPPED (RA-EXT-011 Orca; C17 DONE; FW06 lease).
- **Typed execution/evidence states, routing, control tower, doctor** — `.p2p/system/p2p_capabilities/task_state.py`, `evidence.py`, `orchestration_policy.py`, `control_tower_handoff.py`, `scripts/doctor.py`.
- **Long-term project memory boundaries** — DURABLE_PROJECT_INTELLIGENCE family (12 capabilities).
- **Host/executor discovery & selection** — HOST_CAPABILITY_DISCOVERY, HOST_SELECTION, HOST_EXECUTOR_NEUTRALITY, MINIMUM_SUFFICIENT_HOST in the capability ledger.
- **Deterministic-first evaluation & release separation** — `eval_registry.json` (p2p-eval-registry/1), PROJECT_EVALS / RELEASE_ACCEPTANCE / REGRESSION_CLASSIFICATION, `governance/release-gates.schema.json`, GOAL_PASS_NOT_PROMOTION (AUTO_PROMOTION_AFTER_GOAL_PASS is REJECTED in the capability ledger).
- **MCP external-tool path** — `.agents/skills/mcp-management` (`.claude/.mcp.json` server config).
- **UI taste coverage vs make-interfaces-feel-better** — optical alignment, tabular numerals, 44px touch targets, empty-state composition, icon stroke standardization already present across redesign/stitch/minimalist/brutalist skills.

## 3. The one real gap and the assimilated delta

Gap analysis found these mechanics absent or materially weaker in the P2P UI
surfaces: interruptible-motion discipline; explicit transition-property
discipline for interactive states; frequency-based motion restraint with a
mandatory static cue; concentric border-radius formula; hit-area audit for the
redesign route; icon-stroke-to-text-weight matching; 10%-speed motion
inspection; systematic hover/focus/active/loading/empty state walk; an
evidence-shaped polish review output format.

**Implemented (EXTEND_EXISTING_P2P):** an `Interaction Polish Gate` section in
the existing `UI-taste-skill/skills/redesign-skill/SKILL.md` (the existing
polish surface), kept byte-identical across `.agents/skills`,
`.claude/skills`, and `.p2p/system/.agents/skills` projection copies. Upstream
constants are framed as defaults/heuristics, not universal laws; no parallel
skill, router, or styling system was created. The existing press-scale
guidance was harmonized to a 0.96–0.98 band (never below 0.95).

## 4. Dispositions of the other nine repositories

- **pgbot → DEFERRED external-tool candidate.** Recorded with activation
  conditions: register through the existing mcp-management MCP path only when
  a P2P-managed project actually uses PostgreSQL; read-only role; no
  PostgreSQL infrastructure added now (no P2P project currently uses it).
- **oh-my-hermes → DEFERRED, no adoption.** Duplication mapping in section 2;
  per-model calibration conflicts with P2P executor neutrality; no bounded
  gap justifies new code in this goal.
- **fx → DEFERRED architecture reference.** Future optional ACP-capable host
  only, and only through the existing HOST_* surfaces under a separate goal;
  upstream is experimental.
- **gpt-instruct → REJECTED for implementation.** Covered by existing P2P
  evaluation machinery (section 2). Owner Codex instructions and prompt files
  were NOT touched, per task boundary.
- **lieflat-less-ai-tone → DEFERRED research decision.** Methodology value
  only (corpus contrast, whitelist-only rewriting, operator-hit inspection);
  no Chinese regexes ported; no Vietnamese humanizer created.
- **humanize-text → REJECTED.** Multi-hop translation drift (semantic,
  terminology, citation) is incompatible with precision-sensitive P2P writing
  paths.
- **Octop → REJECTED for integration.** Second orchestration platform is a
  registered rejected pattern; observed primitives already represented
  natively.
- **LibreChat → REJECTED for integration.** UI/control-plane reference only;
  no bounded P2P gap; no runtime duplication for UI.
- **Awesome-Astra-Embodied-AI → RESEARCHED radar source.** Catalog with no
  executable code; no LICENSE file (rights-unspecified: cite, do not copy);
  individual demos are not proof of generalized capability.

## 5. Verification

- `python3 -m pytest tests/test_p2p_external_capability_assimilation_01.py` —
  focused deterministic checks: assimilated content present in all three
  skill copies; copies byte-identical; ledger records RA-EXT-072..081 unique,
  vocabulary-valid, provenance-complete; upstream attribution preserved.
  Result: PASS.
- `python3 -m json.tool governance/research-adoption-ledger.json` — valid
  JSON, 81 records, no duplicate research_id, all statuses inside the
  ledger's own status vocabulary.
- `scripts/check_instruction_contract.py` — unchanged thin-entrypoint/manifest
  contract still satisfied (skill change touches no governed phrase).
- Skill diff scope: only `redesign-skill/SKILL.md` (plus its two projection
  copies); router table, other sub-skills, and all other skills untouched.
- Skill manifests (`.agents`, `.claude`, `.p2p/system` copies): the per-file
  hash of `skills/redesign-skill/SKILL.md` was recalculated (sha256 of file
  bytes, the verified per-file scheme) and updated in all three manifests,
  one line each. The aggregate skill-level `hash` field was left untouched:
  its derivation is not reproducible from this repository (generated by an
  external tool), and inventing a value would violate evidence discipline.
  No P2P runtime or test verifies that aggregate field (existence checks only).
- External-tool bindings: none created; no MCP server registered; no
  destructive/write operation executed against any external system during
  assessment (read-only clones and source reads).

## 6. Unverified / open

- pgbot runtime behavior (would require a live PostgreSQL instance;
  deliberately out of scope).
- fx executable behavior (no binary executed; assessment from source/docs).
- lieflat corpus composition (upstream-stated limit, recorded as such).
- Whether a future Vietnamese writing-quality capability is ever justified —
  requires its own corpus, goal, and Owner selection.
- The aggregate skill-level manifest hash (externally generated, scheme not
  reproducible in-repo) was not recomputed; see section 5.
- Pre-existing on main, NOT caused by this change:
  `scripts/check_instruction_contract.py` reports missing phrases in
  `docs/p2p-development/P2P-AGENTS-INSTALL.md` (verified identical failure on
  unmodified main via stash round-trip). Left untouched: out of this goal's
  change boundary.

## 7. Provenance (section-9 compliance)

| Assimilated mechanism | UPSTREAM_REPO | UPSTREAM_COMMIT_OBSERVED | UPSTREAM_LICENSE | SOURCE_FILES_EXAMINED | P2P_TARGET_SURFACE | COPY_OR_ADAPTATION_STATUS |
| --- | --- | --- | --- | --- | --- | --- |
| Interaction-polish mechanics + review format | jakubkrehel/make-interfaces-feel-better | 35545ea1512ad59fa463e6b1f95ca9c052981fe6 | MIT (c) 2026 Jakub Krehel | skills/make-interfaces-feel-better/SKILL.md, animations.md, surfaces.md, typography.md, icons.md, performance.md | .agents/skills/UI-taste-skill/skills/redesign-skill/SKILL.md (+ synced projections) | CONCEPT_ADAPTED_NOT_VENDORED (attribution note embedded in the skill file) |

No other repository contributed code or text to P2P; their dispositions are
recorded in `governance/research-adoption-ledger.json` RA-EXT-073..081.
