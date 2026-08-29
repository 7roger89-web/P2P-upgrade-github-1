from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
REGISTRY_PATH = SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json"
PROVENANCE_PATH = REPO_ROOT / ".p2p" / "vendor" / "provenance" / "p2p-game-toolchain-02a.json"
EXTERNAL_MANIFEST_PATH = REPO_ROOT / "manifest" / "external-sources.json"
MENGTO_ROOT = REPO_ROOT / ".p2p" / "vendor" / "skill" / "mengto-gameplay-spine-4c716b5"
MAJID_ROOT = REPO_ROOT / ".p2p" / "vendor" / "skill" / "majid-threejs-qa-release-7221c1f"

CURRENT_MAIN_SHA = "29291dae1f3101f3ace9546fb2b27e3d514bca61"
CURRENT_MAIN_TREE = "e5e01a1a2d4ddad207aaab2e25752b571bd5fb9e"
MENGTO_COMMIT = "4c716b516b6b0143f3037631306b3730d2832344"
MENGTO_TREE = "faadfe0963132fdecee0ed55e79c4ed43ebae7e1"
MENGTO_SNAPSHOT = "1d395a2c57b57b2572f3d851bf9105038eee26b5ab2d68f1e1eb7b7aa62382fb"
MAJID_COMMIT = "7221c1f4a6d2ae189a4d85d058d24f3228499d46"
MAJID_TREE = "9add48693c42ab51915576e3b03ede9ad2f61480"
MAJID_SNAPSHOT = "94b65aa700ec7a1ad4f8734891902312a6112f0a7878bfa303c2478079d13db4"
IMG2THREEJS_COMMIT = "dede5909be4e494b228c801a55dda47439143932"
IMG2THREEJS_TREE = "25bcd4e1f1a487b9a61d69ade257342a3da767e3"
IMG2THREEJS_PREVIOUS_COMMIT = "441af85a96523569511154b6321859b79f3592f5"
IMG2THREEJS_PREVIOUS_TREE = "02e909630089bc21162f4ed3340b321b955291d8"

MENGTO_IDS = (
    "game.mengto.build_isometric_arpg",
    "game.mengto.camera_controls",
    "game.mengto.mobile_controls",
    "game.mengto.action_combat",
    "game.mengto.enemy_systems",
    "game.mengto.enemy_ai",
    "game.mengto.encounters",
    "game.mengto.hybrid_assets",
    "game.mengto.rigged_assets",
    "game.mengto.performance",
)
MAJID_ID = "game.majid.threejs_qa_release"
NEW_IDS = (*MENGTO_IDS, MAJID_ID)

sys.path.insert(0, str(SYSTEM_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from p2p_capabilities import CAPABILITY_CLASSES, CANONICAL_IDENTITIES, load_registry  # noqa: E402
from p2p_capabilities import vendor_skill  # noqa: E402
from p2p_capabilities.host_projection import READY as HOST_READY  # noqa: E402
from p2p_capabilities.host_projection import project_host_skill  # noqa: E402
from p2p_capabilities.vendor_skill import (  # noqa: E402
    discover_vendor_skills,
    load_vendor_skill,
    optional_dependency_status,
    snapshot_tree_sha256,
)
import p2p_workflow  # noqa: E402


class P2PGameToolchain02ATests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry_raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        cls.registry = load_registry(REGISTRY_PATH)
        cls.manifests = {item.capability_id: item for item in cls.registry["parsed"]}
        cls.provenance = json.loads(PROVENANCE_PATH.read_text(encoding="utf-8"))
        cls.external_manifest = json.loads(EXTERNAL_MANIFEST_PATH.read_text(encoding="utf-8"))

    @staticmethod
    def _git(*args: str) -> str:
        result = subprocess.run(
            ["git", *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
        return result.stdout.strip()

    @classmethod
    def _route(cls, request: str) -> dict[str, object]:
        return discover_vendor_skills(
            request,
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
        )

    @classmethod
    def _requirement(cls, request: str) -> dict[str, object]:
        return p2p_workflow.derive_orchestration_requirement(
            request,
            {"project_root": str(REPO_ROOT)},
            package_hint=str(REPO_ROOT),
        )

    @classmethod
    def _selection(cls, request: str, requirement: dict[str, object]) -> dict[str, object]:
        return p2p_workflow.select_agents(
            request,
            {"project_root": str(REPO_ROOT)},
            {},
            requirement,
        )

    def test_01_current_main_identity_is_still_the_candidate_ancestor(self) -> None:
        self.assertEqual(self._git("rev-parse", f"{CURRENT_MAIN_SHA}^{{tree}}"), CURRENT_MAIN_TREE)
        self.assertEqual(self._git("merge-base", "HEAD", CURRENT_MAIN_SHA), CURRENT_MAIN_SHA)

    def test_02_registry_preserves_foundation_and_adds_only_selected_skills(self) -> None:
        self.assertEqual(self.registry["capability_count"], 40)
        self.assertTrue(self.registry["valid"])
        self.assertEqual(tuple(self.registry["capability_classes"]), CAPABILITY_CLASSES)
        self.assertEqual(tuple(self.registry["canonical_identities"]), CANONICAL_IDENTITIES)
        self.assertEqual(self.registry["canonical_denominator"], 8)
        self.assertTrue(set(item["TYPE"] for item in self.registry_raw["capabilities"]).issubset(set(CAPABILITY_CLASSES)))
        registry_ids = [item["CAPABILITY_ID"] for item in self.registry_raw["capabilities"]]
        self.assertTrue(all(capability_id in registry_ids for capability_id in NEW_IDS))

        img2threejs = self.manifests["img2threejs"]
        self.assertEqual(img2threejs.type, "SKILL")
        self.assertEqual(img2threejs.semantic_kind, "EXTERNAL_RUNTIME")
        self.assertEqual(img2threejs.status, "DISCOVERED")
        self.assertFalse(img2threejs.canonical_quorum_member)
        self.assertFalse(img2threejs.optional_specialist)
        self.assertIn("C18", img2threejs.requires)
        self.assertIn("C19", img2threejs.requires)
        self.assertIn("img2threejs:ready-for-explicit-adapter", self.manifests["game.mengto.hybrid_assets"].context_pointers)
        self.assertEqual(img2threejs.raw["UPSTREAM_PROVENANCE"]["upstream_commit"], IMG2THREEJS_COMMIT)
        self.assertEqual(img2threejs.raw["UPSTREAM_PROVENANCE"]["upstream_tree"], IMG2THREEJS_TREE)
        self.assertEqual(img2threejs.raw["UPSTREAM_PROVENANCE"]["license"]["kind"], "Apache-2.0")
        self.assertTrue(img2threejs.raw["UPSTREAM_PROVENANCE"]["execution"]["state_evidence_workspace_only"])
        self.assertFalse(img2threejs.raw["UPSTREAM_PROVENANCE"]["execution"]["shell"])

        for capability_id in NEW_IDS:
            manifest = self.manifests[capability_id]
            self.assertEqual(manifest.type, "SKILL")
            self.assertEqual(manifest.status, "DISCOVERED")
            self.assertFalse(manifest.canonical_quorum_member)
            self.assertFalse(manifest.optional_specialist)
            self.assertIn("C18", manifest.requires)
            self.assertIn("C19", manifest.requires)
            for pointer in (".p2p/system/p2p_uiux/router.py", "project-context", "project-pin"):
                self.assertIn(pointer, manifest.context_pointers)
            self.assertIn("existing-p2p-router", manifest.authority)
            self.assertIn("promote-without-owner-gate", manifest.prohibited_actions)
            self.assertEqual(manifest.raw["UPSTREAM_PROVENANCE"]["source_manifest"], ".p2p/vendor/provenance/p2p-game-toolchain-02a.json")

        style = self.manifests["visual.gpt_image_2_style_library"].raw
        self.assertEqual(style["UPSTREAM_PROVENANCE"]["upstream_commit"], "9a7b2e9c39f816d6c699c2a133e11b6d8bfdc464")
        self.assertEqual(style["UPSTREAM_PROVENANCE"]["upstream_tree"], "56b103dad637a95b9ec366eb7215459f28feb73e")
        self.assertEqual(style["UPSTREAM_PROVENANCE"]["rights_review"]["commercial_clearance"], "UNKNOWN")

    def test_03_exact_vendor_closure_and_hashes_are_preserved(self) -> None:
        expected_mengto = {"LICENSE"}
        for skill_name in (
            "build-isometric-arpg",
            "build-game-camera-controls",
            "build-mobile-threejs-games",
            "design-action-combat",
            "build-threejs-enemy-systems",
            "tune-enemy-ai",
            "design-game-encounters",
            "build-hybrid-game-assets",
            "build-rigged-game-assets",
            "optimize-threejs-games",
        ):
            prefix = f"agent-skills/game-development/{skill_name}"
            expected_mengto.update({f"{prefix}/SKILL.md", f"{prefix}/agents/openai.yaml"})
        expected_mengto.update(
            {
                "agent-skills/game-development/build-rigged-game-assets/references/requirements.md",
                "agent-skills/game-development/build-rigged-game-assets/references/catalog-and-testing.md",
                "agent-skills/game-development/build-rigged-game-assets/assets/character-asset-manifest.template.json",
                "agent-skills/game-development/build-rigged-game-assets/assets/monster-asset-manifest.template.json",
                "agent-skills/game-development/build-rigged-game-assets/scripts/validate_asset_manifest.py",
            }
        )
        expected_majid = {
            "LICENSE",
            "skills/threejs-qa-release/SKILL.md",
            "skills/threejs-qa-release/agents/openai.yaml",
            "skills/threejs-qa-release/references/qa-release-checklists.md",
            "skills/threejs-qa-release/references/checklists/visual-verification.md",
            "skills/threejs-qa-release/references/checklists/playtest-qa.md",
            "skills/threejs-qa-release/references/checklists/release.md",
            "skills/threejs-qa-release/references/visual-test-harness.md",
            "skills/threejs-qa-release/references/checklists/visual-test-harness.md",
            "skills/threejs-qa-release/references/playtest-bot.md",
            "skills/threejs-qa-release/references/checklists/bot-playtest.md",
            "skills/threejs-qa-release/references/prompt-templates.md",
            "skills/threejs-qa-release/scripts/inspect-threejs-canvas.mjs",
        }
        expected = {
            "mengto-gameplay-spine-4c716b5": (MENGTO_ROOT, expected_mengto, MENGTO_COMMIT, MENGTO_TREE, MENGTO_SNAPSHOT, "MIT"),
            "majid-threejs-qa-release-7221c1f": (MAJID_ROOT, expected_majid, MAJID_COMMIT, MAJID_TREE, MAJID_SNAPSHOT, "MIT"),
        }
        self.assertEqual({item["vendor_id"] for item in self.provenance["vendors"]}, set(expected))
        for vendor in self.provenance["vendors"]:
            root, expected_paths, commit, tree, snapshot, license_name = expected[vendor["vendor_id"]]
            self.assertEqual(vendor["upstream_commit"], commit)
            self.assertEqual(vendor["upstream_tree"], tree)
            self.assertEqual(vendor["snapshot_sha256"], snapshot)
            self.assertEqual(vendor["license"], license_name)
            files = vendor["files"]
            self.assertEqual({item["upstream_path"] for item in files}, expected_paths)
            self.assertEqual(len(files), len(expected_paths))
            self.assertTrue(root.is_dir())
            self.assertEqual(snapshot_tree_sha256(root), snapshot)
            for item in files:
                path = REPO_ROOT / Path(item["snapshot_path"])
                self.assertTrue(path.is_file(), item["snapshot_path"])
                self.assertEqual(vendor_skill._sha256_file(path), item["sha256"])
                self.assertEqual(item["modification_status"], "UNMODIFIED")
                self.assertEqual(item["status"], "VENDORED")
                self.assertEqual(item["license"], license_name)

        all_snapshot_paths = [item.relative_to(REPO_ROOT).as_posix() for item in MENGTO_ROOT.rglob("*") if item.is_file()]
        self.assertFalse(any("build-game-monster-system" in path for path in all_snapshot_paths))
        self.assertFalse(any("tripo" in path.lower() for path in all_snapshot_paths))

    def test_04_discovery_is_metadata_only_and_jit_is_selective(self) -> None:
        cases = {
            "Write a precise Arena Agent prompt to improve the Three.js camera.": ["game.mengto.camera_controls"],
            "Implement a local combat cooldown bug fix.": ["game.mengto.action_combat"],
            "Create a Three.js xianxia sword from an approved reference.": ["game.mengto.hybrid_assets", MAJID_ID],
            "Improve browser performance in the current Three.js scene.": ["game.mengto.performance"],
        }
        with mock.patch.object(vendor_skill, "_sha256_file", side_effect=AssertionError("discovery must not read vendor content")):
            for request, selected in cases.items():
                with self.subTest(request=request):
                    result = self._route(request)
                    self.assertEqual(result["selected"], selected)
                    self.assertEqual(result["route"]["selected"], selected)
                    self.assertTrue(result["route"]["single_router"])
                    self.assertFalse(result["content_loaded"])
                    self.assertTrue(all(not item["content_loaded"] for item in result["skills"]))

        loaded = load_vendor_skill(
            "game.mengto.hybrid_assets",
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
        )
        self.assertEqual(loaded["status"], "LOADED")
        self.assertEqual(loaded["loaded_paths"], ["agent-skills/game-development/build-hybrid-game-assets/SKILL.md"])
        self.assertTrue(loaded["content_loaded"])
        self.assertFalse(loaded["network_used"])
        self.assertFalse(loaded["permission_grant"])

    def test_05_prompt_composition_keeps_c18_direct_zero_worker_camera_route(self) -> None:
        request = "Write a precise Arena Agent prompt to improve the Three.js camera."
        requirement = self._requirement(request)
        selection = self._selection(request, requirement)
        route = self._route(request)
        self.assertEqual(requirement["profile"]["task_kind"], "PROMPT_COMPOSITION")
        self.assertEqual(requirement["worker_strategy"], "DIRECT")
        self.assertEqual(requirement["context_class"], "MINIMAL")
        self.assertEqual(requirement["reasoning_class"], "LOW")
        self.assertEqual(requirement["verification_class"], "DETERMINISTIC")
        self.assertEqual(selection["selected_agents"], [])
        self.assertEqual(selection["quorum_size"], 0)
        self.assertEqual(route["selected"], ["game.mengto.camera_controls"])
        self.assertFalse(any(token in repr(route["selected"]).lower() for token in ("combat", "enemy", "qa", "hybrid", "rigged", "performance", "img2threejs")))

    def test_06_combat_bug_fix_uses_focused_gameplay_capability_and_one_worker(self) -> None:
        request = "Implement a local combat cooldown bug fix."
        requirement = self._requirement(request)
        selection = self._selection(request, requirement)
        route = self._route(request)
        self.assertEqual(requirement["profile"]["task_kind"], "IMPLEMENTATION")
        self.assertEqual(requirement["worker_strategy"], "ONE_WORKER")
        self.assertEqual(selection["selected_agents"], ["p2p_tecton"])
        self.assertEqual(selection["quorum_size"], 1)
        self.assertEqual(route["selected"], ["game.mengto.action_combat"])
        self.assertFalse(any(item.startswith("visual.") for item in route["selected"]))
        self.assertFalse(any(item == MAJID_ID for item in route["selected"]))

    def test_07_sword_reference_route_reuses_style_pointer_without_implicit_img2threejs(self) -> None:
        request = "Create a Three.js xianxia sword from an approved reference."
        route = self._route(request)
        self.assertEqual(route["selected"], ["game.mengto.hybrid_assets", MAJID_ID])
        hybrid = self.manifests["game.mengto.hybrid_assets"]
        self.assertIn("visual.gpt_image_2_style_library", hybrid.context_pointers)
        self.assertIn("P2P-EXT-CANDIDATE-IMG2THREEJS-01", hybrid.context_pointers)
        self.assertIn("img2threejs:ready-for-explicit-adapter", hybrid.context_pointers)
        self.assertFalse(any("tripo" in item.lower() for item in route["selected"]))
        self.assertFalse(any(item == "visual.gpt_image_2_style_library" for item in route["selected"]))
        requirement = self._requirement(request)
        self.assertEqual(requirement["worker_strategy"], "ONE_WORKER")
        self.assertEqual(self._selection(request, requirement)["selected_agents"], ["p2p_tecton"])

    def test_08_performance_route_excludes_whiteboard_and_unrelated_gameplay(self) -> None:
        request = "Improve browser performance in the current Three.js scene."
        route = self._route(request)
        self.assertEqual(route["selected"], ["game.mengto.performance"])
        self.assertNotIn("media.whiteboard_animation", route["selected"])
        self.assertFalse(any(item in route["selected"] for item in ("game.mengto.rigged_assets", "game.mengto.action_combat", MAJID_ID)))

    def test_09_authoritative_architecture_replacement_remains_c18_blocked(self) -> None:
        requirement = self._requirement("Replace P2P's authoritative game/world architecture.")
        selection = self._selection("Replace P2P's authoritative game/world architecture.", requirement)
        self.assertEqual(requirement["profile"]["task_kind"], "ARCHITECTURE")
        self.assertEqual(requirement["profile"]["owner_gate"], "REQUIRED")
        self.assertEqual(requirement["verification_class"], "HIGH_RISK")
        self.assertEqual(requirement["worker_strategy"], "BLOCKED")
        self.assertEqual(requirement["status"], "BLOCKED")
        self.assertEqual(selection["selected_agents"], [])
        self.assertEqual(selection["quorum_size"], 0)

    def test_10_majid_qa_runtime_is_explicitly_gated_without_install_or_network(self) -> None:
        result = optional_dependency_status(
            MAJID_ID,
            operation="execute",
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
        )
        self.assertEqual(result["status"], "BLOCKED_OPTIONAL_DEPENDENCY")
        self.assertIn("unsupported-optional-operation", result["missing"])
        self.assertTrue(result["checked_without_install"])
        self.assertFalse(result["network_used"])
        integration = self.manifests[MAJID_ID].raw["UPSTREAM_PROVENANCE"]["integration"]
        self.assertEqual(integration["dependency_mode"], "EXTERNAL_RUNTIME_NOT_INSTALLED")
        self.assertEqual(integration["script_runtime_status"], "NOT_EXECUTED_EXTERNAL_DEPENDENCIES_UNINSTALLED")
        self.assertIn("@playwright/test", integration["dependency_notes"])
        self.assertIn("pngjs", integration["dependency_notes"])

    def test_11_img2threejs_current_record_preserves_02a_predecessor(self) -> None:
        candidates = self.external_manifest["candidate_sources"]
        self.assertEqual([item["source_id"] for item in self.external_manifest["sources"]], [f"P2P-EXT-{index:04d}" for index in range(1, 6)])
        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        pending = self.provenance["img2threejs_pending"]
        current = self.provenance["img2threejs_exec_01"]
        for value in (candidate, current):
            self.assertEqual(value["upstream_commit"], IMG2THREEJS_COMMIT)
            self.assertEqual(value["upstream_tree"], IMG2THREEJS_TREE)
            self.assertEqual(value["license"], "Apache-2.0")
        self.assertEqual(current["integration_status"], "REGISTERED_NONCANONICAL_EXPLICIT_ADAPTER")
        self.assertTrue(current["executable_registered_in_p2p"])
        self.assertEqual(current["execution_status"], "EXECUTED_FOCUSED_LOCAL_SMOKE")
        self.assertEqual(current["browser_visual_status"], "NOT_EXECUTED_FUTURE_PROJECT_GATE")
        self.assertEqual(current["owner_gate_status"], "PENDING_EXACT_SUBJECT_REVIEW")
        self.assertEqual(current["predecessor_record"], "img2threejs_pending")
        self.assertEqual(pending["upstream_commit"], IMG2THREEJS_PREVIOUS_COMMIT)
        self.assertEqual(pending["upstream_tree"], IMG2THREEJS_PREVIOUS_TREE)
        self.assertEqual(pending["integration_status"], "EXECUTABLE_REGISTRATION_PENDING_OWNER_GATE")
        self.assertTrue(pending["executable_available_in_upstream"])
        self.assertFalse(pending["executable_registered_in_p2p"])
        self.assertEqual(pending["execution_status"], "NOT_EXECUTED")
        self.assertEqual(candidate["integration_status"], "REGISTERED_NONCANONICAL_EXPLICIT_ADAPTER")
        self.assertTrue(candidate["executable_registered_in_p2p"])
        self.assertEqual(candidate["execution_status"], "EXECUTED_FOCUSED_LOCAL_SMOKE")
        self.assertEqual(candidate["stored_path"], ".p2p/vendor/skill/img2threejs-safe-exec-1.5.1/SKILL.md")
        self.assertEqual(candidate["sha256"], "bc94a52b66fa560d28c569af6e168d325052007fde4bcb11ff5ecbb431843a2f")
        self.assertEqual(candidate["provenance_manifest"], ".p2p/vendor/provenance/p2p-game-toolchain-02a.json")
        self.assertEqual([item["snapshot_path"] for item in pending["files"]], [None] * 5)
        self.assertIn("img2threejs", [item["CAPABILITY_ID"] for item in self.registry_raw["capabilities"]])

    def test_12_img2threejs_explicit_route_loads_only_contract(self) -> None:
        route = self._route("Run img2threejs image-to-3d reconstruction for a future Character Lab.")
        self.assertEqual(route["selected"], ["img2threejs"])
        selected = next(item for item in route["skills"] if item["capability_id"] == "img2threejs")
        self.assertTrue(selected["entrypoint_present"])
        self.assertFalse(selected["content_loaded"])
        self.assertFalse(selected["network_runtime"])
        loaded = load_vendor_skill(
            "img2threejs",
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
        )
        self.assertEqual(loaded["status"], "LOADED")
        self.assertEqual(loaded["loaded_paths"], ["SKILL.md"])
        self.assertFalse(loaded["permission_grant"])
        self.assertFalse(loaded["network_used"])
        self.assertIn("GOLDEN_CHARACTER_READY_FOR_FUTURE_EXECUTION=YES", loaded["skill"]["content"])

    def test_13_img2threejs_host_projection_is_selective_and_pure(self) -> None:
        loaded = load_vendor_skill(
            "img2threejs",
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
        )
        plan = project_host_skill(
            self.manifests["img2threejs"],
            {
                "load_stage": "LOAD",
                "selected": True,
                "entrypoint_content": loaded["skill"]["content"],
                "entrypoint_hash": loaded["skill"]["sha256"],
            },
            {
                "host_kind": "codex",
                "scope": "project",
                "host_evidence": {"status": "OK"},
            },
        )
        self.assertEqual(plan.status, HOST_READY)
        self.assertTrue(plan.content_loaded)
        self.assertEqual(
            [item.relative_target for item in plan.files],
            [
                ".agents/skills/img2threejs/SKILL.md",
                ".agents/skills/img2threejs/agents/openai.yaml",
            ],
        )
        self.assertFalse(plan.writes_performed)
        self.assertFalse(plan.permission_mutated)

    def test_14_missing_img2threejs_capability_fails_closed(self) -> None:
        with self.assertRaisesRegex(vendor_skill.VendorSkillError, "VENDOR_CAPABILITY_NOT_FOUND"):
            load_vendor_skill(
                "img2threejs-missing",
                registry_path=REGISTRY_PATH,
                repository_root=REPO_ROOT,
            )


if __name__ == "__main__":
    unittest.main()
