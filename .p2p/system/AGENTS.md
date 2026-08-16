<!-- anvien:start -->
# Master iron rules
**Temporary directories created by AI — such as .tmp\ or similar — must be located inside the working repo. Creating temporary directories directly on the C: drive is strictly prohibited.**

**When the user asks to "write/create a plan", the AI agent must immediately use the planner skill and create a real docs/plans plan.**

# AGENTS Rules
0. Anvien is a code-intelligence tool — a broad command system that allows an agent, inside a huge repository, to do almost everything needed for repo work: build graph maps -> identify the right problem -> find the right file/symbol -> verify the right flow -> measure impact scope -> refactor safely -> check API contracts -> audit health, all quickly and accurately.
   - MCP tools are Anvien commands exposed to AI agents.
   - CLI commands are Anvien commands exposed through the terminal.
   - Web/API commands are Anvien runtime commands exposed through the local server.
   - Anvien commands are selected by task. Use the full command set when it gives better evidence.
   - Skills are instruments used with Anvien. Anvien serves the work of other repos/projects.
1. How to use Anvien: run command "anvien --help".
2. As each task is completed, update the corresponding checklist item immediately.
3. Anvien Blast-radius **CRITICAL/HIGH** is only a scope warning that the work must be handled carefully; it is **not** a prohibition against editing code.
4. When SPEC context is required, use `SPEC-MAP.md` as the reading order and read the full relevant SPEC cluster; do not rely on keyword search or partial snippets before concluding, planning, or editing.
5. **Write plan (use planner skill) before coding.**
6. **Code first**; tests should only be updated after the behavior has been correctly implemented in code.
7. Playwright scripts must be reusable under `playwright/`, not one-off temp files; official QA evidence must go to `Reports/qa/playwright/...` as both `.json` and `.md`, while `.tmp` is debug-only.
8. Run a full build before validation.
   - For non-UI changes, validate the changed behavior or contract at its nearest real boundary, record what each command proves, and do not count unrelated, stale, broken, or pass-by-default tests as evidence.
   - For UI behavior changes, open the real user-visible runtime first: the web app in the user's browser or the desktop app on the user's PC. Then record browser or Playwright evidence for the changed behavior.
9. Record benchmark results as each benchmarkable task is completed. Benchmarkable means measured product/runtime performance, capacity, package/startup size, graph/DB throughput, or graph inventory counts; build/test/e2e timings are validation evidence unless the slice changes those systems.
10. Record evidence as each evidenced task is completed.
11. For "doc commits" only, do not use Anvien. When write/edit "doc plan" must use Anvien.
12. After each completed implementation slice, commit the work, then continue until the full plan is complete.

# Anvien - Code Intelligence

Anvien is repo-agnostic: the same command surface works for any indexed repository. Use a repository name/path from `anvien list`, wherever examples refer to `<repo>`.

> If any Anvien command or MCP tool warns that the index is stale, run `anvien analyze --force` from the repository root first.

## Always Do

- **MUST refresh the graph before graph-based work.** Run `anvien analyze --force` before using any Anvien CLI command, MCP tool, MCP resource, Web/API view, or accuracy/benchmark command that reads, queries, validates, mutates, or reports on the semantic graph. This includes `file-detail`, `query`, `context`, `impact`, `detect-changes`, `cypher`, `rename`, `file-hotspots`, MCP `route_map`/`tool_map`/`shape_check`/`api_impact`, CLI `api route-map`/`api tool-map`/`api shape-check`/`api impact`, `augment`, `graph-health`, `query-health`, `resolution-inventory`, `source-site-accuracy`, and `benchmark-compare`.
- **MUST run `file-detail` + impact analysis before editing any function, class, method, exported symbol, API handler, graph builder, resolver, analyzer, or shared contract.**
- **MUST report blast radius.** HIGH or CRITICAL impact means warn clearly and proceed carefully; it is not an automatic ban on editing.
- **MUST run change detection before committing implementation work.** Use MCP `detect_changes` or CLI `anvien detect-changes --repo <repo> --scope all`.
- When exploring unfamiliar code, start with the Anvien command that matches the task instead of defaulting to grep.
- When a command has important flags, check `anvien <command> --help`.

## Never Do

- NEVER edit generated `AGENTS.md` / `CLAUDE.md` content as the permanent source of truth. Update the generator that writes these files, then regenerate.
- NEVER edit a function, class, or method without first running `impact` on it.
- NEVER ignore HIGH or CRITICAL impact warnings; explain them and keep the change scoped.
- NEVER rename symbols with find-and-replace; use graph-guided rename when available.
- NEVER commit implementation changes without running change detection.
- NEVER reduce graph evidence just to make output smaller; preserve counts, samples, meaning, and traceability.

## Command Selection Guide

Use Anvien by task, not by a fixed workflow. Pick the command surface that matches the job.

| When you need to... | Use |
|---------------------|-----|
| Refresh or rebuild graph evidence | `anvien analyze --force` |
| Analyze a specific local repository path | `anvien analyze <path> --force` |
| Analyze with embeddings enabled | `anvien analyze --embeddings` |
| Record analyze performance/capacity metrics | `anvien analyze --benchmark-json <file>` |
| Check whether the index is current | `anvien status` |
| See indexed repositories and repo names | MCP `list_repos` or CLI `anvien list` |
| Register an existing local index folder | `anvien index [path...]` |
| Delete current repo index | `anvien clean --force` |
| Delete all indexed repo data | `anvien clean --all --force` |
| Find where a concept, behavior, or bug lives | MCP `query` or CLI `anvien query "<concept>" --repo <repo>` |
| Find files relevant to a concept | CLI `anvien query files "<concept>" --repo <repo>` or MCP `query` with `target_type=files` |
| Inspect one symbol deeply | MCP `context` or CLI `anvien context symbol "<symbol>" --repo <repo>` |
| Read detailed information about a file and its relationships with other files. | Prefer CLI `anvien file-detail <path> --repo <repo> --json`; use `anvien context file <path> --repo <repo>` only when you want the context wrapper / human-oriented view |
| Ask structured graph questions | MCP `cypher` or CLI `anvien cypher "<query>" --repo <repo>` |
| Inspect API route handlers, consumers, and linked flows | MCP `route_map` or CLI `anvien api route-map [route] --repo <repo>` |
| Inspect tool handlers and tool-related graph paths | MCP `tool_map` or CLI `anvien api tool-map [tool] --repo <repo>` |
| Check API response shape drift against consumers | MCP `shape_check` or CLI `anvien api shape-check [route] --repo <repo>` |
| Check route/API impact before changing handlers or contracts | MCP `api_impact` or CLI `anvien api impact [route] --repo <repo>` |
| Add graph context to a text search pattern | `anvien augment "<pattern>"` |
| Check symbol blast radius before editing | MCP `impact` or CLI `anvien impact symbol "<symbol>" --repo <repo> --direction upstream` |
| Check file-level blast radius before editing a file | CLI `anvien impact file <path> --repo <repo> --direction upstream` |
| Check changed symbols, files, and affected flows before commit | MCP `detect_changes` or CLI `anvien detect-changes --repo <repo> --scope all`; use `detect-changes files` for grouped file risk |
| Rename a symbol safely | MCP `rename` or CLI `anvien rename <symbol> <newName> --repo <repo>` |
| Audit topology health, diagnostics, and components | `anvien graph-health summary --repo <repo> --json` |
| Explain graph-health for one node | `anvien graph-health explain "File:<path>" --repo <repo> --json` |
| Audit file-level graph health | `anvien graph-health files --repo <repo> --json` or `anvien file-hotspots --repo <repo> --json` |
| Audit query retrieval quality | `anvien query-health --repo <repo>` |
| Audit source-site and resolved-edge accuracy | `anvien source-site-accuracy --graph .anvien/graph.json` |
| Inspect unresolved references / ResolutionGap inventory | `anvien resolution-inventory --graph .anvien/graph.json` |
| Compare analyze benchmark outputs | `anvien benchmark-compare <before> <after>` |
| Start local Web/API runtime | `anvien serve --host 127.0.0.1 --port <port>` |
| Start the MCP server for agents | `anvien mcp` |
| Configure editor/agent integrations | `anvien setup` |
| Inspect local runtime locks and processes | `anvien doctor locks --repo <repo> --json` or `anvien doctor processes --json` |
| Print Anvien version | `anvien version` |
| Generate shell completion scripts | `anvien completion <shell>` |
| Run Claude Code hook integration (hidden lifecycle helper) | `anvien hook claude` |
| Create a repository group | MCP `group_list` for discovery or CLI `anvien group create <name>` |
| Add an indexed repo to a group | `anvien group add <group> <groupPath> <registryName>` |
| Remove repo from a group | `anvien group remove <group> <path>` |
| List or inspect groups | MCP `group_list` or CLI `anvien group list [name]` |
| Check staleness across group repos | MCP `group_status` or CLI `anvien group status <name>` |
| Sync contract registry from indexed group repos | MCP `group_sync` or CLI `anvien group sync <name>` |
| Search execution flows across group repos | MCP `group_query` or CLI `anvien group query <name> "<query>"` |
| Inspect group contract registry | MCP `group_contracts` or CLI `anvien group contracts <name>` |
| Build packaged runtime binary (hidden lifecycle helper) | `anvien package build-runtime` |
| Prepare Go source for package fallback builds (hidden lifecycle helper) | `anvien package prepare-go-source` |
| Verify packaged runtime for this platform (hidden lifecycle helper) | `anvien package ensure-runtime` |
| Remove temporary package source output (hidden lifecycle helper) | `anvien package clean-go-source` |
| Show wiki capability status | `anvien wiki` |
| Show or set wiki capability mode | `anvien wiki-mode [off|local]` |
| Check exact syntax and flags | `anvien <command> --help` |

## Resources

| Resource | Use for |
|----------|---------|
| `anvien://repos` | All indexed repositories |
| `anvien://setup` | MCP setup and tool reference |
| `anvien://repo/<repo>/context` | Codebase overview and index freshness |
| `anvien://repo/<repo>/clusters` | Functional areas / communities |
| `anvien://repo/<repo>/processes` | Execution flows |
| `anvien://repo/<repo>/schema` | Graph schema for Cypher |
| `anvien://repo/<repo>/cluster/{name}` | Functional area details |
| `anvien://repo/<repo>/process/{name}` | Step-by-step execution trace |

## MCP Prompts

| Prompt | Use |
|--------|-----|
| `detect_impact` | Pre-commit impact workflow using `detect_changes`, `context`, and `impact`; HIGH/CRITICAL are blast-radius warnings, not edit bans. |
| `generate_map` | Evidence-backed architecture map workflow; resolves the repo through `anvien://repos` when needed and uses only resources/tools/command output actually read. |

MCP prompts are agent templates, not CLI commands. They guide tool/resource use and must still follow repository rules for freshness, impact-before-edit, and detect-changes before commit.

## Skill Selection Guide

AI agent chooses the skill that fits the work.

| When you need to... | Use |
|---------------------|-----|
| use when user ask to review spec | `.agents/skills/Architect-review/SKILL.md` |
| Data integrity specialist for schema correctness, owner isolation, projections, hash chains, log separation, snapshots, and replay consistency. Use when validating that data remains correct under sync and persistence rules. | `.agents/skills/Data-Integrity/SKILL.md` |
| Edge-case specialist for reconnects, race conditions, duplicate or out-of-order events, stale state, permission bypasses, and fail-closed behavior. Use when trying to break the system under hostile or weird conditions. | `.agents/skills/Edge-Case/SKILL.md` |
| Chuyển spec sản phẩm, tính năng, UI, backend, auth, sync, lifecycle, external contract, hoặc spec đa nhánh thành SVG flow map ngữ nghĩa có metadata máy đọc được, source coverage, render từng flow, gap detection, verification report, và trạng thái BLOCKED hoặc READY_FOR_OWNER_REVIEW. Dùng khi cần biến spec thành flow map, audit độ đầy đủ của spec trước khi code, so sánh với diagram tham chiếu, phơi bày hành vi chưa định nghĩa, hoặc xác định quyết định Owner trước implementation. | `.agents/skills/Spec-to-SVG-Flow-Map/SKILL.md` |
| Software architecture specialist for system design, scalability, and technical decision-making. Use PROACTIVELY when planning new features, refactoring large systems, or making architectural decisions. | `.agents/skills/System-Architect/SKILL.md` |
| Dùng khi user hỏi về UI animation, motion design, gesture, transition, animation review, polish UI, hoặc cải thiện cảm giác chuyển động của app. | `.agents/skills/UI-animation-design/SKILL.md` |
| Sử dụng khi cần nâng cấp UI UI hiện có, làm UI bớt generic, bớt AI slop, frontend premium, redesign, image-to-code, imagegen web/mobile, brandkit, style variants và full-output. | `.agents/skills/UI-taste-skill/SKILL.md` |
| Use when the user asks to inspect API or MCP surfaces. | `.agents/skills/api-surface/SKILL.md` |
| Use when the user asks to build or change backend code. | `.agents/skills/backend-development/SKILL.md` |
| Use when the user asks to implement Better Auth. | `.agents/skills/better-auth/SKILL.md` |
| Use when the user asks to integrate Bunny.net. | `.agents/skills/bunny/SKILL.md` |
| Use when the task is to implement code changes from an assigned scope, including bug fixes, follow-ups, rejects, or current-worktree repair. | `.agents/skills/coder/SKILL.md` |
| Use when creating, changing, or reviewing MongoDB/PostgreSQL database work in a real repository, including schema, models, migrations, queries, indexes, transactions, connection config, backup/restore assumptions, or performance; follow repo-native tooling and meet the production database bar unless the user explicitly asks for a prototype. | `.agents/skills/databases/SKILL.md` |
| Use when the user asks to debug. | `.agents/skills/debugging/SKILL.md` |
| Use when the user asks to deploy or operate infrastructure. | `.agents/skills/devops/SKILL.md` |
| Use when the user asks to find current technical documentation. | `.agents/skills/docs-seeker/SKILL.md` |
| Use when the user asks to create, edit, or analyze documents. | `.agents/skills/document-skills/docx/SKILL.md` |
| Use when the user asks to design a frontend UI. | `.agents/skills/frontend-design/SKILL.md` |
| Use when the user asks to build or change frontend code. | `.agents/skills/frontend-development/SKILL.md` |
| Use when the user asks to build an MCP server. | `.agents/skills/mcp-builder/SKILL.md` |
| Use when the user asks to manage MCP integrations. | `.agents/skills/mcp-management/SKILL.md` |
| Use when the user asks to process media files. | `.agents/skills/media-processing/SKILL.md` |
| Use when the user asks to create Mermaid diagrams. | `.agents/skills/mermaidjs-v11/SKILL.md` |
| Use for payments, subscriptions, webhooks, refunds, entitlements, or multi-provider orders with SePay, Polar, Stripe, Paddle, or Creem. | `.agents/skills/payment-integration/SKILL.md` |
| Use when the user asks to create, write, or review a docs/plans plan. | `.agents/skills/planner/SKILL.md` |
| Use when creating, reviewing, or troubleshooting Claude Code plugin marketplaces, marketplace.json files, plugin sources, hosting, team allowlists, or install/update failures. | `.agents/skills/plugin-marketplace/SKILL.md` |
| Use when the user asks to solve a hard problem. | `.agents/skills/problem-solving/problem-solving-parent-skill/SKILL.md` |
| Use when the user asks to run QA without fixing code, including mounted runtime behavior, visible user flows, browser-visible app execution, source-of-truth checks, action/state coverage, route/control inventories, Playwright control sweeps, or QA report generation in repositories where Anvien can support | `.agents/skills/qa/SKILL.md` |
| Use when the user asks to refactor code. | `.agents/skills/refactoring/SKILL.md` |
| Use when the user asks to bootstrap a new repo or project. | `.agents/skills/repo-bootstrap/SKILL.md` |
| Use when the user asks to reason step by step. | `.agents/skills/sequential-thinking/SKILL.md` |
| Use when the user asks to build Shopify apps, themes, or extensions. | `.agents/skills/shopify/SKILL.md` |
| Use when the user asks to create or update a skill. | `.agents/skills/skill-creator/SKILL.md` |
| Thảo luận kiến trúc dựa trên SPEC bằng cách đọc tuần tự và đọc hết từng file SPEC trước khi kết luận; trả lại bản nắm bắt kiến trúc gồm invariant, boundary, pipeline, luồng dữ liệu, liên kết thật giữa pipeline, điểm chưa rõ, và câu hỏi thảo luận. Dùng khi user yêu cầu thảo luận kiến trúc, thảo luận về mức độ kiến trúc, bóc tách kiến trúc từ SPEC, hoặc tranh luận một vấn đề kiến trúc dựa trên bộ SPEC. Không dùng để tự cập nhật SPEC, viết code, hoặc review acceptance. | `.agents/skills/spec-architecture-discussion/SKILL.md` |
| Use whenever reviewing completion claims, fixes, diffs, reports, screenshots, or artifacts for acceptance; verify repo/project reality with Anvien evidence. Always use this skill before accepting any agent output, closing any task, or merging any result. | `.agents/skills/supervisor/SKILL.md` |
| Use when the user asks to build 3D web experiences with Three.js. | `.agents/skills/threejs/SKILL.md` |
| Use when binding backend/API data into an already-approved frontend UI without changing approved layout, copy, visual design, component hierarchy, or interaction states. | `.agents/skills/ui-be-binding-skill/SKILL.md` |
| Workflow phát triển phần mềm UI-first cho AI agent. Dùng skill này khi người dùng muốn: xây app mới theo hướng UI trước BE, extract spec từ prototype đã có, chuẩn bị handoff BE implementation từ FE đã code, hoặc nói các cụm như "làm UI trước", "prototype rồi mới spec", "UI-driven", "FE trước BE", "extract contract từ UI", "slot map", "state map", "backend contract map", "chuyển giao kiến trúc sư duyệt". Trigger khi user có HTML prototype hoặc FE components và cần chuyển sang BE. Đây là flow ngược truyền thống — UI là bản đồ thao tác, Spec là luật tối cao, human phải duyệt trước khi implement. | `.agents/skills/ui-driven-spec/SKILL.md` |
| Use when the user asks to style UI. | `.agents/skills/ui-styling/SKILL.md` |
| Use when the user asks to build with Next.js, Turborepo, or web frameworks. | `.agents/skills/web-frameworks/SKILL.md` |

<!-- anvien:end -->
