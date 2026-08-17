# Phase 2 — Hermes Interface Probe (ACTUAL observed/verified contract)

## Source: official docs (observed 2026-08-17)
- CLI commands reference: https://hermes-agent.nousresearch.com/docs/reference/cli-commands
- CLI user guide: https://hermes-agent.nousresearch.com/docs/user-guide/cli
- Releases: https://github.com/NousResearch/hermes-agent/releases → v0.20.2 (v2026.8.16), Aug 16 2026, MIT License, GitHub repo NousResearch/hermes-agent

## Verified interface facts (from docs)
- Entry point: `hermes [global-options] <command>`
- Version: `hermes --version` / `-V`; `hermes version`; `hermes update --check` (preview without install)
- One-shot headless (scripted): **`hermes -z "<prompt>"`** — purest programmatic entry: single prompt in, final response text out; nothing else on stdout/stderr; no banner/spinner. Supports -m/--model, --provider, --usage-file <path> (JSON usage report written after run; env HERMES_INFERENCE_MODEL).
- One-shot chat: `hermes chat -q "<prompt>"` (non-interactive); options: --model, --provider, --toolsets <csv>, --quiet/-Q (suppress banner/spinner/tool previews), --source <tag> (use `tool` for third-party integrations), --max-turns <N>, --ignore-user-config, --ignore-rules, --safe-mode, --worktree, --checkpoints, --yolo, --in <dir> (change cwd before starting), --continue, --resume.
- Providers supported: auto, openrouter, nous, openai-codex, copilot-acp, copilot, anthropic, gemini, huggingface, novita, openai-api, zai, kimi-coding..., deepseek, nvidia, ollama-cloud, xai (alias grok)... etc.
- `hermes setup --portal` for Nous Portal onboarding; `hermes model` interactive model pick.
- `hermes -z` writes a JSON usage report via `--usage-file <path>` (USAGE_EVIDENCE surface).
- Cancellation: Ctrl+C interrupt agent (double-press force exit).
- Sessions: `hermes sessions`, --resume/--continue.
- `hermes doctor`, `hermes status` for health/availability probing.
- Hermes runs terminal commands via `terminal` tool; approval prompts unless --yolo (P2P must NOT use --yolo).
- Status bar shows model, tokens, cost, duration.

## Spec-required P2P constraints
- P2P must NOT use --yolo (dangerously-skip-permissions bypass), no cron, no daemon, no background autonomy (/background), no silent provider switching. Foreground only.
- Transcript never P2P state.

## Plan for real probe (no provider auth available)
1. Install hermes (npm global `hermes` or uvx/pip) — check available.
2. Run `hermes --version`, `hermes --help`, `hermes -z "print the text"` — expect AUTH_REQUIRED failure → classifies as ADAPTER_VALIDATED_AUTH_BLOCKED.
3. Adapter must still produce normalized receipt with error_class=AUTH_REQUIRED.

## ACTUAL probe results on this sandbox (2026-08-17, no user credentials supplied)
- Installed `hermes-agent` npm global → `Hermes Agent v0.20.2 (2026.8.16)`, Python 3.11.15 runtime. Confirms spec version v0.20.2 exists.
- Default config on fresh install: Provider "Custom endpoint", no .env, no model. `hermes -z "..."` (default) → `HTTP 403: { "success": false, "error": "Access denied by security policy." }` — a real, observable failure path (default endpoint unreachable without credentials).
- `hermes -z ... --provider anthropic --model claude-sonnet-4-20250514` with NO credentials → `hermes -z: agent failed: No Anthropic credentials found. Set ANTHROPIC_TOKEN ...` → authentic AUTH_REQUIRED error path (exit 0, error on stderr).
- Same with a fake ANTHROPIC_API_KEY → `HTTP 403: Request not allowed` → AUTH_INVALID path.
- `--provider openai-api --model gpt-4.1-mini` (no key) → `API call failed after 3 retries: Codex Responses stream did not emit a terminal response` (default custom endpoint tried).
- `--usage-file <path>` writes a JSON usage report even on failure (tokens null, cost null) — real USAGE_EVIDENCE surface.
- `hermes sessions list` returns structured table with session_id (e.g. `20260817_100302_6f31e9`), title, workspace, last active — real session registry observable from CLI.
- `hermes chat -q ... --quiet` produces `session_id: <id>` line + response (AUTH error here too).
- `-z` requires exact one-shot semantics; `hermes -z` alone errors (no interactive fallback) — deterministic programmatic entry point confirmed.
- No user credentials provided → Hermes adapter = ADAPTER_IMPLEMENTED + ADAPTER_TESTED, auth state AUTH_REQUIRED → overall classification ADAPTER_VALIDATED_AUTH_BLOCKED. No LIVE_VALIDATED (expected, honest).
- P2P constraints observed: --yolo exists but P2P adapter will NEVER pass it. No cron/daemon invocation.
