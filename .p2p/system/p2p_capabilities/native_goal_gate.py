"""Compose P2P goal eligibility with real host capability probing.

This is the single pre-invocation handshake for native ``/goal``.  It never
launches another Claude/Codex process and never treats a generated slash
command as if it had executed.  A host-status receipt is required after the
host-owned command boundary accepts the command.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

try:
    from .native_goal_activation import (
        ACTIVATE,
        NORMAL,
        NativeGoalActivationError,
        _read_json,
        decide_native_goal_activation,
    )
    from .native_goal_bridge import HOST_KINDS
    from .native_goal_host_probe import READY, probe_native_goal_host
except ImportError:  # Support direct execution from the installed module path.
    runtime_root = Path(__file__).resolve().parents[1]
    if str(runtime_root) not in sys.path:
        sys.path.insert(0, str(runtime_root))
    from p2p_capabilities.native_goal_activation import (  # type: ignore[no-redef]
        ACTIVATE,
        NORMAL,
        NativeGoalActivationError,
        _read_json,
        decide_native_goal_activation,
    )
    from p2p_capabilities.native_goal_bridge import HOST_KINDS  # type: ignore[no-redef]
    from p2p_capabilities.native_goal_host_probe import READY, probe_native_goal_host  # type: ignore[no-redef]

GATE_SCHEMA = "p2p-native-goal-gate/1"
NOT_NEEDED = "NOT_NEEDED"
READY_TO_INVOKE = "READY_TO_INVOKE"
UNAVAILABLE = "UNAVAILABLE"


def evaluate_native_goal_gate(
    host_kind: str,
    goal_state: dict[str, Any],
    task_state: dict[str, Any],
    *,
    baseline_ref: str | None = None,
    probe=None,
) -> dict[str, Any]:
    """Return a truthful pre-invocation state; never claim invocation."""

    activation = decide_native_goal_activation(
        host_kind, goal_state, task_state, baseline_ref=baseline_ref
    )
    common = {
        "schema": GATE_SCHEMA,
        "host_kind": host_kind,
        "goal_id": activation.get("goal_id"),
        "invocation_proven": False,
        "same_session_invocation_assumed": False,
        "native_goal_is_acceptance_authority": False,
        "owner_prompt_required": False,
    }
    if activation["decision"] == NORMAL:
        return {
            **common,
            "status": NOT_NEEDED,
            "reason": activation["reason"],
            "p2p_path": NORMAL,
        }

    probe_fn = probe or probe_native_goal_host
    host_probe = probe_fn(host_kind)
    if host_probe.get("status") != READY:
        return {
            **common,
            "status": UNAVAILABLE,
            "reason": str(host_probe.get("reason", "HOST_NATIVE_GOAL_NOT_READY")),
            "p2p_path": NORMAL,
            "host_probe": host_probe,
            "record_unavailable_with": ".p2p/system/p2p_capabilities/native_goal_receipt.py",
        }

    proof_kind = (
        "CLAUDE_GOAL_STATUS_VIEW" if host_kind == "claude_code" else "CODEX_GOAL_STATUS_VIEW"
    )
    return {
        **common,
        "status": READY_TO_INVOKE,
        "reason": activation["reason"],
        "p2p_path": ACTIVATE,
        "command": activation["command"],
        "condition": activation["condition"],
        "host_probe": host_probe,
        "host_command_boundary_required": True,
        "do_not_launch_nested_host_to_fake_same_session_invocation": True,
        "after_host_acceptance_verify_with": "/goal",
        "receipt_proof_kind": proof_kind,
        "receipt_cli": ".p2p/system/p2p_capabilities/native_goal_receipt.py",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".")
    parser.add_argument("--host", required=True, choices=HOST_KINDS)
    parser.add_argument("--goal-state", default=".p2p/state/autopilot-goal-state.json")
    parser.add_argument("--task-state", default=".p2p/state/task-state.json")
    parser.add_argument("--baseline")
    args = parser.parse_args(argv)
    root = Path(args.root).expanduser().resolve()
    try:
        result = evaluate_native_goal_gate(
            args.host,
            _read_json(root / args.goal_state),
            _read_json(root / args.task_state),
            baseline_ref=args.baseline,
        )
    except (OSError, NativeGoalActivationError, ValueError) as exc:
        print(
            json.dumps(
                {
                    "schema": GATE_SCHEMA,
                    "status": "BLOCKED",
                    "error": str(exc),
                    "invocation_proven": False,
                    "owner_prompt_required": False,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0 if result["status"] in {NOT_NEEDED, READY_TO_INVOKE, UNAVAILABLE} else 2


if __name__ == "__main__":
    raise SystemExit(main())
