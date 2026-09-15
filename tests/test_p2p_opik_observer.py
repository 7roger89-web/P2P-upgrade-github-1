from __future__ import annotations

import importlib.util
import os
import sys
import unittest
from datetime import timezone
from pathlib import Path
from unittest.mock import patch

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "deployments"
    / "hermes-essential-stack"
    / "plugins"
    / "p2p-opik-observer"
    / "__init__.py"
)
spec = importlib.util.spec_from_file_location("p2p_opik_observer", MODULE_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class FakeContext:
    def __init__(self) -> None:
        self.hooks = {}

    def register_hook(self, name, callback) -> None:
        self.hooks[name] = callback


class FakeTrace:
    id = "018f0000-0000-7000-8000-000000000001"


class FakeClient:
    def __init__(self) -> None:
        self.traces = []
        self.spans = []
        self.flush_calls = []

    def trace(self, **kwargs):
        self.traces.append(kwargs)
        return FakeTrace()

    def span(self, **kwargs):
        self.spans.append(kwargs)
        return object()

    def flush(self, timeout=None):
        self.flush_calls.append(timeout)
        return True


class TestP2POpikObserver(unittest.TestCase):
    def setUp(self) -> None:
        mod._turns.clear()
        mod._emitted.clear()
        mod._emitted_order.clear()
        mod._client = None
        mod._client_failed = False

    def _enabled_env(self, *, capture: str = "NO") -> dict[str, str]:
        return {
            "P2P_ENABLE_OPIK": "YES",
            "P2P_OPIK_CAPTURE_CONTENT": capture,
            "OPIK_API_KEY": "test-key",
            "OPIK_WORKSPACE": "test-workspace",
            "OPIK_PROJECT_NAME": "p2p-hermes",
            "OPIK_URL_OVERRIDE": "https://www.comet.com/opik/api",
            "OPIK_ENVIRONMENT": "test",
            "OPIK_ANALYTICS_ENABLE": "false",
        }

    def test_disabled_plugin_registers_nothing(self) -> None:
        ctx = FakeContext()
        with patch.dict(os.environ, {"P2P_ENABLE_OPIK": "NO"}, clear=False):
            mod.register(ctx)
        self.assertEqual(ctx.hooks, {})

    def test_enabled_plugin_registers_documented_observer_hooks(self) -> None:
        ctx = FakeContext()
        with patch.dict(os.environ, self._enabled_env(), clear=False):
            mod.register(ctx)
        self.assertEqual(
            set(ctx.hooks),
            {
                "pre_llm_call",
                "pre_api_request",
                "post_api_request",
                "api_request_error",
                "pre_tool_call",
                "post_tool_call",
                "subagent_start",
                "subagent_stop",
                "post_llm_call",
                "on_session_end",
                "on_session_finalize",
            },
        )

    def test_metadata_only_buffers_hot_path_and_redacts_content(self) -> None:
        fake = FakeClient()
        mod._client = fake
        secrets = {
            "prompt": "SECRET_PROMPT_123",
            "request": "SECRET_REQUEST_456",
            "response": "SECRET_RESPONSE_789",
            "tool_args": "SECRET_TOOL_ARGS_ABC",
            "tool_result": "SECRET_TOOL_RESULT_DEF",
            "assistant": "SECRET_ASSISTANT_GHI",
        }
        with patch.dict(os.environ, self._enabled_env(capture="NO"), clear=False):
            mod._pre_llm_call(
                session_id="session-raw-private",
                turn_id="turn-raw-private",
                task_id="task-raw-private",
                platform="gateway",
                model="test-model",
                user_message=secrets["prompt"],
            )
            mod._pre_api_request(
                session_id="session-raw-private",
                turn_id="turn-raw-private",
                api_request_id="api-private",
                model="test-model",
                provider="test-provider",
                api_call_count=1,
                retry_count=0,
                request={"body": secrets["request"]},
            )
            mod._post_api_request(
                session_id="session-raw-private",
                turn_id="turn-raw-private",
                api_request_id="api-private",
                model="test-model",
                provider="test-provider",
                finish_reason="stop",
                response={"body": secrets["response"]},
                usage={"input_tokens": 11, "output_tokens": 7},
            )
            mod._pre_tool_call(
                session_id="session-raw-private",
                turn_id="turn-raw-private",
                tool_call_id="tool-private",
                tool_name="read_file",
                args={"path": secrets["tool_args"]},
            )
            mod._post_tool_call(
                session_id="session-raw-private",
                turn_id="turn-raw-private",
                tool_call_id="tool-private",
                tool_name="read_file",
                result={"value": secrets["tool_result"]},
                duration_ms=12,
                status="ok",
            )
            self.assertEqual(fake.traces, [])
            self.assertEqual(fake.spans, [])
            mod._post_llm_call(
                session_id="session-raw-private",
                turn_id="turn-raw-private",
                assistant_response=secrets["assistant"],
            )

        self.assertEqual(len(fake.traces), 1)
        self.assertEqual(len(fake.spans), 2)
        serialized = repr((fake.traces, fake.spans))
        for secret in secrets.values():
            self.assertNotIn(secret, serialized)
        self.assertNotIn("session-raw-private", serialized)
        self.assertNotIn("turn-raw-private", serialized)
        self.assertIn("read_file", serialized)
        llm_span = next(item for item in fake.spans if item["type"] == "llm")
        self.assertEqual(
            llm_span["usage"],
            {"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18},
        )
        self.assertFalse(fake.traces[0]["metadata"]["content_capture"])

    def test_api_hook_uses_hermes_epoch_timestamps_and_seconds_duration(self) -> None:
        fake = FakeClient()
        mod._client = fake
        started = 1_756_000_000.0
        ended = 1_756_000_001.234
        with patch.dict(os.environ, self._enabled_env(), clear=False):
            mod._pre_llm_call(session_id="s-api", turn_id="t-api")
            mod._pre_api_request(
                session_id="s-api",
                turn_id="t-api",
                api_request_id="api-1",
                started_at=started,
                api_call_count=1,
                model="m",
                provider="p",
            )
            mod._post_api_request(
                session_id="s-api",
                turn_id="t-api",
                api_request_id="api-1",
                started_at=started,
                ended_at=ended,
                api_duration=1.234,
                finish_reason="stop",
                usage={"input_tokens": 2, "output_tokens": 3},
            )
            mod._post_llm_call(session_id="s-api", turn_id="t-api")

        span = next(item for item in fake.spans if item["type"] == "llm")
        self.assertEqual(span["start_time"].timestamp(), started)
        self.assertAlmostEqual(span["end_time"].timestamp(), ended, places=3)
        self.assertEqual(span["start_time"].tzinfo, timezone.utc)
        self.assertEqual(span["metadata"]["api_duration_seconds"], 1.234)

    def test_subagent_stop_uses_current_hermes_field_names(self) -> None:
        fake = FakeClient()
        mod._client = fake
        with patch.dict(os.environ, self._enabled_env(capture="YES"), clear=False):
            mod._pre_llm_call(session_id="parent", turn_id="turn")
            mod._subagent_start(
                parent_session_id="parent",
                parent_turn_id="turn",
                child_session_id="child-session",
                child_subagent_id="child-id",
                child_role="leaf",
                child_goal="PRIVATE_GOAL",
            )
            mod._subagent_stop(
                parent_session_id="parent",
                parent_turn_id="turn",
                child_session_id="child-session",
                child_role="leaf",
                child_summary="PRIVATE_SUMMARY",
                child_status="completed",
                duration_ms=1234,
            )
            mod._post_llm_call(session_id="parent", turn_id="turn")

        subagent = next(item for item in fake.spans if item["type"] == "general")
        self.assertEqual(subagent["metadata"]["status"], "completed")
        self.assertEqual(subagent["metadata"]["duration_ms"], 1234)
        self.assertIn("PRIVATE_SUMMARY", subagent["output"]["summary"])

    def test_content_capture_is_explicit_and_bounded(self) -> None:
        fake = FakeClient()
        mod._client = fake
        long_prompt = "x" * (mod._MAX_CONTENT_CHARS + 100)
        with patch.dict(os.environ, self._enabled_env(capture="YES"), clear=False):
            mod._pre_llm_call(session_id="s2", turn_id="t2", user_message=long_prompt)
            mod._post_llm_call(
                session_id="s2",
                turn_id="t2",
                assistant_response="VISIBLE_RESPONSE",
            )
        trace = fake.traces[0]
        self.assertTrue(trace["metadata"]["content_capture"])
        self.assertIn("[truncated]", trace["input"]["user_message"])
        self.assertIn("VISIBLE_RESPONSE", trace["output"]["assistant_response"])

    def test_failed_turn_uses_session_end_fallback(self) -> None:
        fake = FakeClient()
        mod._client = fake
        with patch.dict(os.environ, self._enabled_env(), clear=False):
            mod._pre_llm_call(session_id="s3", turn_id="t3", model="m")
            mod._on_session_end(
                session_id="s3",
                turn_id="t3",
                completed=False,
                failed=True,
                turn_exit_reason="provider_error",
            )
        self.assertEqual(len(fake.traces), 1)
        self.assertEqual(fake.traces[0]["metadata"]["status"], "failed")
        self.assertEqual(fake.traces[0]["output"], {"turn_exit_reason_present": True})


if __name__ == "__main__":
    unittest.main()
