# Code-intelligence provider policy

`ANVIEN_ENABLED=NO` and `ANVIEN_REQUIRED=NO` by current Owner direction.

- Do not install, configure, invoke, index with, refresh, or require Anvien for normal P2P work.
- Anvien unavailability is never a task blocker and must not trigger an Owner relay loop.
- Any lower-level skill, template, generated block, historical plan, or report that says Anvien is mandatory is superseded for current execution by this policy.
- Use the smallest provider-neutral evidence that proves the claim: direct source inspection, Git diff/history, targeted text or AST/static analysis when useful, focused tests, runtime/log/data evidence, and contract/schema checks.
- Keep verification risk-proportional. Do not recreate Anvien as a new graph service, index, daemon, router, registry, or mandatory preflight.
- Historical Anvien evidence may remain as historical evidence; it is not a current execution requirement.

<!-- anvien:start -->
# Legacy generated skill catalog

`ANVIEN_ENABLED=NO`. The Anvien command catalog is intentionally disabled. Keep only the skill-selection catalog below; provider-neutral source/Git/test/runtime evidence is the default.

## Skill Selection Guide

AI agent chooses the skill that fits the work.

| When you need to... | Use |
|---------------------|-----|
| use when user ask to review spec | `.claude/skills/Architect-review/SKILL.md` |
| Data integrity specialist for schema correctness, owner isolation, projections, hash chains, log separation, snapshots, and replay consistency. Use when validating that data remains correct under sync and persistence rules. | `.claude/skills/Data-Integrity/SKILL.md` |
| Edge-case specialist for reconnects, race conditions, duplicate or out-of-order events, stale state, permission bypasses, and fail-closed behavior. Use when trying to break the system under hostile or weird conditions. | `.claude/skills/Edge-Case/SKILL.md` |
| Chuyển spec sản phẩm, tính năng, UI, backend, auth, sync, lifecycle, external contract, hoặc spec đa nhánh thành SVG flow map ngữ nghĩa có metadata máy đọc được, source coverage, render từng flow, gap detection, verification report, và trạng thái BLOCKED hoặc READY_FOR_OWNER_REVIEW. Dùng khi cần biến spec thành flow map, audit độ đầy đủ của spec trước khi code, so sánh với diagram tham chiếu, phơi bày hành vi chưa định nghĩa, hoặc xác định quyết định Owner trước implementation. | `.claude/skills/Spec-to-SVG-Flow-Map/SKILL.md` |
| Software architecture specialist for system design, scalability, and technical decision-making. Use PROACTIVELY when planning new features, refactoring large systems, or making architectural decisions. | `.claude/skills/System-Architect/SKILL.md` |
| Dùng khi user hỏi về UI animation, motion design, gesture, transition, animation review, polish UI, hoặc cải thiện cảm giác chuyển động của app. | `.claude/skills/UI-animation-design/SKILL.md` |
| Sử dụng khi cần nâng cấp UI UI hiện có, làm UI bớt generic, bớt AI slop, frontend premium, redesign, image-to-code, imagegen web/mobile, brandkit, style variants và full-output. | `.claude/skills/UI-taste-skill/SKILL.md` |
| Use when the user asks to inspect API or MCP surfaces. | `.claude/skills/api-surface/SKILL.md` |
| Use when the user asks to build or change backend code. | `.claude/skills/backend-development/SKILL.md` |
| Use when the user asks to implement Better Auth. | `.claude/skills/better-auth/SKILL.md` |
| Use when the user asks to integrate Bunny.net. | `.claude/skills/bunny/SKILL.md` |
| Use when the task is to implement code changes from an assigned scope, including bug fixes, follow-ups, rejects, or current-worktree repair. | `.claude/skills/coder/SKILL.md` |
| Use when creating, changing, or reviewing MongoDB/PostgreSQL database work in a real repository, including schema, models, migrations, queries, indexes, transactions, connection config, backup/restore assumptions, or performance; follow repo-native tooling and meet the production database bar unless the user explicitly asks for a prototype. | `.claude/skills/databases/SKILL.md` |
| Use when the user asks to debug. | `.claude/skills/debugging/SKILL.md` |
| Use when the user asks to deploy or operate infrastructure. | `.claude/skills/devops/SKILL.md` |
| Use when the user asks to find current technical documentation. | `.claude/skills/docs-seeker/SKILL.md` |
| Use when the user asks to create, edit, or analyze documents. | `.claude/skills/document-skills/docx/SKILL.md` |
| Use when the user asks to design a frontend UI. | `.claude/skills/frontend-design/SKILL.md` |
| Use when the user asks to build or change frontend code. | `.claude/skills/frontend-development/SKILL.md` |
| Use when the user asks to build an MCP server. | `.claude/skills/mcp-builder/SKILL.md` |
| Use when the user asks to manage MCP integrations. | `.claude/skills/mcp-management/SKILL.md` |
| Use when the user asks to process media files. | `.claude/skills/media-processing/SKILL.md` |
| Use when the user asks to create Mermaid diagrams. | `.claude/skills/mermaidjs-v11/SKILL.md` |
| Use for payments, subscriptions, webhooks, refunds, entitlements, or multi-provider orders with SePay, Polar, Stripe, Paddle, or Creem. | `.claude/skills/payment-integration/SKILL.md` |
| Use when the user asks to create, write, or review a docs/plans plan. | `.claude/skills/planner/SKILL.md` |
| Use when creating, reviewing, or troubleshooting Claude Code plugin marketplaces, marketplace.json files, plugin sources, hosting, team allowlists, or install/update failures. | `.claude/skills/plugin-marketplace/SKILL.md` |
| Use when the user asks to solve a hard problem. | `.claude/skills/problem-solving/problem-solving-parent-skill/SKILL.md` |
| Use when the user asks to run QA without fixing code, including mounted runtime behavior, visible user flows, browser-visible app execution, source-of-truth checks, action/state coverage, route/control inventories, Playwright control sweeps, or QA report generation | `.claude/skills/qa/SKILL.md` |
| Use when the user asks to refactor code. | `.claude/skills/refactoring/SKILL.md` |
| Use when the user asks to bootstrap a new repo or project. | `.claude/skills/repo-bootstrap/SKILL.md` |
| Use when the user asks to reason step by step. | `.claude/skills/sequential-thinking/SKILL.md` |
| Use when the user asks to build Shopify apps, themes, or extensions. | `.claude/skills/shopify/SKILL.md` |
| Use when the user asks to create or update a skill. | `.claude/skills/skill-creator/SKILL.md` |
| Thảo luận kiến trúc dựa trên SPEC bằng cách đọc tuần tự và đọc hết từng file SPEC trước khi kết luận; trả lại bản nắm bắt kiến trúc gồm invariant, boundary, pipeline, luồng dữ liệu, liên kết thật giữa pipeline, điểm chưa rõ, và câu hỏi thảo luận. Dùng khi user yêu cầu thảo luận kiến trúc, thảo luận về mức độ kiến trúc, bóc tách kiến trúc từ SPEC, hoặc tranh luận một vấn đề kiến trúc dựa trên bộ SPEC. Không dùng để tự cập nhật SPEC, viết code, hoặc review acceptance. | `.claude/skills/spec-architecture-discussion/SKILL.md` |
| Use whenever reviewing completion claims, fixes, diffs, reports, screenshots, or artifacts for acceptance; verify repo/project reality with current source, runtime, tests, and relevant evidence. Always use this skill before accepting any agent output, closing any task, or merging any result. | `.claude/skills/supervisor/SKILL.md` |
| Use when the user asks to build 3D web experiences with Three.js. | `.claude/skills/threejs/SKILL.md` |
| Use when binding backend/API data into an already-approved frontend UI without changing approved layout, copy, visual design, component hierarchy, or interaction states. | `.claude/skills/ui-be-binding-skill/SKILL.md` |
| Workflow phát triển phần mềm UI-first cho AI agent. Dùng skill này khi người dùng muốn: xây app mới theo hướng UI trước BE, extract spec từ prototype đã có, chuẩn bị handoff BE implementation từ FE đã code, hoặc nói các cụm như "làm UI trước", "prototype rồi mới spec", "UI-driven", "FE trước BE", "extract contract từ UI", "slot map", "state map", "backend contract map", "chuyển giao kiến trúc sư duyệt". Trigger khi user có HTML prototype hoặc FE components và cần chuyển sang BE. Đây là flow ngược truyền thống — UI là bản đồ thao tác, Spec là luật tối cao, human phải duyệt trước khi implement. | `.claude/skills/ui-driven-spec/SKILL.md` |
| Use when the user asks to style UI. | `.claude/skills/ui-styling/SKILL.md` |
| Use when the user asks to build with Next.js, Turborepo, or web frameworks. | `.claude/skills/web-frameworks/SKILL.md` |

<!-- anvien:end -->
