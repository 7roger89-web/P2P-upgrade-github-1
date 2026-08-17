<!-- RESEARCH_ONLY / NON_CANONICAL / PROPOSAL / NOT_IMPLEMENTATION / NOT_PROMOTED -->

# Hermes Agent source provenance (C32 research artifact)

The official Hermes Agent repository was cloned into the isolated research area `/home/ubuntu/c32_research/hermes`, outside any P2P canonical runtime or source surface. No code was vendored into P2P and nothing will be copied into the P2P repository during this Goal.

| Attribute | Value |
| --- | --- |
| Upstream URL | https://github.com/nousresearch/hermes-agent |
| Tag inspected | `v2026.8.16` (release v0.20.2, commit message "chore: release v0.20.2 (2026.8.16)") |
| Tag commit SHA | `df4b65147d7ddd74dd449f9067aabbca5aef0ec7` |
| Tag date | 2026-08-16T17:24:30Z |
| Repository HEAD at retrieval | `8f97ae9aec729bcb` (2026-08-17T07:27:26Z), default branch `main` |
| Retrieval timestamp | 2026-08-17T07:41Z (sandbox GMT+7 / UTC) |
| License | MIT License, Copyright (c) 2025 Nous Research (`LICENSE` file, MIT) |
| Retrieval method | GitHub API tarball (clone over Git transport was rate-limited at 429; tarball download succeeded with user-supplied PAT) |
| Repo size | ~665 MB (repo stats); extracted tree ~ several thousand files |

License considerations recorded: MIT permits reading, pattern adoption, and even vendoring, but this Goal deliberately restricts itself to pattern/architecture observations (no code copying), so the reuse question is governed by P2P's own policy rather than license constraints. Dependencies of Hermes itself (Python/Node ecosystem packages, e.g. Anthropic/OpenAI SDKs, Playwright for browser tools, optional MCP servers) are runtime dependencies only and do not affect P2P's canonical surfaces during research-only work.
