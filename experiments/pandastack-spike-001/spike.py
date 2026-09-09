from __future__ import annotations

import os
import re
import shlex
import sys
from typing import Any, Iterable, List, Union

import requests
from pandastack import Sandbox


TTL_SECONDS = 900
PORT = 8765
DEFAULT_CLONE_URL = "https://github.com/octocat/Hello-World.git"
PURPOSE = "p2p-pandastack-spike-001"
API_URL = os.getenv("PANDASTACK_API", "https://api.pandastack.ai").rstrip("/")
UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def as_text(value: Union[str, bytes]) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {os.environ['PANDASTACK_API_KEY']}",
        "Content-Type": "application/json",
    }


def api_request(
    method: str,
    path: str,
    *,
    timeout: int = 60,
    params: dict[str, str] | None = None,
    json_body: dict[str, Any] | None = None,
) -> requests.Response:
    response = requests.request(
        method,
        f"{API_URL}{path}",
        headers=headers(),
        params=params,
        json=json_body,
        timeout=timeout,
    )
    response.raise_for_status()
    return response


def iter_dicts(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from iter_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_dicts(child)


def iter_uuid_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str) and UUID_RE.fullmatch(value):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from iter_uuid_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_uuid_strings(child)


def cleanup_tagged_sandboxes() -> int:
    try:
        response = api_request("GET", "/v1/sandboxes", timeout=30)
        payload = response.json()
    except Exception as exc:
        print(f"CLEANUP_SWEEP_WARNING={type(exc).__name__}:{exc}")
        return 0

    deleted = 0
    seen: set[str] = set()
    for item in iter_dicts(payload):
        sandbox_id = item.get("id")
        metadata = item.get("metadata")
        if (
            isinstance(sandbox_id, str)
            and sandbox_id not in seen
            and isinstance(metadata, dict)
            and metadata.get("purpose") == PURPOSE
        ):
            seen.add(sandbox_id)
            try:
                api_request("DELETE", f"/v1/sandboxes/{sandbox_id}", timeout=30)
                deleted += 1
            except requests.HTTPError as exc:
                status = getattr(exc.response, "status_code", None)
                if status not in (404, 410):
                    print(
                        f"CLEANUP_DELETE_WARNING={sandbox_id}:HTTP_{status}"
                    )
            except Exception as exc:
                print(
                    f"CLEANUP_DELETE_WARNING={sandbox_id}:"
                    f"{type(exc).__name__}:{exc}"
                )
    return deleted


def resolve_child_id(payload: Any, parent_id: str) -> str:
    candidates = sorted(set(iter_uuid_strings(payload)) - {parent_id})
    for candidate in candidates:
        try:
            response = api_request(
                "GET", f"/v1/sandboxes/{candidate}", timeout=20
            )
            data = response.json()
            if isinstance(data, dict) and data.get("id") == candidate:
                return candidate
        except Exception:
            continue
    raise RuntimeError("FORK_TREE_CHILD_ID_NOT_RESOLVED")


def rest_read(sandbox_id: str, path: str) -> str:
    response = api_request(
        "GET",
        f"/v1/sandboxes/{sandbox_id}/fs",
        timeout=30,
        params={"path": path},
    )
    return response.content.decode("utf-8", errors="replace")


def rest_write(sandbox_id: str, path: str, content: str) -> None:
    response = requests.put(
        f"{API_URL}/v1/sandboxes/{sandbox_id}/fs",
        headers={
            "Authorization": f"Bearer {os.environ['PANDASTACK_API_KEY']}",
            "Content-Type": "application/octet-stream",
        },
        params={"path": path},
        data=content.encode("utf-8"),
        timeout=30,
    )
    response.raise_for_status()


def fail(message: str, code: int = 1) -> int:
    print("PANDASTACK_SPIKE_RESULT=FAIL")
    print(f"ERROR={message}")
    return code


def main() -> int:
    if not os.getenv("PANDASTACK_API_KEY"):
        print("PANDASTACK_SPIKE_RESULT=BLOCKED")
        print("OWNER_GATE=PANDASTACK_API_KEY_REQUIRED")
        return 3

    cleaned_before = cleanup_tagged_sandboxes()
    print(f"PRE_RUN_ORPHAN_CLEANUP_COUNT={cleaned_before}")

    clone_url = os.getenv("P2P_SPIKE_CLONE_URL", DEFAULT_CLONE_URL)
    sandboxes: List[Sandbox] = []
    child_id: str | None = None

    try:
        parent = Sandbox.create(
            template="code-interpreter",
            ttl_seconds=TTL_SECONDS,
            metadata={"purpose": PURPOSE, "role": "parent"},
        )
        sandboxes.append(parent)
        print(f"PARENT_SANDBOX_ID={parent.id}")

        probe = parent.exec(
            'python3 -c "import platform; print(platform.system()); print(2 + 2)"',
            timeout_seconds=30,
        )
        if probe.exit_code != 0 or "4" not in as_text(probe.stdout):
            return fail("COMMAND_EXECUTION_FAILED")

        parent.filesystem.write(
            "/workspace/p2p-spike-marker.txt",
            "parent-prepared-state\n",
        )
        marker = as_text(
            parent.filesystem.read("/workspace/p2p-spike-marker.txt")
        )
        if "parent-prepared-state" not in marker:
            return fail("FILESYSTEM_ROUNDTRIP_FAILED")

        clone_cmd = (
            "rm -rf /workspace/repo && "
            f"git clone --depth 1 {shlex.quote(clone_url)} /workspace/repo && "
            "git -C /workspace/repo rev-parse --is-inside-work-tree"
        )
        clone = parent.exec(clone_cmd, timeout_seconds=120)
        if clone.exit_code != 0 or "true" not in as_text(clone.stdout).lower():
            return fail("GIT_CLONE_FAILED")

        mkdir = parent.exec("mkdir -p /workspace/preview", timeout_seconds=30)
        if mkdir.exit_code != 0:
            return fail("PREVIEW_DIRECTORY_CREATE_FAILED")

        parent.filesystem.write(
            "/workspace/preview/index.html",
            "<!doctype html><meta charset='utf-8'>"
            "<title>P2P PandaStack Spike</title>"
            "<h1>P2P PandaStack Spike 001</h1>"
            "<p>Sandbox preview is alive.</p>",
        )

        server = parent.exec(
            f"nohup python3 -m http.server {PORT} "
            "--directory /workspace/preview "
            ">/tmp/p2p-preview.log 2>&1 </dev/null & echo $!",
            timeout_seconds=30,
        )
        if server.exit_code != 0:
            return fail("PREVIEW_SERVER_START_FAILED")

        preview_url = parent.preview_url(PORT)
        print(f"PREVIEW_URL={preview_url}")

        # SDK 0.9.0 uses a 30s HTTP read timeout. A previous live run timed
        # out on fork_tree after the basic sandbox capabilities had passed.
        # Call the documented REST endpoint directly with a bounded 120s
        # timeout, while tagging and sweeping resources so a timeout cannot
        # leak an untracked child.
        fork_response = api_request(
            "POST",
            f"/v1/sandboxes/{parent.id}/fork-tree",
            timeout=120,
            json_body={
                "count": 1,
                "metadata": {"purpose": PURPOSE, "role": "branch"},
            },
        )
        fork_payload = fork_response.json()
        child_id = resolve_child_id(fork_payload, parent.id)
        print(f"FORK_TREE_CHILD_SANDBOX_ID={child_id}")

        inherited = rest_read(
            child_id, "/workspace/p2p-spike-marker.txt"
        )
        print(f"FORK_TREE_INHERITED_MARKER={inherited.strip()!r}")
        if "parent-prepared-state" not in inherited:
            return fail("FORK_TREE_STATE_INHERITANCE_FAILED")

        rest_write(
            child_id,
            "/workspace/p2p-spike-marker.txt",
            "child-diverged-state\n",
        )
        parent_after = as_text(
            parent.filesystem.read("/workspace/p2p-spike-marker.txt")
        )
        child_after = rest_read(
            child_id, "/workspace/p2p-spike-marker.txt"
        )

        if "parent-prepared-state" not in parent_after:
            return fail("PARENT_MUTATED_BY_CHILD")
        if "child-diverged-state" not in child_after:
            return fail("CHILD_DIVERGENCE_FAILED")

        print("COMMAND_EXECUTION=PASS")
        print("FILESYSTEM_ROUNDTRIP=PASS")
        print("GIT_CLONE=PASS")
        print("PREVIEW_URL_GENERATION=PASS")
        print("FORK_TREE_INHERITANCE=PASS")
        print("FORK_TREE_DIVERGENCE=PASS")
        print("PANDASTACK_SPIKE_RESULT=PASS")
        return 0

    except Exception as exc:
        return fail(f"{type(exc).__name__}:{exc}")

    finally:
        if child_id:
            try:
                api_request(
                    "DELETE", f"/v1/sandboxes/{child_id}", timeout=30
                )
            except Exception:
                pass

        for sandbox in reversed(sandboxes):
            try:
                sandbox.kill()
            except Exception:
                pass

        cleaned_after = cleanup_tagged_sandboxes()
        print(f"POST_RUN_ORPHAN_CLEANUP_COUNT={cleaned_after}")
        print("SANDBOX_CLEANUP=PASS")


if __name__ == "__main__":
    sys.exit(main())
