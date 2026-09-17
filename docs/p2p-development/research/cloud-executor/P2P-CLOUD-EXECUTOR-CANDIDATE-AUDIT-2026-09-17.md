# P2P Cloud Executor — Candidate Audit

**TASK_ID:** `P2P_CLOUD_EXECUTOR_PILOT_01`
**Artifact:** durable candidate audit + pilot disposition
**Audited:** 2026-09-17 (UTC)
**Canonical base:** `7roger89-web/P2P-upgrade-github-1@main` = `a479e62192f6912e037ee0861e45c1799e9461e2`
**Executor:** ARENA (`EXECUTION_MODE=AUTONOMOUS_UNTIL_TERMINAL`)
**Decision law applied:** `REUSE_EXISTING_UPSTREAM > THIN_ADAPTER > FORK > NEW_IMPLEMENTATION`
(AGENTS.md; notebook RULE 17 `UPSTREAM_FIRST_REFERENCE_PRESERVATION`, RULE 19
`REALITY_FIRST_CAPABILITY_PROBE`, RULE 14 `OVER_ENGINEERING_CHECK`)

**Bounded goal audited against:** let regular ChatGPT Web operate a real Git
repository through remote MCP on independent cloud compute, without the Owner's
Windows PC being powered on, without ChatGPT Work, without Codex Cloud, and
without GitHub Actions as execution compute.

Evidence grades used throughout: `DOCUMENTED` (upstream claims it),
`CODE_VERIFIED` (read in upstream source), `EMPIRICALLY_TESTED` (executed in the
Arena pilot), `NOT_VERIFIED` (could not be established in this environment).

---

## 1. Disposition

```text
DISPOSITION=REUSE
SELECTED_UPSTREAM=xyTom/coding-tools-mcp
UPSTREAM_VERSION_OR_COMMIT=PyPI coding-tools-mcp 0.3.0
  (wheel sha256 4d98f4a2cba6f677444986ae395446069e9ecb508861fc903f30a2aa8cefdba3)
  upstream main HEAD audited = bedb632e1afd2e9ec9b268a50fe0b04695c22c64 (2026-09-03)
FORK_REQUIRED=NO
THIN_ADAPTER_REQUIRED=NO
NEW_GATEWAY_BUILT=NO
```

Rejected alternative: `pokapopo/vps-action-gateway` — see §4.

`SELECTION_REASON` (one factual reason): coding-tools-mcp is the only candidate
whose capability surface matches the CatDesk baseline **and** whose
authentication surface can actually be completed by regular ChatGPT Web
(OAuth 2.1 + PKCE S256 + RFC 7591 dynamic client registration, proven end to
end in the pilot), while vps-action-gateway is a host-wide VPS operations
gateway whose OAuth server requires a pre-shared confidential client that
ChatGPT's connector surface cannot present.

No new gateway, daemon, orchestrator, router or control plane was built.
`CloudDesk` is used only as an Owner-facing capability name for the deployment
package; it names a configuration of upstream software, not a new framework.

---

## 2. Provenance

### 2.1 Candidate 1 — `xyTom/coding-tools-mcp`

```text
CANDIDATE_1_PROVENANCE=CANONICAL_UPSTREAM_CONFIRMED
```

| Property | Value | Grade |
| --- | --- | --- |
| Repository | `https://github.com/xyTom/coding-tools-mcp` | EMPIRICALLY_TESTED (GitHub API + clone) |
| `fork` flag | `false`; `parent`/`source` = `null` → not a fork or mirror | EMPIRICALLY_TESTED |
| Published artifacts | PyPI `coding-tools-mcp` 0.3.0 (2026-08-13); npm launcher package | EMPIRICALLY_TESTED (installed from PyPI) |
| License | Apache-2.0 (+ `NOTICE`, `CITATION.cff`, attribution clause in README) | CODE_VERIFIED |
| Created / last push | 2026-05-21 / 2026-09-15 | EMPIRICALLY_TESTED |
| Commits / contributors | 196 commits; 8 distinct author identities (`cf-pages`, `xyTom`, `Cursor Agent`, `Satori-Bot`, `Claude`, `copilot-swe-agent[bot]`, `Coding Tools MCP`, `ytagent`) | EMPIRICALLY_TESTED |
| Community | 1,105 stars, 180 forks, 19 open issues, 1 watcher | EMPIRICALLY_TESTED |
| Docs site | `https://coding-1afcb9be.mintlify.app` | DOCUMENTED |
| CI | 9 workflows: `compliance`, `docker-image`, `docker-smoke`, `final-audit`, `real-workloads`, `release`, `swebench-lite`, `deploy-sandbox-control`, `start-sandbox` | CODE_VERIFIED |
| `make ci` gate chain | lint → typecheck → test → patch-repro → dispatch-inputs → npm-launcher → protocol → integration → docs-required → schema-drift → dogfood → benchmarks | CODE_VERIFIED |
| Release integrity | tag-triggered pipeline; PyPI trusted publishing, npm provenance (upstream claim) | DOCUMENTED |

`CURRENT_MATURITY=BETA_TO_STABLE` — semver 0.3.0 released, 0.5.0 work merged to
`main` but unreleased (`CHANGELOG.md` "Unreleased"), 23 tags, migration guides
for 0.3 and 0.5. `RECENT_ACTIVITY=ACTIVE` (push 2 days before audit).
`MAINTENANCE_SIGNAL=STRONG` (multi-identity commit history, issue-tracked
limitations with named upstream issues #46/#48, compliance suite, benchmarks).

### 2.2 Candidate 2 — `pokapopo/vps-action-gateway`

```text
CANDIDATE_2_PROVENANCE=REPOSITORY_SELF_IDENTIFIED_CANONICAL;
                       REDDIT_SOURCE_LEAD_UNVERIFIED
```

| Property | Value | Grade |
| --- | --- | --- |
| Repository | `https://github.com/pokapopo/vps-action-gateway` | EMPIRICALLY_TESTED |
| `fork` flag | `false`; `parent`/`source` = `null` → not a GitHub fork or mirror | EMPIRICALLY_TESTED |
| Self-declared origin | `package.json` `repository.url` points at itself; `LICENSE` "MIT © 2026 pokapopo"; no upstream attribution anywhere in tree | CODE_VERIFIED |
| Commit authorship | 11 commits, **all** authored `root <root@uuHalo.vps>` (single identity, VPS hostname) | EMPIRICALLY_TESTED |
| Created / last push | 2026-09-07 / 2026-09-13 | EMPIRICALLY_TESTED |
| Community | 5 stars, 0 forks, 0 open issues, 0 watchers, no homepage, no topics | EMPIRICALLY_TESTED |
| License | MIT | CODE_VERIFIED |
| Version | `0.2.0`, `"private": true` (not published to any registry) | CODE_VERIFIED |
| Tests | `npm test` → 50 tests, 50 pass, 0 fail | EMPIRICALLY_TESTED (run in Arena) |
| Dependencies | exactly one runtime dependency (`yaml ^2.9.0`) | CODE_VERIFIED |
| Size | 46 tracked files, 575 KB | EMPIRICALLY_TESTED |

**Provenance caveat, recorded as required.** The task's source lead was a Reddit
`r/mcp` thread titled *"I built an open-source MCP gateway for operating a VPS
from ChatGPT and Claude"*. Fresh search on 2026-09-17 did **not** surface that
thread, and no page in the repository references a Reddit post, author handle, or
announcement URL. The repository is nonetheless self-evidently not a
clone/repost/mirror (no fork lineage, no attribution, self-referential
`repository.url`, single-author history beginning `feat: establish versioned VPS
action gateway` on 2026-09-02).

```text
CANDIDATE_2_PROVENANCE_VERDICT =
  CANONICAL_UPSTREAM_BY_REPOSITORY_EVIDENCE (not a fork/mirror)
  + ANNOUNCEMENT_THREAD_NOT_LOCATED (Reddit lead UNVERIFIED)
```

Comparison below therefore uses only evidence verifiable from the repository
itself, exactly as instructed.

`CURRENT_MATURITY=EARLY_V0.2`. `RECENT_ACTIVITY=RECENT_BUT_THIN` (11 commits over
12 days, nothing since 2026-09-13). `MAINTENANCE_SIGNAL=WEAK` (single identity,
zero community, no published releases, no issue history).

---

## 3. Audit matrix — Candidate 1: `xyTom/coding-tools-mcp`

| Dimension | Finding | Grade |
| --- | --- | --- |
| LICENSE | Apache-2.0, `NOTICE` + attribution clause preserved | CODE_VERIFIED |
| MCP_TRANSPORT | stdio **and** Streamable HTTP on `/mcp`; stateless since 0.3.0 (no `Mcp-Session-Id`; `DELETE /mcp` → 405 `Allow: POST`); protocol eras `2026-07-28`, `2025-11-25`, `2025-06-18` | EMPIRICALLY_TESTED |
| CHATGPT_REMOTE_COMPATIBILITY | OAuth 2.1 + PKCE S256 + RFC 7591 DCR complete flow proven; public-client `token_endpoint_auth_method: none` supported; `registration_endpoint` advertised | EMPIRICALLY_TESTED |
| AUTHENTICATION | bearer **or** OAuth 2.1; `noauth` only for loopback; non-loopback bind without credentials **fails closed at startup** (exit 2) | EMPIRICALLY_TESTED |
| AUTHORIZATION_MODEL | one workspace = one trust domain; no per-client partitioning (upstream issues #46). Authentication admits a client, it does not isolate clients from each other | DOCUMENTED + CODE_VERIFIED |
| WORKSPACE_CONFINEMENT | root canonicalized once at startup; `/` and `$HOME` rejected as unsafe roots (probed: `ToolFailure: Unsafe workspace root rejected.`) | EMPIRICALLY_TESTED |
| PATH_TRAVERSAL_PROTECTION | `..` → `PATH_OUTSIDE_WORKSPACE`; absolute → `ABSOLUTE_PATH_DENIED`; NUL byte → `INVALID_ARGUMENT` | EMPIRICALLY_TESTED |
| SYMLINK_ESCAPE_PROTECTION | read through symlink → `SYMLINK_ESCAPE`; traversal through symlinked dir → `PATH_OUTSIDE_WORKSPACE`; write through symlink → `SYMLINK_ESCAPE`; `resolve_existing`/`resolve_for_write`/`reject_write_symlink` in `server.py` | EMPIRICALLY_TESTED + CODE_VERIFIED |
| FILE_READ | `read_file` with `start_line`/`end_line`/`max_lines`/`max_bytes`, banner carries revision | EMPIRICALLY_TESTED |
| FILE_SEARCH | `search_text` (regex, globs, context lines, result caps), `list_files`, `list_dir`; excludes `.git`, `node_modules`, build outputs, venvs, caches | EMPIRICALLY_TESTED |
| ATOMIC_EDIT | `apply_patch`: staged, baseline-checked, fsynced, atomic replacement; preserves mode bits/BOM/newline style; graded context matching with `match_quality`; `PATCH_CONTEXT_NOT_FOUND` / `PATCH_CONTEXT_AMBIGUOUS` / `PATCH_CONFLICT` / `PATCH_ROLLBACK_FAILED` | EMPIRICALLY_TESTED + DOCUMENTED |
| MULTI_FILE_EDIT | multi-file envelope proven; one bad hunk → whole envelope refused and first file unchanged (rollback proven); `dry_run` proven non-mutating. `apply_changes` (revision-addressed) exists only on unreleased `main`, **not** in 0.3.0 | EMPIRICALLY_TESTED |
| COMMAND_EXECUTION | `exec_command`: workspace-bound cwd (probed `pwd` == workspace root), faithful exit codes (0 and 7), separate stdout/stderr, process-group isolation | EMPIRICALLY_TESTED |
| LONG_RUNNING_JOBS | `yield_time_ms` (schema max **30000**) returns a durable `command_id` + `next_action`; continuation by `write_stdin(chars="")` across separate calls; output increments advance; `kill_command` terminates cleanly (`signal_sent: SIGTERM`, no leftover host process); `timeout_ms` (max 600000) enforced **after** the call returns (`status: timeout`, `exit_code: -15`) | EMPIRICALLY_TESTED |
| PTY_OR_INTERACTIVE_SESSION | real POSIX PTY, `tty=true`; `write_stdin` feeds a REPL across turns; Windows ConPTY not implemented (`TTY_UNSUPPORTED`) | DOCUMENTED + CODE_VERIFIED (not exercised in this pilot) |
| GIT_STATUS | `git_status` structured entries with `index_status`/`worktree_status`, `include_untracked` | EMPIRICALLY_TESTED |
| GIT_DIFF | `git_diff` bounded unified diff + structured `files[]` (`path`/`status`/`binary`), staged/unstaged selectable | EMPIRICALLY_TESTED |
| GIT_LOG | `git_log` structured commits (`commits[]`, `is_repo`, `max_count`, `skip`, `truncated`); `git_show` (`rev`, **not** `ref`), `git_blame` | EMPIRICALLY_TESTED |
| OUTPUT_BOUNDS | `seq 1 200000` → 1.29 MB stream bounded to 13,999 bytes with `truncated_by: lines`, `dropped_bytes: 830143`; head+rolling-tail retention (`head_retained_bytes: 65536`, `total_retained_bytes: 524288`, `evicted_gap_bytes: 764607`) and an explicit eviction warning; `read_output` pages by absolute byte offset with `next_offset` | EMPIRICALLY_TESTED |
| SECRET_REDACTION | `secret_env_filter: enabled`; API keys/tokens, cloud credentials, shell-startup injection vars dropped; upstream states redaction is defense-in-depth, not primary protection | EMPIRICALLY_TESTED (flag) + DOCUMENTED (scope) |
| ENVIRONMENT_SCRUBBING | `LD_PRELOAD`, `LD_LIBRARY_PATH`, `DYLD_*`, `BASH_ENV`, `ENV`, `PYTHONPATH`, `RUBYLIB`, `NODE_OPTIONS` denied/dropped; `HOME`/`TMPDIR`/`cache_dir` relocated under a server-owned runtime dir (probed: `/srv/clouddesk-pilot/runtime/tmp/coding-tools-mcp/<hash>/<id>/...`) | EMPIRICALLY_TESTED + CODE_VERIFIED |
| NETWORK_CONTROL | `safe` mode denies network-looking commands (`PERMISSION_REQUIRED`); `trusted` allows; denial is **policy-based string classification**, not an egress firewall | EMPIRICALLY_TESTED |
| DESTRUCTIVE_COMMAND_CONTROL | destructive-class commands gated in `safe` (`PERMISSION_REQUIRED` proven); `request_permissions` returns `ELICITATION_UNSUPPORTED` outside `dangerous` mode and is advertised only in `dangerous` from 0.5.0 | EMPIRICALLY_TESTED + DOCUMENTED |
| CONTAINER_OR_VM_BOUNDARY | upstream `Dockerfile` (multi-language sandbox), `docker-compose.yml` (loopback bind), published `ghcr.io/xytom/coding-tools-mcp-sandbox:latest` | CODE_VERIFIED; GHCR availability **NOT_VERIFIED** (ghcr.io egress-blocked in Arena) |
| LINUX_HARDENING | **Landlock ABI v2 `available: true, enabled: true`** on Linux 6.1.158 (`landlock` present in `/sys/kernel/security/lsm`). Kernel-layer proof: `cat "$(printf %s/%s /etc passwd)"` — path assembled at runtime so the string classifier cannot see it — returned `cat: /etc/passwd: Permission denied` plus server diagnostic `LANDLOCK_READ_ROOT_BLOCKED`. Outside **write** likewise denied | EMPIRICALLY_TESTED |
| REMOTE_DEPLOYMENT_COMPLEXITY | LOW. `pip install coding-tools-mcp==0.3.0` into a venv, or one container. No database, no message bus, no second backend process | EMPIRICALLY_TESTED |
| PERSISTENCE_REQUIREMENT | workspace directory must persist. OAuth dynamic client registrations and pending authorization codes are **process-local**; a restart forces clients to re-register (mitigated by a stable `CODING_TOOLS_MCP_OAUTH_TOKEN_SECRET` and by ChatGPT re-running DCR) | DOCUMENTED + CODE_VERIFIED |
| EXPECTED_OPERATING_COST | 1 vCPU / ~1–2 GB RAM / ~5 GB disk sufficient for the bounded pilot (measured runtime footprint: 2 vCPU, 3.9 GB sandbox, server idle RSS not separately metered) | EMPIRICALLY_TESTED (environment) |
| UPSTREAM_UPDATE_PATH | pinned PyPI version bump, or repull GHCR image; Apache-2.0 permits unmodified use with attribution preserved | DOCUMENTED |
| FORK_REQUIRED | **NO** | — |
| THIN_ADAPTER_REQUIRED | **NO** — configuration only (`deployments/clouddesk-pilot/`) | — |

### 3.1 Special-audit items called out by the task

| Item | Result | Grade |
| --- | --- | --- |
| Streamable HTTP endpoint | `POST /mcp`; `GET /mcp` → 405 (no SSE stream); JSON-RPC batches rejected; `notifications/cancelled` accepted in both eras | EMPIRICALLY_TESTED + DOCUMENTED |
| Bearer auth | 401 anonymous, 401 invalid, 200 valid; `WWW-Authenticate: Bearer realm=..., resource_metadata=...` | EMPIRICALLY_TESTED |
| OAuth 2.1 / PKCE current | Authorization Code + PKCE **S256 only**; codes single-use, 5-minute expiry; tokens default 24 h bound to registered client + exact resource URL; secrets stored as digests | EMPIRICALLY_TESTED |
| RFC 7591 dynamic registration | `POST /oauth/register` → 201 + `client_id` for a **public** client (`token_endpoint_auth_method: none`), no pre-shared credential; registration without `redirect_uris` → 400 `invalid_client_metadata`; HTTPS redirects required except loopback | EMPIRICALLY_TESTED |
| PKCE actually enforced | token exchange with a **wrong** verifier → 400 `invalid_grant`; replay of a used code → 400 `invalid_grant`; wrong authorize password → 401 | EMPIRICALLY_TESTED |
| Remote MCP docs | `docs/remote-mcp.md` documents tunnel one-liner, OAuth endpoints, registration rules, session-free HTTP behaviour, `curl` verification recipes, and security notes | CODE_VERIFIED |
| ChatGPT connector compatibility | upstream README states "ChatGPT and Grok connect through their connector settings the same way" — that is an **upstream claim**; this audit instead proves the mechanism ChatGPT actually requires (DCR + PKCE + public client) and does not rely on the claim | DOCUMENTED (claim) + EMPIRICALLY_TESTED (mechanism) |
| Docker image | upstream `Dockerfile` + `docker-compose.yml`; entrypoint is the server itself; image bakes `CODING_TOOLS_MCP_*`; `0.0.0.0` bind forces auth (token generated and printed to stderr if none supplied) | CODE_VERIFIED; **NOT_VERIFIED** at runtime (no Docker daemon in Arena) |
| safe / trusted / dangerous modes | `safe` gates network + shell expansion + inline scripts + destructive; `trusted` opens the first three, keeps secret filtering and destructive checks; `dangerous` disables exec gates and Landlock. Mode probe run on a **second live instance** | EMPIRICALLY_TESTED |
| workspace-root enforcement | see matrix | EMPIRICALLY_TESTED |
| absolute path / `..` rejection | see matrix | EMPIRICALLY_TESTED |
| symlink escape handling | three distinct symlink attacks rejected | EMPIRICALLY_TESTED |
| atomic patches | see matrix | EMPIRICALLY_TESTED |
| secret filtering | `secret_env_filter: enabled` reported by `server_info` and `check_exec_environment` | EMPIRICALLY_TESTED (flag present) |
| command environment | `shell_env_inherit: core`; server-owned `HOME`/`TMPDIR`/`cache_dir`; `global_tmp_write: tmp-prefix` | EMPIRICALLY_TESTED |
| output limits | see matrix | EMPIRICALLY_TESTED |
| timeout / cancellation | `timeout_ms` enforced post-return (proven). Cancellation: upstream documents that `notifications/cancelled` does **not** stop work already started (issue #48) — bound work with `timeout_ms`, terminate with `kill_command` | EMPIRICALLY_TESTED (timeout) + DOCUMENTED (cancellation gap) |
| PTY sessions | real POSIX PTY; not exercised in this pilot | DOCUMENTED + CODE_VERIFIED |
| Landlock on Linux | **enabled and effective**, ABI v2 | EMPIRICALLY_TESTED |
| git tool behaviour | 5 git tools, all exercised | EMPIRICALLY_TESTED |
| SECURITY.md | read in full. States plainly: "`exec_command` must not be treated as a complete OS/container sandbox"; "For production, expose the server only to trusted local clients, bind HTTP to loopback, and run it inside an external container or sandbox with no host secrets, no broad filesystem mounts, and network egress disabled by policy." Lists residual risks: arbitrary project code execution, policy-based (not firewall) network denial, Landlock Linux-only and best-effort, symlink race resistance platform-dependent, redaction can miss transformed secrets | CODE_VERIFIED |

### 3.2 `exec_command` is arbitrary code execution

Recorded explicitly as the task requires. `exec_command` launches real host
processes as the server's Unix identity. Workspace path confinement plus
Landlock plus command classification reduce, and do **not** eliminate, that
fact. **Workspace confinement is not described anywhere in this audit as a
complete OS sandbox**, consistent with upstream's own SECURITY.md.

### 3.3 GitHub Actions cloud sandbox — excluded, as instructed

Upstream `main` contains an **optional** mechanism that starts cloud sandboxes
through GitHub Actions: `infra/cloudflare/sandbox-control/` (a Cloudflare Worker
control plane) dispatches `.github/workflows/start-sandbox.yml`, which boots the
Docker sandbox and publishes it behind an authenticated Cloudflare Tunnel. The
Worker itself runs no code and proxies no MCP traffic.

```text
GITHUB_ACTIONS_AS_EXECUTION_COMPUTE=DISALLOWED (task §6)
ADOPTED=NO
DEPLOYED=NO
REQUIRED_BY_CHOSEN_ARCHITECTURE=NO
```

It is not adopted merely because it exists. The chosen deployment is an ordinary
long-lived Linux container/process on independent cloud compute
(`deployments/clouddesk-pilot/`). Nothing in the pilot or the deployment package
dispatches a workflow, consumes Actions quota, or depends on the Worker. The
`deploy-sandbox-control` and `start-sandbox` workflows belong to **upstream's**
repository, not to P2P's, and are never triggered by this work.

---

## 4. Audit matrix — Candidate 2: `pokapopo/vps-action-gateway`

| Dimension | Finding | Grade |
| --- | --- | --- |
| LICENSE | MIT | CODE_VERIFIED |
| MCP_TRANSPORT | Streamable HTTP; recommended stateless `mcp-v2/` endpoint; legacy `gateway-server.js` endpoint also present | CODE_VERIFIED |
| CHATGPT_REMOTE_COMPATIBILITY | **FAILS.** `mcp-v2/oauth.js` publishes `authorization_endpoint` and `token_endpoint` but **no `registration_endpoint`**; `token_endpoint_auth_methods_supported` = `["client_secret_basic","client_secret_post"]` — **no `none`**. `deploy/vps-action-gateway.env.example` requires a pre-configured `VPS_MCP_V2_OAUTH_CLIENT_ID` / `_CLIENT_SECRET` / `_CALLBACK_URI`, and the shipped example callback is Claude's (`https://claude.ai/api/mcp/auth_callback`). Regular ChatGPT Web can neither self-register nor present a client secret | CODE_VERIFIED (decisive) |
| AUTHENTICATION | OAuth 2.1 Authorization Code + PKCE S256 against a pre-provisioned confidential client; internal adapter→backend key `VPS_ACTION_MCP_KEY`; nginx HTTPS reverse proxy example | CODE_VERIFIED |
| AUTHORIZATION_MODEL | command policy `default: confirm` with regex allow/deny/confirm lists; approval tokens; idempotency keys; SHA guards | CODE_VERIFIED |
| WORKSPACE_CONFINEMENT | `VPS_ACTION_WORKSPACE_ROOTS` (write) and a **separate** `VPS_ACTION_READ_ROOTS`; the shipped example sets `VPS_ACTION_READ_ROOTS=/srv/ai-workspace:/var/log`, i.e. read scope is deliberately broader than the workspace. `path.resolve` + root membership checks in `privileged-server.js` | CODE_VERIFIED |
| PATH_TRAVERSAL_PROTECTION | root-membership check after `path.resolve` | CODE_VERIFIED |
| SYMLINK_ESCAPE_PROTECTION | `assertNoSymlinkEscape(target, roots)` present | CODE_VERIFIED |
| FILE_READ | `read` (v2) / `readFile` (v1) bounded slices; v1 tool text says "anywhere on the VPS without approval" | CODE_VERIFIED |
| FILE_SEARCH | `searchFiles` filename + bounded content search | CODE_VERIFIED |
| ATOMIC_EDIT | `edit`/`applyPatch`/`writeFile` with `expected_sha256` guards and `idempotency_key` | CODE_VERIFIED |
| MULTI_FILE_EDIT | no multi-file atomic envelope; `operationBatch` runs 1–16 **independent** operations concurrently, which is not an atomic multi-file transaction | CODE_VERIFIED |
| COMMAND_EXECUTION | `execute`/`runCommand`/`startJob`; v1 descriptions state **"Run as root."**; backend spawns via `/usr/sbin/runuser` when `process.getuid() === 0`, else `/bin/bash` | CODE_VERIFIED |
| LONG_RUNNING_JOBS | durable `job_id`, `getJob` bounded output with offset/limit, `cancelJob`, `next_action` continuation; job state under `VPS_ACTION_JOB_ROOT` | CODE_VERIFIED |
| PTY_OR_INTERACTIVE_SESSION | none found | CODE_VERIFIED (absence) |
| GIT_STATUS / GIT_DIFF / GIT_LOG | **no first-class git tools.** Git is reachable only through `execute`, and `policy.yaml` pre-allows only `^git\s+(?:status\|diff\|rev-parse\|log)(?:\s\|$)` while `git push` sits in `confirm`. Any other git verb falls to `default: confirm` and needs an approval round-trip | CODE_VERIFIED |
| OUTPUT_BOUNDS | `truncated` flag, bounded `lines`/`limit` (≤16384), response page budget test present | CODE_VERIFIED |
| SECRET_REDACTION | redaction counter in the public output schema (`redactions`); backend claims redaction | CODE_VERIFIED |
| ENVIRONMENT_SCRUBBING | not found as a distinct control | NOT_VERIFIED |
| NETWORK_CONTROL | not found as a command-class gate; policy is regex-based per command | CODE_VERIFIED |
| DESTRUCTIVE_COMMAND_CONTROL | `deletePath` moves to recoverable trash + `restorePath`; `manageService`/`managePackage` destructive; annotations mark `execute`, `manage`, `operation`, `invokeInterface` as `openWorldHint: true, destructiveHint: true` | CODE_VERIFIED |
| CONTAINER_OR_VM_BOUNDARY | **none.** No Dockerfile, no container support; deployment is two systemd units + nginx on the host | CODE_VERIFIED |
| LINUX_HARDENING | relies on a dedicated low-privilege `vpsagent` account for the **adapter**, while the **backend** is designed to run commands as root | CODE_VERIFIED |
| REMOTE_DEPLOYMENT_COMPLEXITY | MEDIUM–HIGH: Linux + Node 22+, `npm ci`, two systemd units, `/etc/vps-action-gateway/` root-owned config, `interfaces.d` YAML manifests, nginx TLS | CODE_VERIFIED |
| PERSISTENCE_REQUIREMENT | job root, trash root, idempotency store, interfaces dir — four persistent host paths | CODE_VERIFIED |
| EXPECTED_OPERATING_COST | small VPS; no measurement taken | NOT_VERIFIED |
| UPSTREAM_UPDATE_PATH | `git pull` + `npm ci`; `"private": true`, no published package, no releases, no tags | CODE_VERIFIED |
| FORK_REQUIRED | would be **YES** for this bounded goal (needs a git surface, workspace-only confinement, and either DCR or a public-client OAuth path) | — |
| THIN_ADAPTER_REQUIRED | would be **YES** at minimum for the OAuth/DCR gap | — |

### 4.1 Fail-closed conditions triggered (task §15)

Two of the listed reject conditions are met by the **minimal supported
deployment** of this candidate, not by a worst-case configuration:

```text
BROAD_HOST_FILESYSTEM_EXPOSURE = YES
  separate READ_ROOTS deliberately wider than the workspace; shipped example
  reads /var/log; v1 tool text advertises reads "anywhere on the VPS"

ROOT_OR_PRIVILEGED_EXECUTION_BACKEND = YES
  runCommand/startJob documented "Run as root."; backend uses runuser when uid 0;
  managePackage drives the system package manager

DESTRUCTIVE_OPERATIONS_ENABLED_WITH_NO_EXTERNAL_SANDBOX = YES
  no container/VM boundary exists in the project at all; execute/manage/
  operation are annotated openWorldHint+destructiveHint

NO_PRACTICAL_WAY_TO_AUTHENTICATE_REMOTE_CHATGPT = YES
  no registration_endpoint, no public-client ("none") token auth, pre-shared
  client_secret required -> ChatGPT's connector surface cannot complete the flow
```

`NO_FIRST_CLASS_GIT_SURFACE = YES` additionally breaks the CatDesk baseline
(`git status`, `git diff`) without an approval round-trip per non-allowlisted
verb.

### 4.2 What candidate 2 does well (recorded for fairness)

Low-privilege adapter ↔ Unix-socket backend split is a genuinely good design;
`expected_sha256` guards, idempotency keys, recoverable trash with `restorePath`,
`next_action` continuation, YAML facility manifests instead of tool-list growth,
and 50 passing tests are all real strengths. For its actual target — **operating
a VPS** (systemd, journal, packages, browser facilities) — it is a coherent
design. It is simply not a workspace-confined coding runtime, and it cannot be
connected by regular ChatGPT Web as shipped.

```text
CANDIDATE_2_VERDICT=REJECT_FOR_THIS_BOUNDED_GOAL
  (fit-for-purpose for VPS operations; not a ChatGPT-connectable coding runtime)
```

---

## 5. CatDesk baseline coverage (task §3)

| CatDesk capability actually required | coding-tools-mcp | vps-action-gateway |
| --- | --- | --- |
| workspace-scoped filesystem access | YES — one root, enforced (`EMPIRICALLY_TESTED`) | PARTIAL — workspace roots exist but read roots are host-wide by design (`CODE_VERIFIED`) |
| read / search | YES (`EMPIRICALLY_TESTED`) | YES (`CODE_VERIFIED`) |
| safe edit / write | YES — staged atomic patch + rollback (`EMPIRICALLY_TESTED`) | PARTIAL — SHA-guarded single-file edits, no atomic multi-file envelope (`CODE_VERIFIED`) |
| command execution | YES (`EMPIRICALLY_TESTED`) | YES, root-oriented, `default: confirm` (`CODE_VERIFIED`) |
| background / long-running continuation | YES — `command_id` + `next_action` (`EMPIRICALLY_TESTED`) | YES — `job_id` + `next_action` (`CODE_VERIFIED`) |
| git status | YES — first-class tool (`EMPIRICALLY_TESTED`) | NO — regex-allowlisted shell only (`CODE_VERIFIED`) |
| git diff | YES — first-class tool (`EMPIRICALLY_TESTED`) | NO (`CODE_VERIFIED`) |
| tests | YES — proven fail → repair → retest loop (`EMPIRICALLY_TESTED`) | PARTIAL — needs approval for most runners (`CODE_VERIFIED`) |
| durable enough execution evidence | YES — exit codes, bounded output with drop accounting, diagnostics, `command_id` (`EMPIRICALLY_TESTED`) | YES — `job_id`, truncation, redaction counters (`CODE_VERIFIED`) |
| usable from regular ChatGPT through MCP | **YES** — DCR + PKCE + public client proven end to end (`EMPIRICALLY_TESTED`) | **NO** — confidential client only (`CODE_VERIFIED`) |

GUI/browser automation was **not** required: no evidence in either candidate or
in the bounded goal makes it necessary. Candidate 2's `examples/interfaces/browser.yaml`
and `codex-window-control.js` are out of scope and were not adopted.

---

## 6. ChatGPT compatibility contract (verified facts only)

Established from OpenAI's public developer documentation plus the empirical
OAuth probe; no claim here rests on "another MCP client connects".

| Fact | Value | Source / grade |
| --- | --- | --- |
| MCP URL shape | `https://<host>/mcp` (single remote endpoint) | OpenAI docs + upstream `docs/remote-mcp.md` — DOCUMENTED |
| Transport | **Streamable HTTP required** for a production endpoint | OpenAI docs — DOCUMENTED |
| HTTPS required | Yes for a remote connector | OpenAI docs — DOCUMENTED |
| Authentication type | **OAuth**. ChatGPT cannot present custom API keys or a static `Authorization` header, and does not support machine-to-machine grants (client credentials, service accounts, JWT bearer assertions) | OpenAI docs / connector compatibility — DOCUMENTED |
| OAuth DCR | Supported: "Dynamic client registration remains supported when configured"; ChatGPT also prefers Client ID Metadata Documents where the AS offers them, with public-client (`none`) or `private_key_jwt` token exchange | OpenAI docs — DOCUMENTED |
| Registration behaviour | Dynamic registration runs once per server connection; the registered client is reused | OpenAI docs — DOCUMENTED |
| Resource indicators | ChatGPT appends `resource` (RFC 8707) to both the authorization and the token request | OpenAI docs — DOCUMENTED |
| Enablement path | ChatGPT → **Settings → Security and login → Developer mode** ON, then add the server URL under Plugins/Connectors; Plus/Pro/Business/Enterprise/Edu on the web app; managed workspaces may need an admin to permit custom connectors | OpenAI docs — DOCUMENTED |
| Bearer-token configuration usable in ChatGPT? | **NO** for the connector surface. Bearer remains correct for header-capable clients (Claude Desktop, Cursor, VS Code, Cline) | OpenAI docs — DOCUMENTED |
| Does upstream satisfy it? | **YES** — DCR endpoint advertised, public client `none` supported, PKCE S256 enforced, `resource` accepted and bound into the token, discovery documents published, issuer pinnable so it survives a reverse proxy | EMPIRICALLY_TESTED (18/18 checks) |
| Actual ChatGPT Web end-to-end connection | **NOT performed** — requires the Owner's ChatGPT account and a stable public HTTPS origin. No Owner credential was used and none is required by this pilot | NOT_VERIFIED |

Consequence: `REMOTE_CHATGPT_E2E=PENDING_STABLE_CLOUD_ENDPOINT`. This is a
missing **endpoint and Owner action**, not a missing capability — every protocol
mechanism ChatGPT needs was proven against the live server.

---

## 7. Cloud deployment requirements (task §13 — minimum first, then ≤3 categories)

### 7.1 Minimum requirements

```text
CPU                        = 1 vCPU sufficient (2 vCPU comfortable)
RAM                        = 1 GB minimum, 2 GB recommended
DISK                       = 5 GB minimum + workspace growth
PERSISTENT_DISK_NEEDED     = YES (the workspace IS the Git repository)
DOCKER_NEEDED              = NO (recommended, not required; both paths documented)
PUBLIC_HTTPS_NEEDED        = YES (ChatGPT requires a remote HTTPS endpoint)
CUSTOM_DOMAIN_NEEDED       = STRONGLY_RECOMMENDED
                             (pins OAuth issuer/audience/resource; an ephemeral
                              tunnel hostname forces re-authorization and breaks
                              token audience stability)
LONG_LIVED_PROCESS         = YES (systemd unit or container with restart policy)
SLEEP_TO_ZERO_ACCEPTABLE   = NO for the workspace volume; process restart is
                             acceptable (OAuth DCR registrations are process-local
                             and ChatGPT re-registers; a stable
                             OAUTH_TOKEN_SECRET keeps issued tokens meaningful)
ESTIMATED_EGRESS           = LOW: MCP JSON-RPC text + git clone/fetch of ONE
                             repository. No large artifact transfer, no media.
                             Bounded by design (output caps, head+tail retention).
PAID_RESOURCE_PROVISIONED  = NO (task §16 — nothing purchased, nothing created)
```

### 7.2 Viable compute categories (at most three)

| # | Category | Fit | Note |
| --- | --- | --- | --- |
| 1 | **Cheap Linux VPS** (1 vCPU / 1–2 GB / persistent disk, systemd + Caddy) | BEST FIT | Exactly the shape validated in the pilot. Persistent disk, stable hostname, long-lived process, no Docker required. Lowest cost, lowest complexity, no vendor control plane |
| 2 | **Managed container with persistent storage** (compose/K8s + a persistent volume + ingress TLS) | GOOD FIT | Uses `docker-compose.yml` as-is; container replaces Landlock as the boundary. Requires a genuinely persistent volume — a container platform with ephemeral storage does not qualify |
| 3 | **Ephemeral devbox/sandbox** | NOT SUITABLE as the durable executor | Fails `PERSISTENT_DISK_NEEDED=YES` and `SLEEP_TO_ZERO_ACCEPTABLE=NO`. Acceptable only for exactly what it was used for here: disposable evidence generation |

No provider was researched beyond these categories, no provider was chosen, and
nothing was purchased. The Owner is **not** asked to pick a provider: category 1
and category 2 are technically equivalent for this bounded goal and differ only
in whether Docker is present, so per RULE 20 §E the choice does not materially
change risk, cost or capability and is not escalated.

---

## 8. Residual security risks (explicit)

Carried forward from upstream `SECURITY.md` / `docs/limitations.md` and from
pilot observation. None of these is a reason to reject the candidate for this
bounded use; all of them are reasons to keep the deployment shape narrow.

1. **`exec_command` is arbitrary code execution.** Workspace confinement +
   Landlock + command classification are not an OS sandbox. Mitigation: dedicated
   non-root Unix user (proven) **and** container/VM boundary in production, one
   disposable-or-non-critical workspace, no host secrets, no broad mounts.
2. **Network denial is string classification, not an egress firewall.**
   `trusted` mode allows network outright. Mitigation: `safe` mode for stricter
   posture, or platform-level egress rules; never rely on the classifier alone.
3. **One workspace = one trust domain.** Any authenticated client can read,
   write stdin to, or kill any command by `command_id`; retained output is
   consumed globally; quotas are per workspace. Mitigation: exactly one client
   (the Owner's ChatGPT) and one credential per workspace; separate processes +
   workspaces + credentials for mutually distrusting clients. Upstream issues #46.
4. **Cancellation does not stop work already started** (upstream issue #48).
   Mitigation: bound everything with `timeout_ms`, terminate with `kill_command`
   — both proven in the pilot.
5. **Retained output expires** (300 s TTL, most recent 32 completed commands;
   head+rolling-tail can evict the middle of a very large stream). Mitigation:
   redirect large output to a file and page it with `read_file`; the server emits
   an explicit eviction warning when this happens.
6. **OAuth registrations and pending codes are process-local.** A restart
   requires dynamic clients to re-register. Mitigation: pin
   `CODING_TOOLS_MCP_OAUTH_TOKEN_SECRET`; expect one re-authorization after a
   restart.
7. **Secret redaction can miss transformed or fragmented secrets.** Upstream
   states redaction is defense-in-depth, not primary protection. Mitigation: keep
   production secrets out of the environment entirely — the pilot ran with no
   production credentials present.
8. **Symlink race resistance depends on platform support** for anchored/no-follow
   operations. Mitigation: Linux + Landlock (proven), container boundary.
9. **Browser `Origin` is denied by default with HTTP 403.** This is correct CSRF
   / DNS-rebinding defence and does not affect a server-to-server connector
   runtime (no `Origin` header → 200, proven). Risk is a **mis-deployment**: a
   reverse proxy that synthesizes an `Origin` header would break the connection.
   Mitigation: proxy must not add `Origin`; set `CODING_TOOLS_MCP_ALLOWED_ORIGINS`
   to an exact origin only if a browser-based MCP client is genuinely required.
10. **Unsafe workspace root produces an unhandled traceback** rather than a clean
    operator-facing error line (observed when starting with
    `CODING_TOOLS_MCP_WORKSPACE=/`). It **fails closed** — the server does not
    start — so this is a UX/diagnostics nit, not a security gap. Worth an
    upstream issue; not a blocker.
11. **`dangerous` mode disables exec gates and Landlock.** Never use it outside
    an isolated container/VM. The pilot ran `trusted` for the main instance and
    `safe` for the gate probe; `dangerous` was never enabled.

---

## 9. OE gate (RULE 14)

```text
Không bị over engineering chứ?
OE_GATE=DO_IT
```

Reason: the bounded goal requires proving a real capability before any P2P
integration is canonicalized (RULE 19 `PROBE_PASS != PROMOTED_CAPABILITY`), and
the artifacts produced are configuration + validation only. What was deliberately
**not** built: no gateway, no proxy of our own, no daemon, no orchestrator, no
router, no registry, no capability abstraction, no CloudDesk framework, no
second MCP server, no vendored upstream source, no fork. `SIMPLER_PATH` was
taken: reuse upstream as-is, wrap it in config, prove it, stop.

---

## 10. P2P integration boundary (task §14)

```text
P2P_INTEGRATION_READY=YES
RULE_20_MODIFIED_BY_THIS_TASK=NO
NEW_EXECUTOR_CANONICALIZED_BY_THIS_TASK=NO
```

Empirical pilot evidence now exists, so a follow-up task may propose the
smallest integration. This task deliberately does **not** canonicalize a
`CloudDesk` executor and does **not** touch RULE 20.

`FOLLOW_UP_MINIMUM_DELTA` — exact minimum files/rule delta for a follow-up task:

1. `docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md` → inside **RULE 20 only**:
   - add a `CLOUDDISK`/`CloudDesk` executor profile section beside `C. CATDESK
     executor profile` and `D. ARENA executor profile`, defining
     `CLOUDDESK_AVAILABLE=<YES|NO>` as a **health-probed** condition (reachable
     HTTPS origin + authenticated `server_info`), not a name registration;
   - extend `E. AUTO routing policy` with the two evidence-based routing clauses
     the Owner expects (CatDesk available → CatDesk may be selected; CatDesk
     unavailable **and** CloudDesk healthy → CloudDesk may be selected; isolated
     Arena evidence required → Arena);
   - add the Owner-facing command `"Tiếp tục công việc, dùng CloudDesk"` to the
     canonical command list;
   - keep `AUTO_IS_ROUTING_POLICY_NOT_EXECUTOR=YES` and the existing
     no-new-daemon clause unchanged.
2. `AGENTS.md` → one digest line in the RULE 20 bullet (the thin installed
   entrypoint mirrors the notebook; no rule bodies copied).
3. `governance/` → no schema change expected; only the standing
   `RULE_ASSIMILATION_LEDGER` entry flipping from `PENDING` to `VERIFIED` once a
   Writer task names the artifact and section.
4. **Not** required: no new capability class, no `BACKEND_PROVIDER` registry
   entry, no router change, no new CI workflow, no new state directory. A
   CloudDesk backend is a deployment, not a P2P capability identity — registering
   one before a second real reuse would violate RULE 17 (`ABSTRACTION_LATER=YES`,
   "only multiple real reuses justify a generic capability abstraction").

Precondition for that follow-up task: a **stable public HTTPS endpoint** exists
and one real ChatGPT Web connection has been completed by the Owner
(`REMOTE_CHATGPT_E2E=PASS`). Until then the profile would register a name ahead
of proof, which task §14 forbids.
