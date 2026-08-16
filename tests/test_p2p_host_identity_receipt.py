from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK_DIR = ROOT / ".p2p" / "system" / "scripts"
sys.path.insert(0, str(HOOK_DIR))

import p2p_host_identity_hook as hook  # noqa: E402


class HostIdentityReceiptTests(unittest.TestCase):
    def project(self) -> tempfile.TemporaryDirectory[str]:
        temp = tempfile.TemporaryDirectory(dir=str(ROOT / ".tmp"))
        project = Path(temp.name)
        (project / ".p2p" / "state").mkdir(parents=True)
        (project / ".codex").mkdir()
        (project / ".codex" / "config.toml").write_text("[agents]\nenabled = true\n", encoding="utf-8")
        return temp

    def payload(
        self,
        *,
        event: str = "SubagentStart",
        agent_type: str = "p2p_aesthetica",
        agent_id: str = "agent-1",
    ) -> dict[str, object]:
        value: dict[str, object] = {
            "session_id": "session-1",
            "turn_id": "turn-1",
            "transcript_path": None,
            "cwd": str(ROOT),
            "hook_event_name": event,
            "model": "gpt-5",
            "permission_mode": "default",
            "agent_id": agent_id,
            "agent_type": agent_type,
        }
        if event == "SubagentStop":
            value.update(
                {
                    "agent_transcript_path": None,
                    "stop_hook_active": False,
                    "last_assistant_message": None,
                }
            )
        return value

    def test_a_exact_aesthetica_receipt_is_recorded_and_verified(self) -> None:
        with self.project() as raw:
            result = hook.process_payload(self.payload(), raw)
            ledger = Path(raw) / ".p2p" / "state" / "execution-ledger.jsonl"
            receipt = hook.find_verified_identity(ledger, agent_id="agent-1")
            self.assertEqual(result["status"], "RECORDED")
            self.assertIsNotNone(receipt)
            assert receipt is not None
            self.assertEqual(receipt["schema"], hook.RECEIPT_SCHEMA)
            self.assertEqual(receipt["agent_type"], "p2p_aesthetica")
            self.assertEqual(receipt["source"], hook.HOST_SOURCE)
            self.assertNotIn("transcript_path", receipt)

    def test_b_supported_generic_default_is_recorded_as_host_default(self) -> None:
        with self.project() as raw:
            result = hook.process_payload(self.payload(agent_type="default"), raw)
            ledger = Path(raw) / ".p2p" / "state" / "execution-ledger.jsonl"
            self.assertEqual(result["status"], "RECORDED")
            receipt = hook.find_verified_identity(ledger, expected_agent_type="default", agent_id="agent-1")
            self.assertIsNotNone(receipt)
            self.assertEqual(hook.host_agent_class("default"), "HOST_DEFAULT / GENERIC")
            self.assertEqual(hook.read_receipts(ledger)[0]["agent_type"], "default")

    def test_canonical_host_agent_types_are_explicitly_allowlisted(self) -> None:
        with self.project() as raw:
            ledger = Path(raw) / ".p2p" / "state" / "execution-ledger.jsonl"
            for agent_type in sorted(hook.CANONICAL_HOST_AGENT_TYPES):
                result = hook.process_payload(
                    self.payload(agent_type=agent_type, agent_id=f"agent-{agent_type}"),
                    raw,
                )
                self.assertEqual(result["status"], "RECORDED")
                self.assertTrue(hook.is_supported_host_agent_type(agent_type))
                self.assertEqual(hook.host_agent_class(agent_type), "CUSTOM_PROFILE")
            self.assertEqual(len(hook.read_receipts(ledger)), len(hook.CANONICAL_HOST_AGENT_TYPES))

    def test_unknown_host_agent_type_fails_closed_without_a_receipt(self) -> None:
        with self.project() as raw:
            result = hook.process_payload(self.payload(agent_type="untrusted_worker"), raw)
            ledger = Path(raw) / ".p2p" / "state" / "execution-ledger.jsonl"
            self.assertEqual(result["status"], "IGNORED")
            self.assertFalse(ledger.exists())

    def test_missing_agent_type_fails_closed_without_a_receipt(self) -> None:
        payload = self.payload()
        payload.pop("agent_type")
        with self.project() as raw:
            result = hook.process_payload(payload, raw)
            ledger = Path(raw) / ".p2p" / "state" / "execution-ledger.jsonl"
            self.assertEqual(result["status"], "IGNORED")
            self.assertFalse(ledger.exists())

    def test_d_malformed_json_returns_success_without_writing(self) -> None:
        with self.project() as raw:
            result = subprocess.run(
                [sys.executable, str(HOOK_DIR / "p2p_host_identity_hook.py"), "--root", raw],
                input=b"{not-json",
                capture_output=True,
                check=False,
            )
            ledger = Path(raw) / ".p2p" / "state" / "execution-ledger.jsonl"
            self.assertEqual(result.returncode, 0)
            self.assertEqual(result.stdout, b"")
            self.assertEqual(result.stderr, b"")
            self.assertFalse(ledger.exists())

    def test_e_sensitive_fields_are_not_persisted(self) -> None:
        payload = self.payload()
        payload.update(
            {
                "prompt": "private prompt should not persist",
                "last_assistant_message": "secret assistant output should not persist",
                "environment": {"API_KEY": "do-not-store"},
                "tool_input": {"password": "do-not-store"},
            }
        )
        with self.project() as raw:
            result = hook.process_payload(payload, raw)
            ledger = Path(raw) / ".p2p" / "state" / "execution-ledger.jsonl"
            text = ledger.read_text(encoding="utf-8")
            self.assertEqual(result["status"], "RECORDED")
            for secret in ("private prompt", "secret assistant", "do-not-store", "API_KEY", "tool_input"):
                self.assertNotIn(secret, text)

    def test_secret_like_known_value_fails_closed_without_persisting_it(self) -> None:
        payload = self.payload()
        payload["model"] = "token=should-not-be-recorded"
        with self.project() as raw:
            result = hook.process_payload(payload, raw)
            ledger = Path(raw) / ".p2p" / "state" / "execution-ledger.jsonl"
            self.assertEqual(result["status"], "IGNORED")
            self.assertFalse(ledger.exists())

    def test_f_duplicate_payload_is_deterministic(self) -> None:
        with self.project() as raw:
            first = hook.process_payload(self.payload(), raw)
            second = hook.process_payload(self.payload(), raw)
            ledger = Path(raw) / ".p2p" / "state" / "execution-ledger.jsonl"
            lines = ledger.read_text(encoding="utf-8").splitlines()
            self.assertEqual(first["status"], "RECORDED")
            self.assertEqual(second["status"], "DUPLICATE")
            self.assertEqual(len(lines), 1)
            self.assertEqual(json.loads(lines[0])["event"], hook.LEDGER_EVENT)

    def test_subagent_stop_uses_the_official_allow_list(self) -> None:
        receipt = hook.build_receipt(self.payload(event="SubagentStop"))
        self.assertIsNotNone(receipt)
        assert receipt is not None
        self.assertEqual(receipt["event"], "SubagentStop")
        self.assertNotIn("last_assistant_message", receipt)

    def test_project_config_matches_the_official_windows_command_shape(self) -> None:
        import tomllib

        config = tomllib.loads((ROOT / ".codex" / "config.toml").read_text(encoding="utf-8"))
        groups = config["hooks"]["SubagentStart"]
        self.assertEqual(len(groups), 1)
        self.assertEqual(
            groups[0]["matcher"],
            "^(?:default|p2p_(?:iris|tecton|axiom|vector|datos|anon|architecton|helios|aesthetica))$",
        )
        command = groups[0]["hooks"][0]
        self.assertEqual(command["type"], "command")
        self.assertIn("p2p_host_identity_hook.py", command["command_windows"])
        self.assertEqual(command["timeout"], 3)


if __name__ == "__main__":
    unittest.main()
