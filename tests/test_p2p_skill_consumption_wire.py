"""Focused tests for Issue #298 P2P Skill Consumption Wire."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities.capability_intelligence import (  # noqa: E402
    compute_execution_requirements,
)
from p2p_capabilities.control_tower_handoff import (  # noqa: E402
    BindingError,
    ControlTower,
    ControlTowerReturnPacket,
    ControlTowerState,
    SessionBinding,
    build_execution_prompt,
)
from p2p_capabilities.p2p_skill_eligibility import skill_eligibility_set  # noqa: E402
from p2p_capabilities.skill_consumption import (  # noqa: E402
    RECEIPT_SCHEMA,
    load_selected_skills,
    prepare_skill_handoff,
    select_skills_for_task,
    skill_handoff_prompt_lines,
    validate_consumption_receipt,
)


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

    def test_explicit_repo_native_skill_outside_capability_registry_loads(self):
        registry = json.loads(
            (SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json")
            .read_text(encoding="utf-8")
        )
        ids = {
            item["CAPABILITY_ID"] for item in registry["capabilities"]
        }
        self.assertNotIn("p2p-scope", ids)
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
            len(handoff["SKILL_SOURCE_HASHES"]["p2p-scope"]),
            64,
        )

    def test_repo_native_unadmitted_skill_is_never_implicit_auto_route(self):
        selection = select_skills_for_task(
            REPO_ROOT,
            "Organize this substantial multi-step work with checkpoints",
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

    def test_required_repo_native_unadmitted_skill_is_supported(self):
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
