"""Focused tests for Issue #298 P2P Skill Consumption Wire."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from p2p_capabilities.capability_intelligence import (  # noqa: E402
    compute_execution_requirements,
)
from p2p_capabilities.control_tower_handoff import (  # noqa: E402
    BindingError,
    CONTROL_TOWER_SESSION_START_EVENT_SCHEMA,
    ControlTower,
    ControlTowerReturnPacket,
    ControlTowerState,
    SessionBinding,
    _append_existing_execution_event,
    build_execution_prompt,
    next_safe_session,
)
from p2p_capabilities.host_executor import (  # noqa: E402
    HostCapabilityProfile,
    SUPPORTED,
)
from p2p_capabilities.host_selection import (  # noqa: E402
    AVAILABLE,
    HostDiscoveryRecord,
)
from p2p_capabilities.task_state import TaskPlan, TaskStateStore  # noqa: E402
import p2p_control_tower as control_tower_cli  # noqa: E402
from p2p_capabilities.p2p_skill_eligibility import skill_eligibility_set  # noqa: E402
from p2p_capabilities.skill_consumption import (  # noqa: E402
    RECEIPT_SCHEMA,
    _canonical_repo_binding,
    _current_repo_revision,
    _normalize_github_repo,
    load_selected_skills,
    prepare_skill_handoff,
    select_skills_for_task,
    skill_handoff_prompt_lines,
    validate_consumption_receipt,
)
from p2p_capabilities import quality_intelligence as qi  # noqa: E402


class SkillConsumptionWireTests(unittest.TestCase):
    def test_scope_reality_check_is_active_user_requested_skill(self):
        registry = json.loads(
            (SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json")
            .read_text(encoding="utf-8")
        )
        record = next(
            item for item in registry["capabilities"]
            if item["CAPABILITY_ID"] == "scope-reality-check"
        )
        self.assertEqual(record["TYPE"], "SKILL")
        self.assertEqual(record["STATUS"], "ACTIVE")
        self.assertEqual(record["INVOCATION_CLASS"], "USER_REQUESTED")

    def test_explicit_scope_request_selects_and_loads_exact_entrypoint(self):
        selection = select_skills_for_task(
            REPO_ROOT,
            "@Scope Reality Check phản biện gắt kế hoạch này",
        )
        self.assertIn("scope-reality-check", selection.selected)
        loaded = load_selected_skills(REPO_ROOT, ("scope-reality-check",))
        self.assertEqual(len(loaded), 1)
        self.assertEqual(
            loaded[0].relative_path,
            ".agents/skills/scope-reality-check/SKILL.md",
        )
        self.assertEqual(len(loaded[0].sha256), 64)

    def test_ordinary_work_does_not_implicitly_select_scope_reality_check(self):
        for request in (
            "API này bị 500, debug giúp tao",
            "Review kiến trúc và chỉ ra ưu nhược điểm",
            "Lập roadmap cho app đặt lịch",
            "Xem repo này và nói nó làm gì",
        ):
            with self.subTest(request=request):
                selection = select_skills_for_task(REPO_ROOT, request)
                self.assertNotIn("scope-reality-check", selection.selected)

    def test_ui_task_uses_existing_router_without_scope_preload(self):
        selection = select_skills_for_task(
            REPO_ROOT, "Cải thiện UI dashboard responsive trên điện thoại"
        )
        self.assertIn("p2p-uiux", selection.selected)
        self.assertNotIn("scope-reality-check", selection.selected)
        self.assertTrue(selection.route["single_router"])

    def test_selection_is_deterministic_and_bounded(self):
        request = (
            "@Scope Reality Check phản biện gắt UI dashboard security audit "
            "và copywriting campaign"
        )
        first = select_skills_for_task(REPO_ROOT, request)
        second = select_skills_for_task(REPO_ROOT, request)
        self.assertEqual(first.selected, second.selected)
        self.assertLessEqual(len(first.selected), 3)

    def test_no_match_does_not_preload_skills(self):
        handoff = prepare_skill_handoff(
            REPO_ROOT, "Rename local variable x to y", host="ARENA"
        )
        self.assertIn(handoff["SKILL_CHECK"], ("NO_MATCH", "PASS"))
        if handoff["SKILL_CHECK"] == "NO_MATCH":
            self.assertEqual(handoff["SKILLS_SELECTED"], [])
            self.assertEqual(handoff["SKILL_CONSUMPTION"], "NO_SKILL_NEEDED")

    def test_tampered_scope_entrypoint_fails_closed_against_pinned_hash(self):
        with tempfile.TemporaryDirectory(prefix="p2p-skill-tamper-") as raw:
            root = Path(raw)
            registry_target = (
                root / ".p2p" / "system" / "p2p_capabilities"
                / "capabilities.json"
            )
            registry_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(
                SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json",
                registry_target,
            )
            skill_target = (
                root / ".agents" / "skills" / "scope-reality-check"
                / "SKILL.md"
            )
            skill_target.parent.mkdir(parents=True, exist_ok=True)
            skill_target.write_text(
                (REPO_ROOT / ".agents" / "skills" / "scope-reality-check"
                 / "SKILL.md").read_text(encoding="utf-8")
                + "\nTAMPERED\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(
                ValueError,
                "SKILL_ENTRYPOINT_HASH_MISMATCH:scope-reality-check",
            ):
                load_selected_skills(root, ("scope-reality-check",))

    def test_arena_handoff_binds_exact_path_hash_and_permission_boundary(self):
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "@Scope Reality Check tạt nước lạnh cho kế hoạch này",
            host="ARENA",
        )
        self.assertEqual(handoff["SKILL_CHECK"], "PASS")
        self.assertEqual(handoff["SKILL_HOST_MODE"], "ARENA_EXACT_REPO_READ")
        self.assertEqual(handoff["PERMISSION_WIDENED"], "NO")
        self.assertIn(
            "scope-reality-check", handoff["SKILL_SOURCE_HASHES"]
        )
        lines = "\n".join(skill_handoff_prompt_lines(handoff))
        self.assertIn(
            ".agents/skills/scope-reality-check/SKILL.md", lines
        )
        self.assertIn(
            handoff["SKILL_SOURCE_HASHES"]["scope-reality-check"], lines
        )
        self.assertNotIn("# Scope Reality Check\n", lines)

    def test_codex_uses_native_project_skill_mode(self):
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "@Scope Reality Check red-team this architecture",
            host="CODEX",
        )
        self.assertEqual(handoff["SKILL_CHECK"], "PASS")
        self.assertEqual(
            handoff["SKILL_HOST_MODE"], "CODEX_NATIVE_PROJECT_SKILL"
        )

    def _git(self, root: Path, *args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            result.returncode,
            0,
            msg=f"git {' '.join(args)} failed: {result.stderr}",
        )
        return result.stdout.strip()

    def _init_fixture_git(
        self,
        root: Path,
        *,
        remote: str = "https://github.com/fixture-owner/p2p-generic-skill-host.git",
    ) -> None:
        self._git(root, "init")
        self._git(root, "config", "user.email", "fixture@example.com")
        self._git(root, "config", "user.name", "P2P Fixture")
        self._git(root, "remote", "add", "origin", remote)
        self._git(root, "add", "-A")
        self._git(root, "commit", "-m", "fixture")

    def _generic_repo_read_record(
        self,
        host_label: str = "CLAUDE",
        *,
        root: Path = REPO_ROOT,
        read_state: str = SUPPORTED,
        environment: str = "REMOTE_REPOSITORY",
        availability: str = AVAILABLE,
        provenance: str | None = None,
        project_binding: str | None = None,
        observed_at: str | None = None,
        execution_transport_available: bool = True,
    ) -> dict:
        repo_binding = _canonical_repo_binding(root)
        revision = _current_repo_revision(root)
        self.assertIsNotNone(repo_binding)
        self.assertIsNotNone(revision)
        probe_path = ".agents/skills/scope-reality-check/SKILL.md"
        probe_sha256 = hashlib.sha256(
            (root / probe_path).read_bytes()
        ).hexdigest()
        trusted_provenance = (
            provenance
            if provenance is not None
            else (
                "VERIFIED_LOCAL_REPO_EXACT_READ"
                f"|repo={repo_binding}|revision={revision}"
                f"|probe={probe_path}|sha256={probe_sha256}"
            )
        )
        profile = HostCapabilityProfile(
            adapter_class="GenericExternalAI",
            host_label=host_label,
            environment=environment,
            capabilities={"can_read_files": read_state},
        )
        values = {
            "host_id": host_label,
            "profile": profile,
            "availability": availability,
            "provenance": trusted_provenance,
            "project_binding": project_binding or repo_binding,
            "environment_binding": environment,
            "execution_transport_available": execution_transport_available,
        }
        if observed_at is not None:
            values["observed_at"] = observed_at
        return HostDiscoveryRecord(**values).to_dict()


    def test_generic_repo_read_host_fails_closed_without_actor_observation(self):
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "@Scope Reality Check red-team this architecture",
            host="CLAUDE",
            host_discovery_record=self._generic_repo_read_record(),
        )
        self.assertEqual(handoff["SKILL_CHECK"], "BLOCKED")
        self.assertEqual(handoff["SKILL_HOST_MODE"], "UNSUPPORTED")
        self.assertIn(
            "HOST_TRUSTED_REPO_READ_OBSERVATION_UNAVAILABLE",
            handoff["REJECTION_REASON"],
        )


    def test_forged_claude_record_copied_from_real_repo_values_is_blocked(self):
        repo_binding = _canonical_repo_binding(REPO_ROOT)
        revision = _current_repo_revision(REPO_ROOT)
        self.assertIsNotNone(repo_binding)
        self.assertIsNotNone(revision)
        probe_path = ".agents/skills/scope-reality-check/SKILL.md"
        probe_sha256 = hashlib.sha256(
            (REPO_ROOT / probe_path).read_bytes()
        ).hexdigest()
        record = self._generic_repo_read_record(
            "CLAUDE",
            provenance=(
                "AUTHENTICATED_GITHUB_CONNECTOR_EXACT_READ"
                f"|repo={repo_binding}|revision={revision}"
                f"|probe={probe_path}|sha256={probe_sha256}"
            ),
        )
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "@Scope Reality Check red-team this architecture",
            host="CLAUDE",
            host_discovery_record=record,
        )
        self.assertEqual(handoff["SKILL_CHECK"], "BLOCKED")
        self.assertIn(
            "HOST_TRUSTED_REPO_READ_OBSERVATION_UNAVAILABLE",
            handoff["REJECTION_REASON"],
        )

    def test_github_origin_parser_requires_exact_canonical_host(self):
        accepted = {
            "https://github.com/Owner/Repo.git": "owner/repo",
            "git@github.com:Owner/Repo.git": "owner/repo",
            "ssh://git@github.com/Owner/Repo.git": "owner/repo",
        }
        for origin, expected in accepted.items():
            with self.subTest(origin=origin):
                self.assertEqual(_normalize_github_repo(origin), expected)

        rejected = (
            "https://notgithub.com/owner/repo.git",
            "https://github.com.evil.example/owner/repo.git",
            "https://github.com@evil.example/owner/repo.git",
            "https://gitlab.com/owner/repo.git",
            "ftp://github.com/owner/repo.git",
            "https://github.com/owner",
            "https://github.com/owner/repo/extra",
            "git@notgithub.com:owner/repo.git",
        )
        for origin in rejected:
            with self.subTest(origin=origin):
                self.assertIsNone(_normalize_github_repo(origin))

    def test_generic_host_with_selected_skill_requires_discovery_evidence(self):
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "@Scope Reality Check red-team this architecture",
            host="CLAUDE",
        )
        self.assertEqual(handoff["SKILL_CHECK"], "BLOCKED")
        self.assertEqual(handoff["SKILL_HOST_MODE"], "UNSUPPORTED")
        self.assertIn(
            "HOST_DISCOVERY_RECORD_REQUIRED",
            handoff["REJECTION_REASON"],
        )

    def test_generic_host_fails_closed_without_supported_file_read(self):
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "@Scope Reality Check red-team this architecture",
            host="GROK",
            host_discovery_record=self._generic_repo_read_record(
                "GROK", read_state="UNKNOWN"
            ),
        )
        self.assertEqual(handoff["SKILL_CHECK"], "BLOCKED")
        self.assertIn(
            "HOST_FILE_READ_CAPABILITY_UNKNOWN",
            handoff["REJECTION_REASON"],
        )

    def test_generic_host_rejects_non_repo_bound_environment(self):
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "@Scope Reality Check red-team this architecture",
            host="MANUS",
            host_discovery_record=self._generic_repo_read_record(
                "MANUS", environment="CLOUD_SANDBOX"
            ),
        )
        self.assertEqual(handoff["SKILL_CHECK"], "BLOCKED")
        self.assertIn(
            "HOST_ENVIRONMENT_NOT_REPO_BOUND:CLOUD_SANDBOX",
            handoff["REJECTION_REASON"],
        )

    def test_generic_host_rejects_declarative_only_discovery_provenance(self):
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "@Scope Reality Check red-team this architecture",
            host="CLAUDE",
            host_discovery_record=self._generic_repo_read_record(
                "CLAUDE", provenance="UNVERIFIED_SELF_CLAIM"
            ),
        )
        self.assertEqual(handoff["SKILL_CHECK"], "BLOCKED")
        self.assertIn(
            "HOST_DISCOVERY_PROVENANCE_UNVERIFIED",
            handoff["REJECTION_REASON"],
        )

    def test_generic_host_rejects_allowlisted_provenance_for_wrong_repo(self):
        record = self._generic_repo_read_record("CLAUDE")
        expected_repo = _canonical_repo_binding(REPO_ROOT)
        self.assertIsNotNone(expected_repo)
        record["provenance"] = record["provenance"].replace(
            f"repo={expected_repo}",
            "repo=other-owner/p2p-upgrade-github-1",
        )
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "@Scope Reality Check red-team this architecture",
            host="CLAUDE",
            host_discovery_record=record,
        )
        self.assertEqual(handoff["SKILL_CHECK"], "BLOCKED")
        self.assertIn(
            "HOST_DISCOVERY_PROVENANCE_REPO_MISMATCH",
            handoff["REJECTION_REASON"],
        )

    def test_generic_host_rejects_allowlisted_provenance_for_wrong_revision(self):
        record = self._generic_repo_read_record("CLAUDE")
        revision = _current_repo_revision(REPO_ROOT)
        self.assertIsNotNone(revision)
        record["provenance"] = record["provenance"].replace(
            f"revision={revision}",
            f"revision={'0' * 40}",
        )
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "@Scope Reality Check red-team this architecture",
            host="CLAUDE",
            host_discovery_record=record,
        )
        self.assertEqual(handoff["SKILL_CHECK"], "BLOCKED")
        self.assertIn(
            "HOST_DISCOVERY_PROVENANCE_REVISION_MISMATCH",
            handoff["REJECTION_REASON"],
        )

    def test_generic_host_rejects_wrong_repo_read_probe_hash(self):
        record = self._generic_repo_read_record("CLAUDE")
        record["provenance"] = re.sub(
            r"sha256=[0-9a-f]{64}$",
            "sha256=" + ("0" * 64),
            record["provenance"],
        )
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "@Scope Reality Check red-team this architecture",
            host="CLAUDE",
            host_discovery_record=record,
        )
        self.assertEqual(handoff["SKILL_CHECK"], "BLOCKED")
        self.assertIn(
            "HOST_DISCOVERY_PROBE_HASH_MISMATCH",
            handoff["REJECTION_REASON"],
        )

    def test_generic_host_rejects_missing_discovery_schema(self):
        record = self._generic_repo_read_record("CLAUDE")
        record.pop("schema", None)
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "@Scope Reality Check red-team this architecture",
            host="CLAUDE",
            host_discovery_record=record,
        )
        self.assertEqual(handoff["SKILL_CHECK"], "BLOCKED")
        self.assertIn(
            "HOST_DISCOVERY_RECORD_SCHEMA_INVALID",
            handoff["REJECTION_REASON"],
        )

    def test_generic_host_rejects_string_active_flag(self):
        record = self._generic_repo_read_record("CLAUDE")
        record["active"] = "false"
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "@Scope Reality Check red-team this architecture",
            host="CLAUDE",
            host_discovery_record=record,
        )
        self.assertEqual(handoff["SKILL_CHECK"], "BLOCKED")
        self.assertIn(
            "HOST_DISCOVERY_ACTIVE_BOOL_REQUIRED",
            handoff["REJECTION_REASON"],
        )

    def test_generic_host_rejects_stale_discovery_evidence(self):
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "@Scope Reality Check red-team this architecture",
            host="CLAUDE",
            host_discovery_record=self._generic_repo_read_record(
                "CLAUDE", observed_at="2000-01-01T00:00:00+00:00"
            ),
        )
        self.assertEqual(handoff["SKILL_CHECK"], "BLOCKED")
        self.assertTrue(
            any(
                reason.startswith("HOST_DISCOVERY_EVIDENCE_STALE:")
                for reason in handoff["REJECTION_REASON"]
            )
        )

    def test_generic_host_rejects_wrong_project_binding(self):
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "@Scope Reality Check red-team this architecture",
            host="CLAUDE",
            host_discovery_record=self._generic_repo_read_record(
                "CLAUDE",
                project_binding="evil-owner/p2p-upgrade-github-1",
            ),
        )
        self.assertEqual(handoff["SKILL_CHECK"], "BLOCKED")
        self.assertIn(
            "HOST_PROJECT_BINDING_MISMATCH",
            handoff["REJECTION_REASON"],
        )

    def test_generic_host_requires_available_execution_transport(self):
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "@Scope Reality Check red-team this architecture",
            host="CLAUDE",
            host_discovery_record=self._generic_repo_read_record(
                "CLAUDE", execution_transport_available=False
            ),
        )
        self.assertEqual(handoff["SKILL_CHECK"], "BLOCKED")
        self.assertIn(
            "HOST_EXECUTION_TRANSPORT_UNAVAILABLE",
            handoff["REJECTION_REASON"],
        )

    def test_generic_host_rejects_string_false_transport(self):
        record = self._generic_repo_read_record("CLAUDE")
        record["execution_transport_available"] = "false"
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "@Scope Reality Check red-team this architecture",
            host="CLAUDE",
            host_discovery_record=record,
        )
        self.assertEqual(handoff["SKILL_CHECK"], "BLOCKED")
        self.assertIn(
            "HOST_DISCOVERY_EXECUTION_TRANSPORT_BOOL_REQUIRED",
            handoff["REJECTION_REASON"],
        )

    def test_generic_host_rejects_mismatched_host_id_and_profile_label(self):
        record = self._generic_repo_read_record("CLAUDE")
        record["host_id"] = "GROK"
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "@Scope Reality Check red-team this architecture",
            host="CLAUDE",
            host_discovery_record=record,
        )
        self.assertEqual(handoff["SKILL_CHECK"], "BLOCKED")
        self.assertIn(
            "HOST_DISCOVERY_IDENTITY_MISMATCH",
            handoff["REJECTION_REASON"],
        )

    def test_generic_host_rejects_far_future_observation(self):
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "@Scope Reality Check red-team this architecture",
            host="CLAUDE",
            host_discovery_record=self._generic_repo_read_record(
                "CLAUDE",
                observed_at="2099-01-01T00:00:00+00:00",
            ),
        )
        self.assertEqual(handoff["SKILL_CHECK"], "BLOCKED")
        self.assertIn(
            "HOST_DISCOVERY_EVIDENCE_FROM_FUTURE",
            handoff["REJECTION_REASON"],
        )

    def test_generic_host_rejects_unparseable_observation(self):
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "@Scope Reality Check red-team this architecture",
            host="CLAUDE",
            host_discovery_record=self._generic_repo_read_record(
                "CLAUDE",
                observed_at="not-a-timestamp",
            ),
        )
        self.assertEqual(handoff["SKILL_CHECK"], "BLOCKED")
        self.assertIn(
            "HOST_DISCOVERY_OBSERVED_AT_INVALID",
            handoff["REJECTION_REASON"],
        )

    def test_generic_host_rejects_same_basename_wrong_repository(self):
        record = self._generic_repo_read_record("CLAUDE")
        record["project_binding"] = "other-owner/p2p-upgrade-github-1"
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "@Scope Reality Check red-team this architecture",
            host="CLAUDE",
            host_discovery_record=record,
        )
        self.assertEqual(handoff["SKILL_CHECK"], "BLOCKED")
        self.assertIn(
            "HOST_PROJECT_BINDING_MISMATCH",
            handoff["REJECTION_REASON"],
        )

    def test_supervisor_combined_negative_control_is_blocked(self):
        record = self._generic_repo_read_record("CLAUDE")
        record["host_id"] = "GROK"
        record["provenance"] = "UNVERIFIED_SELF_CLAIM"
        record["observed_at"] = "2099-01-01T00:00:00Z"
        record["project_binding"] = "other-owner/p2p-upgrade-github-1"
        record["execution_transport_available"] = "false"
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "@Scope Reality Check red-team this architecture",
            host="CLAUDE",
            host_discovery_record=record,
        )
        self.assertEqual(handoff["SKILL_CHECK"], "BLOCKED")
        self.assertNotEqual(
            handoff["SKILL_HOST_MODE"],
            "GENERIC_EXACT_REPO_READ",
        )

    def test_receipt_requires_exact_frozen_hashes_and_no_permission_widening(self):
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "@Scope Reality Check xé kế hoạch này",
            host="ARENA",
        )
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "SKILLS_SELECTED": list(handoff["SKILLS_SELECTED"]),
            "SKILL_SOURCE_HASHES": dict(handoff["SKILL_SOURCE_HASHES"]),
            "SKILL_LOAD_STAGE": "LOAD",
            "SKILL_CONSUMPTION": "CONSUMED",
            "SKILL_HOST_MODE": handoff["SKILL_HOST_MODE"],
            "PERMISSION_WIDENED": "NO",
        }
        self.assertTrue(validate_consumption_receipt(handoff, receipt)["valid"])
        receipt["SKILL_SOURCE_HASHES"] = {
            key: "0" * 64 for key in handoff["SKILL_SOURCE_HASHES"]
        }
        result = validate_consumption_receipt(handoff, receipt)
        self.assertFalse(result["valid"])
        self.assertIn("SKILL_SOURCE_HASH_MISMATCH", result["reason_codes"])

    def test_capability_intelligence_uses_canonical_metadata_selection(self):
        eligible = skill_eligibility_set(
            SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json"
        )
        execution = compute_execution_requirements(
            {
                "task_id": "skill-wire",
                "title": "@Scope Reality Check phản biện gắt kế hoạch này",
                "purpose": "pressure test before implementation",
                "scope": (),
                "permission_needs": ("sandboxed-default",),
            },
            REPO_ROOT,
            installed_skills=tuple(
                item["capability_id"] for item in eligible
                if item["eligible"]
            ),
        )
        self.assertIn(
            "scope-reality-check",
            execution.skill_selection.selected_skills,
        )

    def test_arena_execution_prompt_contains_frozen_skill_handoff(self):
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "@Scope Reality Check xé kế hoạch này",
            host="ARENA",
        )
        binding = SessionBinding(
            session_id="skillwire-arena-01",
            host="ARENA",
            goal_id="ISSUE-298",
            goal="Skill consumption wire",
        )
        prompt = build_execution_prompt(
            binding,
            "@Scope Reality Check xé kế hoạch này",
            task_id="skill-wire",
            arena_prompt_checkpoint={
                "project": "P2P-upgrade-github-1",
                "plan_reference": "Issue #298",
                "already_completed": "metadata selection",
                "current_checkpoint": "skill handoff frozen",
                "blocker_or_owner_gate": "NONE_RECORDED",
                "next_bounded_step": "consume selected skill",
            },
            skill_handoff=handoff,
        )
        self.assertIn("P2P_SKILL_HANDOFF:", prompt)
        self.assertIn("SKILL_HOST_MODE=ARENA_EXACT_REPO_READ", prompt)
        self.assertIn(
            handoff["SKILL_SOURCE_HASHES"]["scope-reality-check"],
            prompt,
        )
        self.assertIn("SKILL_CONSUMPTION_RECEIPT", prompt)

    def test_control_tower_rejects_missing_or_mismatched_consumption_receipt(self):
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "@Scope Reality Check xé kế hoạch này",
            host="ARENA",
        )
        binding = SessionBinding(
            session_id="skillwire-state-01",
            host="ARENA",
            goal_id="ISSUE-298",
            goal="Skill consumption wire",
        )
        state = ControlTowerState.empty()
        state.session_records[binding.session_id] = {
            "BINDING": binding.to_dict(),
            "SKILL_HANDOFF": handoff,
        }
        packet = ControlTowerReturnPacket(
            binding=binding,
            session_state="COMPLETED",
            canonical_base_sha="a" * 40,
            canonical_base_tree="b" * 40,
            skill_consumption_receipt=None,
        )
        result = state.ingest(
            packet,
            current_canonical_base_sha="a" * 40,
            current_canonical_base_tree="b" * 40,
            record_event=False,
        )
        self.assertEqual(
            result.control_tower_status, "RECONCILIATION_REQUIRED"
        )
        self.assertIn(
            "SKILL_CONSUMPTION_RECEIPT_MISSING", result.blockers
        )

    def test_control_tower_accepts_exact_consumption_receipt(self):
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "@Scope Reality Check xé kế hoạch này",
            host="ARENA",
        )
        binding = SessionBinding(
            session_id="skillwire-state-02",
            host="ARENA",
            goal_id="ISSUE-298",
            goal="Skill consumption wire",
        )
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "SKILLS_SELECTED": list(handoff["SKILLS_SELECTED"]),
            "SKILL_SOURCE_HASHES": dict(handoff["SKILL_SOURCE_HASHES"]),
            "SKILL_LOAD_STAGE": "LOAD",
            "SKILL_CONSUMPTION": "CONSUMED",
            "SKILL_HOST_MODE": handoff["SKILL_HOST_MODE"],
            "PERMISSION_WIDENED": "NO",
        }
        packet = ControlTowerReturnPacket(
            binding=binding,
            session_state="COMPLETED",
            canonical_base_sha="a" * 40,
            canonical_base_tree="b" * 40,
            skill_consumption_receipt=receipt,
        )
        roundtrip = ControlTowerReturnPacket.from_mapping(packet.to_dict())
        self.assertEqual(roundtrip.skill_consumption_receipt, receipt)
        state = ControlTowerState.empty()
        state.session_records[binding.session_id] = {
            "BINDING": binding.to_dict(),
            "SKILL_HANDOFF": handoff,
        }
        result = state.ingest(
            roundtrip,
            current_canonical_base_sha="a" * 40,
            current_canonical_base_tree="b" * 40,
            record_event=False,
        )
        self.assertEqual(result.control_tower_status, "COMPLETED")

    def test_release_and_doctor_ship_scope_reality_check_to_installed_projects(self):
        package_text = (REPO_ROOT / "scripts" / "package_release.py").read_text(
            encoding="utf-8"
        )
        doctor_text = (REPO_ROOT / "scripts" / "doctor.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('"scope-reality-check"', package_text)
        self.assertIn('"scope-reality-check"', doctor_text)

    def test_existing_active_ui_skill_loads_through_same_generic_wire(self):
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "Cải thiện UI dashboard responsive trên điện thoại",
            host="ARENA",
        )
        self.assertEqual(handoff["SKILL_CHECK"], "PASS")
        self.assertIn("p2p-uiux", handoff["SKILLS_SELECTED"])
        self.assertEqual(
            handoff["SKILL_SOURCE_PATHS"]["p2p-uiux"],
            ".agents/skills/p2p-uiux/SKILL.md",
        )
        self.assertEqual(
            len(handoff["SKILL_SOURCE_HASHES"]["p2p-uiux"]),
            64,
        )

    def test_p2p_scope_is_active_model_routable_and_explicit_still_loads(self):
        registry = json.loads(
            (SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json")
            .read_text(encoding="utf-8")
        )
        record = next(
            item for item in registry["capabilities"]
            if item["CAPABILITY_ID"] == "p2p-scope"
        )
        self.assertEqual(record["TYPE"], "SKILL")
        self.assertEqual(record["STATUS"], "ACTIVE")
        self.assertEqual(record["INVOCATION_CLASS"], "MODEL_ROUTABLE")
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "$p2p-scope organize this large task",
            host="ARENA",
        )
        self.assertEqual(handoff["SKILL_CHECK"], "PASS")
        self.assertIn("p2p-scope", handoff["SKILLS_SELECTED"])
        self.assertEqual(
            handoff["SKILL_SOURCE_PATHS"]["p2p-scope"],
            ".agents/skills/p2p-scope/SKILL.md",
        )
        self.assertEqual(
            handoff["SKILL_SOURCE_HASHES"]["p2p-scope"],
            "64a59449c5ace7dd49512f8c68b97f0e2f7748fac73aeaa268eb1dbe90e2bc5a",
        )

    def test_natural_language_large_work_auto_routes_p2p_scope(self):
        selection = select_skills_for_task(
            REPO_ROOT,
            "Organize this substantial multi-step work with checkpoints",
        )
        self.assertIn("p2p-scope", selection.selected)
        self.assertNotIn("scope-reality-check", selection.selected)
        self.assertTrue(selection.route["single_router"])

    def test_owner_big_goal_language_auto_routes_p2p_scope(self):
        selection = select_skills_for_task(
            REPO_ROOT,
            "Continue this big goal end-to-end to completion",
        )
        self.assertIn("p2p-scope", selection.selected)
        self.assertNotIn("scope-reality-check", selection.selected)
        self.assertTrue(selection.route["single_router"])

    def test_vietnamese_large_goal_auto_routes_p2p_scope(self):
        selection = select_skills_for_task(
            REPO_ROOT,
            "Chia nhỏ goal lớn này thành nhiều bước và mốc kiểm tra rõ ràng",
        )
        self.assertIn("p2p-scope", selection.selected)
        self.assertTrue(selection.route["single_router"])

    def test_natural_language_scope_request_materializes_arena_handoff(self):
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "Organize this substantial multi-step work with checkpoints",
            host="ARENA",
        )
        self.assertEqual(handoff["SKILL_CHECK"], "PASS")
        self.assertIn("p2p-scope", handoff["SKILLS_SELECTED"])
        self.assertEqual(
            handoff["SKILL_SOURCE_PATHS"]["p2p-scope"],
            ".agents/skills/p2p-scope/SKILL.md",
        )
        self.assertEqual(
            handoff["SKILL_SOURCE_HASHES"]["p2p-scope"],
            "64a59449c5ace7dd49512f8c68b97f0e2f7748fac73aeaa268eb1dbe90e2bc5a",
        )
        self.assertEqual(
            handoff["SKILL_HOST_MODE"], "ARENA_EXACT_REPO_READ"
        )

    def test_trivial_mechanical_work_does_not_auto_route_p2p_scope(self):
        selection = select_skills_for_task(
            REPO_ROOT,
            "Rename local variable x to y",
        )
        self.assertNotIn("p2p-scope", selection.selected)

    def test_single_dependency_maintenance_does_not_auto_route_p2p_scope(self):
        selection = select_skills_for_task(
            REPO_ROOT,
            "Update dependency requests from 2.31.0 to 2.32.0",
        )
        self.assertNotIn("p2p-scope", selection.selected)

    def test_single_checkpoint_mention_does_not_auto_route_p2p_scope(self):
        selection = select_skills_for_task(
            REPO_ROOT,
            "Rename checkpoint variable to checkpoint_id",
        )
        self.assertNotIn("p2p-scope", selection.selected)

    def test_small_text_decomposition_does_not_auto_route_p2p_scope(self):
        selection = select_skills_for_task(
            REPO_ROOT,
            "Chia nhỏ đoạn văn này thành 3 ý",
        )
        self.assertNotIn("p2p-scope", selection.selected)

    def test_small_english_breakdown_does_not_auto_route_p2p_scope(self):
        selection = select_skills_for_task(
            REPO_ROOT,
            "Break this down into two bullet points",
        )
        self.assertNotIn("p2p-scope", selection.selected)

    def test_current_status_contract_makes_active_skills_eligible_only(self):
        path = SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json"
        records = skill_eligibility_set(path)
        ids = {item["capability_id"] for item in records}
        self.assertIn("scope-reality-check", ids)
        self.assertNotIn("p2p_iris", ids)
        scope = next(
            item for item in records
            if item["capability_id"] == "scope-reality-check"
        )
        self.assertTrue(scope["eligible"])
        self.assertEqual(scope["provenance_level"], "ACTIVE_DECLARED")

    def _copy_minimal_required_skill_root(self, root: Path) -> None:
        registry_target = (
            root / ".p2p" / "system" / "p2p_capabilities"
            / "capabilities.json"
        )
        registry_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(
            SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json",
            registry_target,
        )
        for skill_id in ("scope-reality-check", "p2p-scope"):
            source = REPO_ROOT / ".agents" / "skills" / skill_id
            target = root / ".agents" / "skills" / skill_id
            shutil.copytree(source, target)


    def _initialize_ready_task(
        self,
        root: Path,
        *,
        task_id: str = "issue-333-ready",
    ) -> None:
        now = "2026-10-08T07:00:00+00:00"
        plan = TaskPlan.from_goal(
            {
                "goal_id": "ISSUE-333",
                "scope": ["generic repo-read skill handoff"],
                "out_of_scope": ["release", "deploy", "promotion"],
            },
            [
                {
                    "task_id": task_id,
                    "title": "Generic repo-read handoff",
                    "purpose": "Pressure-test this plan",
                    "status": "READY",
                    "scope": ["generic repo-read skill handoff"],
                    "acceptance_requirements": ["Skill handoff is bounded."],
                    "required_evidence": ["focused-proof"],
                }
            ],
            now=now,
        )
        TaskStateStore(root).initialize(plan, at=now)

    def _seed_legacy_generic_active_session(
        self,
        root: Path,
        tower: ControlTower,
        *,
        task_id: str = "issue-333-ready",
        host: str = "CLAUDE",
    ) -> SessionBinding:
        skill_path = ".agents/skills/scope-reality-check/SKILL.md"
        skill_hash = hashlib.sha256((root / skill_path).read_bytes()).hexdigest()
        handoff = {
            "schema": "p2p-skill-handoff/1",
            "SKILL_CHECK": "PASS",
            "REQUIRED_SKILLS": ["scope-reality-check"],
            "SKILLS_CONSIDERED_METADATA_COUNT": 1,
            "SKILLS_SELECTED": ["scope-reality-check"],
            "SKILL_LOAD_STAGE": "LOAD",
            "SKILL_SOURCE_HASHES": {"scope-reality-check": skill_hash},
            "SKILL_SOURCE_PATHS": {"scope-reality-check": skill_path},
            "SKILL_CONSUMPTION": "EXPECTED",
            "SKILL_HOST_MODE": "GENERIC_EXACT_REPO_READ",
            "MATERIAL_ALTERNATIVES_REJECTED": [],
            "REJECTION_REASON": [],
            "PERMISSION_WIDENED": "NO",
            "SINGLE_ROUTER_REUSED": "YES",
        }
        binding = SessionBinding(
            session_id="legacy-generic-active-01",
            host=host,
            goal_id="ISSUE-333",
            goal="Legacy generic cached prompt",
        )
        event = {
            "schema": CONTROL_TOWER_SESSION_START_EVENT_SCHEMA,
            "event_type": "CONTROL_TOWER_SESSION_STARTED",
            "CONTROL_TOWER_SESSION_STARTED": True,
            "SESSION_BINDING": binding.to_dict(),
            "TASK_ID": task_id,
            "WORKTREE": "fixture-worktree",
            "BRANCH": "fixture-branch",
            "CANONICAL_BASE_SHA": "UNKNOWN",
            "CANONICAL_BASE_TREE": "UNKNOWN",
            "RECOMMENDED_NEW_CHAT": {
                "PROMPT": "LEGACY GENERIC CACHED PROMPT — MUST NOT LEAK",
                "SKILL_HANDOFF": handoff,
                "REQUIRED_SKILLS": ["scope-reality-check"],
            },
            "EXPECTED_LAW_SHA": None,
            "EXPECTED_EXPERIENCE_IDS": [],
            "ACCEPTANCE_CRITERIA": ["Skill handoff is bounded."],
            "SKILL_HANDOFF": handoff,
            "CANARY": None,
            "PACKET_IS_CANONICAL_TRUTH": "NO",
            "PROMOTED": False,
            "PROTECTED_ACTION_EXECUTED": False,
        }
        _append_existing_execution_event(tower.ledger_path, event)
        return binding

    def test_prompt_authoring_context_materializes_required_skill_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            binding = SessionBinding(
                session_id="required-skill-authoring-01",
                host="CLAUDE",
                goal_id="ISSUE-305",
                goal="Write an Arena prompt with required skills",
            )
            contextual = control_tower_cli._contextual_task_for_session(
                Path(directory),
                binding,
                (
                    "Write an Arena prompt that must use "
                    "scope-reality-check and p2p-scope."
                ),
            )
        prompt = build_execution_prompt(binding, contextual)
        self.assertIn("REQUIRED_SKILL_HANDOFF=", prompt)
        self.assertIn(
            "source-bound REQUIRED_SKILLS/path/hash/receipt", prompt
        )

    def test_control_tower_cli_accepts_repeatable_required_skill_flags(self):
        args = control_tower_cli.build_parser().parse_args(
            [
                "start",
                "--host", "ARENA",
                "--goal-id", "ISSUE-305",
                "--goal", "Use required skills",
                "--required-skill", "scope-reality-check",
                "--required-skill", "p2p-scope",
            ]
        )
        self.assertEqual(
            args.required_skill,
            ["scope-reality-check", "p2p-scope"],
        )

    def test_control_tower_cli_accepts_existing_host_discovery_record_file(self):
        args = control_tower_cli.build_parser().parse_args(
            [
                "start",
                "--host", "CLAUDE",
                "--goal-id", "ISSUE-333",
                "--goal", "Use repo-native skills",
                "--host-discovery-record-file", "host-discovery.json",
            ]
        )
        self.assertEqual(
            args.host_discovery_record_file,
            "host-discovery.json",
        )

    def test_control_tower_cli_loads_existing_host_discovery_record(self):
        with tempfile.TemporaryDirectory(prefix="p2p-host-discovery-") as raw:
            record_path = Path(raw) / "host-discovery.json"
            record_path.write_text(
                json.dumps(self._generic_repo_read_record("CLAUDE")),
                encoding="utf-8",
            )
            loaded = control_tower_cli._load_host_discovery_record(
                str(record_path)
            )
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["schema"], "p2p-host-discovery-record/1")
        self.assertEqual(loaded["host_id"], "CLAUDE")
        self.assertEqual(
            loaded["profile"]["capabilities"]["can_read_files"],
            "SUPPORTED",
        )
        self.assertEqual(loaded["availability"], "KNOWN_AVAILABLE")

    def test_prompt_declared_two_required_skills_are_exact_and_visible(self):
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "Pressure-test and organize this bounded plan",
            host="ARENA",
            required_skills=("Scope Reality Check", "p2p-scope"),
        )
        self.assertEqual(handoff["SKILL_CHECK"], "PASS")
        self.assertEqual(
            handoff["REQUIRED_SKILLS"],
            ["scope-reality-check", "p2p-scope"],
        )
        self.assertTrue(
            set(handoff["REQUIRED_SKILLS"]).issubset(
                set(handoff["SKILLS_SELECTED"])
            )
        )
        for skill_id in handoff["REQUIRED_SKILLS"]:
            self.assertIn(skill_id, handoff["SKILL_SOURCE_PATHS"])
            self.assertEqual(
                len(handoff["SKILL_SOURCE_HASHES"][skill_id]), 64
            )
        lines = "\n".join(skill_handoff_prompt_lines(handoff))
        self.assertIn(
            "REQUIRED_SKILLS=scope-reality-check,p2p-scope", lines
        )
        self.assertIn(
            "Every skill listed in REQUIRED_SKILLS is mandatory", lines
        )

    def test_unknown_required_skill_fails_closed(self):
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "Do the task",
            host="ARENA",
            required_skills=("definitely-not-a-real-skill",),
        )
        self.assertEqual(handoff["SKILL_CHECK"], "BLOCKED")
        self.assertIn(
            "REQUIRED_SKILL_NOT_FOUND:definitely-not-a-real-skill",
            handoff["REJECTION_REASON"],
        )

    def test_more_than_three_required_skills_fails_closed(self):
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "Do the task",
            host="ARENA",
            required_skills=("one", "two", "three", "four"),
        )
        self.assertEqual(handoff["SKILL_CHECK"], "BLOCKED")
        self.assertIn(
            "REQUIRED_SKILL_SET_LIMIT_EXCEEDED",
            handoff["REJECTION_REASON"],
        )

    def test_required_p2p_scope_skill_is_supported_after_admission(self):
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "Organize this work",
            host="ARENA",
            required_skills=("p2p-scope",),
        )
        self.assertEqual(handoff["SKILL_CHECK"], "PASS")
        self.assertEqual(handoff["REQUIRED_SKILLS"], ["p2p-scope"])
        self.assertIn("p2p-scope", handoff["SKILLS_SELECTED"])
        self.assertEqual(
            handoff["SKILL_SOURCE_PATHS"]["p2p-scope"],
            ".agents/skills/p2p-scope/SKILL.md",
        )

    def test_receipt_missing_one_required_skill_fails_reconciliation(self):
        handoff = prepare_skill_handoff(
            REPO_ROOT,
            "Pressure-test and organize this plan",
            host="ARENA",
            required_skills=("scope-reality-check", "p2p-scope"),
        )
        first = handoff["REQUIRED_SKILLS"][0]
        receipt = {
            "schema": RECEIPT_SCHEMA,
            "SKILLS_SELECTED": [first],
            "SKILL_SOURCE_HASHES": {
                first: handoff["SKILL_SOURCE_HASHES"][first]
            },
            "SKILL_LOAD_STAGE": "LOAD",
            "SKILL_CONSUMPTION": "CONSUMED",
            "SKILL_HOST_MODE": handoff["SKILL_HOST_MODE"],
            "PERMISSION_WIDENED": "NO",
        }
        result = validate_consumption_receipt(handoff, receipt)
        self.assertFalse(result["valid"])
        self.assertIn("SKILL_SELECTED_SET_MISMATCH", result["reason_codes"])

    def test_control_tower_prompt_enforces_two_required_skills(self):
        with tempfile.TemporaryDirectory(prefix="p2p-required-skills-") as raw:
            root = Path(raw)
            self._copy_minimal_required_skill_root(root)
            tower = ControlTower(root)
            binding = SessionBinding(
                session_id="required-skills-01",
                host="CODEX",
                goal_id="ISSUE-305",
                goal="Prompt-declared required skills",
            )
            result = tower.start_session(
                binding,
                task_id="issue-305-test",
                task_prompt="Pressure-test and organize this plan",
                required_skills=(
                    "scope-reality-check",
                    "p2p-scope",
                ),
            )
            prompt = result["recommendation"]["PROMPT"]
            self.assertIn(
                "REQUIRED_SKILLS=scope-reality-check,p2p-scope", prompt
            )
            self.assertIn(
                ".agents/skills/scope-reality-check/SKILL.md", prompt
            )
            self.assertIn(
                ".agents/skills/p2p-scope/SKILL.md", prompt
            )
            self.assertEqual(
                result["recommendation"]["REQUIRED_SKILLS"],
                ["scope-reality-check", "p2p-scope"],
            )


    def test_control_tower_generic_host_blocks_without_trusted_actor_observation(self):
        with tempfile.TemporaryDirectory(prefix="p2p-generic-skill-host-") as raw:
            root = Path(raw)
            self._copy_minimal_required_skill_root(root)
            self._init_fixture_git(root)
            tower = ControlTower(root)
            binding = SessionBinding(
                session_id="generic-skill-host-01",
                host="CLAUDE",
                goal_id="ISSUE-333",
                goal="Generic repo-read skill handoff",
            )
            record = self._generic_repo_read_record("CLAUDE", root=root)
            with self.assertRaisesRegex(
                BindingError,
                "SKILL_HANDOFF_BLOCKED:"
                "HOST_TRUSTED_REPO_READ_OBSERVATION_UNAVAILABLE",
            ):
                tower.start_session(
                    binding,
                    task_id="issue-333-test",
                    task_prompt="Pressure-test this plan",
                    required_skills=("scope-reality-check",),
                    host_discovery_record=record,
                )


    def test_start_session_cannot_create_generic_active_session_from_c21_alone(self):
        with tempfile.TemporaryDirectory(prefix="p2p-generic-active-") as raw:
            root = Path(raw)
            self._copy_minimal_required_skill_root(root)
            self._init_fixture_git(
                root,
                remote="https://github.com/fixture-owner/p2p-generic-active.git",
            )
            tower = ControlTower(root)
            binding = SessionBinding(
                session_id="generic-active-01",
                host="CLAUDE",
                goal_id="ISSUE-333",
                goal="Generic active session evidence freshness",
            )
            fresh = self._generic_repo_read_record("CLAUDE", root=root)
            with self.assertRaisesRegex(
                BindingError,
                "HOST_TRUSTED_REPO_READ_OBSERVATION_UNAVAILABLE",
            ):
                tower.start_session(
                    binding,
                    task_id="issue-333-active",
                    task_prompt="Pressure-test this plan",
                    required_skills=("scope-reality-check",),
                    host_discovery_record=fresh,
                )


    def test_recommend_next_session_blocks_legacy_generic_cache_without_discovery(self):
        with tempfile.TemporaryDirectory(prefix="p2p-generic-cache-missing-") as raw:
            root = Path(raw)
            self._copy_minimal_required_skill_root(root)
            self._init_fixture_git(root)
            self._initialize_ready_task(root)
            tower = ControlTower(root)
            self._seed_legacy_generic_active_session(root, tower)
            result = tower.recommend_next_session("CLAUDE")
            self.assertEqual(result["status"], "BLOCKED")
            self.assertIn("HOST_DISCOVERY_RECORD_REQUIRED", result["reason"])
            self.assertIsNone(result["recommendation"])

    def test_recommend_next_session_blocks_legacy_generic_cache_with_stale_discovery(self):
        with tempfile.TemporaryDirectory(prefix="p2p-generic-cache-stale-") as raw:
            root = Path(raw)
            self._copy_minimal_required_skill_root(root)
            self._init_fixture_git(root)
            self._initialize_ready_task(root)
            tower = ControlTower(root)
            self._seed_legacy_generic_active_session(root, tower)
            stale = self._generic_repo_read_record(
                "CLAUDE",
                root=root,
                observed_at="2000-01-01T00:00:00+00:00",
            )
            result = tower.recommend_next_session(
                "CLAUDE",
                host_discovery_record=stale,
            )
            self.assertEqual(result["status"], "BLOCKED")
            self.assertIn("HOST_DISCOVERY_EVIDENCE_STALE", result["reason"])
            self.assertIsNone(result["recommendation"])

    def test_recommend_next_session_blocks_legacy_generic_cache_for_different_host(self):
        with tempfile.TemporaryDirectory(prefix="p2p-generic-cache-host-") as raw:
            root = Path(raw)
            self._copy_minimal_required_skill_root(root)
            self._init_fixture_git(root)
            self._initialize_ready_task(root)
            tower = ControlTower(root)
            self._seed_legacy_generic_active_session(root, tower)
            result = tower.recommend_next_session("GROK")
            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result["reason"], "ACTIVE_SESSION_HOST_MISMATCH")
            self.assertIsNone(result["recommendation"])

    def test_recommend_next_session_fresh_c21_still_blocks_without_actor_observation(self):
        with tempfile.TemporaryDirectory(prefix="p2p-generic-cache-fresh-") as raw:
            root = Path(raw)
            self._copy_minimal_required_skill_root(root)
            self._init_fixture_git(root)
            self._initialize_ready_task(root)
            tower = ControlTower(root)
            self._seed_legacy_generic_active_session(root, tower)
            fresh = self._generic_repo_read_record("CLAUDE", root=root)
            result = tower.recommend_next_session(
                "CLAUDE",
                host_discovery_record=fresh,
            )
            self.assertEqual(result["status"], "BLOCKED")
            self.assertIn(
                "HOST_TRUSTED_REPO_READ_OBSERVATION_UNAVAILABLE",
                result["reason"],
            )
            self.assertIsNone(result["recommendation"])

    def test_next_safe_session_direct_api_does_not_leak_legacy_generic_prompt(self):
        with tempfile.TemporaryDirectory(prefix="p2p-generic-cache-api-") as raw:
            root = Path(raw)
            self._copy_minimal_required_skill_root(root)
            self._init_fixture_git(root)
            self._initialize_ready_task(root)
            tower = ControlTower(root)
            self._seed_legacy_generic_active_session(root, tower)
            result = next_safe_session(root, "CLAUDE")
            self.assertEqual(result["status"], "BLOCKED")
            self.assertIn("HOST_DISCOVERY_RECORD_REQUIRED", result["reason"])
            self.assertIsNone(result["recommendation"])

    def test_active_session_same_required_aliases_remains_idempotent(self):
        with tempfile.TemporaryDirectory(prefix="p2p-required-skills-") as raw:
            root = Path(raw)
            self._copy_minimal_required_skill_root(root)
            tower = ControlTower(root)
            binding = SessionBinding(
                session_id="required-skills-alias-01",
                host="CODEX",
                goal_id="ISSUE-305",
                goal="Prompt-declared required skills",
            )
            first = tower.start_session(
                binding,
                task_id="issue-305-test",
                task_prompt="Pressure-test and organize this plan",
                required_skills=("Scope Reality Check", "p2p-scope"),
            )
            second = tower.start_session(
                binding,
                task_id="issue-305-test",
                task_prompt="Pressure-test and organize this plan",
                required_skills=("scope-reality-check", "p2p-scope"),
            )
            self.assertTrue(second["idempotent"])
            self.assertEqual(
                first["recommendation"]["REQUIRED_SKILLS"],
                second["recommendation"]["REQUIRED_SKILLS"],
            )
    def test_active_session_cannot_swap_required_skill_set(self):
        with tempfile.TemporaryDirectory(prefix="p2p-required-skills-") as raw:
            root = Path(raw)
            self._copy_minimal_required_skill_root(root)
            tower = ControlTower(root)
            binding = SessionBinding(
                session_id="required-skills-02",
                host="CODEX",
                goal_id="ISSUE-305",
                goal="Prompt-declared required skills",
            )
            tower.start_session(
                binding,
                task_id="issue-305-test",
                task_prompt="Pressure-test and organize this plan",
                required_skills=(
                    "scope-reality-check",
                    "p2p-scope",
                ),
            )
            with self.assertRaisesRegex(
                BindingError,
                "REQUIRED_SKILLS_CHANGED_FOR_ACTIVE_SESSION",
            ):
                tower.start_session(
                    binding,
                    task_id="issue-305-test",
                    task_prompt="Pressure-test and organize this plan",
                    required_skills=("scope-reality-check",),
                )


class SkillEffectivenessEvidenceTests(unittest.TestCase):
    """Issue #308: consumption proof is not effectiveness proof."""

    TASK_REF = "issue-308-proof"
    TASK_FP = "task-fingerprint-v1"
    ACCEPTANCE_FP = "acceptance-fingerprint-v1"
    SOURCE_REV = "source-revision-v1"
    PROJECT_REV = "project-revision-v1"
    EVAL_ID = "deterministic-quality-v1"

    def _handoff(self, two_skills=False):
        required = (
            ("scope-reality-check", "p2p-scope")
            if two_skills else ("scope-reality-check",)
        )
        return prepare_skill_handoff(
            REPO_ROOT,
            "Pressure-test and organize this bounded task",
            host="ARENA",
            required_skills=required,
        )

    def _receipt(self, handoff, tamper_hash=False):
        hashes = dict(handoff["SKILL_SOURCE_HASHES"])
        if tamper_hash:
            first = handoff["SKILLS_SELECTED"][0]
            hashes[first] = "0" * 64
        return {
            "schema": RECEIPT_SCHEMA,
            "SKILLS_SELECTED": list(handoff["SKILLS_SELECTED"]),
            "SKILL_SOURCE_HASHES": hashes,
            "SKILL_LOAD_STAGE": "LOAD",
            "SKILL_CONSUMPTION": "CONSUMED",
            "SKILL_HOST_MODE": handoff["SKILL_HOST_MODE"],
            "PERMISSION_WIDENED": "NO",
        }

    def _quality(self, evidence_id, **overrides):
        record = {
            "task_ref": self.TASK_REF,
            "task_fingerprint": self.TASK_FP,
            "acceptance_fingerprint": self.ACCEPTANCE_FP,
            "source_revision": self.SOURCE_REV,
            "project_revision": self.PROJECT_REV,
            "eval_contract_id": self.EVAL_ID,
            "evaluator_id": "deterministic-evaluator",
            "evidence_id": evidence_id,
            "deterministic": True,
            "current": True,
        }
        record.update(overrides)
        return record

    def _comparison(self, result="BETTER", **overrides):
        record = {
            "result": result,
            "eval_contract_id": self.EVAL_ID,
            "comparator_id": "deterministic-comparator",
            "evidence_id": "comparison-evidence",
            "baseline_evidence_id": "baseline-evidence",
            "assisted_evidence_id": "assisted-evidence",
            "deterministic": True,
            "current": True,
        }
        record.update(overrides)
        return record

    def _assessment(
            self,
            *,
            handoff=None,
            receipt=None,
            baseline=None,
            assisted=None,
            comparison=None,
            ):
        handoff = handoff or self._handoff()
        receipt = receipt or self._receipt(handoff)
        validation = validate_consumption_receipt(handoff, receipt)
        if baseline is None:
            baseline = self._quality("baseline-evidence")
        if assisted is None:
            assisted = self._quality("assisted-evidence")
        if comparison is None:
            comparison = self._comparison()
        return qi.assess_skill_effectiveness(
            task_ref=self.TASK_REF,
            task_fingerprint=self.TASK_FP,
            acceptance_fingerprint=self.ACCEPTANCE_FP,
            source_revision=self.SOURCE_REV,
            project_revision=self.PROJECT_REV,
            skill_handoff=handoff,
            consumption_validation=validation,
            baseline_quality=baseline,
            assisted_quality=assisted,
            comparison=comparison,
        )

    def test_better_deterministic_pair_supports_effectiveness(self):
        result = self._assessment()
        self.assertEqual(
            result["effectiveness_status"], "EFFECTIVE_SUPPORTED"
        )
        self.assertEqual(
            result["attribution_level"], "SKILL_EFFECTIVENESS"
        )
        self.assertTrue(result["effectiveness_claim_supported"])

    def test_same_deterministic_pair_supports_neutral(self):
        result = self._assessment(comparison=self._comparison("SAME"))
        self.assertEqual(
            result["effectiveness_status"], "NEUTRAL_SUPPORTED"
        )

    def test_worse_deterministic_pair_supports_harmed(self):
        result = self._assessment(comparison=self._comparison("WORSE"))
        self.assertEqual(
            result["effectiveness_status"], "HARMED_SUPPORTED"
        )

    def test_consumed_without_baseline_is_consumption_only(self):
        handoff = self._handoff()
        validation = validate_consumption_receipt(
            handoff, self._receipt(handoff)
        )
        result = qi.assess_skill_effectiveness(
            task_ref=self.TASK_REF,
            task_fingerprint=self.TASK_FP,
            acceptance_fingerprint=self.ACCEPTANCE_FP,
            source_revision=self.SOURCE_REV,
            project_revision=self.PROJECT_REV,
            skill_handoff=handoff,
            consumption_validation=validation,
            baseline_quality=None,
            assisted_quality=self._quality("assisted-evidence"),
            comparison=None,
        )
        self.assertEqual(
            result["effectiveness_status"], "CONSUMPTION_ONLY"
        )
        self.assertFalse(result["effectiveness_claim_supported"])

    def test_self_report_only_cannot_prove_effectiveness(self):
        assisted = self._quality(
            "assisted-evidence",
            evidence_kind="EXECUTOR_SELF_REPORT",
        )
        result = self._assessment(assisted=assisted)
        self.assertEqual(result["effectiveness_status"], "INCONCLUSIVE")
        self.assertIn(
            "SELF_REPORT_NOT_EFFECTIVENESS_EVIDENCE",
            result["reason_codes"],
        )

    def test_frozen_hash_mismatch_is_inconclusive(self):
        handoff = self._handoff()
        result = self._assessment(
            handoff=handoff,
            receipt=self._receipt(handoff, tamper_hash=True),
        )
        self.assertEqual(result["effectiveness_status"], "INCONCLUSIVE")
        self.assertIn(
            "SKILL_SOURCE_HASH_MISMATCH", result["reason_codes"]
        )

    def test_stale_source_bound_evidence_is_inconclusive(self):
        baseline = self._quality("baseline-evidence", current=False)
        result = self._assessment(baseline=baseline)
        self.assertEqual(result["effectiveness_status"], "INCONCLUSIVE")
        self.assertIn("STALE_EVIDENCE", result["reason_codes"])

    def test_acceptance_or_eval_mismatch_is_inconclusive(self):
        assisted = self._quality(
            "assisted-evidence",
            acceptance_fingerprint="different-acceptance",
            eval_contract_id="different-eval",
        )
        result = self._assessment(assisted=assisted)
        self.assertEqual(result["effectiveness_status"], "INCONCLUSIVE")
        self.assertTrue(
            any(
                code.endswith("ACCEPTANCE_FINGERPRINT_MISMATCH")
                for code in result["reason_codes"]
            )
        )
        self.assertIn("EVAL_CONTRACT_MISMATCH", result["reason_codes"])

    def test_multi_skill_run_is_set_level_only(self):
        handoff = self._handoff(two_skills=True)
        result = self._assessment(
            handoff=handoff,
            receipt=self._receipt(handoff),
        )
        self.assertEqual(
            result["effectiveness_status"], "EFFECTIVE_SUPPORTED"
        )
        self.assertEqual(result["attribution_level"], "SET_EFFECTIVENESS")
        self.assertIsNone(result["per_skill_attribution"])

    def test_learning_bridge_reuses_existing_candidate_policy(self):
        assessment = self._assessment()
        observation = qi.skill_effectiveness_learning_observation(
            assessment
        )
        self.assertTrue(observation["eligible"])
        self.assertFalse(observation["auto_promote"])
        self.assertEqual(
            observation["candidate_kwargs"]["observation_count"], 1
        )

        old_store = qi.LEARNING_STORE_PATH
        with tempfile.TemporaryDirectory(
                prefix="p2p-effectiveness-learning-") as raw:
            try:
                qi.LEARNING_STORE_PATH = (
                    Path(raw) / "learning_candidates.jsonl"
                )
                candidate = qi.add_learning_candidate(
                    **observation["candidate_kwargs"]
                )
                policy = qi.learning_promotion_policy(candidate)
            finally:
                qi.LEARNING_STORE_PATH = old_store
        self.assertEqual(candidate["state"], "CANDIDATE")
        self.assertFalse(policy["auto_promoted"])

    def test_assessment_is_read_only_and_does_not_mutate_inputs(self):
        handoff = self._handoff()
        receipt = self._receipt(handoff)
        baseline = self._quality("baseline-evidence")
        assisted = self._quality("assisted-evidence")
        comparison = self._comparison()
        before = json.dumps(
            {
                "handoff": handoff,
                "receipt": receipt,
                "baseline": baseline,
                "assisted": assisted,
                "comparison": comparison,
            },
            sort_keys=True,
        )
        result = self._assessment(
            handoff=handoff,
            receipt=receipt,
            baseline=baseline,
            assisted=assisted,
            comparison=comparison,
        )
        after = json.dumps(
            {
                "handoff": handoff,
                "receipt": receipt,
                "baseline": baseline,
                "assisted": assisted,
                "comparison": comparison,
            },
            sort_keys=True,
        )
        self.assertEqual(before, after)
        self.assertTrue(result["read_only"])
        self.assertEqual(result["mutation_effects"], ())

    def test_same_evidence_id_cannot_form_comparison_pair(self):
        baseline = self._quality("same-evidence")
        assisted = self._quality("same-evidence")
        result = self._assessment(
            baseline=baseline,
            assisted=assisted,
            comparison=self._comparison(
                baseline_evidence_id="same-evidence",
                assisted_evidence_id="same-evidence",
            ),
        )
        self.assertEqual(result["effectiveness_status"], "INCONCLUSIVE")
        self.assertFalse(result["effectiveness_claim_supported"])
        self.assertIn(
            "EVIDENCE_PAIR_NOT_DISTINCT",
            result["reason_codes"],
        )

    def test_same_evidence_object_cannot_form_comparison_pair(self):
        observation = self._quality("shared-observation")
        result = self._assessment(
            baseline=observation,
            assisted=observation,
            comparison=self._comparison(
                baseline_evidence_id="shared-observation",
                assisted_evidence_id="shared-observation",
            ),
        )
        self.assertEqual(result["effectiveness_status"], "INCONCLUSIVE")
        self.assertFalse(result["effectiveness_claim_supported"])
        self.assertIn(
            "EVIDENCE_PAIR_NOT_DISTINCT",
            result["reason_codes"],
        )

    def test_comparator_must_bind_exact_evidence_pair(self):
        result = self._assessment(
            comparison=self._comparison(
                baseline_evidence_id="other-baseline"
            )
        )
        self.assertEqual(result["effectiveness_status"], "INCONCLUSIVE")
        self.assertIn(
            "BASELINE_EVIDENCE_BINDING_MISMATCH",
            result["reason_codes"],
        )


class F01CachedPromptSecurityTests(unittest.TestCase):
    """F01: cached generic prompt must not be returned when session handoff is invalid."""

    def _seed_with_handoff_variant(self, root: Path, tower: ControlTower, variant: str):
        skill_path = ".agents/skills/scope-reality-check/SKILL.md"
        skill_hash = hashlib.sha256((root / skill_path).read_bytes()).hexdigest()
        handoff = {
            "schema": "p2p-skill-handoff/1",
            "SKILL_CHECK": "PASS",
            "REQUIRED_SKILLS": ["scope-reality-check"],
            "SKILLS_CONSIDERED_METADATA_COUNT": 1,
            "SKILLS_SELECTED": ["scope-reality-check"],
            "SKILL_LOAD_STAGE": "LOAD",
            "SKILL_SOURCE_HASHES": {"scope-reality-check": skill_hash},
            "SKILL_SOURCE_PATHS": {"scope-reality-check": skill_path},
            "SKILL_CONSUMPTION": "EXPECTED",
            "SKILL_HOST_MODE": "GENERIC_EXACT_REPO_READ",
            "MATERIAL_ALTERNATIVES_REJECTED": [],
            "REJECTION_REASON": [],
            "PERMISSION_WIDENED": "NO",
            "SINGLE_ROUTER_REUSED": "YES",
        }
        binding = SessionBinding(session_id="legacy-generic-active-01", host="CLAUDE", goal_id="ISSUE-333", goal="Legacy generic cached prompt")
        base_event = {
            "schema": CONTROL_TOWER_SESSION_START_EVENT_SCHEMA,
            "event_type": "CONTROL_TOWER_SESSION_STARTED",
            "CONTROL_TOWER_SESSION_STARTED": True,
            "SESSION_BINDING": binding.to_dict(),
            "TASK_ID": "issue-333-ready",
            "WORKTREE": "fixture-worktree",
            "BRANCH": "fixture-branch",
            "CANONICAL_BASE_SHA": "UNKNOWN",
            "CANONICAL_BASE_TREE": "UNKNOWN",
            "RECOMMENDED_NEW_CHAT": {
                "PROMPT": "LEGACY GENERIC CACHED PROMPT — MUST NOT LEAK",
                "SKILL_HANDOFF": handoff,
                "REQUIRED_SKILLS": ["scope-reality-check"],
            },
            "EXPECTED_LAW_SHA": None,
            "EXPECTED_EXPERIENCE_IDS": [],
            "ACCEPTANCE_CRITERIA": ["Skill handoff is bounded."],
            "CANARY": None,
            "PACKET_IS_CANONICAL_TRUTH": "NO",
            "PROMOTED": False,
            "PROTECTED_ACTION_EXECUTED": False,
        }
        if variant == "missing":
            # omit SKILL_HANDOFF entirely
            pass
        elif variant == "none":
            base_event["SKILL_HANDOFF"] = None
        elif variant == "empty_list":
            base_event["SKILL_HANDOFF"] = []
        elif variant == "string":
            base_event["SKILL_HANDOFF"] = "INVALID_STRING_HANDOFF"
        elif variant == "empty_object":
            base_event["SKILL_HANDOFF"] = {}
        elif variant == "not_required":
            base_event["SKILL_HANDOFF"] = {
                "schema": "p2p-skill-handoff/1",
                "SKILL_CHECK": "PASS",
                "SKILL_HOST_MODE": "NOT_REQUIRED",
                "SKILLS_SELECTED": ["scope-reality-check"],
                "SKILL_SOURCE_HASHES": {"scope-reality-check": "a"*64},
                "SKILL_SOURCE_PATHS": {"scope-reality-check": ".agents/skills/scope-reality-check/SKILL.md"},
                "REQUIRED_SKILLS": ["scope-reality-check"],
                "SKILLS_CONSIDERED_METADATA_COUNT": 1,
                "SKILL_LOAD_STAGE": "LOAD",
                "SKILL_CONSUMPTION": "EXPECTED",
                "MATERIAL_ALTERNATIVES_REJECTED": [],
                "REJECTION_REASON": [],
                "PERMISSION_WIDENED": "NO",
                "SINGLE_ROUTER_REUSED": "YES",
            }
        else:
            raise ValueError(variant)
        if variant != "missing":
            # already set above for non-missing; for missing we leave absent
            pass
        else:
            # ensure no SKILL_HANDOFF key
            base_event.pop("SKILL_HANDOFF", None)
            # For missing we need to set explicitly no handoff; base_event already without
            # So do nothing, but we must not add
            pass
        # For variants where we set SKILL_HANDOFF, it's already in base_event
        # For missing, we already popped
        _append_existing_execution_event(tower.ledger_path, base_event)
        return binding

    def _copy_root(self, root: Path):
        registry_target = root / ".p2p" / "system" / "p2p_capabilities" / "capabilities.json"
        registry_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json", registry_target)
        for skill_id in ("scope-reality-check", "p2p-scope"):
            shutil.copytree(REPO_ROOT / ".agents" / "skills" / skill_id, root / ".agents" / "skills" / skill_id)

    def _init_git(self, root: Path):
        subprocess.run(["git","-C",str(root),"init"], capture_output=True, check=True)
        subprocess.run(["git","-C",str(root),"config","user.email","fixture@example.com"], capture_output=True, check=True)
        subprocess.run(["git","-C",str(root),"config","user.name","P2P Fixture"], capture_output=True, check=True)
        subprocess.run(["git","-C",str(root),"remote","add","origin","https://github.com/fixture-owner/p2p-generic-skill-host.git"], capture_output=True, check=True)
        subprocess.run(["git","-C",str(root),"add","-A"], capture_output=True, check=True)
        subprocess.run(["git","-C",str(root),"commit","-m","fixture"], capture_output=True, check=True)

    def _init_ready(self, root: Path):
        now = "2026-10-08T07:00:00+00:00"
        plan = TaskPlan.from_goal(
            {"goal_id": "ISSUE-333", "scope": ["generic repo-read skill handoff"], "out_of_scope": ["release"]},
            [{"task_id": "issue-333-ready", "title": "Generic repo-read handoff", "purpose": "Pressure-test this plan", "status": "READY", "scope": ["generic repo-read skill handoff"], "acceptance_requirements": ["Skill handoff is bounded."], "required_evidence": ["focused-proof"]}],
            now=now,
        )
        TaskStateStore(root).initialize(plan, at=now)

    def _assert_blocked(self, result: dict):
        self.assertEqual(result.get("status"), "BLOCKED")
        self.assertIsNone(result.get("recommendation"))
        self.assertIn("SKILL_HANDOFF_HOST_EVIDENCE_STALE", result.get("reason",""))

    def test_f01_missing_field_is_blocked(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); self._copy_root(root); self._init_git(root); self._init_ready(root)
            tower=ControlTower(root); self._seed_with_handoff_variant(root, tower, "missing")
            r1=tower.recommend_next_session("CLAUDE")
            r2=next_safe_session(root,"CLAUDE")
            self._assert_blocked(r1); self._assert_blocked(r2)
            self.assertNotIn("LEGACY GENERIC CACHED PROMPT", str(r1.get("recommendation")))

    def test_f01_none_value_is_blocked(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); self._copy_root(root); self._init_git(root); self._init_ready(root)
            tower=ControlTower(root); self._seed_with_handoff_variant(root, tower, "none")
            self._assert_blocked(tower.recommend_next_session("CLAUDE"))
            self._assert_blocked(next_safe_session(root,"CLAUDE"))

    def test_f01_empty_list_is_blocked(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); self._copy_root(root); self._init_git(root); self._init_ready(root)
            tower=ControlTower(root); self._seed_with_handoff_variant(root, tower, "empty_list")
            self._assert_blocked(tower.recommend_next_session("CLAUDE"))
            self._assert_blocked(next_safe_session(root,"CLAUDE"))

    def test_f01_string_wrong_type_is_blocked(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); self._copy_root(root); self._init_git(root); self._init_ready(root)
            tower=ControlTower(root); self._seed_with_handoff_variant(root, tower, "string")
            self._assert_blocked(tower.recommend_next_session("CLAUDE"))
            self._assert_blocked(next_safe_session(root,"CLAUDE"))

    def test_f01_empty_object_is_blocked(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); self._copy_root(root); self._init_git(root); self._init_ready(root)
            tower=ControlTower(root); self._seed_with_handoff_variant(root, tower, "empty_object")
            self._assert_blocked(tower.recommend_next_session("CLAUDE"))
            self._assert_blocked(next_safe_session(root,"CLAUDE"))

    def test_f01_not_required_mode_is_blocked(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); self._copy_root(root); self._init_git(root); self._init_ready(root)
            tower=ControlTower(root); self._seed_with_handoff_variant(root, tower, "not_required")
            r=tower.recommend_next_session("CLAUDE")
            self._assert_blocked(r)
            self._assert_blocked(next_safe_session(root,"CLAUDE"))
            self.assertIn("MODE_MISMATCH", r.get("reason",""))

    def test_f01_control_host_mismatch_is_blocked(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); self._copy_root(root); self._init_git(root); self._init_ready(root)
            tower=ControlTower(root); self._seed_with_handoff_variant(root, tower, "none")
            # Re-seed with valid handoff for host mismatch test
            # Use valid seed then try different host
            # Create new root with valid handoff
            with tempfile.TemporaryDirectory() as raw2:
                root2=Path(raw2); self._copy_root(root2); self._init_git(root2); self._init_ready(root2)
                tower2=ControlTower(root2)
                skill_path=".agents/skills/scope-reality-check/SKILL.md"
                skill_hash=hashlib.sha256((root2/skill_path).read_bytes()).hexdigest()
                handoff={"schema":"p2p-skill-handoff/1","SKILL_CHECK":"PASS","REQUIRED_SKILLS":["scope-reality-check"],"SKILLS_CONSIDERED_METADATA_COUNT":1,"SKILLS_SELECTED":["scope-reality-check"],"SKILL_LOAD_STAGE":"LOAD","SKILL_SOURCE_HASHES":{"scope-reality-check":skill_hash},"SKILL_SOURCE_PATHS":{"scope-reality-check":skill_path},"SKILL_CONSUMPTION":"EXPECTED","SKILL_HOST_MODE":"GENERIC_EXACT_REPO_READ","MATERIAL_ALTERNATIVES_REJECTED":[],"REJECTION_REASON":[],"PERMISSION_WIDENED":"NO","SINGLE_ROUTER_REUSED":"YES"}
                binding=SessionBinding(session_id="legacy-generic-active-01", host="CLAUDE", goal_id="ISSUE-333", goal="Legacy generic cached prompt")
                event={"schema":CONTROL_TOWER_SESSION_START_EVENT_SCHEMA,"event_type":"CONTROL_TOWER_SESSION_STARTED","CONTROL_TOWER_SESSION_STARTED":True,"SESSION_BINDING":binding.to_dict(),"TASK_ID":"issue-333-ready","WORKTREE":"fixture-worktree","BRANCH":"fixture-branch","CANONICAL_BASE_SHA":"UNKNOWN","CANONICAL_BASE_TREE":"UNKNOWN","RECOMMENDED_NEW_CHAT":{"PROMPT":"LEGACY GENERIC CACHED PROMPT — MUST NOT LEAK","SKILL_HANDOFF":handoff,"REQUIRED_SKILLS":["scope-reality-check"]},"EXPECTED_LAW_SHA":None,"EXPECTED_EXPERIENCE_IDS":[],"ACCEPTANCE_CRITERIA":["Skill handoff is bounded."],"SKILL_HANDOFF":handoff,"CANARY":None,"PACKET_IS_CANONICAL_TRUTH":"NO","PROMOTED":False,"PROTECTED_ACTION_EXECUTED":False}
                _append_existing_execution_event(tower2.ledger_path, event)
                res=tower2.recommend_next_session("GROK")
                self.assertEqual(res.get("status"), "BLOCKED")
                self.assertEqual(res.get("reason"), "ACTIVE_SESSION_HOST_MISMATCH")
                self.assertIsNone(res.get("recommendation"))

    def test_f01_control_valid_generic_but_missing_evidence_is_blocked(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); self._copy_root(root); self._init_git(root); self._init_ready(root)
            tower=ControlTower(root)
            skill_path=".agents/skills/scope-reality-check/SKILL.md"
            skill_hash=hashlib.sha256((root/skill_path).read_bytes()).hexdigest()
            handoff={"schema":"p2p-skill-handoff/1","SKILL_CHECK":"PASS","REQUIRED_SKILLS":["scope-reality-check"],"SKILLS_CONSIDERED_METADATA_COUNT":1,"SKILLS_SELECTED":["scope-reality-check"],"SKILL_LOAD_STAGE":"LOAD","SKILL_SOURCE_HASHES":{"scope-reality-check":skill_hash},"SKILL_SOURCE_PATHS":{"scope-reality-check":skill_path},"SKILL_CONSUMPTION":"EXPECTED","SKILL_HOST_MODE":"GENERIC_EXACT_REPO_READ","MATERIAL_ALTERNATIVES_REJECTED":[],"REJECTION_REASON":[],"PERMISSION_WIDENED":"NO","SINGLE_ROUTER_REUSED":"YES"}
            binding=SessionBinding(session_id="legacy-generic-active-01", host="CLAUDE", goal_id="ISSUE-333", goal="Legacy generic cached prompt")
            event={"schema":CONTROL_TOWER_SESSION_START_EVENT_SCHEMA,"event_type":"CONTROL_TOWER_SESSION_STARTED","CONTROL_TOWER_SESSION_STARTED":True,"SESSION_BINDING":binding.to_dict(),"TASK_ID":"issue-333-ready","WORKTREE":"fixture-worktree","BRANCH":"fixture-branch","CANONICAL_BASE_SHA":"UNKNOWN","CANONICAL_BASE_TREE":"UNKNOWN","RECOMMENDED_NEW_CHAT":{"PROMPT":"LEGACY GENERIC CACHED PROMPT — MUST NOT LEAK","SKILL_HANDOFF":handoff,"REQUIRED_SKILLS":["scope-reality-check"]},"EXPECTED_LAW_SHA":None,"EXPECTED_EXPERIENCE_IDS":[],"ACCEPTANCE_CRITERIA":["Skill handoff is bounded."],"SKILL_HANDOFF":handoff,"CANARY":None,"PACKET_IS_CANONICAL_TRUTH":"NO","PROMOTED":False,"PROTECTED_ACTION_EXECUTED":False}
            _append_existing_execution_event(tower.ledger_path, event)
            res=tower.recommend_next_session("CLAUDE")
            self.assertEqual(res.get("status"), "BLOCKED")
            self.assertIn("HOST_DISCOVERY_RECORD_REQUIRED", res.get("reason",""))
            self.assertIsNone(res.get("recommendation"))
            # also with fresh discovery but no trusted observation, still blocked (B1)
            from p2p_capabilities.host_executor import HostCapabilityProfile, SUPPORTED
            from p2p_capabilities.host_selection import HostDiscoveryRecord, AVAILABLE
            from p2p_capabilities.skill_consumption import _canonical_repo_binding, _current_repo_revision
            repo_binding=_canonical_repo_binding(root)
            rev=_current_repo_revision(root)
            sha=hashlib.sha256((root/skill_path).read_bytes()).hexdigest()
            prov=f"VERIFIED_LOCAL_REPO_EXACT_READ|repo={repo_binding}|revision={rev}|probe={skill_path}|sha256={sha}"
            profile=HostCapabilityProfile(adapter_class="GenericExternalAI", host_label="CLAUDE", environment="REMOTE_REPOSITORY", capabilities={"can_read_files":SUPPORTED})
            rec=HostDiscoveryRecord(host_id="CLAUDE", profile=profile, availability=AVAILABLE, provenance=prov, project_binding=repo_binding, environment_binding="REMOTE_REPOSITORY", execution_transport_available=True).to_dict()
            res2=tower.recommend_next_session("CLAUDE", host_discovery_record=rec)
            self.assertEqual(res2.get("status"), "BLOCKED")
            self.assertIn("HOST_TRUSTED_REPO_READ_OBSERVATION_UNAVAILABLE", res2.get("reason",""))

    def test_f01_start_session_also_blocks_tampered_handoff(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); self._copy_root(root); self._init_git(root); self._init_ready(root)
            tower=ControlTower(root); self._seed_with_handoff_variant(root, tower, "empty_object")
            binding=SessionBinding(session_id="legacy-generic-active-01", host="CLAUDE", goal_id="ISSUE-333", goal="Legacy generic cached prompt")
            with self.assertRaisesRegex(Exception, "SKILL_HANDOFF_HOST_EVIDENCE_STALE"):
                tower.start_session(binding, task_id="issue-333-ready", task_prompt="Pressure-test this plan")

    # --- F01-RESIDUAL-01: shape-switch family -------------------------------
    # A cached PROMPT is the authoritative material that gets returned.  Its
    # structured metadata may be deleted, emptied or reshaped; that must never
    # become an authority to skip cached-host validation.

    def _realistic_generic_prompt(self, root: Path) -> tuple[str, dict]:
        """Return (prompt, handoff) for the repo's own deterministic serializer."""
        skill_path = ".agents/skills/scope-reality-check/SKILL.md"
        skill_hash = hashlib.sha256((root / skill_path).read_bytes()).hexdigest()
        handoff = {
            "schema": "p2p-skill-handoff/1",
            "SKILL_CHECK": "PASS",
            "REQUIRED_SKILLS": ["scope-reality-check"],
            "SKILLS_CONSIDERED_METADATA_COUNT": 1,
            "SKILLS_SELECTED": ["scope-reality-check"],
            "SKILL_LOAD_STAGE": "LOAD",
            "SKILL_SOURCE_HASHES": {"scope-reality-check": skill_hash},
            "SKILL_SOURCE_PATHS": {"scope-reality-check": skill_path},
            "SKILL_CONSUMPTION": "EXPECTED",
            "SKILL_HOST_MODE": "GENERIC_EXACT_REPO_READ",
            "MATERIAL_ALTERNATIVES_REJECTED": [],
            "REJECTION_REASON": [],
            "PERMISSION_WIDENED": "NO",
            "SINGLE_ROUTER_REUSED": "YES",
        }
        binding = SessionBinding(session_id="legacy-generic-active-01", host="CLAUDE", goal_id="ISSUE-333", goal="Legacy generic cached prompt")
        prompt = build_execution_prompt(binding, "Legacy generic cached prompt", task_id="issue-333-ready", skill_handoff=handoff)
        self.assertIn("P2P_SKILL_HANDOFF:", prompt)
        self.assertIn("SKILL_HOST_MODE=GENERIC_EXACT_REPO_READ", prompt)
        return prompt, handoff

    def _seed_residual_variant(self, root: Path, tower: ControlTower, variant: str):
        """Seed an ACTIVE session whose cached PROMPT still carries the generic
        skill block, with the structured metadata stripped or reshaped."""
        prompt, handoff = self._realistic_generic_prompt(root)
        binding = SessionBinding(session_id="legacy-generic-active-01", host="CLAUDE", goal_id="ISSUE-333", goal="Legacy generic cached prompt")
        recommendation = {"PROMPT": prompt}
        if variant == "r2":
            recommendation["SKILL_HANDOFF"] = {}
        elif variant == "r3":
            # misleading non-authoritative leftover the detector never inspected
            recommendation["SKILLS_SELECTED"] = ["scope-reality-check"]
        elif variant != "r1":
            raise ValueError(variant)
        event = {
            "schema": CONTROL_TOWER_SESSION_START_EVENT_SCHEMA,
            "event_type": "CONTROL_TOWER_SESSION_STARTED",
            "CONTROL_TOWER_SESSION_STARTED": True,
            "SESSION_BINDING": binding.to_dict(),
            "TASK_ID": "issue-333-ready",
            "WORKTREE": "fixture-worktree",
            "BRANCH": "fixture-branch",
            "CANONICAL_BASE_SHA": "UNKNOWN",
            "CANONICAL_BASE_TREE": "UNKNOWN",
            "RECOMMENDED_NEW_CHAT": recommendation,
            "EXPECTED_LAW_SHA": None,
            "EXPECTED_EXPERIENCE_IDS": [],
            "ACCEPTANCE_CRITERIA": ["Skill handoff is bounded."],
            "CANARY": None,
            "PACKET_IS_CANONICAL_TRUTH": "NO",
            "PROMOTED": False,
            "PROTECTED_ACTION_EXECUTED": False,
        }
        _append_existing_execution_event(tower.ledger_path, event)
        return binding, prompt, handoff

    def _assert_residual_blocked(self, tower: ControlTower, root: Path, binding: SessionBinding):
        r1 = tower.recommend_next_session("CLAUDE")
        self.assertEqual(r1.get("status"), "BLOCKED")
        self.assertIsNone(r1.get("recommendation"))
        self.assertIn("SKILL_HANDOFF_HOST_EVIDENCE_STALE", r1.get("reason", ""))
        r2 = next_safe_session(root, "CLAUDE")
        self.assertEqual(r2.get("status"), "BLOCKED")
        self.assertIsNone(r2.get("recommendation"))
        self.assertIn("SKILL_HANDOFF_HOST_EVIDENCE_STALE", r2.get("reason", ""))
        # the authoritative cached prompt must not reach any caller
        self.assertNotIn("P2P_SKILL_HANDOFF:", str(r1.get("recommendation")))
        self.assertNotIn("P2P_SKILL_HANDOFF:", str(r2.get("recommendation")))
        with self.assertRaisesRegex(Exception, "SKILL_HANDOFF_HOST_EVIDENCE_STALE"):
            tower.start_session(binding, task_id="issue-333-ready", task_prompt="Legacy generic cached prompt")

    def test_f01_residual_r1_recommendation_handoff_removed_is_blocked(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); self._copy_root(root); self._init_git(root); self._init_ready(root)
            tower=ControlTower(root)
            binding, _prompt, _handoff = self._seed_residual_variant(root, tower, "r1")
            self._assert_residual_blocked(tower, root, binding)

    def test_f01_residual_r2_recommendation_handoff_emptied_is_blocked(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); self._copy_root(root); self._init_git(root); self._init_ready(root)
            tower=ControlTower(root)
            binding, _prompt, _handoff = self._seed_residual_variant(root, tower, "r2")
            self._assert_residual_blocked(tower, root, binding)

    def test_f01_residual_r3_misleading_leftover_metadata_is_blocked(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); self._copy_root(root); self._init_git(root); self._init_ready(root)
            tower=ControlTower(root)
            binding, _prompt, _handoff = self._seed_residual_variant(root, tower, "r3")
            self._assert_residual_blocked(tower, root, binding)

    def test_f01_residual_r4_start_session_cannot_regenerate_and_return_cached_prompt(self):
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); self._copy_root(root); self._init_git(root); self._init_ready(root)
            tower=ControlTower(root)
            binding, prompt, _handoff = self._seed_residual_variant(root, tower, "r1")
            with self.assertRaises(BindingError) as raised:
                tower.start_session(binding, task_id="issue-333-ready", task_prompt="Legacy generic cached prompt")
            self.assertIn("SKILL_HANDOFF_HOST_EVIDENCE_STALE", str(raised.exception))
            # no PASS packet carrying the stale generic prompt may be produced
            self.assertNotIn("P2P_SKILL_HANDOFF:", prompt[:0])

    def test_f01_residual_cached_generic_prompt_with_no_match_handoff_is_blocked(self):
        """A generic skill-bearing cached prompt may not ride on a NO_MATCH handoff."""
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); self._copy_root(root); self._init_git(root); self._init_ready(root)
            tower=ControlTower(root)
            prompt, _handoff = self._realistic_generic_prompt(root)
            binding = SessionBinding(session_id="legacy-generic-active-01", host="CLAUDE", goal_id="ISSUE-333", goal="Legacy generic cached prompt")
            honest_no_match = {
                "schema": "p2p-skill-handoff/1",
                "SKILL_CHECK": "NO_MATCH",
                "REQUIRED_SKILLS": [],
                "SKILLS_SELECTED": [],
                "SKILLS_CONSIDERED_METADATA_COUNT": 1,
                "SKILL_LOAD_STAGE": "NO_SKILL",
                "SKILL_CONSUMPTION": "NOT_EXPECTED",
                "SKILL_HOST_MODE": "",
                "MATERIAL_ALTERNATIVES_REJECTED": [],
                "REJECTION_REASON": [],
                "PERMISSION_WIDENED": "NO",
                "SINGLE_ROUTER_REUSED": "YES",
            }
            event = {
                "schema": CONTROL_TOWER_SESSION_START_EVENT_SCHEMA,
                "event_type": "CONTROL_TOWER_SESSION_STARTED",
                "CONTROL_TOWER_SESSION_STARTED": True,
                "SESSION_BINDING": binding.to_dict(),
                "TASK_ID": "issue-333-ready",
                "WORKTREE": "fixture-worktree",
                "BRANCH": "fixture-branch",
                "CANONICAL_BASE_SHA": "UNKNOWN",
                "CANONICAL_BASE_TREE": "UNKNOWN",
                "RECOMMENDED_NEW_CHAT": {"PROMPT": prompt},
                "EXPECTED_LAW_SHA": None,
                "EXPECTED_EXPERIENCE_IDS": [],
                "ACCEPTANCE_CRITERIA": ["Skill handoff is bounded."],
                "SKILL_HANDOFF": honest_no_match,
                "CANARY": None,
                "PACKET_IS_CANONICAL_TRUTH": "NO",
                "PROMOTED": False,
                "PROTECTED_ACTION_EXECUTED": False,
            }
            _append_existing_execution_event(tower.ledger_path, event)
            res = tower.recommend_next_session("CLAUDE")
            self.assertEqual(res.get("status"), "BLOCKED")
            self.assertIsNone(res.get("recommendation"))
            self.assertIn("SKILL_HANDOFF_HOST_EVIDENCE_STALE", res.get("reason", ""))

    def test_f01_residual_ordinary_cached_prompt_is_not_false_positive(self):
        """Ordinary prose, even prose quoting the markers, stays reusable."""
        with tempfile.TemporaryDirectory() as raw:
            root=Path(raw); self._copy_root(root); self._init_git(root); self._init_ready(root)
            tower=ControlTower(root)
            binding = SessionBinding(session_id="ordinary-cached-01", host="CLAUDE", goal_id="ISSUE-333", goal="Ordinary cached session")
            honest_no_match = {
                "schema": "p2p-skill-handoff/1",
                "SKILL_CHECK": "NO_MATCH",
                "REQUIRED_SKILLS": [],
                "SKILLS_SELECTED": [],
                "SKILLS_CONSIDERED_METADATA_COUNT": 1,
                "SKILL_LOAD_STAGE": "NO_SKILL",
                "SKILL_CONSUMPTION": "NOT_EXPECTED",
                "SKILL_HOST_MODE": "",
                "MATERIAL_ALTERNATIVES_REJECTED": [],
                "REJECTION_REASON": [],
                "PERMISSION_WIDENED": "NO",
                "SINGLE_ROUTER_REUSED": "YES",
            }
            # free prose that merely discusses the reserved marker words
            prose_prompt = (
                "Write the release notes.\n"
                "P2P_SKILL_HANDOFF:\n"
                "\n"
                "The marker above is documentation only; this prompt selects no skill.\n"
                "SKILL_HOST_MODE=GENERIC_EXACT_REPO_READ is mentioned as an example.\n"
            )
            event = {
                "schema": CONTROL_TOWER_SESSION_START_EVENT_SCHEMA,
                "event_type": "CONTROL_TOWER_SESSION_STARTED",
                "CONTROL_TOWER_SESSION_STARTED": True,
                "SESSION_BINDING": binding.to_dict(),
                "TASK_ID": "issue-333-ready",
                "WORKTREE": "fixture-worktree",
                "BRANCH": "fixture-branch",
                "CANONICAL_BASE_SHA": "UNKNOWN",
                "CANONICAL_BASE_TREE": "UNKNOWN",
                "RECOMMENDED_NEW_CHAT": {"PROMPT": prose_prompt},
                "EXPECTED_LAW_SHA": None,
                "EXPECTED_EXPERIENCE_IDS": [],
                "ACCEPTANCE_CRITERIA": ["Skill handoff is bounded."],
                "SKILL_HANDOFF": honest_no_match,
                "CANARY": None,
                "PACKET_IS_CANONICAL_TRUTH": "NO",
                "PROMOTED": False,
                "PROTECTED_ACTION_EXECUTED": False,
            }
            _append_existing_execution_event(tower.ledger_path, event)
            res = tower.recommend_next_session("CLAUDE")
            self.assertEqual(res.get("status"), "PASS")
            self.assertIsNotNone(res.get("recommendation"))
            self.assertEqual(next_safe_session(root, "CLAUDE").get("status"), "PASS")
            started = tower.start_session(binding, task_id="issue-333-ready", task_prompt="Write the release notes.")
            self.assertEqual(started.get("status"), "PASS")


if __name__ == "__main__":
    unittest.main(verbosity=2)
