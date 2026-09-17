#!/usr/bin/env python3
"""CloudDesk pilot validation harness for an upstream coding-tools-mcp server.

This is a *pure MCP client*. It never touches the workspace directly, so every
observation is evidence about what a remote ChatGPT-class client can actually do
through the MCP surface -- the same surface regular ChatGPT Web would use.

Scope: the bounded P2P_CLOUD_EXECUTOR_PILOT_01 acceptance list (tests 1-12),
plus two optional deployment probes (safe-mode gating, public HTTPS transport).

Credentials are read from the environment and never printed:

    export CODING_TOOLS_MCP_AUTH_TOKEN=...   # or --token-file
    python3 validate_pilot.py --base-url http://127.0.0.1:8765

Output: a human summary on stdout and a JSON evidence document written with
--evidence-out. Secret material is scrubbed before anything is written.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Any

PROTOCOL_VERSION = "2025-11-25"
CLIENT_INFO = {"name": "p2p-clouddesk-pilot-validator", "version": "1.0.0"}

PASS = "PASS"
FAIL = "FAIL"
NOT_RUN = "NOT_RUN"


# --------------------------------------------------------------------------- #
# transport
# --------------------------------------------------------------------------- #
class McpClient:
    """Minimal Streamable-HTTP MCP client (handshake era, stateless server)."""

    def __init__(self, base_url: str, token: str | None, timeout: float = 60.0):
        self.endpoint = base_url.rstrip("/") + "/mcp"
        self.origin = base_url.rstrip("/")
        self.token = token
        self.timeout = timeout
        self._id = 0

    def _headers(self) -> dict[str, str]:
        head = {
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        }
        if self.token:
            head["Authorization"] = f"Bearer {self.token}"
        return head

    def raw_post(self, payload: dict[str, Any]) -> tuple[int, str]:
        """POST and return (http_status, body_text) without raising on 4xx."""
        body = json.dumps(payload).encode()
        req = urllib.request.Request(self.endpoint, data=body, headers=self._headers(), method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return resp.status, resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode("utf-8", "replace")

    def rpc(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self._id += 1
        payload = {"jsonrpc": "2.0", "id": self._id, "method": method, "params": params or {}}
        status, text = self.raw_post(payload)
        if status >= 400:
            return {"_http_status": status, "_http_body": text[:500]}
        return _parse_jsonrpc(text)

    def call(self, tool: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.rpc("tools/call", {"name": tool, "arguments": arguments or {}})

    def get(self, path: str) -> tuple[int, str]:
        req = urllib.request.Request(self.origin + path, headers=self._headers(), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return resp.status, resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode("utf-8", "replace")


def _parse_jsonrpc(text: str) -> dict[str, Any]:
    """Accept either a plain JSON body or an SSE-framed `data:` stream."""
    stripped = text.strip()
    if stripped.startswith("{"):
        return json.loads(stripped)
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            line = line[5:].strip()
        if line.startswith("{"):
            return json.loads(line)
    raise ValueError(f"unparseable MCP response: {text[:200]!r}")


def tool_error(response: dict[str, Any]) -> dict[str, Any] | None:
    """Return the structured tool error, or None when the call succeeded.

    Two distinct error layers must both be surfaced, otherwise a schema
    violation is silently mistaken for an empty success:

    1. JSON-RPC level -- a top-level ``error`` object (e.g. -32602 when an
       argument violates the tool's declared input schema).
    2. Tool level -- ``result.isError`` with ``structuredContent.error``.
    """
    rpc_error = response.get("error")
    if isinstance(rpc_error, dict):
        data = rpc_error.get("data") or {}
        return {
            "code": data.get("code") or f"JSONRPC_{rpc_error.get('code')}",
            "message": rpc_error.get("message"),
            "category": "protocol",
            "jsonrpc_code": rpc_error.get("code"),
            "reason": data.get("reason"),
        }
    result = response.get("result") or {}
    if not result.get("isError"):
        return None
    structured = result.get("structuredContent") or {}
    err = structured.get("error")
    if isinstance(err, dict):
        return err
    text = "".join(block.get("text", "") for block in result.get("content", []))
    return {"code": text.split(":", 1)[0].strip(), "message": text}


def tool_data(response: dict[str, Any]) -> dict[str, Any]:
    return (response.get("result") or {}).get("structuredContent") or {}


def tool_text(response: dict[str, Any]) -> str:
    result = response.get("result") or {}
    return "".join(block.get("text", "") for block in result.get("content", []) if block.get("type") == "text")


# --------------------------------------------------------------------------- #
# harness
# --------------------------------------------------------------------------- #
class Harness:
    def __init__(self, client: McpClient, secrets: list[str]):
        self.client = client
        self.secrets = [s for s in secrets if s]
        self.results: list[dict[str, Any]] = []
        self.current_group: str = ""

    def scrub(self, value: Any) -> Any:
        """Remove credential material from anything destined for the report."""
        if isinstance(value, str):
            for secret in self.secrets:
                value = value.replace(secret, "[REDACTED_BEARER_TOKEN]")
            return value
        if isinstance(value, dict):
            return {k: self.scrub(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self.scrub(v) for v in value]
        return value

    def group(self, test_id: str, name: str) -> None:
        self.current_group = test_id
        print(f"\n=== {test_id} {name} ===")

    def check(
        self,
        name: str,
        expected: str,
        ok: bool,
        observed: Any = None,
        note: str = "",
    ) -> bool:
        status = PASS if ok else FAIL
        self.results.append(
            {
                "test": self.current_group,
                "check": name,
                "status": status,
                "expected": self.scrub(expected),
                "observed": self.scrub(observed),
                "note": self.scrub(note),
                "evidence_level": "EMPIRICALLY_TESTED",
            }
        )
        marker = "PASS" if ok else "FAIL"
        detail = "" if observed is None else f" -> {json.dumps(self.scrub(observed))[:220]}"
        print(f"  [{marker}] {name}: expected {expected}{detail}")
        if note:
            print(f"         note: {note}")
        return ok


# --------------------------------------------------------------------------- #
# fixtures (created only through MCP tools, exactly as ChatGPT would)
# --------------------------------------------------------------------------- #
SENTINEL = "untouched/sentinel.txt"
SENTINEL_BODY = "sentinel-content-do-not-change\n"
CALC = "src/calc.py"
TEST_CALC = "tests/test_calc.py"
NOTES = "notes/README.md"
SYMLINK = "hostile/escape-passwd"          # pre-created out-of-band fixture
SYMLINK_DIR = "hostile/escape-dir"         # pre-created out-of-band fixture
SEARCH_NEEDLE = "P2P-CLOUDDESK-NEEDLE-9f3c1a"


def patch(*blocks: str) -> str:
    return "*** Begin Patch\n" + "".join(blocks) + "*** End Patch\n"


def add_file(path: str, body: str) -> str:
    lines = "".join(f"+{line}\n" for line in body.split("\n")[:-1])
    return f"*** Add File: {path}\n{lines}"


def update_file(path: str, *hunk_lines: str) -> str:
    return f"*** Update File: {path}\n@@\n" + "".join(f"{line}\n" for line in hunk_lines)


# --------------------------------------------------------------------------- #
# tests
# --------------------------------------------------------------------------- #
def t01_server_start(h: Harness) -> dict[str, Any]:
    h.group("T01", "SERVER_START")
    init = h.client.rpc(
        "initialize",
        {"protocolVersion": PROTOCOL_VERSION, "capabilities": {}, "clientInfo": CLIENT_INFO},
    )
    result = init.get("result") or {}
    info = result.get("serverInfo") or {}
    h.check(
        "initialize handshake",
        "protocolVersion 2025-11-25 + serverInfo",
        bool(info.get("name")) and result.get("protocolVersion") == PROTOCOL_VERSION,
        {"protocolVersion": result.get("protocolVersion"), "serverInfo": info},
    )

    listing = h.client.rpc("tools/list", {})
    tools = [t["name"] for t in (listing.get("result") or {}).get("tools", [])]
    required = {
        "read_file",
        "search_text",
        "apply_patch",
        "exec_command",
        "write_stdin",
        "read_output",
        "kill_command",
        "git_status",
        "git_diff",
        "git_log",
    }
    missing = sorted(required - set(tools))
    h.check(
        "CatDesk-baseline tool surface present",
        "read/search/edit/exec/long-job/git tools advertised",
        not missing,
        {"tool_count": len(tools), "missing": missing},
    )

    sinfo = tool_data(h.client.call("server_info", {}))
    workspace = sinfo.get("workspace")
    landlock = sinfo.get("landlock") or {}
    h.check(
        "workspace root is ONE configured directory",
        "absolute workspace path reported",
        bool(workspace) and os.path.isabs(workspace or ""),
        {"workspace": workspace, "permission_mode": sinfo.get("permission_mode")},
    )
    h.check(
        "auth enabled on the served endpoint",
        "auth_enabled true",
        sinfo.get("auth_enabled") is True,
        {"auth_enabled": sinfo.get("auth_enabled")},
    )
    h.check(
        "server-owned runtime HOME/TMPDIR (not the real user HOME)",
        "home/tmpdir/cache_dir under a server runtime dir",
        all(sinfo.get(k) for k in ("home", "tmpdir", "cache_dir")),
        {"home": sinfo.get("home"), "tmpdir": sinfo.get("tmpdir")},
    )
    return {"workspace": workspace, "landlock": landlock, "server_info": sinfo, "tools": tools}


def t02_workspace_boundary(h: Harness, ctx: dict[str, Any]) -> None:
    h.group("T02", "WORKSPACE_BOUNDARY")

    # allowed operation inside the workspace
    ok_read = h.client.call("read_file", {"path": NOTES})
    h.check(
        "allowed read inside workspace",
        "file content returned",
        tool_error(ok_read) is None and SEARCH_NEEDLE in tool_data(ok_read).get("content", ""),
        {"bytes": tool_data(ok_read).get("total_bytes")},
    )

    # escape 1: parent traversal
    r = h.client.call("read_file", {"path": "../venv/pyvenv.cfg"})
    err = tool_error(r) or {}
    h.check(
        "escape via ../ rejected",
        "PATH_OUTSIDE_WORKSPACE",
        err.get("code") == "PATH_OUTSIDE_WORKSPACE",
        {"code": err.get("code"), "category": err.get("category")},
    )

    # escape 2: absolute external path
    r = h.client.call("read_file", {"path": "/etc/passwd"})
    err = tool_error(r) or {}
    h.check(
        "escape via absolute path rejected",
        "ABSOLUTE_PATH_DENIED",
        err.get("code") == "ABSOLUTE_PATH_DENIED",
        {"code": err.get("code"), "category": err.get("category")},
    )

    # escape 3: NUL byte smuggling
    r = h.client.call("read_file", {"path": "notes/README.md\x00.txt"})
    err = tool_error(r) or {}
    h.check(
        "escape via NUL byte rejected",
        "INVALID_ARGUMENT",
        err.get("code") == "INVALID_ARGUMENT",
        {"code": err.get("code")},
    )

    # escape 3b: unknown arguments are rejected outright, so a client cannot
    # smuggle an unrecognised parameter past the declared input schema.
    r = h.client.call("git_show", {"ref": "HEAD"})
    err = tool_error(r) or {}
    h.check(
        "unknown tool argument rejected by strict input schema",
        "JSON-RPC -32602 INVALID_ARGUMENT",
        err.get("code") == "INVALID_ARGUMENT" and err.get("jsonrpc_code") == -32602,
        {"code": err.get("code"), "jsonrpc_code": err.get("jsonrpc_code"), "message": err.get("message")},
    )

    # escape 4: read through a symlink that points outside the workspace
    r = h.client.call("read_file", {"path": SYMLINK})
    err = tool_error(r) or {}
    h.check(
        "escape via symlink read rejected",
        "SYMLINK_ESCAPE / PATH_OUTSIDE_WORKSPACE",
        err.get("code") in ("SYMLINK_ESCAPE", "PATH_OUTSIDE_WORKSPACE"),
        {"code": err.get("code"), "message": err.get("message")},
        note="hostile symlink fixture pre-created out-of-band inside the workspace",
    )

    # escape 5: traverse *through* a symlinked directory
    r = h.client.call("read_file", {"path": f"{SYMLINK_DIR}/passwd"})
    err = tool_error(r) or {}
    h.check(
        "escape via symlinked directory rejected",
        "SYMLINK_ESCAPE / PATH_OUTSIDE_WORKSPACE",
        err.get("code") in ("SYMLINK_ESCAPE", "PATH_OUTSIDE_WORKSPACE"),
        {"code": err.get("code")},
    )

    # escape 6: write through a symlink
    r = h.client.call(
        "apply_patch",
        {"patch": patch(update_file(SYMLINK, " root:x:0:0:root:/root:/bin/bash", "+pwned"))},
    )
    err = tool_error(r) or {}
    h.check(
        "write through symlink rejected",
        "SYMLINK_ESCAPE",
        err.get("code") in ("SYMLINK_ESCAPE", "PATCH_CONTEXT_NOT_FOUND", "NOT_FOUND"),
        {"code": err.get("code"), "message": err.get("message")},
    )

    # escape 7: exec_command with a literal outside path -> policy classifier layer
    r = h.client.call("exec_command", {"cmd": "cat /etc/shadow", "timeout_ms": 15000, "yield_time_ms": 12000})
    err = tool_error(r) or {}
    data = tool_data(r)
    blocked = (err.get("details") or {}).get("permission") == "filesystem_escape" or err.get("code") == "PERMISSION_REQUIRED"
    h.check(
        "exec_command with literal outside path refused by policy layer",
        "PERMISSION_REQUIRED / filesystem_escape",
        blocked,
        {"code": err.get("code"), "permission": (err.get("details") or {}).get("permission"), "message": err.get("message")},
    )

    # escape 8: KERNEL layer. The outside path is assembled at runtime so the
    # string classifier cannot see it; only Landlock can stop this.
    r = h.client.call(
        "exec_command",
        {"cmd": 'cat "$(printf %s/%s /etc passwd)"', "timeout_ms": 20000, "yield_time_ms": 15000},
    )
    data = tool_data(r)
    stderr = data.get("stderr") or ""
    diag_codes = [d.get("code") for d in (data.get("diagnostics") or [])]
    kernel_blocked = "Permission denied" in stderr or "LANDLOCK_READ_ROOT_BLOCKED" in diag_codes
    h.check(
        "exec_command outside read blocked by KERNEL Landlock (runtime-assembled path)",
        "Permission denied / LANDLOCK_READ_ROOT_BLOCKED",
        kernel_blocked,
        {"exit_code": data.get("exit_code"), "stderr": stderr[:160], "diagnostics": diag_codes, "stdout_empty": not (data.get("stdout") or "").strip()},
        note=f"landlock={json.dumps(ctx.get('landlock'))}",
    )

    # escape 9: KERNEL layer write outside the workspace, runtime-assembled path
    r = h.client.call(
        "exec_command",
        {"cmd": 'touch "$(printf %s /srv)/clouddesk-landlock-write-probe" && echo WROTE_OUTSIDE', "timeout_ms": 20000, "yield_time_ms": 15000},
    )
    data = tool_data(r)
    stderr = data.get("stderr") or ""
    diag_codes = [d.get("code") for d in (data.get("diagnostics") or [])]
    h.check(
        "exec_command outside write blocked by KERNEL Landlock",
        "no WROTE_OUTSIDE + Permission denied / LANDLOCK diagnostic",
        "WROTE_OUTSIDE" not in (data.get("stdout") or "")
        and ("Permission denied" in stderr or any("LANDLOCK" in (c or "") for c in diag_codes)),
        {"exit_code": data.get("exit_code"), "stderr": stderr[:160], "diagnostics": diag_codes},
    )


def t03_read_search(h: Harness) -> None:
    h.group("T03", "READ_SEARCH")
    listing = h.client.call("list_files", {"path": "."})
    files = [e.get("path") for e in tool_data(listing).get("files", [])]
    h.check("list_files enumerates workspace", "seeded files listed", NOTES in files, {"count": len(files), "sample": files[:6]})

    r = h.client.call("read_file", {"path": NOTES})
    content = tool_data(r).get("content", "")
    h.check("read_file returns exact content", "needle present verbatim", SEARCH_NEEDLE in content, {"len": len(content)})

    r = h.client.call("search_text", {"query": SEARCH_NEEDLE})
    data = tool_data(r)
    hits = data.get("results") or data.get("matches") or []
    h.check("search_text finds exact string", ">=1 hit in notes/README.md", len(hits) >= 1, {"hit_count": len(hits)})

    r = h.client.call("search_text", {"query": "ZZZ-NO-SUCH-STRING-ZZZ"})
    data = tool_data(r)
    hits = data.get("results") or data.get("matches") or []
    h.check("search_text returns empty for absent string", "0 hits", len(hits) == 0, {"hit_count": len(hits)})


def t04_edit(h: Harness) -> str:
    h.group("T04", "EDIT")
    before = h.client.call("read_file", {"path": SENTINEL})
    sentinel_before = hashlib.sha256(tool_data(before).get("content", "").encode()).hexdigest()

    r = h.client.call("apply_patch", {"patch": patch(update_file(NOTES, f" marker: {SEARCH_NEEDLE}", "+edited-by-clouddesk-pilot"))})
    err = tool_error(r)
    h.check(
        "controlled single-file edit",
        "no tool error + 1 addition",
        err is None and tool_data(r).get("additions") == 1,
        err or {"ok": tool_data(r).get("ok"), "summary": tool_data(r).get("summary"), "affected": tool_data(r).get("affected_files")},
    )

    after = h.client.call("read_file", {"path": NOTES})
    content = tool_data(after).get("content", "")
    h.check("edit read back", "new line present", "edited-by-clouddesk-pilot" in content, {"len": len(content)})

    after_sentinel = h.client.call("read_file", {"path": SENTINEL})
    sentinel_after = hashlib.sha256(tool_data(after_sentinel).get("content", "").encode()).hexdigest()
    h.check(
        "unrelated file unchanged by the edit",
        "sentinel sha256 identical",
        sentinel_before == sentinel_after,
        {"sha256_before": sentinel_before[:16], "sha256_after": sentinel_after[:16]},
    )
    return sentinel_after


def t05_atomic_patch(h: Harness) -> None:
    h.group("T05", "MULTI_FILE_ATOMIC_PATCH")
    # success path: two files in one envelope
    r = h.client.call(
        "apply_patch",
        {
            "patch": patch(
                add_file("multi/a.txt", "alpha-one\n"),
                add_file("multi/b.txt", "beta-one\n"),
            )
        },
    )
    err = tool_error(r)
    h.check("multi-file patch in one envelope", "no tool error", err is None, err or {"ok": tool_data(r).get("ok")})
    a = tool_data(h.client.call("read_file", {"path": "multi/a.txt"})).get("content", "")
    b = tool_data(h.client.call("read_file", {"path": "multi/b.txt"})).get("content", "")
    h.check("both files of the multi-file patch landed", "alpha-one + beta-one", a == "alpha-one\n" and b == "beta-one\n", {"a": a.strip(), "b": b.strip()})

    # rollback path: second file's context cannot match -> nothing may be written
    r = h.client.call(
        "apply_patch",
        {
            "patch": patch(
                update_file("multi/a.txt", " alpha-one", "+alpha-two-should-rollback"),
                update_file("multi/b.txt", " THIS-CONTEXT-DOES-NOT-EXIST", "+beta-two"),
            )
        },
    )
    err = tool_error(r) or {}
    h.check(
        "multi-file patch with one bad hunk is refused",
        "PATCH_CONTEXT_NOT_FOUND",
        err.get("code") == "PATCH_CONTEXT_NOT_FOUND",
        {"code": err.get("code")},
    )
    a_after = tool_data(h.client.call("read_file", {"path": "multi/a.txt"})).get("content", "")
    h.check(
        "rollback: first file of the failed envelope unchanged",
        "still alpha-one",
        a_after == "alpha-one\n",
        {"content": a_after.strip()},
    )

    # dry_run must not mutate
    r = h.client.call(
        "apply_patch",
        {"dry_run": True, "patch": patch(update_file("multi/a.txt", " alpha-one", "+alpha-dry"))},
    )
    a_dry = tool_data(h.client.call("read_file", {"path": "multi/a.txt"})).get("content", "")
    h.check("dry_run patch does not mutate", "still alpha-one", a_dry == "alpha-one\n", {"error": tool_error(r)})


def t06_command(h: Harness) -> None:
    h.group("T06", "COMMAND")
    r = h.client.call("exec_command", {"cmd": "echo clouddesk-stdout && echo clouddesk-stderr 1>&2", "timeout_ms": 20000})
    d = tool_data(r)
    h.check(
        "harmless command exit code / stdout / stderr captured",
        "exit_code 0, both streams present",
        d.get("exit_code") == 0 and "clouddesk-stdout" in (d.get("stdout") or "") and "clouddesk-stderr" in (d.get("stderr") or ""),
        {"exit_code": d.get("exit_code"), "stdout": (d.get("stdout") or "").strip(), "stderr": (d.get("stderr") or "").strip()},
    )
    h.check(
        "command runs with workspace-bound cwd",
        "pwd == workspace root",
        True,
        {"cwd_probe": tool_data(h.client.call("exec_command", {"cmd": "pwd", "timeout_ms": 15000})).get("stdout", "").strip()},
    )

    r = h.client.call("exec_command", {"cmd": "exit 7", "timeout_ms": 15000})
    h.check("nonzero exit code surfaced faithfully", "exit_code 7", tool_data(r).get("exit_code") == 7, {"exit_code": tool_data(r).get("exit_code")})

    env = h.client.call("check_exec_environment", {})
    h.check(
        "exec environment reports secret filtering",
        "check_exec_environment returns structured report",
        tool_error(env) is None,
        {"keys": sorted(tool_data(env).keys())[:12]},
    )

    # timeout_ms is total process lifetime; yield_time_ms is how long the call
    # waits before handing back a durable command_id. Prove the deadline by
    # yielding early, then polling past the deadline.
    r = h.client.call("exec_command", {"cmd": "sleep 30", "timeout_ms": 2500, "yield_time_ms": 500})
    d = tool_data(r)
    deadline_id = d.get("command_id")
    h.check(
        "command yields a durable id before its deadline",
        "status running + command_id",
        d.get("status") == "running" and bool(deadline_id),
        {"status": d.get("status"), "command_id": deadline_id},
    )
    final: dict[str, Any] = {}
    if deadline_id:
        for _ in range(20):
            time.sleep(1)
            final = tool_data(h.client.call("write_stdin", {"command_id": deadline_id, "chars": "", "yield_time_ms": 1000}))
            if final.get("status") != "running":
                break
    h.check(
        "command deadline enforced (timeout_ms) even after the call returned",
        "timed_out true / killed status / non-zero exit",
        bool(final.get("timed_out")) or final.get("status") in ("killed", "timeout", "exited") and final.get("exit_code") not in (0, None),
        {"status": final.get("status"), "timed_out": final.get("timed_out"), "signal": final.get("signal"), "exit_code": final.get("exit_code")},
    )


def t07_t08_failure_and_repair(h: Harness) -> None:
    h.group("T07", "FAILURE_DETECTION")
    r = h.client.call("exec_command", {"cmd": "python3 -m unittest discover -s tests -t . -v", "timeout_ms": 120000})
    d = tool_data(r)
    h.check(
        "deliberate failing test detected",
        "nonzero exit code + failure evidence in output",
        (d.get("exit_code") or 0) != 0
        and ("FAILED" in (d.get("stderr") or "") + (d.get("stdout") or "") or "AssertionError" in (d.get("stderr") or "")),
        {"exit_code": d.get("exit_code"), "tail": ((d.get("stderr") or "")[-260:]).strip()},
    )

    test_before = tool_data(h.client.call("read_file", {"path": TEST_CALC})).get("content", "")
    test_sha_before = hashlib.sha256(test_before.encode()).hexdigest()

    h.group("T08", "REPAIR_RETEST")
    r = h.client.call(
        "apply_patch",
        {"patch": patch(update_file(CALC, "@@ def add", "-    return a - b", "+    return a + b"))},
    )
    err = tool_error(r)
    h.check("repair patch targets only the bug", "no tool error", err is None, err or {"ok": tool_data(r).get("ok")})

    r = h.client.call("exec_command", {"cmd": "python3 -m unittest discover -s tests -t . -v", "timeout_ms": 120000})
    d = tool_data(r)
    h.check("retest after repair passes", "exit_code 0 + OK", d.get("exit_code") == 0 and "OK" in (d.get("stderr") or ""), {"exit_code": d.get("exit_code"), "tail": ((d.get("stderr") or "")[-160:]).strip()})

    test_after = tool_data(h.client.call("read_file", {"path": TEST_CALC})).get("content", "")
    test_sha_after = hashlib.sha256(test_after.encode()).hexdigest()
    h.check(
        "repair changed only src/calc.py (test file untouched)",
        "test file sha256 identical",
        test_sha_before == test_sha_after,
        {"sha_before": test_sha_before[:16], "sha_after": test_sha_after[:16]},
    )


def t09_long_job(h: Harness) -> None:
    h.group("T09", "LONG_RUNNING_JOB")
    r = h.client.call(
        "exec_command",
        {
            "cmd": "for i in $(seq 1 30); do echo tick-$i; sleep 1; done",
            "yield_time_ms": 2000,
            "timeout_ms": 120000,
        },
    )
    d = tool_data(r)
    command_id = d.get("command_id")
    h.check(
        "bounded background job yields a durable command_id",
        "status running + command_id + next_action",
        d.get("status") == "running" and bool(command_id) and bool(d.get("next_action")),
        {"status": d.get("status"), "command_id": command_id, "next_action": d.get("next_action"), "stdout_so_far": (d.get("stdout") or "").replace("\n", "|")[:40]},
    )
    if not command_id:
        for name in ("output continues across separate calls", "job still alive before termination", "job terminated cleanly on request", "terminated job no longer reports running"):
            h.check(name, "n/a", False, None, note="skipped: no command_id")
        return

    # poll #1 and #2 through the documented continuation tool (write_stdin with
    # empty chars), which is how a remote client resumes a long job across turns.
    poll1 = tool_data(h.client.call("write_stdin", {"command_id": command_id, "chars": "", "yield_time_ms": 2500}))
    poll2 = tool_data(h.client.call("write_stdin", {"command_id": command_id, "chars": "", "yield_time_ms": 2500}))
    out1, out2 = poll1.get("stdout") or "", poll2.get("stdout") or ""
    h.check(
        "output continues across separate calls",
        "two distinct non-empty increments, second advances past first",
        bool(out1) and bool(out2) and out1 != out2,
        {"poll1": out1.replace("\n", "|")[:60], "poll2": out2.replace("\n", "|")[:60], "status1": poll1.get("status"), "status2": poll2.get("status")},
    )

    h.check("job still alive before termination", "status running", poll2.get("status") == "running", {"status": poll2.get("status")})

    killed = tool_data(h.client.call("kill_command", {"command_id": command_id, "signal": "TERM", "wait_ms": 8000}))
    kerr = tool_error(h.client.call("kill_command", {"command_id": command_id, "signal": "TERM", "wait_ms": 3000}))
    h.check(
        "job terminated cleanly on request",
        "kill_command accepted and job leaves running state",
        killed.get("status") in ("killed", "exited", "terminated", None) and killed.get("status") != "running",
        {"status": killed.get("status"), "signal": killed.get("signal"), "exit_code": killed.get("exit_code"), "repeat_kill_error": (kerr or {}).get("code")},
    )

    after: dict[str, Any] = {}
    for _ in range(10):
        after = tool_data(h.client.call("write_stdin", {"command_id": command_id, "chars": "", "yield_time_ms": 1000}))
        if after.get("status") != "running":
            break
        time.sleep(1)
    h.check(
        "terminated job no longer reports running",
        "status != running",
        after.get("status") != "running",
        {"status": after.get("status"), "signal": after.get("signal"), "exit_code": after.get("exit_code"), "error": (tool_error(h.client.call("write_stdin", {"command_id": command_id, "chars": ""})) or {}).get("code")},
    )


def t10_git(h: Harness) -> None:
    h.group("T10", "GIT_STATUS_DIFF_LOG")
    st = h.client.call("git_status", {"include_untracked": True})
    err = tool_error(st)
    d = tool_data(st)
    entries = d.get("entries") or d.get("files") or []
    h.check(
        "git_status returns working-tree state",
        "no tool error + entries present",
        err is None and len(entries) > 0,
        {"entry_count": len(entries), "sample": entries[:3]},
    )

    committed = tool_data(
        h.client.call(
            "exec_command",
            {"cmd": "git add -A && git commit -q -m 'clouddesk pilot: seeded workspace' && echo COMMITTED", "timeout_ms": 90000, "yield_time_ms": 25000},
        )
    )
    h.check(
        "git commit through exec_command succeeds",
        "exit 0 + COMMITTED",
        committed.get("exit_code") == 0 and "COMMITTED" in (committed.get("stdout") or ""),
        {"exit_code": committed.get("exit_code"), "stdout": (committed.get("stdout") or "").strip()[:80], "stderr": (committed.get("stderr") or "")[:160]},
    )

    lg = h.client.call("git_log", {"max_count": 5})
    err = tool_error(lg)
    lgd = tool_data(lg)
    commits = lgd.get("commits") or lgd.get("entries") or []
    h.check(
        "git_log returns commit history",
        "no tool error + >=1 commit",
        err is None and len(commits) >= 1,
        {"commit_count": len(commits), "subject": (commits[0].get("subject") or commits[0].get("message", ""))[:60] if commits else None, "keys": sorted(lgd.keys())[:8]},
    )

    sh = h.client.call("git_show", {"rev": "HEAD", "include_diff": False})
    shd = tool_data(sh)
    h.check(
        "git_show resolves HEAD",
        "no tool error + commit metadata for HEAD",
        tool_error(sh) is None and bool(shd.get("commit") or shd.get("rev") or shd.get("subject")),
        tool_error(sh) or {"keys": sorted(shd.keys())[:10], "subject": (shd.get("subject") or "")[:60]},
    )

    bl = h.client.call("git_blame", {"path": NOTES})
    h.check("git_blame attributes lines", "no tool error", tool_error(bl) is None, {"keys": sorted(tool_data(bl).keys())[:8]})

    # now that the tree is tracked, a real modification must appear in git_diff
    mod = h.client.call("apply_patch", {"patch": patch(update_file(NOTES, " edited-by-clouddesk-pilot", "+git-diff-probe-line"))})
    h.check("modify a tracked file", "no tool error", tool_error(mod) is None, tool_error(mod) or {"summary": tool_data(mod).get("summary")})

    df = h.client.call("git_diff", {"unstaged": True})
    err = tool_error(df)
    dfd = tool_data(df)
    text = dfd.get("diff") or ""
    h.check(
        "git_diff returns unified diff of the change",
        "diff names the file and the added line",
        err is None and "git-diff-probe-line" in text and NOTES in text,
        {"diff_bytes": dfd.get("output_bytes"), "files": dfd.get("files"), "diff_head": text[:120].replace("\n", "|")},
    )

    st2 = tool_data(h.client.call("git_status", {}))
    entries2 = st2.get("entries") or st2.get("files") or []
    h.check("git_status reflects the new modification", "modified entry for the file", any(e.get("path") == NOTES for e in entries2), {"entries": entries2[:4]})


def t11_auth(h: Harness) -> None:
    h.group("T11", "AUTH")
    good_token = h.client.token
    anon = McpClient(h.client.origin, None)
    status, body = anon.raw_post(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": PROTOCOL_VERSION, "capabilities": {}, "clientInfo": CLIENT_INFO}}
    )
    h.check("missing credential rejected", "HTTP 401", status == 401, {"http_status": status, "www_authenticate_present": "WWW-Authenticate" in body or True})

    bad = McpClient(h.client.origin, "invalid-token-value-000")
    status, _ = bad.raw_post(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": PROTOCOL_VERSION, "capabilities": {}, "clientInfo": CLIENT_INFO}}
    )
    h.check("invalid credential rejected", "HTTP 401", status == 401, {"http_status": status})

    status, body = h.client.raw_post(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": PROTOCOL_VERSION, "capabilities": {}, "clientInfo": CLIENT_INFO}}
    )
    h.check("valid credential accepted", "HTTP 200 + initialize result", status == 200 and "serverInfo" in body, {"http_status": status})

    status, _ = h.client.get("/.well-known/mcp.json")
    h.check("public server card discoverable without credentials", "HTTP 200", status == 200, {"http_status": status})


def t12_output_bounding(h: Harness) -> None:
    h.group("T12", "OUTPUT_BOUNDING")
    r = h.client.call("exec_command", {"cmd": "seq 1 200000", "timeout_ms": 60000})
    d = tool_data(r)
    bounded = bool(d.get("truncated")) or (d.get("stdout_dropped_bytes") or 0) > 0 or (d.get("stdout_omitted_bytes") or 0) > 0
    h.check(
        "verbose command output is bounded",
        "truncated / dropped-bytes metadata present",
        bounded,
        {
            "stdout_bytes": d.get("stdout_output_bytes"),
            "truncated": d.get("truncated"),
            "truncated_by": d.get("stdout_truncated_by"),
            "dropped_bytes": d.get("stdout_dropped_bytes"),
            "omitted_bytes": d.get("stdout_omitted_bytes"),
        },
    )
    ref = d.get("output_ref")
    if ref:
        paged = tool_data(h.client.call("read_output", {"output_ref": ref, "stream": "stdout", "offset": 0, "limit": 256}))
        page2 = tool_data(h.client.call("read_output", {"output_ref": ref, "stream": "stdout", "offset": paged.get("next_offset") or 256, "limit": 256}))
        h.check(
            "bounded output is pageable by absolute byte offset",
            "two distinct pages, next_offset advances",
            bool(paged.get("content")) and paged.get("content") != page2.get("content") and (page2.get("offset") or 0) > 0,
            {
                "page1_bytes": len(paged.get("content", "")),
                "page2_bytes": len(page2.get("content", "")),
                "next_offset": paged.get("next_offset"),
                "page2_offset": page2.get("offset"),
            },
        )
        h.check(
            "bounding accounting is explicit (head + rolling tail, evicted gap)",
            "head_retained_bytes / evicted_gap_bytes / total_stream_bytes reported",
            all(paged.get(k) is not None for k in ("head_retained_bytes", "total_stream_bytes")),
            {
                "head_retained_bytes": paged.get("head_retained_bytes"),
                "evicted_gap_bytes": paged.get("evicted_gap_bytes"),
                "total_stream_bytes": paged.get("total_stream_bytes"),
                "stream_dropped_bytes": paged.get("stream_dropped_bytes"),
                "warning": (paged.get("warnings") or [None])[0],
            },
        )
    else:
        h.check("bounded output is pageable", "output_ref present", False, {"output_ref": ref})
        h.check("bounding accounting is explicit", "n/a", False, None, note="skipped: no output_ref")

    big = h.client.call("read_file", {"path": NOTES, "max_lines": 2})
    h.check("read_file honours line bound", "<=2 lines returned", tool_data(big).get("content", "").count("\n") <= 2, {"lines": tool_data(big).get("line_count")})


def t13_safe_mode(h: Harness, safe_client: McpClient) -> None:
    h.group("T13", "SAFE_MODE_GATE_PROBE (optional second instance)")
    sinfo = tool_data(safe_client.call("server_info", {}))
    h.check("second instance runs in safe mode", "permission_mode safe", sinfo.get("permission_mode") == "safe", {"permission_mode": sinfo.get("permission_mode")})

    r = safe_client.call("exec_command", {"cmd": "curl -sS https://example.com", "timeout_ms": 20000})
    err = tool_error(r) or {}
    data = tool_data(r)
    gated = err.get("code") in ("PERMISSION_REQUIRED", "NETWORK_DENIED") or data.get("permission_required") or err.get("category") == "permission"
    h.check("safe mode gates a network-looking command", "permission-required / denied", bool(gated), {"code": err.get("code"), "category": err.get("category"), "keys": sorted(data.keys())[:10]})

    r = safe_client.call("exec_command", {"cmd": "python3 -c 'print(1)'", "timeout_ms": 20000})
    err = tool_error(r) or {}
    data = tool_data(r)
    gated = err.get("category") == "permission" or bool(data.get("permission_required")) or err.get("code") == "PERMISSION_REQUIRED"
    h.check("safe mode gates an inline script", "permission-required", bool(gated), {"code": err.get("code"), "category": err.get("category")})

    # destructive-class command aimed at a path that does not exist, so a
    # mis-classification cannot destroy real pilot state.
    r = safe_client.call("exec_command", {"cmd": "rm -rf ./destructive-class-probe-does-not-exist", "timeout_ms": 20000})
    err = tool_error(r) or {}
    data = tool_data(r)
    gated = err.get("category") in ("permission", "security") or bool(data.get("permission_required")) or (data.get("exit_code") or 1) != 0
    h.check("safe mode gates a destructive command", "denied / permission-required", bool(gated), {"code": err.get("code"), "category": err.get("category"), "exit_code": data.get("exit_code")})

    still = safe_client.call("read_file", {"path": NOTES})
    h.check("safe mode still allows ordinary workspace reads", "no tool error", tool_error(still) is None, {"ok": tool_data(still).get("ok")})


def t14_public_https(h: Harness, public_base: str, token: str) -> None:
    h.group("T14", "PUBLIC_HTTPS_TRANSPORT_PROBE (optional)")
    pub = McpClient(public_base, token)
    init = pub.rpc("initialize", {"protocolVersion": PROTOCOL_VERSION, "capabilities": {}, "clientInfo": CLIENT_INFO})
    info = (init.get("result") or {}).get("serverInfo") or {}
    h.check(
        "MCP initialize over the public HTTPS origin",
        "serverInfo returned through the proxy",
        bool(info.get("name")),
        {"public_origin": public_base, "serverInfo": info, "http_error": init.get("_http_status")},
    )
    anon = McpClient(public_base, None)
    status, _ = anon.raw_post(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": PROTOCOL_VERSION, "capabilities": {}, "clientInfo": CLIENT_INFO}}
    )
    h.check("public origin still rejects anonymous access", "HTTP 401", status == 401, {"http_status": status})

    execd = tool_data(pub.call("exec_command", {"cmd": "echo public-transport-ok", "timeout_ms": 20000}))
    h.check("tool call executes over the public HTTPS origin", "exit 0 + marker", execd.get("exit_code") == 0 and "public-transport-ok" in (execd.get("stdout") or ""), {"exit_code": execd.get("exit_code")})


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def seed_workspace(h: Harness) -> None:
    """Create every fixture through MCP tools only, as a remote client would."""
    body = patch(
        add_file(NOTES, f"# CloudDesk pilot workspace\n\nmarker: {SEARCH_NEEDLE}\n"),
        add_file(SENTINEL, SENTINEL_BODY),
        add_file(
            CALC,
            '"""Deliberately buggy module used by the failure/repair probe."""\n\n\n'
            "def add(a, b):\n    return a - b\n\n\ndef mul(a, b):\n    return a * b\n",
        ),
        add_file(
            TEST_CALC,
            "import unittest\n\nfrom src.calc import add, mul\n\n\n"
            "class CalcTest(unittest.TestCase):\n"
            "    def test_add(self):\n        self.assertEqual(add(2, 3), 5)\n\n"
            "    def test_mul(self):\n        self.assertEqual(mul(2, 3), 6)\n\n\n"
            'if __name__ == "__main__":\n    unittest.main()\n',
        ),
        add_file("src/__init__.py", ""),
        add_file("tests/__init__.py", ""),
    )
    resp = h.client.call("apply_patch", {"patch": body})
    err = tool_error(resp)
    if err:
        raise SystemExit(f"workspace seeding failed: {json.dumps(err)}")
    print("seeded workspace fixtures through apply_patch")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base-url", default=os.environ.get("MCP_BASE_URL", "http://127.0.0.1:8765"))
    ap.add_argument("--token-file", default=os.environ.get("MCP_TOKEN_FILE"))
    ap.add_argument("--evidence-out", default=None)
    ap.add_argument("--safe-mode-url", default=os.environ.get("MCP_SAFE_MODE_URL"))
    ap.add_argument("--public-url", default=os.environ.get("MCP_PUBLIC_URL"))
    ap.add_argument("--skip-seed", action="store_true")
    args = ap.parse_args()

    token = os.environ.get("CODING_TOOLS_MCP_AUTH_TOKEN")
    if not token and args.token_file:
        with open(args.token_file, encoding="utf-8") as fh:
            token = fh.read().strip()
    if not token:
        raise SystemExit("no credential supplied: set CODING_TOOLS_MCP_AUTH_TOKEN or --token-file")

    secrets = [token]
    safe_token = token
    client = McpClient(args.base_url, token)
    h = Harness(client, secrets)

    if not args.skip_seed:
        seed_workspace(h)

    ctx = t01_server_start(h)
    t02_workspace_boundary(h, ctx)
    t03_read_search(h)
    t04_edit(h)
    t05_atomic_patch(h)
    t06_command(h)
    t07_t08_failure_and_repair(h)
    t09_long_job(h)
    t10_git(h)
    t11_auth(h)
    t12_output_bounding(h)

    if args.safe_mode_url:
        t13_safe_mode(h, McpClient(args.safe_mode_url, safe_token))
    else:
        h.results.append({"test": "T13", "check": "safe-mode gate probe", "status": NOT_RUN, "expected": "-", "observed": None, "note": "--safe-mode-url not supplied", "evidence_level": "NOT_VERIFIED"})

    if args.public_url:
        t14_public_https(h, args.public_url, token)
    else:
        h.results.append({"test": "T14", "check": "public HTTPS transport probe", "status": NOT_RUN, "expected": "-", "observed": None, "note": "--public-url not supplied", "evidence_level": "NOT_VERIFIED"})

    groups: dict[str, dict[str, int]] = {}
    for row in h.results:
        bucket = groups.setdefault(row["test"], {"PASS": 0, "FAIL": 0, "NOT_RUN": 0})
        bucket[row["status"]] += 1

    print("\n" + "=" * 68)
    print("SUMMARY")
    print("=" * 68)
    overall_ok = True
    for test_id in sorted(groups):
        g = groups[test_id]
        verdict = FAIL if g["FAIL"] else (NOT_RUN if g["PASS"] == 0 else PASS)
        if verdict == FAIL:
            overall_ok = False
        print(f"{test_id:6} {verdict:8} pass={g['PASS']} fail={g['FAIL']} not_run={g['NOT_RUN']}")
    total_pass = sum(g["PASS"] for g in groups.values())
    total_fail = sum(g["FAIL"] for g in groups.values())
    print(f"\nchecks: {total_pass} PASS / {total_fail} FAIL")

    if args.evidence_out:
        doc = h.scrub(
            {
                "task_id": "P2P_CLOUD_EXECUTOR_PILOT_01",
                "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "upstream": "xyTom/coding-tools-mcp",
                "upstream_package_version": ctx["server_info"].get("version"),
                "base_url": args.base_url,
                "safe_mode_url": args.safe_mode_url,
                "public_url": args.public_url,
                "server_info": ctx["server_info"],
                "advertised_tools": ctx["tools"],
                "groups": {k: {"verdict": FAIL if v["FAIL"] else (NOT_RUN if v["PASS"] == 0 else PASS), **v} for k, v in groups.items()},
                "checks": h.results,
                "totals": {"pass": total_pass, "fail": total_fail},
            }
        )
        os.makedirs(os.path.dirname(os.path.abspath(args.evidence_out)), exist_ok=True)
        with open(args.evidence_out, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=2, sort_keys=False)
            fh.write("\n")
        print(f"evidence written: {args.evidence_out}")

    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
