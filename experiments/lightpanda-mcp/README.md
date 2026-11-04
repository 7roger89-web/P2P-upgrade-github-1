# Lightpanda Arena + ChatGPT MCP pilot

Owner scope: no Chromium dependency, no Logistics app/data mutation, no paid infrastructure. Pin Lightpanda version `1.0.2`.

**Arena**: install the official `lightpanda==1.0.2` wheel from PyPI (it includes the browser binary) into a new virtual environment; verify `lightpanda version`, `lightpanda fetch --dump markdown https://example.com`, and local `lightpanda mcp` initialization. Record actual log PASS/FAIL/BLOCKED. The full executable smoke script is in the user-facing pilot ZIP.

**ChatGPT**: this directory's Dockerfile starts the upstream official Lightpanda HTTP MCP server on port `10000`; deploy this folder as a free-tier Render Docker web service. The remote endpoint is `https://<render-host>/mcp`. In ChatGPT Web use Plugins → + → Add custom MCP server → HTTPS endpoint → No authentication → create and install. Workspace permissions may require an admin.

**Boundaries**: this is a public, unauthenticated, disposable trial, for public websites only. No secrets or login sessions. Render free instances sleep, and Lightpanda does not replace Chromium for visual/browser UI QA. `--block-private-networks` and `--obey-robots` are enabled.
