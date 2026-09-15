"""Deterministic contract tests for the bounded FCC Claude adapter.

No FCC installation, provider credential, network request, or free-tier quota is
required.  Live certification is deliberately out of scope for this slice.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SYSTEM_ROOT = os.path.join(REPO_ROOT, ".p2p", "system")
if SYSTEM_ROOT not in sys.path:
    sys.path.insert(0, SYSTEM_ROOT)

from p2p_capabilities.backend_contract import BackendContractError  # noqa: E402
from p2p_capabilities.backend_execution_bridge import (  # noqa: E402
    BackendAdapterRegistry,
    BackendExecutionBridge,
    contract_request_fingerprint,
)
from p2p_capabilities.fcc_claude_adapter import (  # noqa: E402
    FCC_CLAUDE_ADAPTER_ID,
    FCC_PROTOCOL,
    FccClaudeAdapter,
)


def _successful_run(stdout: str = '{"result":"4","usage":{"input_tokens":8}}') -> dict:
    return {
        "stdout": stdout,
        "stderr": "",
        "exit_code": 0,
        "elapsed": 0.125,
        "timeout": False,
        "spawn_error": False,
    }


def _minimal_contract(**overrides) -> dict:
    contract = {
        "schema": "p2p-autopilot-task-contract/1",
        "goal_id": "g-fcc-test",
        "task_id": "t-fcc-test",
        "task_objective": "Answer in exactly one word: what is 2+2?",
        "workspace": "/tmp/p2p-fcc-test",
        "allowed_scope": ("read",),
        "execution_target": FCC_CLAUDE_ADAPTER_ID,
        "expected_output": ("answer",),
        "verify_spec": ("default",),
    }
    contract.update(overrides)
    return contract


class TestFccIdentityAndHealth:
    def test_missing_launcher_is_architecturally_compatible_not_fake_live(self):
        adapter = FccClaudeAdapter()
        with mock.patch(
            "p2p_capabilities.fcc_claude_adapter._fcc_binary_path",
            return_value=None,
        ):
            identity = adapter.identity()
            health = adapter.health()
        assert identity.adapter_id == FCC_CLAUDE_ADAPTER_ID
        assert identity.adapter_state == "ARCHITECTURALLY_COMPATIBLE"
        assert identity.protocol == FCC_PROTOCOL
        assert identity.provider_identity == "fcc-proxy"
        assert identity.toolset_capabilities == (
            "REPO_READ",
            "REPO_SEARCH",
            "STATIC_ANALYSIS",
        )
        assert health.healthy is False
        assert health.auth_state == "UNKNOWN"
        assert health.availability == "UNAVAILABLE"

    def test_present_launcher_is_implemented_but_auth_stays_unknown(self):
        adapter = FccClaudeAdapter()
        with (
            mock.patch(
                "p2p_capabilities.fcc_claude_adapter._fcc_binary_path",
                return_value="/usr/local/bin/fcc-claude",
            ),
            mock.patch(
                "p2p_capabilities.fcc_claude_adapter._run_fcc",
                return_value=_successful_run("Claude Code 9.9 via FCC"),
            ),
        ):
            identity = adapter.identity()
            health = adapter.health()
        assert identity.adapter_state == "ADAPTER_IMPLEMENTED"
        assert "Claude Code" in str(identity.harness_identity)
        assert health.healthy is True
        assert health.auth_state == "UNKNOWN"
        assert health.availability == "AVAILABLE"


class TestFccExecutionSafety:
    def test_command_is_bounded_plan_mode_and_model_is_explicit(self):
        adapter = FccClaudeAdapter()
        observed: dict[str, object] = {}

        def fake_run(args, *, workdir, timeout_seconds):
            observed["args"] = args
            observed["workdir"] = workdir
            observed["timeout_seconds"] = timeout_seconds
            return _successful_run()

        with mock.patch(
            "p2p_capabilities.fcc_claude_adapter._run_fcc",
            side_effect=fake_run,
        ):
            result = adapter.execute(
                request_id="p2p-t-fcc",
                request_fingerprint="a" * 64,
                task_id="t-fcc",
                goal_id="g-fcc",
                prompt="what is 2+2?",
                max_turns=7,
                timeout_seconds=90,
                workdir="/tmp/fcc-work",
                provider="open_router",
                model="open_router/openrouter/free",
            )

        args = tuple(observed["args"])
        assert args[:2] == ("-p", "what is 2+2?")
        assert ("--permission-mode", "plan") == (
            args[args.index("--permission-mode")],
            args[args.index("--permission-mode") + 1],
        )
        assert "--no-session-persistence" in args
        assert args[args.index("--max-turns") + 1] == "7"
        assert args[args.index("--model") + 1] == "open_router/openrouter/free"
        assert "--dangerously-skip-permissions" not in args
        assert "--allow-dangerously-skip-permissions" not in args
        assert "--provider" not in args
        assert "open_router" not in args
        assert observed["timeout_seconds"] == 90
        assert result.execution_status == "SUCCEEDED"
        assert result.possible_mutation is False
        assert result.mutation_surface == "NONE_PLANNING_MODE"

    def test_free_lane_is_intent_not_zero_cost_claim(self):
        adapter = FccClaudeAdapter()
        with mock.patch(
            "p2p_capabilities.fcc_claude_adapter._run_fcc",
            return_value=_successful_run(
                '{"result":"4","total_cost_usd":0.0,"num_turns":1}'
            ),
        ):
            result = adapter.execute(
                request_id="p2p-free-lane",
                request_fingerprint="b" * 64,
                task_id="t-free",
                goal_id="g-free",
                prompt="2+2?",
                provider="open_router",
                model="open_router/openrouter/free",
            )
        usage = dict(result.usage_evidence)
        assert usage["requested_model"] == "open_router/openrouter/free"
        assert usage["requested_provider_hint"] == "open_router"
        assert usage["fallback_policy_source"] == "FCC_SERVER_CONFIG"
        assert usage["actual_provider"] == "UNKNOWN"
        assert usage["actual_model"] == "UNKNOWN"
        assert usage["fallback_observed"] == "UNKNOWN"
        assert usage["free_tier_guaranteed"] is False
        assert usage["total_cost_usd"] == 0.0

    def test_timeout_normalizes_without_claiming_clean_state(self):
        adapter = FccClaudeAdapter()
        run = {
            "stdout": "",
            "stderr": "P2P_TIMEOUT",
            "exit_code": -1,
            "elapsed": 20.0,
            "timeout": True,
            "spawn_error": False,
        }
        with mock.patch(
            "p2p_capabilities.fcc_claude_adapter._run_fcc",
            return_value=run,
        ):
            result = adapter.execute(
                request_id="p2p-timeout",
                request_fingerprint="c" * 64,
                task_id="t-timeout",
                goal_id="g-timeout",
                prompt="hello",
                timeout_seconds=20,
            )
        assert result.execution_status == "FAILED"
        assert result.error_class == "TIMEOUT"
        assert result.possible_mutation is True

    def test_unknown_nonzero_failure_fails_closed(self):
        adapter = FccClaudeAdapter()
        run = {
            "stdout": "",
            "stderr": "strange upstream wobble with no canonical marker",
            "exit_code": 9,
            "elapsed": 0.2,
            "timeout": False,
            "spawn_error": False,
        }
        with mock.patch(
            "p2p_capabilities.fcc_claude_adapter._run_fcc",
            return_value=run,
        ):
            result = adapter.execute(
                request_id="p2p-unknown",
                request_fingerprint="d" * 64,
                task_id="t-unknown",
                goal_id="g-unknown",
                prompt="hello",
            )
        assert result.execution_status == "FAILED"
        assert result.error_class == "EXECUTION_FAILED"
        assert result.possible_mutation is False

    def test_invalid_contract_is_rejected_before_execution(self):
        adapter = FccClaudeAdapter()
        with pytest.raises(BackendContractError, match="MAX_TURNS_OUT_OF_RANGE"):
            adapter.execute(
                request_id="p2p-invalid",
                request_fingerprint="e" * 64,
                task_id="t-invalid",
                goal_id="g-invalid",
                prompt="hello",
                max_turns=0,
            )


class TestFccEvidenceAndBridgeReuse:
    def test_evidence_redacts_prompt_and_keeps_route_truth_bounded(self, tmp_path: Path):
        adapter = FccClaudeAdapter()
        secretish_prompt = "private task text that must not be duplicated in evidence"
        with mock.patch(
            "p2p_capabilities.fcc_claude_adapter._run_fcc",
            return_value=_successful_run(),
        ):
            result = adapter.execute(
                request_id="p2p-evidence",
                request_fingerprint="f" * 64,
                task_id="t-evidence",
                goal_id="g-evidence",
                prompt=secretish_prompt,
                evidence_dir=str(tmp_path),
                model="open_router/openrouter/free",
            )
        assert result.raw_backend_receipt_pointer is not None
        text = Path(result.raw_backend_receipt_pointer).read_text(encoding="utf-8")
        assert secretish_prompt not in text
        assert "<PROMPT>" in text
        assert '"actual_provider": "UNKNOWN"' in text
        assert '"free_tier_guaranteed": false' in text

    def test_existing_backend_bridge_accepts_adapter_without_router_changes(self):
        contract = _minimal_contract()
        registry = BackendAdapterRegistry()
        registry.register(FCC_CLAUDE_ADAPTER_ID, FccClaudeAdapter)
        profile = {
            "adapter_id": FCC_CLAUDE_ADAPTER_ID,
            "model": "open_router/openrouter/free",
            "provider": "open_router",
            "max_turns": 5,
            "timeout_seconds": 30,
        }
        bridge = BackendExecutionBridge(registry, profile)
        with mock.patch(
            "p2p_capabilities.fcc_claude_adapter._run_fcc",
            return_value=_successful_run(),
        ):
            result = bridge.execute(contract)
        assert result["bound_to_contract"] is True
        assert result["execution_status"] == "SUCCEEDED"
        assert result["request_fingerprint"] == contract_request_fingerprint(contract)
        receipt = result["execution_receipt"]
        assert receipt["adapter_id"] == FCC_CLAUDE_ADAPTER_ID
        assert result["usage_evidence"]["actual_provider"] == "UNKNOWN"
