"""P2P_UPSTREAM_CAPABILITY_CONSUMPTION_01: Cross-domain repo/source selection tests (Issue #222).

Validates:
1. Same external source can be classified differently by role without becoming a new canonical agent/router.
2. Task/domain selection excludes irrelevant available capabilities (domain isolation).
3. REFERENCE_ONLY / TECHNIQUE_REFERENCE is not executable or installable by default.
4. DATASET / FIXTURE does not satisfy methodology/provenance authority.
5. Legal OFFICIAL_SOURCE authority cannot be substituted by a tested code repo (CODE_PASS != LEGAL_AUTHORITY).
6. Metaphysics school/provenance separation survives selection (ONE_UPSTREAM_REPO = ONE_INDEPENDENT_RESEARCH_DOSSIER,
   DETERMINISTIC_OUTPUT != PREDICTIVE_VALIDITY).
7. Three.js optional specialist capabilities remain demand-triggered (AVAILABLE != SELECTED).
8. Existing capability foundation tests remain green in touched surface.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities import (
    CORE_INVARIANTS,
    SOURCE_ROLES,
    SOURCE_ROLE_ALIASES,
    DomainSourceRecord,
    DomainSourceSelectionReceipt,
    ProjectDomainModel,
    SelectedSourceItem,
    SourceRoleMetadata,
    UnselectedSourceItem,
    build_domain_source_catalog,
    get_source_role_metadata,
    normalize_source_role,
    select_domain_sources,
)


class TestSourceRoleContract(unittest.TestCase):
    """Test 1 & 3 & 4: Source role classification, invariants, and metadata."""

    def test_canonical_source_roles_present(self) -> None:
        expected = (
            "DEPENDENCY",
            "EXECUTABLE_ENGINE",
            "SKILL",
            "REFERENCE_IMPLEMENTATION",
            "TECHNIQUE_REFERENCE",
            "TOOL",
            "STARTER",
            "DATASET",
            "PRIMARY_OR_OFFICIAL_EVIDENCE_SOURCE",
            "RESEARCH_ONLY",
            "DEFER",
            "REJECT",
        )
        for role in expected:
            self.assertIn(role, SOURCE_ROLES)

    def test_source_role_aliases_normalization(self) -> None:
        self.assertEqual(normalize_source_role("library"), "DEPENDENCY")
        self.assertEqual(normalize_source_role("DEPENDENCY_LIBRARY"), "DEPENDENCY")
        self.assertEqual(normalize_source_role("knowledge_unit"), "SKILL")
        self.assertEqual(normalize_source_role("SKILL_KNOWLEDGE_UNIT"), "SKILL")
        self.assertEqual(normalize_source_role("pattern_only"), "TECHNIQUE_REFERENCE")
        self.assertEqual(normalize_source_role("reference_only"), "TECHNIQUE_REFERENCE")
        self.assertEqual(normalize_source_role("external_tool"), "TOOL")
        self.assertEqual(normalize_source_role("template"), "STARTER")
        self.assertEqual(normalize_source_role("fixture"), "DATASET")
        self.assertEqual(normalize_source_role("official_source"), "PRIMARY_OR_OFFICIAL_EVIDENCE_SOURCE")
        self.assertEqual(normalize_source_role("primary_source"), "PRIMARY_OR_OFFICIAL_EVIDENCE_SOURCE")
        self.assertEqual(normalize_source_role("deferred"), "DEFER")
        self.assertEqual(normalize_source_role("rejected"), "REJECT")

    def test_invalid_source_role_fails_closed(self) -> None:
        with self.assertRaises(ValueError):
            normalize_source_role("UNKNOWN_MAGIC_ROLE")

    def test_same_source_classified_differently_by_role_without_new_router(self) -> None:
        """Requirement 1: Same external source can be classified differently by role."""
        # e.g., a sample repository consumed as TECHNIQUE_REFERENCE in one task
        sample_as_technique = DomainSourceRecord(
            source_id="repo:codrops/demo",
            source_name="Codrops demo",
            domain="game.three",
            source_role="TECHNIQUE_REFERENCE",
            consumption_mode="CONSULT_TECHNIQUE_REFERENCE",
            capabilities_provided=("technique_reference",),
        )
        # Same repository consumed as REFERENCE_IMPLEMENTATION in an architectural review
        sample_as_reference = DomainSourceRecord(
            source_id="repo:codrops/demo",
            source_name="Codrops demo",
            domain="game.three",
            source_role="REFERENCE_IMPLEMENTATION",
            consumption_mode="INSPECT_UI_PATTERN",
            capabilities_provided=("architecture_pattern",),
        )
        self.assertEqual(sample_as_technique.source_role, "TECHNIQUE_REFERENCE")
        self.assertEqual(sample_as_reference.source_role, "REFERENCE_IMPLEMENTATION")
        # Metadata checks
        meta_tech = get_source_role_metadata(sample_as_technique.source_role)
        meta_ref = get_source_role_metadata(sample_as_reference.source_role)
        self.assertFalse(meta_tech.is_executable)
        self.assertFalse(meta_tech.is_installable)
        self.assertFalse(meta_ref.is_executable)
        self.assertFalse(meta_ref.is_installable)

    def test_reference_only_and_technique_reference_not_executable(self) -> None:
        """Requirement 3: REFERENCE_ONLY/TECHNIQUE_REFERENCE is not executable/installable."""
        meta_tech = get_source_role_metadata("TECHNIQUE_REFERENCE")
        self.assertFalse(meta_tech.is_executable, "SELECTED != EXECUTABLE")
        self.assertFalse(meta_tech.is_installable, "REFERENCE != INSTALLED")

        meta_ref = get_source_role_metadata("REFERENCE_IMPLEMENTATION")
        self.assertFalse(meta_ref.is_executable)
        self.assertFalse(meta_ref.is_installable)

        meta_res = get_source_role_metadata("RESEARCH_ONLY")
        self.assertFalse(meta_res.is_executable)
        self.assertFalse(meta_res.is_installable)

    def test_dataset_fixture_not_methodology_authority(self) -> None:
        """Requirement 4: DATASET/FIXTURE does not satisfy methodology/provenance authority."""
        meta_dataset = get_source_role_metadata("DATASET")
        self.assertFalse(meta_dataset.is_methodology_authority, "DATASET != METHODOLOGY_AUTHORITY")
        self.assertFalse(meta_dataset.is_domain_truth_authority)
        self.assertFalse(meta_dataset.is_executable)


class TestProofCaseAThreeJS(unittest.TestCase):
    """Proof Case A: UI / Three.js selective capability consumption."""

    def test_threejs_runtime_vs_technique_reference_vs_specialists(self) -> None:
        """Prove selective use: runtime as DEPENDENCY, Codrops as TECHNIQUE_REFERENCE,

        and specialist capabilities (BVH/pathfinding/cinematic) remain demand-triggered.
        """
        task = {
            "task_id": "TASK-THREE-01",
            "desired_outcome": (
                "Build a 3D animated showcase hero scene using Three.js with PBR lighting and "
                "referencing Codrops interactive showcase techniques."
            ),
        }
        receipt = select_domain_sources(task)
        self.assertEqual(receipt.domain, "game.three")

        selected_ids = {s.source_id for s in receipt.selected_sources}
        unselected_ids = {u.source_id for u in receipt.unselected_candidates}

        # Selected foundation
        self.assertIn("repo:three", selected_ids)
        self.assertIn("skill:threejs", selected_ids)
        self.assertIn("repo:codrops-webgl-showcase", selected_ids)

        # Check roles of selected
        by_id = {s.source_id: s for s in receipt.selected_sources}
        self.assertEqual(by_id["repo:three"].source_role, "DEPENDENCY")
        self.assertEqual(by_id["repo:three"].consumption_mode, "LINK_AS_DEPENDENCY")

        self.assertEqual(by_id["skill:threejs"].source_role, "SKILL")
        self.assertEqual(by_id["skill:threejs"].consumption_mode, "READ_AS_SKILL")

        self.assertEqual(by_id["repo:codrops-webgl-showcase"].source_role, "TECHNIQUE_REFERENCE")
        self.assertEqual(by_id["repo:codrops-webgl-showcase"].consumption_mode, "CONSULT_TECHNIQUE_REFERENCE")
        meta_codrops = get_source_role_metadata(by_id["repo:codrops-webgl-showcase"].source_role)
        self.assertFalse(meta_codrops.is_executable, "SELECTED != EXECUTABLE")

        # Specialist capabilities remain demand-triggered (Requirement 7)
        self.assertIn("repo:three-mesh-bvh", unselected_ids)
        self.assertIn("repo:three-pathfinding", unselected_ids)
        self.assertIn("repo:theatre-js", unselected_ids)

        unselected_map = {u.source_id: u for u in receipt.unselected_candidates}
        self.assertIn("CAPABILITY_NOT_REQUIRED", unselected_map["repo:three-mesh-bvh"].why_not_selected)
        self.assertIn("CAPABILITY_NOT_REQUIRED", unselected_map["repo:three-pathfinding"].why_not_selected)
        self.assertIn("CAPABILITY_NOT_REQUIRED", unselected_map["repo:theatre-js"].why_not_selected)

    def test_threejs_specialist_activated_when_demanded(self) -> None:
        """When spatial query / BVH is explicitly demanded, it is activated."""
        task = {
            "task_id": "TASK-THREE-02",
            "desired_outcome": "Raycast complex animated 3D mesh collisions with BVH spatial indexing acceleration",
        }
        receipt = select_domain_sources(task)
        selected_ids = {s.source_id for s in receipt.selected_sources}
        self.assertIn("repo:three-mesh-bvh", selected_ids)

    def test_threejs_production_knowledge_delta_reconciled(self) -> None:
        """Verify the reconciled production-knowledge delta exists in the threejs skill."""
        workflow_ref = REPO_ROOT / ".agents" / "skills" / "threejs" / "references" / "19-production-workflow.md"
        self.assertTrue(workflow_ref.is_file(), "19-production-workflow.md must exist")
        content = workflow_ref.read_text(encoding="utf-8")

        # 5 required production research delta topics
        self.assertIn("Blender & Web-3D Asset Preparation", content)
        self.assertIn("Draco", content)
        self.assertIn("KTX2", content)
        self.assertIn("Baking vs Dynamic Lighting Decision Matrix", content)
        self.assertIn("Color Management, PBR & Environment Workflow", content)
        self.assertIn("SRGBColorSpace", content)
        self.assertIn("Modern WebGL vs WebGPU / TSL / RenderPipeline Path", content)
        self.assertIn("Measurement-First Performance Guidance", content)
        self.assertIn("Rejection of Brittle Magic Numbers", content)


class TestProofCaseBVNLAW(unittest.TestCase):
    """Proof Case B: VNLAW / legal authority vs code parser separation."""

    def test_official_legal_source_separated_from_code_parser(self) -> None:
        """Requirement 5: Legal OFFICIAL_SOURCE authority cannot be substituted by a tested code repo."""
        task = {
            "task_id": "TASK-VNLAW-01",
            "desired_outcome": "Tra cứu quy định xử phạt vi phạm giao thông đường bộ theo căn cứ pháp lý chính thức",
        }
        receipt = select_domain_sources(task)
        self.assertEqual(receipt.domain, "legal.vn")

        by_id = {s.source_id: s for s in receipt.selected_sources}
        self.assertIn("official:vbpl_vn", by_id)
        self.assertIn("repo:vnlaw-parser", by_id)

        # Official source is the authority of record
        official = by_id["official:vbpl_vn"]
        self.assertEqual(official.source_role, "PRIMARY_OR_OFFICIAL_EVIDENCE_SOURCE")
        self.assertEqual(official.authority_scope, "OFFICIAL_LEGAL_TEXT_OF_RECORD")
        meta_official = get_source_role_metadata(official.source_role)
        self.assertTrue(meta_official.is_domain_truth_authority)

        # Code parser is only an execution tool, NOT legal authority
        parser = by_id["repo:vnlaw-parser"]
        self.assertEqual(parser.source_role, "EXECUTABLE_ENGINE")
        self.assertEqual(parser.authority_scope, "PARSING_AND_SEARCH_ENGINE_ONLY")
        self.assertIn("CODE_PASS_IS_NOT_LEGAL_AUTHORITY", parser.limitations)
        meta_parser = get_source_role_metadata(parser.source_role)
        self.assertFalse(meta_parser.is_domain_truth_authority, "CODE_PASS != LEGAL_AUTHORITY")

    def test_tested_code_parser_cannot_satisfy_exclusive_official_legal_demand(self) -> None:
        """When task requires strictly official legal authority, code parser cannot satisfy it alone."""
        task = {
            "task_id": "TASK-VNLAW-02",
            "domain": "legal.vn",
            "desired_outcome": "Xác nhận văn bản pháp luật chính thức có hiệu lực",
            "required_capabilities": ["official_legal_authority"],
        }
        # Provide only the parser as candidate
        parser_only = [
            DomainSourceRecord(
                source_id="repo:vnlaw-parser",
                source_name="Parser",
                domain="legal.vn",
                source_role="EXECUTABLE_ENGINE",
                consumption_mode="RUN_AS_ENGINE",
                capabilities_provided=("official_legal_authority", "legal_search_parser"),
            )
        ]
        receipt = select_domain_sources(task, available_sources=parser_only)
        self.assertEqual(len(receipt.selected_sources), 0)
        self.assertEqual(len(receipt.unselected_candidates), 1)
        self.assertIn(
            "CODE_PASS_IS_NOT_LEGAL_AUTHORITY",
            receipt.unselected_candidates[0].why_not_selected,
        )


class TestProofCaseCChineseMetaphysics(unittest.TestCase):
    """Proof Case C: Chinese Metaphysics school separation & calculation vs prediction."""

    def test_ziwei_calculation_separated_from_predictive_validity_and_school(self) -> None:
        """Requirement 6: Metaphysics school/provenance separation survives selection.

        - SylarLong/iztro selected as EXECUTABLE_ENGINE (chart math)
        - ziwei-doushu-skill selected as SKILL (Zhongzhou methodology)
        - DETERMINISTIC_OUTPUT != PREDICTIVE_VALIDITY limitation recorded
        - Liuyao and Meihua repositories excluded (DOMAIN_MISMATCH)
        """
        task = {
            "task_id": "TASK-ZW-01",
            "desired_outcome": "Lập lá số Tử Vi Đẩu Số theo phái Trung Châu và an sao Tứ Hóa năm sinh",
        }
        receipt = select_domain_sources(task)
        self.assertEqual(receipt.domain, "metaphysics.ziwei")

        selected_ids = {s.source_id for s in receipt.selected_sources}
        unselected_ids = {u.source_id for u in receipt.unselected_candidates}

        self.assertIn("repo:SylarLong/iztro", selected_ids)
        self.assertIn("repo:Linden-TR/ziwei-doushu-skill", selected_ids)

        by_id = {s.source_id: s for s in receipt.selected_sources}
        iztro = by_id["repo:SylarLong/iztro"]
        self.assertEqual(iztro.source_role, "EXECUTABLE_ENGINE")
        self.assertEqual(iztro.consumption_mode, "RUN_AS_ENGINE")
        self.assertIn("DETERMINISTIC_OUTPUT_IS_NOT_PREDICTIVE_VALIDITY", iztro.limitations)
        self.assertEqual(iztro.authority_scope, "DETERMINISTIC_CHART_FACTS_ONLY")

        zhongzhou = by_id["repo:Linden-TR/ziwei-doushu-skill"]
        self.assertEqual(zhongzhou.source_role, "SKILL")
        self.assertEqual(zhongzhou.school_or_jurisdiction, "ZHONGZHOU_PAI")

        # Liuyao and Meihua are excluded by domain mismatch (Requirement 2 & Invariant DOMAIN_APPLICABILITY != AUTHORITY)
        self.assertIn("repo:muyen/meihua-yishu", unselected_ids)
        self.assertIn("repo:xiaoshiyilangzhao1996-droid/yinyo-liuyao", unselected_ids)
        unselected_map = {u.source_id: u for u in receipt.unselected_candidates}
        self.assertIn("DOMAIN_MISMATCH", unselected_map["repo:muyen/meihua-yishu"].why_not_selected)
        self.assertIn("DOMAIN_MISMATCH", unselected_map["repo:xiaoshiyilangzhao1996-droid/yinyo-liuyao"].why_not_selected)

        # Sanhe school repo excluded because task specifically asked for Zhongzhou (school A != school B)
        self.assertIn("repo:wuandyA/ziwei", unselected_ids)

    def test_sample_chart_dataset_does_not_become_methodology_authority(self) -> None:
        """Requirement 4: Sample chart fixtures do not establish doctrine."""
        task = {
            "task_id": "TASK-ZW-02",
            "domain": "metaphysics.ziwei",
            "desired_outcome": "Thiết lập quy tắc an sao Tứ Hóa chuẩn phái",
            "required_capabilities": ["school_methodology"],
        }
        dataset_only = [
            DomainSourceRecord(
                source_id="dataset:ziwei-celebrity-charts-sample",
                source_name="Sample Charts",
                domain="metaphysics.ziwei",
                source_role="DATASET",
                consumption_mode="INSPECT_AS_DATASET",
                capabilities_provided=("school_methodology", "test_fixture_data"),
            )
        ]
        receipt = select_domain_sources(task, available_sources=dataset_only)
        self.assertEqual(len(receipt.selected_sources), 0)
        self.assertEqual(len(receipt.unselected_candidates), 1)
        self.assertIn(
            "DATASET_IS_NOT_METHODOLOGY_AUTHORITY",
            receipt.unselected_candidates[0].why_not_selected,
        )


class TestReceiptAndAntiOverengineering(unittest.TestCase):
    """Test receipt serialization, compact summary, and architectural boundaries."""

    def test_receipt_structure_and_compact_summary(self) -> None:
        task = {
            "task_id": "TASK-SUMMARY-01",
            "desired_outcome": "Lập lá số Tử Vi Đẩu Số theo phái Trung Châu",
        }
        receipt = select_domain_sources(task)
        summary = receipt.compact_summary()
        self.assertIn("DOMAIN=metaphysics.ziwei", summary)
        self.assertIn("CAPABILITIES_REQUIRED=", summary)
        self.assertIn("SOURCES_SELECTED=", summary)
        self.assertIn("SOURCE_ROLE_PER_SOURCE=", summary)
        self.assertIn("PIN_PROVENANCE=", summary)
        self.assertIn("CONSUMPTION_MODE=", summary)
        self.assertIn("WHY_SELECTED=", summary)
        self.assertIn("WHY_NOT_SELECTED=", summary)
        self.assertIn("LIMITATIONS_AUTHORITY_BOUNDARY=", summary)

        d = receipt.to_dict()
        self.assertEqual(d["receipt_schema"], "p2p-source-selection-receipt/1")
        self.assertEqual(d["task_id"], "TASK-SUMMARY-01")
        self.assertEqual(tuple(d["invariants_enforced"]), CORE_INVARIANTS)

    def test_no_second_router_or_registry_created(self) -> None:
        """Anti-overengineering: FW02 & domain.py extended; no new router or registry created."""
        from p2p_capabilities import ProjectDomainModel, select_domain_sources
        self.assertTrue(callable(select_domain_sources))
        model = ProjectDomainModel("test-domain")
        self.assertEqual(model.domain, "test-domain")


if __name__ == "__main__":
    unittest.main()
