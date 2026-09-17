# P2P Cloud Executor — Pilot Terminal Report

**TASK_ID:** `P2P_CLOUD_EXECUTOR_PILOT_01`
**STATUS:** `MISSION_COMPLETE`
**Executed:** 2026-09-17 (UTC)
**Executor:** ARENA — `EXECUTION_MODE=AUTONOMOUS_UNTIL_TERMINAL` (notebook RULE 20 §B)
**Companion artifact:** `P2P-CLOUD-EXECUTOR-CANDIDATE-AUDIT-2026-09-17.md`
**Machine evidence:** `evidence/pilot-evidence.json`, `evidence/oauth-dcr-evidence.json`,
`evidence/deployment-posture-probe.txt`

```text
DISPOSITION=REUSE
SELECTED_UPSTREAM=xyTom/coding-tools-mcp
UPSTREAM_VERSION_OR_COMMIT=PyPI coding-tools-mcp 0.3.0
FORK_REQUIRED=NO
THIN_ADAPTER_REQUIRED=NO
NEW_GATEWAY_BUILT=NO
REMOTE_CHATGPT_E2E=PENDING_STABLE_CLOUD_ENDPOINT
P2P_INTEGRATION_READY=YES
```

---

## 1. Owner-facing summary (Vietnamese, per Supreme Law #7)

**Kết quả:** Đã tìm được và **chứng minh chạy thật** một "cloud coding executor"
cho phép ChatGPT Web thông thường điều khiển một Git repository thật trên máy
cloud — **không cần bật PC Windows ở nhà**.

**Đã chọn:** dùng lại dự án mã nguồn mở có sẵn `xyTom/coding-tools-mcp`
(Apache-2.0). **Không tự xây** gateway mới, **không fork**, **không viết
framework "CloudDesk"** — chỉ thêm file cấu hình triển khai và script kiểm tra.

**Đã kiểm chứng bằng chạy thật trong môi trường cách ly của Arena:** 64/64 hạng
mục đạt (đọc/tìm/sửa file, chạy lệnh, bắt lỗi → sửa → chạy lại đạt, tiến trình
chạy dài, git status/diff/log, chặn thoát khỏi thư mục làm việc, giới hạn output)
**và** 18/18 hạng mục OAuth 2.1 + PKCE + tự đăng ký client — đúng cơ chế mà
ChatGPT Web bắt buộc phải dùng.

**Còn thiếu duy nhất một thứ:** một địa chỉ HTTPS cloud **cố định** để Owner dán
vào ChatGPT. Đây là việc triển khai + một thao tác của Owner, **không phải** thiếu
năng lực kỹ thuật. Toàn bộ cơ chế kết nối đã được chứng minh với server thật.

**Ứng viên thứ hai** (`pokapopo/vps-action-gateway`) bị loại có bằng chứng: nó là
gateway quản trị cả VPS (chạy lệnh với quyền root, đọc được ngoài workspace), và
OAuth của nó **yêu cầu client secret cấu hình sẵn** — thứ mà ChatGPT Web không
thể cung cấp. Nó cũng **không có** công cụ git riêng.

**Một việc Owner cần làm:** xem mục 12 (`NEXT_OWNER_ACTION`).

---

## 2. Pilot server, isolation and workspace

```text
PILOT_SERVER   = coding-tools-mcp 0.3.0 (PyPI wheel, pinned)
                 wheel sha256 = 4d98f4a2cba6f677444986ae395446069e9ecb508861fc903f30a2aa8cefdba3
                 transport    = Streamable HTTP, POST /mcp, stateless
                 instances    = :8765 bearer+trusted (main), :8766 bearer+safe (gate probe),
                                :8767 oauth+trusted (DCR proof), :8768 oauth+pinned-origin,
                                :8769 bearer+origin-allowlist (Origin probe)

PILOT_ISOLATION = DEDICATED_NON_ROOT_UNIX_USER + UPSTREAM_WORKSPACE_ROOT
                  + KERNEL_LANDLOCK_ABI_V2
                  NOT_DOCKER (no Docker daemon exists in the Arena sandbox)
                  process identity proven: uid 999 (ctmpilot), NOT root
                  host egress to ghcr.io blocked; PyPI reachable

PILOT_WORKSPACE = /srv/clouddesk-pilot/workspace
                  ONE disposable synthetic Git repository, branch main,
                  no remote, no Owner credentials, wiped and rebuilt per run
                  by deployments/clouddesk-pilot/prepare_workspace.sh

HOST             = Debian 12, Linux 6.1.158+, 2 vCPU, 3.9 GB RAM
                  LSM list includes landlock -> Landlock available AND enabled
```

Docker was unavailable, so isolation was built from the primitives that **were**
available and are honest about their own scope: a dedicated non-root Unix user
(a real OS identity boundary), upstream's workspace-root confinement, and the
kernel's Landlock LSM. The audit does **not** describe this as equivalent to a
container, and the production deployment package offers the container path
because upstream `SECURITY.md` explicitly recommends an external container or VM
for untrusted work.

---

## 3. Empirical pilot results (task §11)

Every row below is `EMPIRICALLY_TESTED` against a live server through the MCP
surface only. `validate_pilot.py` is a **pure MCP client** — it never touches the
workspace filesystem directly, so each observation is evidence about what a
remote ChatGPT-class client can actually do.

| # | Requirement | Result | Key observed evidence |
| --- | --- | --- | --- |
| 1 | SERVER START | **PASS** 5/5 | `initialize` → protocolVersion `2025-11-25`, serverInfo `coding-tools-mcp 0.3.0`; workspace `/srv/clouddesk-pilot/workspace`; `auth_enabled: true`; 18 tools; all CatDesk-baseline tools present; server-owned `HOME`/`TMPDIR`/`cache_dir` under a runtime dir |
| 2 | WORKSPACE BOUNDARY | **PASS** 11/11 | allowed read OK; `../` → `PATH_OUTSIDE_WORKSPACE`; absolute → `ABSOLUTE_PATH_DENIED`; NUL byte → `INVALID_ARGUMENT`; unknown tool argument → JSON-RPC `-32602`; symlink read → `SYMLINK_ESCAPE`; symlinked-dir traversal → `PATH_OUTSIDE_WORKSPACE`; symlink write → `SYMLINK_ESCAPE`; literal outside path in a command → `PERMISSION_REQUIRED/filesystem_escape`; **kernel Landlock** blocked a runtime-assembled outside read (`cat: /etc/passwd: Permission denied` + `LANDLOCK_READ_ROOT_BLOCKED`) and an outside write |
| 3 | READ / SEARCH | **PASS** 4/4 | `list_files` → 6 seeded paths; `read_file` returns exact content with the planted needle; `search_text` → 1 exact hit; absent string → 0 hits |
| 4 | EDIT | **PASS** 3/3 | single-file `apply_patch` → `summary: M notes/README.md`, `additions: 1`; read back confirms; **sentinel file sha256 identical** before/after (no unrelated file changed) |
| 5 | MULTI-FILE / ATOMIC PATCH | **PASS** 5/5 | two files in one envelope both landed; one bad hunk → whole envelope refused with `PATCH_CONTEXT_NOT_FOUND` **and the first file unchanged** (rollback proven); `dry_run` proven non-mutating |
| 6 | COMMAND | **PASS** 6/6 | exit 0 with separate stdout/stderr; `pwd` == workspace root; `exit 7` surfaced faithfully; `check_exec_environment` reports landlock/mode/secret-filter; durable id before deadline; **deadline enforced after the call returned** (`status: timeout`, `timed_out: true`, `signal: SIGTERM`, `exit_code: -15`) |
| 7 | FAILURE DETECTION | **PASS** 1/1 | deliberate bug `return a - b` → `python3 -m unittest` exit **1** with `AssertionError: -1 != 5` in stderr |
| 8 | REPAIR LOOP | **PASS** 3/3 | patch fixed **only** `src/calc.py`; retest exit **0** / `OK`; `tests/test_calc.py` sha256 identical (repair did not touch the test) |
| 9 | LONG-RUNNING JOB | **PASS** 5/5 | 30-iteration job yielded `command_id` + `next_action` after 2 s; two separate polls returned advancing increments (`tick-3`, then `tick-4`); still `running` before termination; `kill_command` → `status: terminated`, `signal: SIGTERM`, `exit_code: -15`; **no leftover host process**; job no longer reports running |
| 10 | GIT | **PASS** 8/8 | `git_status` structured entries; `git commit` via `exec_command` exit 0; `git_log` → 1 commit with subject; `git_show` resolves HEAD; `git_blame` attributes lines; `git_diff` → 224-byte unified diff naming the file and added line + structured `files[]`; `git_status` then reflects the modification. No remote push required or performed |
| 11 | AUTH | **PASS** 4/4 (+18/18 OAuth) | 401 anonymous, 401 invalid token, 200 valid token, public server card 200 without credentials. Full OAuth 2.1 + PKCE S256 + RFC 7591 DCR flow proven separately (§4). **No secret value appears in any artifact** |
| 12 | OUTPUT BOUNDING | **PASS** 4/4 | `seq 1 200000` (1.29 MB) bounded to 13,999 bytes, `truncated_by: lines`, `dropped_bytes: 830143`; `read_output` pages by absolute byte offset (`next_offset` advances); explicit accounting `head_retained_bytes: 65536`, `evicted_gap_bytes: 764607`, `total_stream_bytes: 1288895` + eviction warning; `read_file` honours `max_lines` |
| 13 | SAFE-MODE GATE PROBE | **PASS** 5/5 | second live instance in `safe` mode: network-looking command → `PERMISSION_REQUIRED`; inline script → `PERMISSION_REQUIRED`; destructive-class command → `PERMISSION_REQUIRED`; ordinary workspace reads still work |
| 14 | PUBLIC HTTPS TRANSPORT | **NOT_RUN** | Arena's preview origin is not reachable from inside the sandbox (TLS `SSL_ERROR_SYSCALL` on hairpin). Reverse-proxy posture proven locally instead (§5). Classified, not failed, per task §10 |

```text
TOTALS = 64 PASS / 0 FAIL / 1 NOT_RUN (T14, environment-limited by design)
```

### 3.1 Repair loop actually exercised (RULE 20 §B)

The first harness run scored 46 PASS / 10 FAIL. Per the autonomous loop, each
failure was diagnosed to root cause before any repair, then retested:

| Failure | Root cause | Layer | Fix | Retest |
| --- | --- | --- | --- | --- |
| Landlock read probe "failed" | harness read `exit_code` from a response that was a **tool error** (`PERMISSION_REQUIRED/filesystem_escape`) — the boundary had in fact held | harness | treat policy refusal as a block; add a runtime-assembled-path probe that only the **kernel** can stop | PASS |
| `list_files` count 0 | wrong key (`entries` vs actual `files`) | harness | use `files` | PASS |
| `PATCH_CONTEXT_NOT_FOUND` | hunk context omitted the `marker: ` prefix, so it matched nothing | harness | correct context line | PASS |
| deadline check | `timeout_ms` is total process lifetime; the call yields early by design | harness | yield, then poll past the deadline | PASS |
| long-job poll / kill | `output_ref` is not the continuation handle; continuation is `write_stdin(chars="")`. `kill_command` signal enum is `TERM`/`KILL`/`INT`, **not** `SIGTERM` | harness | poll via `write_stdin`; use `TERM` | PASS |
| git cascade (5 checks) | `yield_time_ms: 60000` exceeds the schema **maximum 30000** → server answered JSON-RPC `-32602`, which the harness silently swallowed as an empty success | harness | clamp to 25000 **and** make the harness surface JSON-RPC-level errors | PASS |
| `git_show` | argument is `rev`, not `ref`; server strictly rejected the unknown argument with `-32602` | harness | use `rev`; record strict-argument rejection as a positive finding | PASS |

All seven root causes were harness expectation defects. **Zero upstream defects
were found.** Two repairs improved the harness itself rather than the test: the
JSON-RPC error-surfacing fix (a protocol error was being mistaken for an empty
success — a real false-pass risk) and the addition of the strict-argument-
rejection check.

---

## 4. ChatGPT compatibility — OAuth 2.1 + PKCE + RFC 7591 DCR proven

This is the decisive regular-ChatGPT-Web question, because ChatGPT's connector
surface cannot paste a static `Authorization: Bearer` header and cannot present a
client secret. It must discover, self-register, and run PKCE.

`validate_oauth_dcr.py` drove the complete flow against a live `--oauth-mode`
instance: **18 PASS / 0 FAIL**.

| Group | Result | Key observed evidence |
| --- | --- | --- |
| O1 DISCOVERY | PASS 5/5 | RFC 9728 `/.well-known/oauth-protected-resource` → `resource` + `authorization_servers` + `bearer_methods_supported: ["header"]`; RFC 8414 `/.well-known/oauth-authorization-server` → issuer/authorization/token endpoints; **`registration_endpoint` advertised**; `code_challenge_methods_supported: ["S256"]`; **`token_endpoint_auth_methods_supported` includes `none`** (public client) |
| O2 ANONYMOUS CHALLENGE | PASS 2/2 | anonymous `/mcp` → 401; `WWW-Authenticate: Bearer realm="coding-tools-mcp", resource_metadata="…/.well-known/oauth-protected-resource"` |
| O3 DYNAMIC REGISTRATION | PASS 2/2 | `POST /oauth/register` with `token_endpoint_auth_method: none` and a loopback redirect → **201 + client_id**, no pre-shared credential; registration without `redirect_uris` → 400 `invalid_client_metadata` |
| O4 AUTH CODE + PKCE | PASS 4/4 | `GET /oauth/authorize` renders an operator consent page carrying `client_id`, `redirect_uri`, `code_challenge`, `code_challenge_method`, `state`, `resource`; correct password → **302** to the registered redirect with `code` and matching `state`; wrong password → **401**, no code; token exchange with the correct verifier → **200 + access_token**, `token_type: Bearer`, `expires_in: 86400`, **no client secret presented** |
| O5 NEGATIVE CASES | PASS 2/2 | replaying the used code → 400 `invalid_grant` (single-use enforced); token exchange with a **wrong** PKCE verifier → 400 `invalid_grant` (**PKCE actually enforced, not merely advertised**) |
| O6 AUTHENTICATED MCP | PASS 3/3 | `initialize` with the OAuth access token → 200 + serverInfo; `tools/list` → 18 tools including `apply_patch` and `exec_command`; forged bearer token → 401 |

```text
CHATGPT_COMPATIBILITY_MECHANISM = PROVEN_END_TO_END
ACTUAL_CHATGPT_WEB_CONNECTION   = NOT_PERFORMED
  reason: requires the Owner's ChatGPT account and a stable public HTTPS origin.
  No Owner credential was requested, used, or stored.
```

Per task §12, compatibility is **not** claimed merely because another MCP client
connects. The claim rests on OpenAI's published connector requirements (OAuth
required; custom API keys unsupported; DCR "remains supported when configured";
CIMD preferred where offered; `resource`/RFC 8707 appended; Developer mode
enablement path) matched against mechanisms proven live on this server. Full
fact table: audit §6.

---

## 5. Reverse-proxy / deployment posture probe

Because the public origin could not be reached from inside the sandbox, the
posture a real nginx/Caddy deployment depends on was proven locally against live
instances, including a pinned-origin instance and an origin-allowlist instance.
`probe_deployment_posture.sh`: **11 PASS / 0 FAIL / 1 SKIP** (the skipped probe is
the public-origin one, by design).

| Probe | Result |
| --- | --- |
| anonymous / invalid / valid bearer | 401 / 401 / 200 |
| server card public without credentials | 200 |
| **server-to-server request (no `Origin`) accepted** | **200** |
| loopback browser `Origin` accepted by default | 200 |
| unallowlisted remote browser `Origin` denied | 403 `{"error":{"code":-32600,"message":"Origin denied"}}` |
| `Origin` with embedded userinfo (`https://chatgpt.com@evil.example`) denied | 403 |
| pinned `SERVER_URL` yields a stable public issuer despite a loopback request | `https://mcp.clouddesk.example` |
| **spoofed `Host:` header cannot move the issuer** | issuer unchanged |
| **spoofed `X-Forwarded-Host` ignored when proxy headers untrusted** | issuer unchanged |
| allowlisted exact origin accepted after opt-in | 200 |
| allowlist does **not** weaken auth (allowed origin, no token) | 401 |

The browser-`Origin` 403 is correct CSRF / DNS-rebinding defence and is **not** a
block on remote MCP: a server-to-server connector runtime sends no `Origin`
header and gets 200. The deployment risk it creates is a **mis-configured proxy
that synthesizes an `Origin`**; `README.md` in the deployment package states this
explicitly.

Two additional fail-closed controls were proven before the harness ever ran:

```text
non-loopback bind with CODING_TOOLS_MCP_AUTH_MODE=noauth
  -> "ERROR: non-loopback HTTP binding requires --auth-token,
      CODING_TOOLS_MCP_AUTH_TOKEN, or --oauth-mode." ; exit code 2
CODING_TOOLS_MCP_WORKSPACE=/
  -> ToolFailure: "Unsafe workspace root rejected." ; server does not start
```

---

## 6. Architecture actually built

```text
regular ChatGPT Web  (Control Tower / brain — unchanged)
        |
        | HTTPS + Streamable HTTP
        | OAuth 2.1 + PKCE S256 + RFC 7591 DCR   <-- PROVEN
        v
reverse proxy (Caddy/nginx) — TLS, forwards Host, adds NO Origin
        |
        | http://127.0.0.1:8765/mcp  (loopback only)
        v
upstream coding-tools-mcp — NON-ROOT, ONE workspace, mode-gated, Landlock
        |
        v
ONE approved workspace  =  disposable synthetic Git repository
```

Confirmed against task §9 prohibitions:

```text
NO_PUBLIC_UNAUTHENTICATED_SHELL     = YES (401 anonymous, fail-closed startup)
NO_ROOT_FACING_MCP_PROCESS          = YES (uid 999 proven; systemd User=; container USER)
NO_BROAD_HOST_FILESYSTEM_MOUNT      = YES (one workspace volume / one workspace root)
NO_PRODUCTION_SECRETS               = YES (none present; two generated pilot secrets)
NO_PRODUCTION_DATABASE              = YES (none exists in the architecture)
NO_BUSINESS_PRODUCTION_REPO         = YES (disposable synthetic repo, no remote)
NO_OWNER_PC_REQUIRED                = YES
NO_NEW_DAEMON_ORCHESTRATOR_ROUTER   = YES (config + validation scripts only)
```

---

## 7. Artifacts created (task §17)

```text
deployments/clouddesk-pilot/
  README.md                        deployment + security + ChatGPT contract notes
  Dockerfile.clouddesk             thin image: pinned PyPI wheel + git, non-root
  docker-compose.yml               hardened container shape, loopback bind, one volume
  clouddesk-mcp.service            systemd unit for the no-Docker path (the validated one)
  healthcheck.py                   container health probe (validated live, 6/6)
  .env.example                     config template; secrets stay out of Git
  start-server.sh                  privilege-dropping launcher (root reads cred, drops to user)
  prepare_workspace.sh             reset disposable workspace + plant hostile symlink fixtures
  validate_pilot.py                pure-MCP-client harness, 12 bounded tests + safe-mode probe
  validate_oauth_dcr.py            OAuth 2.1 + PKCE + DCR end-to-end validator
  probe_deployment_posture.sh      re-verify auth/Origin/proxy posture after deploying

docs/p2p-development/research/cloud-executor/
  P2P-CLOUD-EXECUTOR-CANDIDATE-AUDIT-2026-09-17.md
  P2P-CLOUD-EXECUTOR-PILOT-REPORT-2026-09-17.md      (this file)
  evidence/pilot-evidence.json                       64 checks, machine-readable
  evidence/oauth-dcr-evidence.json                   18 checks, machine-readable
  evidence/deployment-posture-probe.txt              11 probes, raw output
```

Deliberately **not** created: no vendored upstream source, no fork, no copied
upstream tree, no new gateway/proxy/daemon/router/registry, no capability
identity, no CI workflow, no RULE 20 modification. Upstream's own `Dockerfile`
and published image are referenced rather than duplicated; the thin image exists
only because the bounded pilot needs Python + git and not upstream's
Rust/Go/JDK/Maven toolchain payload.

OE gate (RULE 14): `Không bị over engineering chứ?` → `OE_GATE=DO_IT`. Three
validation scripts is one per distinct proof surface (capability, ChatGPT auth
mechanism, deployment posture); each answers a question the bounded goal cannot
answer without it, and none is a harness, framework, or service.

### 7.1 Post-write configuration verification (defects found and fixed)

After the package was written, every configuration name it uses was checked
against the upstream source that actually consumes it, and every file was
re-parsed. This caught three real defects before commit:

```text
DEFECT 1  .env.example/compose set CODING_TOOLS_MCP_PUBLIC_ORIGIN, a name that
          does not exist upstream (a silent no-op on the systemd path, where
          compose's alias mapping does not apply).
          FIX  use the real upstream name CODING_TOOLS_MCP_SERVER_URL, which is
          also what the empirically tested launcher passes. Verified live:
          SERVER_URL=https://mcp.clouddesk.example pinned issuer AND
          registration_endpoint, and code_challenge_methods_supported=[S256].

DEFECT 2  compose healthcheck hardcoded port 8765, so any non-default
          CODING_TOOLS_MCP_PORT would produce a permanently "unhealthy"
          container that was in fact serving correctly.
          FIX  healthcheck.py reads the port from the container's own env.
          Verified live 6/6: 8765/8767/8768 -> exit 0, default fallback ->
          exit 0, dead port -> exit 1 + diagnostic, malformed port -> exit 1
          (caught, never raises). Probe target /.well-known/mcp.json answers 200
          without credentials in BOTH bearer and oauth modes; /mcp answers 401
          by design and is therefore not a valid probe target.

DEFECT 3  CODING_TOOLS_MCP_VERSION was listed under ".env runtime posture"
          although the server never reads it; it is a Docker build ARG.
          FIX  moved under an explicit build-time heading with a note that
          changing it requires a rebuild.

ALSO  resource-cap variables were named CODEX_MEM_LIMIT / CODEX_CPUS, which
      collides with the "not Codex Cloud" boundary of this task. Renamed
      CLOUDDESK_MEM_LIMIT / CLOUDDESK_CPUS.

RESULT  13 of the 14 CODING_TOOLS_MCP_* names this package sets at runtime are
        confirmed consumed by upstream server-side code (coding_tools_mcp/,
        via the ENV_PREFIX="CODING_TOOLS_MCP" helper in envutils.py); the 14th
        (VERSION) is confirmed build-time only and is now labelled as such.
        No referenced variable is a silent no-op.
```

Repo-level validation run for this change set, at the nearest real boundary:
`sh -n` on all three shell scripts, `py_compile` on both validators and the
probe, YAML parse + hardening assertions on `docker-compose.yml` (loopback-only
publish, `read_only`, `cap_drop: [ALL]`, `no-new-privileges`), structural parse
+ hardening assertions on the systemd unit (non-root `User=`,
`NoNewPrivileges`, `ProtectSystem=strict`, `ProtectHome`, empty
`CapabilityBoundingSet`, `SystemCallFilter=@system-service`, `UMask=0077`,
scoped `ReadWritePaths`), and an assertion that every secret placeholder in
`.env.example` is empty.

`python3 scripts/doctor.py --package .` reports
`[FAIL] role: Requested role 'portable' does not match detected role
'development'`. This is a **pre-existing baseline failure, proven unrelated**:
the identical command on a clean detached worktree of `origin/main`
(`a479e62`, containing none of this task's files) produces the identical FAIL.
It is the wrong validation lane for a development-source checkout (`--package`
expects an unpacked release package). Observed but not fixed here, as fixing it
is out of this task's scope: `AGENTS.md` documents
`.p2p/system/scripts/doctor.py --root .`, but that script accepts `--source`
and rejects `--root` — a pre-existing doc/implementation drift on `main`.

### 7.2 Independent re-run (reproducibility) and evidence hygiene

The whole suite was executed twice against the live servers, with a full
workspace reset and hostile-symlink replant between the runs
(`prepare_workspace.sh`), and the two evidence documents were compared
programmatically rather than by eye:

```text
RUN 1  2026-09-17T09:06:42Z (pilot) / 09:03:40Z (oauth)
RUN 2  2026-09-17T09:23:43Z (pilot) / 09:23:50Z (oauth)

pilot-evidence.json       totals {pass:64, fail:0} identical in both runs
                          14/14 group verdicts identical
                          65/65 checks identical on id + group + name + verdict
oauth-dcr-evidence.json   totals {pass:18, fail:0} identical in both runs
                          6/6 group verdicts identical
                          18/18 checks identical on id + group + name + verdict

=> 83/83 check verdicts reproduced exactly. The committed evidence is RUN 2.

deployment-posture-probe.txt      re-run with the same instance mapping
                                 (loopback :8765, pinned :8768, dynamic oauth
                                 :8767, EXPECTED_ISSUER pinned) and byte-
                                 identical to the committed copy: 11 PASS +
                                 1 SKIP, POSTURE_PROBE=PASS. The SKIP is
                                 section D, which only runs when PUBLIC_URL is
                                 supplied - correct, since no stable public
                                 endpoint exists yet (see §10).
```

The 65th pilot check is T14 (`NOT_RUN`), the public-HTTPS-to-ChatGPT group, so
64 PASS + 1 NOT_RUN is the expected shape and not a discrepancy.

Credential handling in the committed evidence was verified field-by-field, not
assumed. Every sensitive-keyed leaf in both documents is one of:

```text
RETAINED (non-credential by construction)
  loopback discovery URLs        issuer / authorization_endpoint /
                                 token_endpoint / registration_endpoint on
                                 127.0.0.1 - public metadata, no secret value
  upstream error codes           PATH_OUTSIDE_WORKSPACE, ABSOLUTE_PATH_DENIED,
                                 SYMLINK_ESCAPE, PERMISSION_REQUIRED,
                                 PATCH_CONTEXT_NOT_FOUND, INVALID_ARGUMENT
                                 (these ARE the confinement assertions)
  registered_client_id           RFC 7591 identifier for a PUBLIC client
                                 (token_endpoint_auth_methods includes "none"),
                                 issued by a disposable loopback instance. An
                                 identifier, not a credential; ChatGPT's own DCR
                                 flow mints one per connection.

NOT PRESENT AS VALUES (recorded as booleans instead)
  access_token                   access_token_present: true
  authorization code             code_present: true
  PKCE code_verifier             compared in-process, never serialized
  client_secret                  none exists for a public client
  authorize password             never read into the evidence document
  bearer token                   read from a 0600 file, never serialized
```

A direct string search for both live secret values (the 43-char bearer token and
the 32-char authorize password, read from their `0600` files for the sole
purpose of the search and never printed) returns **0 matches** across all 16
deliverable files.


---

## 8. Cost and quota compliance (task §16)

```text
CHATGPT_WORK_USED                 = NO
CODEX_CLOUD_USED                  = NO
GITHUB_ACTIONS_COMPUTE_USED       = NO (no workflow was adopted as execution
                                     compute; all pilot compute ran on the
                                     Arena sandbox host itself)
GITHUB_ACTIONS_TRIGGERED          = ONE REQUIRED REPO GATE, UNAVOIDABLE
                                  .github/workflows/p2p-shield-ci-slice.yml
                                  fires on `pull_request: branches: [main]` with
                                  NO path filter, so ANY PR to main runs it -
                                  including a docs-and-deployment-config PR that
                                  touches none of its subject matter. Recorded
                                  per task §18 rather than suppressed: it was not
                                  re-run by hand and no matrix/cache/artifact
                                  service was added. The other six workflows in
                                  the repo are path- or branch-scoped and are NOT
                                  triggered by this change set (verified by
                                  reading each `on:` block; in particular
                                  hermes-essential-stack and
                                  hermes-runtime-compatibility match only
                                  deployments/hermes-*/** and the root
                                  Dockerfile, none of which this task touched).
GATE_OBSERVED_RESULT              = FAIL, PRE-EXISTING BASELINE, PROVEN
                                  UNRELATED (see §8.1). PR #201 run 35205364862.
                                  Not fixed here: repairing it means editing
                                  workflow files, which is a different lane and
                                  outside this task's scope.
MERGE_STATUS                      = NOT_MERGED (Owner Gate / validated-merge
                                  authority respected; a red required gate is
                                  never merged over silently)
PAID_RESOURCE_PROVISIONED         = NO
OWNER_PAT_OR_CREDENTIALS_USED     = NO
OWNER_PC_REQUIRED                 = NO
UPSTREAM_CLOUD_SANDBOX_MECHANISM  = NOT_ADOPTED (infra/cloudflare/sandbox-control
                                  + .github/workflows/start-sandbox.yml exist
                                  upstream; explicitly excluded per task §6)
```

### 8.1 The one required gate is red on `main` already — baseline proof

The predicted gate did run and did fail. Because a red required gate is never
merged over on assumption, it was traced to root cause rather than dismissed.

```text
PR #201 run 35205364862, job 105149698840
  step 5 "Run focused Shield contract tests" -> failure
  steps 1-4 success, step 6 skipped, steps 7-10 success

CAUSE  SHIELD-CI-01 (Zizmor 1.29.0, --no-config, offline Regular persona) scans
       .github/workflows/*.yml and reports status=FAIL, findings_count=16 on the
       real repository target. Every finding is in a PRE-EXISTING workflow file:
         chinese-metaphysics-executable-focused.yml  unpinned-uses, artipacked,
                                                     adhoc-packages
         chinese-metaphysics-upstream-audit.yml      unpinned-uses, adhoc-packages
         p2p-fcc-adapter-ci.yml                      unpinned-uses, artipacked
       (plus the remainder of the same 16, all under .github/workflows/)

WHY IT IS NOT THIS TASK'S
  1. `git diff --name-only a479e621 HEAD | grep -c '^\.github/workflows/'` = 0.
     This change set touches ZERO workflow files. Its only two top-level paths
     are deployments/clouddesk-pilot and docs/p2p-development.
  2. The SAME workflow, on branch main, at head_sha a479e621 - the exact
     CANONICAL_BASE_SHA this branch was cut from, containing none of this task's
     files - fails identically: run 35200293474, step 5
     "Run focused Shield contract tests" = failure, with the identical
     surrounding step pattern.
  3. main was GREEN at fcaf63aa (07:47:10Z) and RED at 52fae352 (07:49:46Z) and
     a479e621 (08:33:19Z). The regression landed on main BEFORE this branch
     existed.
  4. Unrelated branches fail the same gate in the same window
     (fix/control-tower-self-law-gate repeatedly; the prior arena/01a0ae43 PR).

VERDICT  PRE_EXISTING_BASELINE_FAILURE, PROVEN UNRELATED (RULE 11 condition 3).
         Reproducing it is a workflow-hardening lane of its own (pin 16 `uses:`
         references to commit SHAs, replace artipacked patterns, declare
         packages explicitly). It is deliberately NOT folded into this pilot:
         that would expand scope into CI files this task was told to leave alone
         and would spend Actions quota on an unrelated repair.

NOTE ON FIXTURES  The same job also emits PASS/BLOCKED/FAIL evidence records
         against synthetic targets under /tmp/shield-base-* (e.g.
         fail_leaked_worktree, blocked_unavailable_provider). Those are the
         harness's own self-test fixtures exercising its verdict logic, not
         findings about this repository, and are not evidence against this PR.
```

---

## 9. Security findings and residual risks

`SECURITY_FINDINGS` — three findings, none blocking:

1. **Kernel Landlock is genuinely effective, not just advertised.** Proven by
   defeating the string classifier first: a path assembled at runtime
   (`cat "$(printf %s/%s /etc passwd)"`) was still blocked at the syscall layer
   with `LANDLOCK_READ_ROOT_BLOCKED`. This is the strongest single piece of
   evidence in the pilot, and it is why the no-Docker path is defensible at all.
2. **Two independent input-validation layers are strict and fail closed.**
   Unknown tool arguments are rejected with JSON-RPC `-32602` rather than
   ignored, and over-maximum values (`yield_time_ms: 60000` > schema max 30000)
   are rejected rather than clamped. Strictness is a security property here: it
   prevents argument smuggling. It also produced the pilot's only false-pass
   risk, because a naive client reads an error response as an empty success —
   `validate_pilot.py` now surfaces both layers.
3. **Unsafe-root rejection crashes with a traceback** instead of a clean operator
   error line. It fails closed (no server starts), so this is a diagnostics nit
   worth an upstream issue, not a security gap.

`RESIDUAL_RISKS` — carried explicitly, all documented in audit §8:
`exec_command` is arbitrary code execution and workspace confinement is **not** a
complete OS sandbox; network denial is string classification, not an egress
firewall; one workspace is one trust domain with no per-client partitioning
(upstream #46); cancellation does not stop work already started (upstream #48);
retained output expires (300 s / 32 commands) and can evict the middle of a very
large stream; OAuth registrations are process-local so a restart forces
re-registration; secret redaction can miss transformed secrets; symlink race
resistance is platform-dependent; browser `Origin` is denied by default (correct,
but a proxy that synthesizes `Origin` would break the connection); `dangerous`
mode disables exec gates and Landlock and was never enabled in this pilot.

---

## 10. Exact next step for stable cloud deployment

```text
STEP 1  Provision ONE cheap Linux VPS: 1 vCPU / 1-2 GB RAM / >=5 GB PERSISTENT
        disk, with a hostname the Owner controls (a custom domain is strongly
        recommended: it pins the OAuth issuer, audience and resource, and an
        ephemeral tunnel hostname forces re-authorization and destabilizes token
        audience).
STEP 2  Deploy Path A (container) or Path B (systemd, the validated path) from
        deployments/clouddesk-pilot/README.md. Fill .env: SERVER_URL,
        OAUTH_PASSWORD, OAUTH_TOKEN_SECRET. Keep the bind on 127.0.0.1.
STEP 3  Put Caddy or nginx in front for TLS. Forward the real Host. Do NOT
        synthesize an Origin header. Keep TRUST_PROXY_HEADERS=0.
STEP 4  Clone ONE non-critical Git repository into the workspace volume.
        No production repo, no production secrets.
STEP 5  Re-verify from the operator side:
          TOKEN_FILE=... PUBLIC_URL=https://mcp.<domain> \
            sh probe_deployment_posture.sh
        and re-run validate_pilot.py against the deployed endpoint.
STEP 6  OWNER ACTION: ChatGPT -> Settings -> Security and login -> Developer
        mode ON -> Plugins/Connectors -> + -> https://mcp.<domain>/mcp ->
        Authentication: OAuth -> type the OAUTH_PASSWORD once on the authorize
        page. Then ask it to run git status through the connector.
STEP 7  Only after STEP 6 succeeds: open the FOLLOW_UP task that adds the
        CloudDesk executor profile to RULE 20 (audit §10 for the exact minimum
        delta). Do not canonicalize the name before that proof exists.
```

Steps 1–4 are the only ones needing a purchase decision, and they are bounded
(one small VPS + one domain). Nothing was bought or provisioned by this task.

---

## 11. Definition-of-done reconciliation (task §20)

| Requirement | Status |
| --- | --- |
| both candidates investigated with provenance | DONE — audit §2, incl. the unlocated-Reddit-lead caveat recorded as required |
| one evidence-backed disposition | DONE — `REUSE`, audit §1 |
| no unnecessary new gateway built | DONE — zero new servers; config + validation only |
| chosen upstream executed in an isolated pilot | DONE — 5 live instances, non-root uid, Landlock on |
| filesystem boundary evidence | DONE — T02, 11/11 incl. kernel-layer Landlock proof |
| read/search/edit evidence | DONE — T03 4/4, T04 3/3, T05 5/5 |
| command evidence | DONE — T06 6/6 |
| failure→repair→retest evidence | DONE — T07 1/1 → T08 3/3 (and the harness's own 7-root-cause repair loop, §3.1) |
| long-running-job evidence | DONE — T09 5/5 incl. clean termination and no leftover host process |
| git evidence | DONE — T10 8/8 (status, diff, log, show, blame, commit) |
| auth evidence (remote HTTP mode supported) | DONE — T11 4/4 + OAuth/DCR 18/18 + posture 11/11 |
| residual security risks explicit | DONE — §9 and audit §8 |
| PC-at-home not required by architecture | DONE — §6 |
| no Work/Codex/GitHub Actions compute dependency | DONE — §8 |
| exact next step for stable cloud deployment | DONE — §10 |
| P2P integration readiness determined | DONE — §12 |

---

## 12. Terminal state

```text
STATUS=MISSION_COMPLETE

REMOTE_CHATGPT_E2E=PENDING_STABLE_CLOUD_ENDPOINT
  (every protocol mechanism ChatGPT requires is proven against the live server;
   what is missing is a stable public HTTPS origin plus one Owner action, not a
   capability. Per task §10 this is NOT a pilot failure.)

P2P_INTEGRATION_READY=YES
RULE_20_MODIFIED_BY_THIS_TASK=NO
NEW_EXECUTOR_CANONICALIZED_BY_THIS_TASK=NO
FOLLOW_UP_MINIMUM_DELTA = audit §10 (RULE 20 profile + AUTO routing clauses +
  Owner command line in the notebook; one digest line in AGENTS.md; nothing else)
  PRECONDITION: a stable public HTTPS endpoint exists AND the Owner has completed
  one real ChatGPT Web connection.

NEXT_OWNER_ACTION = approve provisioning ONE small Linux VPS (1 vCPU / 1-2 GB /
  >=5 GB persistent disk) plus a hostname, so the deployment package in
  deployments/clouddesk-pilot/ can be brought up and the single remaining
  unproven step -- a real ChatGPT Web connection -- can be completed.
  This is the only Owner Gate in the task: it is an infrastructure commitment
  and a material spend decision (notebook RULE 11), and nothing was purchased
  autonomously.

DELIVERY_STATE
  BRANCH  = arena/01a0ae84-p2p-upgrade-github-1 (one bounded task branch, never
            main; base a479e62192f6912e037ee0861e45c1799e9461e2)
  PR      = #201 -> main, OPEN
  MERGED  = NO. Owner Gate / validated-merge authority respected; this task does
            not self-merge.
  GATES   = the one required gate that any PR to main triggers
            (p2p-shield-ci-slice.yml) reports FAIL, PROVEN a pre-existing
            baseline failure on main at the base SHA and unrelated to this
            change set - see §8.1. All six other workflows are path/branch-
            scoped and correctly did not trigger.
```
