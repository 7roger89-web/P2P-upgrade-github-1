from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
REGISTRY_PATH = SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json"
sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities.model import CANONICAL_IDENTITIES, load_registry  # noqa: E402
from p2p_capabilities import reverse_skill_reference as reference_module  # noqa: E402
from p2p_capabilities.reverse_skill_reference import (  # noqa: E402
    EXCLUDED_EXECUTION_SURFACES,
    REVERSE_SKILL_COMMIT,
    REVIEWED_SOURCE_SURFACES,
    ReverseSkillReferenceError,
    reverse_skill_reference_for,
    reverse_skill_reference_ids,
)


EXPECTED_COMMIT = "7e2097fd90d25c2f976f6eba26d6c00aa88051df"
EXPECTED_P2P_IDS = {
    "android.protection.detect",
    "android.artifact.decode",
    "security.mobile.static.assess",
    "android.runtime.instrument",
    "android.network.inspect",
    "reverse.identify",
    "reverse.decompile.managed",
    "reverse.decompile.native",
    "reverse.deobfuscate",
    "reverse.callgraph",
    "reverse.semantic_reconstruct",
}


class P2PReverseSkillReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_registry(REGISTRY_PATH)
        cls.registry_ids = set(cls.registry["identities"])

    def test_01_exact_upstream_pin_and_reviewed_surfaces(self) -> None:
        self.assertEqual(REVERSE_SKILL_COMMIT, EXPECTED_COMMIT)
        self.assertEqual(
            set(REVIEWED_SOURCE_SURFACES),
            {
                "skills/config/routing.json",
                "skills/ops/scope-contract.md",
                "skills/ops/skill-supply-chain.md",
                "LICENSE",
            },
        )

    def test_02_bridge_only_maps_existing_p2p_capabilities(self) -> None:
        self.assertEqual(set(reverse_skill_reference_ids()), EXPECTED_P2P_IDS)
        self.assertTrue(EXPECTED_P2P_IDS <= self.registry_ids)
        self.assertEqual(tuple(self.registry["canonical_identities"]), CANONICAL_IDENTITIES)
        self.assertEqual(self.registry["canonical_denominator"], 8)
        self.assertEqual(self.registry["full_quorum"], "8/8")

    def test_03_reference_is_post_route_and_never_grants_execution(self) -> None:
        for capability_id in reverse_skill_reference_ids():
            with self.subTest(capability_id=capability_id):
                result = reverse_skill_reference_for(capability_id)
                self.assertEqual(result["capability_id"], capability_id)
                self.assertEqual(result["p2p_router_authority"], "SOLE")
                self.assertEqual(result["upstream_router_authority"], "NONE")
                self.assertFalse(result["bootstrap_allowed"])
                self.assertFalse(result["auto_install_allowed"])
                self.assertFalse(result["mcp_registration_allowed"])
                self.assertFalse(result["network_runtime_allowed"])
                self.assertFalse(result["external_execution_authorized"])
                self.assertIn(
                    result["reference"]["execution_class_ceiling"],
                    {"SAFE_READONLY", "ANALYSIS_LOCAL", "ACTIVE_TEST_AUTHORIZED"},
                )

    def test_04_dangerous_upstream_execution_surfaces_are_explicitly_excluded(self) -> None:
        required = {
            "README_AI.md",
            "RULES.md",
            "skills/scripts/",
            "skills/attack-chain/",
            "skills/edr-bypass-re/",
            "skills/patch-diff-exploit/",
            "skills/pentest-tools/",
            "skills/pwn-chain/",
            "CTF-Sandbox-Orchestrator/",
        }
        self.assertTrue(required <= set(EXCLUDED_EXECUTION_SURFACES))
        self.assertTrue(set(REVIEWED_SOURCE_SURFACES).isdisjoint(EXCLUDED_EXECUTION_SURFACES))

    def test_05_unknown_capability_fails_closed(self) -> None:
        with self.assertRaisesRegex(ReverseSkillReferenceError, "UNMAPPED_P2P_CAPABILITY"):
            reverse_skill_reference_for("reverse.not-real")

    def test_06_bridge_contains_no_execution_or_install_primitives(self) -> None:
        source = inspect.getsource(reference_module).lower()
        for forbidden in (
            "subprocess.run(",
            "subprocess.popen(",
            "os.system(",
            "requests.get(",
            "urllib.request",
            "pip install",
            "npm install",
            "curl |",
            "invoke-webrequest",
        ):
            self.assertNotIn(forbidden, source)

    def test_07_upstream_route_ids_are_metadata_not_a_task_classifier(self) -> None:
        source = inspect.getsource(reference_module)
        self.assertNotIn("classify_capabilities(", source)
        self.assertNotIn("master-route", source.lower())
        self.assertNotIn("task_text", source)
        self.assertNotIn("request:", source)


if __name__ == "__main__":
    unittest.main()
