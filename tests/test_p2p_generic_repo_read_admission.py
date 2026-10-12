"""Focused fail-closed tests for Issue #333 generic repo-read admission."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

import p2p_control_tower as control_tower_cli  # noqa: E402
from p2p_capabilities.skill_consumption import prepare_skill_handoff  # noqa: E402


class GenericRepoReadAdmissionTests(unittest.TestCase):
    HOST = "GITHUB_COPILOT_CLI_ACTIONS"
    PROBE_PATH = ".agents/skills/scope-reality-check/SKILL.md"

    def _repo_binding(self):
        helper = prepare_skill_handoff.__globals__["_canonical_repo_binding"]
        return helper(REPO_ROOT)

    def _revision(self):
        helper = prepare_skill_handoff.__globals__["_current_repo_revision"]
        return helper(REPO_ROOT)

    def _record(self, **updates):
        repo = self._repo_binding()
        revision = self._revision()
        self.assertIsNotNone(repo)
        self.assertIsNotNone(revision)
        probe_sha = hashlib.sha256(
            (REPO_ROOT / self.PROBE_PATH).read_bytes()
        ).hexdigest()
        value = {
            "schema": "p2p-host-discovery-record/1",
            "host_id": self.HOST,
            "profile": {
                "schema": "p2p-host-executor-contract/1",
                "adapter_class": "GitHubCopilotCLI",
                "host_label": self.HOST,
                "environment": "REMOTE_REPOSITORY",
                "capabilities": {"can_read_files": "SUPPORTED"},
            },
            "availability": "KNOWN_AVAILABLE",
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "provenance": (
                "GITHUB_ACTIONS_OIDC_EXACT_READ"
                f"|repo={repo}|revision={revision}"
                f"|probe={self.PROBE_PATH}|sha256={probe_sha}"
            ),
            "environment_binding": "REMOTE_REPOSITORY",
            "project_binding": repo,
            "profile_version": "1",
            "active": True,
            "reconciliation_burden": 0,
            "execution_transport_available": True,
        }
        value.update(updates)
        return value

    def test_c21_only_stays_blocked_without_signed_evidence(self):
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "execute the bounded implementation plan",
            host=self.HOST,
            required_skills=("p2p-scope",),
            host_discovery_record=self._record(),
        )
        self.assertEqual(handoff["SKILL_CHECK"], "BLOCKED")
        self.assertIn(
            "GENERIC_READ_EVIDENCE_REQUIRED",
            handoff["REJECTION_REASON"],
        )

    def test_false_transport_blocks_before_signed_evidence(self):
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "execute the bounded implementation plan",
            host=self.HOST,
            required_skills=("p2p-scope",),
            host_discovery_record=self._record(
                execution_transport_available=False
            ),
        )
        self.assertEqual(handoff["SKILL_CHECK"], "BLOCKED")
        self.assertIn(
            "HOST_EXECUTION_TRANSPORT_UNAVAILABLE",
            handoff["REJECTION_REASON"],
        )

    def test_mismatched_actor_identity_blocks(self):
        record = self._record()
        record["profile"] = dict(record["profile"])
        record["profile"]["host_label"] = "OTHER_HOST"
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "execute the bounded implementation plan",
            host=self.HOST,
            required_skills=("p2p-scope",),
            host_discovery_record=record,
        )
        self.assertEqual(handoff["SKILL_CHECK"], "BLOCKED")
        self.assertIn(
            "HOST_DISCOVERY_IDENTITY_MISMATCH",
            handoff["REJECTION_REASON"],
        )

    def test_native_arena_does_not_require_generic_evidence(self):
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "execute the bounded implementation plan",
            host="ARENA",
            required_skills=("p2p-scope",),
        )
        self.assertEqual(handoff["SKILL_CHECK"], "PASS")
        self.assertEqual(
            handoff["SKILL_HOST_MODE"], "ARENA_EXACT_REPO_READ"
        )

    def test_cli_accepts_explicit_generic_evidence_files(self):
        args = control_tower_cli.build_parser().parse_args([
            "start",
            "--host", self.HOST,
            "--goal-id", "g1",
            "--goal", "bounded task",
            "--host-discovery-record-file", "host.json",
            "--generic-read-evidence-file", "evidence.json",
        ])
        self.assertEqual(args.host_discovery_record_file, "host.json")
        self.assertEqual(args.generic_read_evidence_file, "evidence.json")

    def test_cli_loads_existing_discovery_record_object(self):
        record = self._record()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "host.json"
            path.write_text(json.dumps(record), encoding="utf-8")
            loaded = control_tower_cli._load_json_object_file(
                str(path),
                field="HOST_DISCOVERY_RECORD",
                expected_schema="p2p-host-discovery-record/1",
            )
        self.assertEqual(loaded["host_id"], self.HOST)

    def test_generic_no_match_never_claims_repo_read_mode(self):
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "zzzz-no-skill-trigger-issue333",
            host=self.HOST,
        )
        self.assertEqual(handoff["SKILL_CHECK"], "NO_MATCH")
        self.assertEqual(handoff["SKILL_HOST_MODE"], "NOT_REQUIRED")


if __name__ == "__main__":
    unittest.main(verbosity=2)
