#!/usr/bin/env python3
"""Container health probe for the CloudDesk pilot MCP server.

Probes ``/.well-known/mcp.json``, which upstream coding-tools-mcp 0.3.0 answers
with HTTP 200 and no credentials in BOTH bearer and oauth auth modes. It is the
same probe upstream's own ``.github/workflows/docker-smoke.yml`` uses. The MCP
endpoint itself (``/mcp``) is deliberately NOT probed: it answers 401 by design,
so a 401 there is success, not failure, and using it would make the healthcheck
either always-fail or always-pass.

The port is read from the container's own ``CODING_TOOLS_MCP_PORT`` so that a
non-default port cannot silently turn this probe into a false negative.

Exit 0 = healthy. Exit 1 = unhealthy, with one diagnostic line on stderr.
A probe must never raise, so every failure mode is caught.
"""

from __future__ import annotations

import os
import sys
import urllib.request

PROBE_PATH = "/.well-known/mcp.json"


def main() -> int:
    port = os.environ.get("CODING_TOOLS_MCP_PORT", "8765")
    timeout = float(os.environ.get("CLOUDDESK_HEALTH_TIMEOUT", "5"))
    url = f"http://127.0.0.1:{port}{PROBE_PATH}"

    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            status = getattr(response, "status", 200)
    except Exception as exc:  # noqa: BLE001 - a probe must never propagate
        print(f"unhealthy: {url} -> {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    if status != 200:
        print(f"unhealthy: {url} -> HTTP {status}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
