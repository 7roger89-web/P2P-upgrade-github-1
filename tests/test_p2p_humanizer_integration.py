from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
REGISTRY_PATH = SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json"
VENDOR_ROOT = REPO_ROOT / ".p2p" / "vendor" / "skill" / "blader-humanizer-e2e92e7"
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "p2p-humanizer"
CAPABILITY_ID = "creative.prose.humanize"
EXPECTED_SNAPSHOT_HASH = "46249684a9dbb7f4a8b759f04178f0078dd3448ef5b77d203dbf7834d0c88607"
EXPECTED_SKILL_HASH = "14fc8a965b6e0a8dc100ba4dffeab55cb94bbac112abbde7e014d5c15a35c202"
EXPECTED_UPSTREAM_COMMIT = "e2e92e7b4b8229253ed5c8e81dc65463fdeddda5"
EXPECTED_UPSTREAM_TREE = "b8a8804ed9210e539531fc26c2d84fdb603960f4"

sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities import load_registry  # noqa: E402
from p2p_capabilities.vendor_skill import (  # noqa: E402
    discover_vendor_skills,
    load_vendor_skill,
    optional_dependency_status,
    snapshot_tree_sha256,
)


def _read(name: str) -> str:
    return (FIXTURE_ROOT / name).read_text(encoding="utf-8")


def _frontmatter(text: str) -> str:
    match = re.match(r"\A---\n.*?\n---\n", text, flags=re.DOTALL)
    if not match:
        raise AssertionError("fixture must have YAML frontmatter")
    return match.group(0)


def _fenced_blocks(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"(?ms)^```[^\n]*\n.*?^```\n?", text))


def _link_targets(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"\]\(([^)]+)\)", text))


def _tables(text: str) -> tuple[str, ...]:
    lines = text.splitlines(keepends=True)
    blocks: list[str] = []
    current: list[str] = []
    for line in lines:
        if line.startswith("|"):
            current.append(line)
        elif current:
            blocks.append("".join(current))
            current = []
    if current:
        blocks.append("".join(current))
    return tuple(blocks)


def _inline_code(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"`[^`\n]+`", text))


def _quoted_evidence(text: str) -> tuple[str, ...]:
    return tuple(line for line in text.splitlines() if line.startswith(">"))


class P2PHumanizerIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = load_registry(REGISTRY_PATH)
        cls.manifest = next(item for item in cls.registry["parsed"] if item.capability_id == CAPABILITY_ID)

    def route(self, request: str) -> dict:
        return discover_vendor_skills(
            request,
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
        )

    def test_a_obvious_ai_style_fixture_becomes_natural_without_fact_drift(self) -> None:
        before = _read("obvious-ai.before.md")
        after = _read("obvious-ai.after.md")
        self.assertNotEqual(before, after)
        for fact in ("dashboard", "CSV files", "12 users"):
            with self.subTest(fact=fact):
                self.assertIn(fact, before)
                self.assertIn(fact, after)
        for unsupported in ("20 users", "real-time analytics", "North America", "January 2027"):
            self.assertNotIn(unsupported, after)
        for ai_phrase in ("significant step forward", "ongoing journey", "It is important to note", "comprehensive improvement"):
            self.assertNotIn(ai_phrase, after)

    def test_b_no_fabrication_contract_is_explicit(self) -> None:
        prohibited = set(self.manifest.prohibited_actions)
        for action in (
            "add-unsupported-facts",
            "add-unsupported-names",
            "add-unsupported-numbers",
            "add-unsupported-dates",
            "add-unsupported-quotes",
            "add-unsupported-citations",
            "detector-evasion",
            "promise-detector-bypass",
        ):
            with self.subTest(action=action):
                self.assertIn(action, prohibited)
        loaded = load_vendor_skill(CAPABILITY_ID, registry_path=REGISTRY_PATH, repository_root=REPO_ROOT)
        self.assertIn("Do not invent facts.", loaded["skill"]["content"])

    def test_c_supplied_writer_sample_changes_cadence_and_style(self) -> None:
        sample = _read("writer-sample.md")
        before = _read("voice.before.md")
        after = _read("voice.after.md")
        self.assertNotEqual(before, after)
        self.assertIn("So", sample)
        self.assertTrue(after.startswith("So "))
        self.assertEqual(after.count("."), 2)
        for fact in ("update", "export flow"):
            self.assertIn(fact, before)
            self.assertIn(fact, after)
        self.assertNotIn("comprehensive", after)
        self.assertNotIn("highlights", after)

    def test_d_mixed_markdown_changes_prose_only(self) -> None:
        before = _read("mixed.before.md")
        after = _read("mixed.after.md")
        self.assertNotEqual(before, after)
        self.assertEqual(_frontmatter(before), _frontmatter(after))
        self.assertEqual(_fenced_blocks(before), _fenced_blocks(after))
        self.assertEqual(_link_targets(before), _link_targets(after))
        self.assertEqual(_tables(before), _tables(after))
        self.assertIn("This launch note explains the small update.", after)
        self.assertNotIn("comprehensive overview", after)

    def test_e_technical_text_preserves_hashes_commands_values_and_citations(self) -> None:
        before = _read("technical.before.md")
        after = _read("technical.after.md")
        self.assertNotEqual(before, after)
        self.assertEqual(_inline_code(before), _inline_code(after))
        self.assertEqual(_quoted_evidence(before), _quoted_evidence(after))
        self.assertEqual(_link_targets(before), _link_targets(after))
        for exact in (
            "d80934bc0090ef0cc6770f8c7d09b7b4cd4670b7",
            "b2d5d03bcb81058ae4be9fea525603d53ea28ee5",
            EXPECTED_SKILL_HASH,
            "python -m unittest -q tests.test_p2p_vendor_skill_integration",
        ):
            with self.subTest(exact=exact):
                self.assertIn(exact, before)
                self.assertIn(exact, after)

    def test_f_capability_is_not_loaded_globally_by_default(self) -> None:
        for request in ("", "Write an article about natural prose.", "Explain a PostgreSQL index."):
            with self.subTest(request=request):
                result = self.route(request)
                self.assertNotIn(CAPABILITY_ID, result["selected"])
                self.assertFalse(result["content_loaded"])
        metadata = next(item for item in self.route("")["skills"] if item["capability_id"] == CAPABILITY_ID)
        self.assertEqual(metadata["load_mode"], "ON_DEMAND")
        self.assertFalse(metadata["content_loaded"])

    def test_g_explicit_invocation_selects_only_the_new_capability(self) -> None:
        result = self.route("Use creative.prose.humanize to humanize this prose in my voice.")
        self.assertEqual(result["selected"], [CAPABILITY_ID])
        self.assertEqual(result["route"]["selected"], [CAPABILITY_ID])
        self.assertTrue(result["route"]["single_router"])
        self.assertEqual(result["route"]["adaptive_quorum"]["canonical_denominator"], 8)
        self.assertEqual(result["route"]["adaptive_quorum"]["full_quorum"], "8/8")
        loaded = load_vendor_skill(CAPABILITY_ID, registry_path=REGISTRY_PATH, repository_root=REPO_ROOT)
        self.assertEqual(loaded["loaded_paths"], ["SKILL.md"])
        self.assertFalse(loaded["permission_grant"])
        self.assertFalse(loaded["network_used"])

    def test_h_exact_snapshot_and_humanizer_workflow_are_preserved(self) -> None:
        self.assertEqual(
            tuple(sorted(path.relative_to(VENDOR_ROOT).as_posix() for path in VENDOR_ROOT.rglob("*") if path.is_file())),
            ("LICENSE", "SKILL.md"),
        )
        self.assertEqual(snapshot_tree_sha256(VENDOR_ROOT), EXPECTED_SNAPSHOT_HASH)
        provenance = self.manifest.upstream_provenance
        self.assertEqual(provenance["upstream_commit"], EXPECTED_UPSTREAM_COMMIT)
        self.assertEqual(provenance["upstream_tree"], EXPECTED_UPSTREAM_TREE)
        self.assertEqual(provenance["license"]["kind"], "MIT")
        loaded = load_vendor_skill(CAPABILITY_ID, registry_path=REGISTRY_PATH, repository_root=REPO_ROOT)
        content = loaded["skill"]["content"]
        for contract in (
            "A writing sample takes priority",
            "Read the source and mark each AI pattern.",
            "What still sounds AI-generated?",
            "Did the rewrite add or remove any fact",
            "Write the final version.",
            "File mode",
            "code blocks",
            "YAML metadata",
            "link targets",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, content)

    def test_i_core_load_has_no_dependency_install_network_or_permission_path(self) -> None:
        integration = self.manifest.upstream_provenance["integration"]
        self.assertEqual(integration["dependency_mode"], "NONE")
        self.assertEqual(integration["references"], [])
        self.assertEqual(integration["assets"], [])
        self.assertEqual(integration["script_entrypoints"], [])
        self.assertFalse(integration["network_runtime"])
        self.assertFalse(integration["credentials"])
        self.assertEqual(
            optional_dependency_status(CAPABILITY_ID, operation="load", registry_path=REGISTRY_PATH, repository_root=REPO_ROOT)["status"],
            "NOT_REQUIRED",
        )


if __name__ == "__main__":
    unittest.main()
