from __future__ import annotations

import os
import shlex
import sys
from typing import List

from pandastack import Sandbox


TTL_SECONDS = 900
PORT = 8765
DEFAULT_CLONE_URL = "https://github.com/octocat/Hello-World.git"


def fail(message: str, code: int = 1) -> int:
    print("PANDASTACK_SPIKE_RESULT=FAIL")
    print(f"ERROR={message}")
    return code


def main() -> int:
    if not os.getenv("PANDASTACK_API_KEY"):
        print("PANDASTACK_SPIKE_RESULT=BLOCKED")
        print("OWNER_GATE=PANDASTACK_API_KEY_REQUIRED")
        return 3

    clone_url = os.getenv("P2P_SPIKE_CLONE_URL", DEFAULT_CLONE_URL)
    sandboxes: List[Sandbox] = []

    try:
        parent = Sandbox.create(
            template="code-interpreter",
            ttl_seconds=TTL_SECONDS,
            metadata={"purpose": "p2p-pandastack-spike-001", "role": "parent"},
        )
        sandboxes.append(parent)
        print(f"PARENT_SANDBOX_ID={parent.id}")

        probe = parent.exec(
            'python3 -c "import platform; print(platform.system()); print(2 + 2)"',
            timeout_seconds=30,
        )
        if probe.exit_code != 0 or "4" not in probe.stdout:
            return fail("COMMAND_EXECUTION_FAILED")

        parent.filesystem.write(
            "/workspace/p2p-spike-marker.txt",
            "parent-prepared-state\n",
        )
        marker = parent.filesystem.read("/workspace/p2p-spike-marker.txt")
        if "parent-prepared-state" not in marker:
            return fail("FILESYSTEM_ROUNDTRIP_FAILED")

        clone_cmd = (
            "rm -rf /workspace/repo && "
            f"git clone --depth 1 {shlex.quote(clone_url)} /workspace/repo && "
            "git -C /workspace/repo rev-parse --is-inside-work-tree"
        )
        clone = parent.exec(clone_cmd, timeout_seconds=120)
        if clone.exit_code != 0 or "true" not in clone.stdout.lower():
            return fail("GIT_CLONE_FAILED")

        parent.filesystem.write(
            "/workspace/preview/index.html",
            "<!doctype html><meta charset='utf-8'>"
            "<title>P2P PandaStack Spike</title>"
            "<h1>P2P PandaStack Spike 001</h1>"
            "<p>Sandbox preview is alive.</p>",
        )
        server = parent.exec(
            f"mkdir -p /workspace/preview && "
            f"nohup python3 -m http.server {PORT} "
            "--directory /workspace/preview "
            ">/tmp/p2p-preview.log 2>&1 </dev/null & echo $!",
            timeout_seconds=30,
        )
        if server.exit_code != 0:
            return fail("PREVIEW_SERVER_START_FAILED")

        preview_url = parent.preview_url(PORT)
        print(f"PREVIEW_URL={preview_url}")

        child = parent.fork(metadata={"purpose": "p2p-pandastack-spike-001", "role": "child"})
        sandboxes.append(child)
        print(f"CHILD_SANDBOX_ID={child.id}")

        inherited = child.filesystem.read("/workspace/p2p-spike-marker.txt")
        if "parent-prepared-state" not in inherited:
            return fail("FORK_STATE_INHERITANCE_FAILED")

        child.filesystem.write(
            "/workspace/p2p-spike-marker.txt",
            "child-diverged-state\n",
        )
        parent_after = parent.filesystem.read("/workspace/p2p-spike-marker.txt")
        child_after = child.filesystem.read("/workspace/p2p-spike-marker.txt")

        if "parent-prepared-state" not in parent_after:
            return fail("PARENT_MUTATED_BY_CHILD")
        if "child-diverged-state" not in child_after:
            return fail("CHILD_DIVERGENCE_FAILED")

        print("COMMAND_EXECUTION=PASS")
        print("FILESYSTEM_ROUNDTRIP=PASS")
        print("GIT_CLONE=PASS")
        print("PREVIEW_URL_GENERATION=PASS")
        print("FORK_AND_DIVERGENCE=PASS")
        print("PANDASTACK_SPIKE_RESULT=PASS")
        return 0

    except Exception as exc:
        return fail(f"{type(exc).__name__}:{exc}")

    finally:
        cleanup_errors = []
        for sandbox in reversed(sandboxes):
            try:
                sandbox.kill()
            except Exception as exc:
                cleanup_errors.append(f"{getattr(sandbox, 'id', 'unknown')}:{type(exc).__name__}")
        if cleanup_errors:
            print("CLEANUP_WARNINGS=" + ",".join(cleanup_errors))
        else:
            print("SANDBOX_CLEANUP=PASS")


if __name__ == "__main__":
    sys.exit(main())
