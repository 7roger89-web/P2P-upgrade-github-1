# CloudDesk pilot deployment package

Minimum deployment wrapper for running **upstream
[`xyTom/coding-tools-mcp`](https://github.com/xyTom/coding-tools-mcp)** as a cloud
coding runtime that regular ChatGPT Web can drive over remote MCP.

This package contains **configuration and validation only**. It vendors no
upstream source, forks nothing, and adds no daemon, orchestrator, router or
control plane. `P2P_ROLE=CONTROL_PLANE_ORCHESTRATOR`, `UPSTREAM_FIRST=YES`
(RULE 17).

```text
regular ChatGPT Web  (Control Tower / brain)
        |
        | HTTPS + Streamable HTTP, OAuth 2.1 + PKCE + RFC 7591 DCR
        v
reverse proxy (Caddy or nginx) — terminates TLS, forwards Host, adds NO Origin
        |
        | http://127.0.0.1:8765/mcp   (loopback only)
        v
upstream coding-tools-mcp — non-root, ONE workspace, permission mode gated
        |
        v
Git repository inside the workspace
```

## Contents

| File | Purpose |
| --- | --- |
| `Dockerfile.clouddesk` | Thin image: pinned upstream wheel from PyPI + git, non-root |
| `docker-compose.yml` | Container deployment: loopback bind, one workspace volume, hardened |
| `clouddesk-mcp.service` | systemd unit for the no-Docker path (the empirically validated one) |
| `.env.example` | Configuration template; `.env` is deployment state, never committed |
| `start-server.sh` | Privilege-dropping launcher used by the Arena pilot |
| `prepare_workspace.sh` | Resets the disposable workspace and plants hostile symlink fixtures |
| `validate_pilot.py` | Pure-MCP-client harness for the 12 bounded acceptance tests |
| `validate_oauth_dcr.py` | End-to-end OAuth 2.1 + PKCE + RFC 7591 dynamic registration proof |
| `probe_deployment_posture.sh` | Re-verify auth / Origin / reverse-proxy posture after deploying |

## Path A — container (recommended for real cloud compute)

```bash
cp .env.example .env && chmod 600 .env      # fill in the two secrets
docker compose up -d --build
curl -s http://127.0.0.1:8765/.well-known/mcp.json
```

Upstream also publishes a toolchain-rich image
(`ghcr.io/xytom/coding-tools-mcp-sandbox:latest`, built by its own
`.github/workflows/docker-image.yml`) and ships its own multi-language
`Dockerfile`. Use those when the workspace needs Rust/Go/JDK/Maven. The thin
image here is for the bounded pilot, which needs only Python + git.

> Inside a container, Docker's default seccomp profile does not allow the
> `landlock_*` syscalls, so upstream Landlock reports unavailable. That is
> expected: the container namespace, read-only rootfs and dropped capabilities
> are the boundary instead. Do not add `seccomp=unconfined` to "restore"
> Landlock — that would trade a real boundary for a redundant one.

## Path B — plain VPS, no Docker (empirically validated in the Arena pilot)

```bash
sudo useradd --system --home /nonexistent --shell /usr/sbin/nologin clouddesk
sudo install -d -m 0755 /srv/clouddesk /srv/clouddesk/workspace /srv/clouddesk/runtime
sudo python3 -m venv /srv/clouddesk/venv
sudo /srv/clouddesk/venv/bin/pip install "coding-tools-mcp==0.3.0"
sudo chown -R clouddesk:clouddesk /srv/clouddesk/workspace /srv/clouddesk/runtime
```

Then follow the install header in `clouddesk-mcp.service`. On a kernel with
Landlock in `/sys/kernel/security/lsm`, `exec_command` additionally gets
kernel-level filesystem confinement — verified live in the pilot on Linux 6.1
with Landlock ABI v2.

## Reverse proxy

Caddy (automatic HTTPS):

```text
mcp.example.com {
    reverse_proxy 127.0.0.1:8765
}
```

nginx: proxy to `127.0.0.1:8765`, forward the real `Host`, and **do not
synthesize an `Origin` header**. Upstream rejects a browser `Origin` that is not
loopback or explicitly allowlisted with HTTP 403 `Origin denied`. A
server-to-server MCP connector runtime sends no `Origin` and is unaffected; a
browser-based client needs `CODING_TOOLS_MCP_ALLOWED_ORIGINS` set to its exact
origin.

Keep `CODING_TOOLS_MCP_TRUST_PROXY_HEADERS=0` unless the proxy is under your
control and genuinely needs forwarded-header trust. Upstream ignores
`Forwarded` / `X-Forwarded-*` by default, which is what makes a spoofed
`X-Forwarded-Host` unable to move the OAuth issuer.

## Connecting regular ChatGPT Web

1. ChatGPT → **Settings → Security and login → Developer mode** ON.
2. ChatGPT Plugins / Connectors → **+** → enter `https://mcp.example.com/mcp`.
3. Authentication: **OAuth**. ChatGPT discovers
   `/.well-known/oauth-protected-resource`, then
   `/.well-known/oauth-authorization-server`, self-registers at
   `/oauth/register`, and runs Authorization Code + PKCE S256.
4. The operator types the `CODING_TOOLS_MCP_OAUTH_PASSWORD` value on the
   authorize page once.

Do **not** plan on a static bearer header for ChatGPT: the connector surface
cannot present custom API keys. Bearer mode remains correct for MCP clients that
can set headers (Claude Desktop, Cursor, VS Code, Cline).

## Validation

```bash
# 1. disposable workspace + hostile symlink fixtures
sudo PILOT_USER=clouddesk sh prepare_workspace.sh /srv/clouddesk/workspace

# 2. the 12 bounded acceptance tests (pure MCP client, no direct FS access)
python3 validate_pilot.py --base-url http://127.0.0.1:8765 \
    --token-file /path/to/token --evidence-out evidence.json

# 3. OAuth 2.1 + PKCE + DCR end to end (needs an oauth-mode instance)
python3 validate_oauth_dcr.py --base-url http://127.0.0.1:8767 \
    --password-file /path/to/authorize-password --evidence-out oauth.json

# 4. after the proxy is in place, re-verify posture against the public origin
TOKEN_FILE=/path/to/token PUBLIC_URL=https://mcp.example.com \
    sh probe_deployment_posture.sh
```

Both validators treat every credential as a secret: values are read from files,
never printed, and scrubbed from the evidence documents they write.

## Explicitly out of scope for this pilot

- **GitHub Actions as execution compute — DISALLOWED.** Upstream ships an
  optional Cloudflare-Worker control plane (`infra/cloudflare/sandbox-control`)
  that dispatches `.github/workflows/start-sandbox.yml` to boot an ephemeral
  sandbox. It is not used, not deployed and not required here; this package
  deploys an ordinary long-lived Linux container/process instead.
- No ChatGPT Work, no Codex Cloud.
- No Owner PAT, no Owner GitHub credentials, no production secrets, no
  production database, no business production repository.
- The Owner's Windows PC is never part of this architecture.
