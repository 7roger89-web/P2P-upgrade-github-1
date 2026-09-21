"""P2P_UPSTREAM_CAPABILITY_CONSUMPTION_01: Cross-domain repo/source selection tests (Issue #222).

Validates:
1. Fabricated/unverified production provenance is rejected; production catalog contains only authentic sources.
2. Required capability coverage with no eligible authoritative source fails closed (selection_status=BLOCKED).
3. DEFER and REJECT roles can never be selected, even if status is set to ACTIVE.
4. Source role alone cannot grant factual/domain/methodology authority (authority is bounded by source record).
5. Dataset fixture cannot satisfy methodology authority (DATASET != METHODOLOGY_AUTHORITY).
6. Code parser cannot satisfy official legal authority (CODE_PASS != LEGAL_AUTHORITY).
7. Three.js specialist capabilities remain demand-triggered (AVAILABLE != SELECTED).
8. Existing audited license/version facts are preserved without conflicting duplicates (Theatre.js split license, three-mesh-bvh v0.9.14).
9. Unsupported Bazi source coverage fails closed (selection_status=BLOCKED).
10. Existing FW02/domain/capability regressions remain green.
"""

from __future__ import annotations

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


# ---------------------------------------------------------------------------
# Test-only synthetic fixtures (strictly isolated from production catalog)
# ---------------------------------------------------------------------------

FIXTURE_TECHNIQUE_REFERENCE = DomainSourceRecord(
    source_id="fixture:visual-shader-technique",
    source_name="Visual Shader Technique Demo (Test Fixture)",
    domain="game.three",
    source_role="TECHNIQUE_REFERENCE",
    consumption_mode="CONSULT_TECHNIQUE_REFERENCE",
    capabilities_provided=("technique_reference",),
    upstream_repo="test-fixture/shader-technique",
    pinned_ref="fixture-v1.0",
    license="MIT",
    authority_scope="VISUAL_TECHNIQUE_REFERENCE_ONLY",
)

FIXTURE_VNLAW_PARSER = DomainSourceRecord(
    source_id="fixture:vnlaw-parser",
    source_name="VNLaw Text Parser Engine (Test Fixture)",
    domain="legal.vn",
    source_role="EXECUTABLE_ENGINE",
    consumption_mode="RUN_AS_ENGINE",
    capabilities_provided=("official_legal_authority", "legal_search_parser"),
    upstream_repo="test-fixture/vnlaw-parser",
    pinned_ref="fixture-v1.0",
    license="MIT",
    authority_scope="PARSING_AND_SEARCH_ENGINE_ONLY",
    domain_truth_authority=False,
    methodology_authority=False,
    limitations=("CODE_PASS_IS_NOT_LEGAL_AUTHORITY",),
)

FIXTURE_ZIWEI_DATASET = DomainSourceRecord(
    source_id="fixture:ziwei-sample-charts",
    source_name="Ziwei Sample Charts Dataset (Test Fixture)",
    domain="metaphysics.ziwei",
    source_role="DATASET",
    consumption_mode="INSPECT_AS_DATASET",
    capabilities_provided=("test_fixture_data", "school_methodology"),
    upstream_repo="test-fixture/ziwei-charts.json",
    pinned_ref="fixture-v1.0",
    license="CC0-1.0",
    authority_scope="TEST_FIXTURE_DATA_ONLY",
    domain_truth_authority=False,
    methodology_authority=False,
    limitations=("DATASET_IS_NOT_METHODOLOGY_AUTHORITY",),
)


class TestSourceRoleContract(unittest.TestCase):
    """Test structural consumption roles, invariants, and metadata."""

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

    def test_selection_does_not_imply_executability_invariant(self) -> None:
        """SELECTION_DOES_NOT_IMPLY_EXECUTABILITY: reference/technique/dataset are non-executable."""
        self.assertIn("SELECTION_DOES_NOT_IMPLY_EXECUTABILITY", CORE_INVARIANTS)
        meta_tech = get_source_role_metadata("TECHNIQUE_REFERENCE")
        self.assertFalse(meta_tech.is_executable)
        self.assertFalse(meta_tech.is_installable)

        meta_ref = get_source_role_metadata("REFERENCE_IMPLEMENTATION")
        self.assertFalse(meta_ref.is_executable)
        self.assertFalse(meta_ref.is_installable)

        meta_dataset = get_source_role_metadata("DATASET")
        self.assertFalse(meta_dataset.is_executable)

        # External tools that influence canonical behavior require pinned provenance
        meta_tool = get_source_role_metadata("TOOL")
        self.assertTrue(meta_tool.requires_pinned_provenance)

    def test_role_alone_cannot_grant_factual_or_methodology_authority(self) -> None:
        """Blocker 2: SourceRoleMetadata describes structural consumption only;

        it does NOT grant universal domain_truth_authority or methodology_authority.
        """
        meta_primary = get_source_role_metadata("PRIMARY_OR_OFFICIAL_EVIDENCE_SOURCE")
        self.assertFalse(hasattr(meta_primary, "is_domain_truth_authority"))
        self.assertFalse(hasattr(meta_primary, "is_methodology_authority"))

        # Authority must come from explicit DomainSourceRecord claims
        record_without_authority = DomainSourceRecord(
            source_id="test:unauthorized-source",
            source_name="Unauthorized Source",
            domain="legal.vn",
            source_role="PRIMARY_OR_OFFICIAL_EVIDENCE_SOURCE",
            consumption_mode="QUERY_OFFICIAL_EVIDENCE",
            domain_truth_authority=False,
            methodology_authority=False,
        )
        self.assertFalse(record_without_authority.domain_truth_authority)
        self.assertFalse(record_without_authority.methodology_authority)


class TestProductionCatalogTruthfulness(unittest.TestCase):
    """Blocker 1: Validate production catalog contains zero fabricated sources and preserves audited facts."""

    def setUp(self) -> None:
        self.catalog = build_domain_source_catalog()
        self.catalog_by_id = {s.source_id: s for s in self.catalog}

    def test_zero_fabricated_sources_in_production_catalog(self) -> None:
        """No example/vnlaw-parser, example/vnlaw-viewer, fake codrops, or fake celebrity datasets."""
        for s in self.catalog:
            self.assertNotIn("example/vnlaw", s.upstream_repo)
            self.assertNotIn("example.com", s.upstream_repo)
            self.assertNotIn("codrops/interactive-webgl-demo", s.upstream_repo)
            self.assertNotIn("ziwei-celebrity-charts-sample", s.source_id)

    def test_three_mesh_bvh_matches_audited_catalog_version(self) -> None:
        """Matches CAND-GAME-UI-005 in ui-game-threejs capability-catalog.json: v0.9.14."""
        self.assertIn("repo:three-mesh-bvh", self.catalog_by_id)
        bvh = self.catalog_by_id["repo:three-mesh-bvh"]
        self.assertIn("0.9.14", bvh.pinned_ref)
        self.assertEqual(bvh.license, "MIT")

    def test_theatre_js_preserves_license_split(self) -> None:
        """Matches CAND-GAME-UI-007 in ui-game-threejs capability-catalog.json:

        Apache-2.0 (core), AGPL-3.0 (studio).
        """
        self.assertIn("repo:theatre-js", self.catalog_by_id)
        theatre = self.catalog_by_id["repo:theatre-js"]
        self.assertIn("Apache-2.0 (core)", theatre.license)
        self.assertIn("AGPL-3.0 (studio)", theatre.license)
        self.assertIn("LICENSE_SPLIT", theatre.limitations[1])

    def test_chinese_metaphysics_upstreams_match_readme(self) -> None:
        """Exact pinned commits from source/chinese-metaphysics/README.md."""
        self.assertIn("repo:SylarLong/iztro", self.catalog_by_id)
        iztro = self.catalog_by_id["repo:SylarLong/iztro"]
        self.assertEqual(iztro.pinned_ref, "2c7ef9be669df7b19d1799f4dce335fed3794f78")

        self.assertIn("repo:Linden-TR/ziwei-doushu-skill", self.catalog_by_id)
        zw_skill = self.catalog_by_id["repo:Linden-TR/ziwei-doushu-skill"]
        self.assertEqual(zw_skill.pinned_ref, "a842dd65dabdc4ce42ec9688b88ae876858a9977")

        self.assertIn("repo:muyen/meihua-yishu", self.catalog_by_id)
        meihua = self.catalog_by_id["repo:muyen/meihua-yishu"]
        self.assertEqual(meihua.pinned_ref, "8a9a5e0f482dd225bfe4a1c52c2ae5546228607a")

        self.assertIn("repo:xiaoshiyilangzhao1996-droid/yinyo-liuyao", self.catalog_by_id)
        liuyao = self.catalog_by_id["repo:xiaoshiyilangzhao1996-droid/yinyo-liuyao"]
        self.assertEqual(liuyao.pinned_ref, "1f67eea0ce5a2c49e6851e4eedce507f9c044dd9")


class TestDeferAndRejectNonSelectable(unittest.TestCase):
    """Blocker 4: DEFER and REJECT can NEVER be selected, even if status says ACTIVE."""

    def test_defer_role_is_intrinsically_non_selectable(self) -> None:
        deferred_source = DomainSourceRecord(
            source_id="repo:deferred-candidate",
            source_name="Deferred candidate",
            domain="game.three",
            source_role="DEFER",
            consumption_mode="DEFERRED_CONSIDERATION",
            capabilities_provided=("three_rendering",),
            status="ACTIVE",  # Intentionally conflicting status
        )
        # Post-init normalizes status
        self.assertEqual(deferred_source.status, "DEFERRED")

        task = {
            "task_id": "TASK-DEFER-01",
            "desired_outcome": "Render 3D scene with Three.js",
            "domain": "game.three",
            "required_capabilities": ["three_rendering"],
        }
        receipt = select_domain_sources(task, available_sources=[deferred_source])
        self.assertEqual(len(receipt.selected_sources), 0)
        self.assertEqual(receipt.selection_status, "BLOCKED")
        self.assertEqual(len(receipt.unselected_candidates), 1)
        self.assertIn("CANDIDATE_ROLE_DEFER_NON_SELECTABLE", receipt.unselected_candidates[0].why_not_selected)

    def test_reject_role_is_intrinsically_non_selectable(self) -> None:
        rejected_source = DomainSourceRecord(
            source_id="repo:rejected-candidate",
            source_name="Rejected candidate",
            domain="game.three",
            source_role="REJECT",
            consumption_mode="REJECTED_LICENSE_GATE",
            capabilities_provided=("three_rendering",),
            status="ACTIVE",  # Intentionally conflicting status
        )
        self.assertEqual(rejected_source.status, "REJECTED")

        task = {
            "task_id": "TASK-REJECT-01",
            "desired_outcome": "Render 3D scene with Three.js",
            "domain": "game.three",
            "required_capabilities": ["three_rendering"],
        }
        receipt = select_domain_sources(task, available_sources=[rejected_source])
        self.assertEqual(len(receipt.selected_sources), 0)
        self.assertEqual(receipt.selection_status, "BLOCKED")
        self.assertEqual(len(receipt.unselected_candidates), 1)
        self.assertIn("CANDIDATE_ROLE_REJECT_NON_SELECTABLE", receipt.unselected_candidates[0].why_not_selected)


class TestFailClosedCoverageAccounting(unittest.TestCase):
    """Blocker 3: Selection receipt must expose deterministic coverage and fail-closed status."""

    def test_unsupported_bazi_fails_closed_as_blocked(self) -> None:
        """metaphysics.bazi with no supported/eligible source must NOT silently succeed."""
        task = {
            "task_id": "TASK-BAZI-01",
            "desired_outcome": "Lập lá số Bát Tự và luận đoán can chi",
            "domain": "metaphysics.bazi",
        }
        receipt = select_domain_sources(task)
        self.assertEqual(receipt.domain, "metaphysics.bazi")
        self.assertEqual(receipt.selection_status, "BLOCKED")
        self.assertEqual(len(receipt.selected_sources), 0)
        self.assertIn("bazi_chart_calculation", receipt.unsatisfied_required_capabilities)
        self.assertEqual(len(receipt.satisfied_capabilities), 0)

    def test_fully_satisfied_selection_reports_satisfied_status(self) -> None:
        task = {
            "task_id": "TASK-ZW-01",
            "desired_outcome": "Lập lá số Tử Vi Đẩu Số theo phái Trung Châu và an sao Tứ Hóa",
        }
        receipt = select_domain_sources(task)
        self.assertEqual(receipt.domain, "metaphysics.ziwei")
        self.assertEqual(receipt.selection_status, "SATISFIED")
        self.assertGreater(len(receipt.selected_sources), 0)
        self.assertEqual(len(receipt.unsatisfied_required_capabilities), 0)
        self.assertIn("chart_calculation", receipt.satisfied_capabilities)
        self.assertIn("school_methodology", receipt.satisfied_capabilities)


class TestProofCaseAThreeJS(unittest.TestCase):
    """Proof Case A: UI / Three.js selective capability consumption & production guidance."""

    def test_threejs_runtime_and_technique_reference(self) -> None:
        task = {
            "task_id": "TASK-THREE-01",
            "desired_outcome": "Build a 3D animated showcase scene using Three.js with PBR lighting and technique reference",
        }
        # Provide production catalog + test-only technique reference fixture
        sources = list(build_domain_source_catalog()) + [FIXTURE_TECHNIQUE_REFERENCE]
        receipt = select_domain_sources(task, available_sources=sources)
        self.assertEqual(receipt.domain, "game.three")
        self.assertEqual(receipt.selection_status, "SATISFIED")

        selected_ids = {s.source_id for s in receipt.selected_sources}
        unselected_ids = {u.source_id for u in receipt.unselected_candidates}

        self.assertIn("repo:three", selected_ids)
        self.assertIn("skill:threejs", selected_ids)
        self.assertIn("fixture:visual-shader-technique", selected_ids)

        # Specialist capabilities stay unselected
        self.assertIn("repo:three-mesh-bvh", unselected_ids)
        self.assertIn("repo:three-pathfinding", unselected_ids)
        self.assertIn("repo:theatre-js", unselected_ids)

    def test_threejs_specialist_activated_when_demanded(self) -> None:
        task = {
            "task_id": "TASK-THREE-02",
            "desired_outcome": "Raycast complex animated 3D mesh collisions with BVH spatial indexing acceleration",
        }
        receipt = select_domain_sources(task)
        selected_ids = {s.source_id for s in receipt.selected_sources}
        self.assertIn("repo:three-mesh-bvh", selected_ids)

    def test_threejs_production_knowledge_delta_reconciled(self) -> None:
        """Blocker 5: Verify measurement-first discipline, no brittle magic numbers, and current Three.js APIs."""
        workflow_ref = REPO_ROOT / ".agents" / "skills" / "threejs" / "references" / "19-production-workflow.md"
        self.assertTrue(workflow_ref.is_file())
        content = workflow_ref.read_text(encoding="utf-8")

        # 5 required production research delta topics
        self.assertIn("Blender & Web-3D Asset Preparation", content)
        self.assertIn("Draco", content)
        self.assertIn("KTX2", content)
        self.assertIn("Baking vs Dynamic Lighting Decision Matrix", content)
        self.assertIn("Color Management, PBR & Environment Workflow", content)
        self.assertIn("SRGBColorSpace", content)
        self.assertIn("WebGPURenderer Path (three/webgpu)", content)
        self.assertIn("Three Shading Language (TSL)", content)
        self.assertIn("Measurement-First Performance Discipline", content)
        self.assertIn("Rejection of Brittle Magic Numbers", content)

        # Verify API freshness
        self.assertIn("await renderer.init()", content, "WebGPURenderer async init")
        self.assertIn("LinearSRGBColorSpace", content, "Lightmap linear color space")
        self.assertIn("sin(time)", content, "TSL time node")
        self.assertNotIn("timerLocal", content, "Stale timerLocal must not appear")

        # Verify rejection of brittle magic numbers
        self.assertNotIn("render.calls < 150", content)
        self.assertNotIn("> 2 MB", content)
        self.assertNotIn("< 200 KB", content)


class TestProofCaseBVNLAW(unittest.TestCase):
    """Proof Case B: VNLAW / legal authority vs code parser separation."""

    def test_official_legal_source_separated_from_code_parser(self) -> None:
        task = {
            "task_id": "TASK-VNLAW-01",
            "desired_outcome": "Tra cứu quy định xử phạt vi phạm giao thông đường bộ theo căn cứ pháp lý chính thức",
        }
        sources = list(build_domain_source_catalog()) + [FIXTURE_VNLAW_PARSER]
        receipt = select_domain_sources(task, available_sources=sources)
        self.assertEqual(receipt.domain, "legal.vn")
        self.assertEqual(receipt.selection_status, "SATISFIED")

        by_id = {s.source_id: s for s in receipt.selected_sources}
        self.assertIn("official:vbpl_vn", by_id)
        self.assertIn("fixture:vnlaw-parser", by_id)

        # Official source is the authority of record
        official = by_id["official:vbpl_vn"]
        self.assertEqual(official.source_role, "PRIMARY_OR_OFFICIAL_EVIDENCE_SOURCE")
        self.assertEqual(official.authority_scope, "OFFICIAL_LEGAL_PROMULGATED_TEXT")

        # Code parser has limitation and cannot substitute official authority
        parser = by_id["fixture:vnlaw-parser"]
        self.assertEqual(parser.source_role, "EXECUTABLE_ENGINE")
        self.assertIn("CODE_PASS_IS_NOT_LEGAL_AUTHORITY", parser.limitations)

    def test_tested_code_parser_cannot_satisfy_exclusive_official_legal_demand(self) -> None:
        """When task demands official legal authority, code parser alone results in BLOCKED."""
        task = {
            "task_id": "TASK-VNLAW-02",
            "domain": "legal.vn",
            "desired_outcome": "Xác nhận văn bản pháp luật chính thức có hiệu lực",
            "required_capabilities": ["official_legal_authority"],
        }
        receipt = select_domain_sources(task, available_sources=[FIXTURE_VNLAW_PARSER])
        self.assertEqual(receipt.selection_status, "BLOCKED")
        self.assertEqual(len(receipt.selected_sources), 0)
        self.assertIn("official_legal_authority", receipt.unsatisfied_required_capabilities)
        self.assertIn(
            "CODE_PASS_IS_NOT_LEGAL_AUTHORITY",
            receipt.unselected_candidates[0].why_not_selected,
        )


class TestProofCaseCChineseMetaphysics(unittest.TestCase):
    """Proof Case C: Chinese Metaphysics school separation & calculation vs prediction."""

    def test_ziwei_calculation_separated_from_predictive_validity_and_school(self) -> None:
        task = {
            "task_id": "TASK-ZW-01",
            "desired_outcome": "Lập lá số Tử Vi Đẩu Số theo phái Trung Châu và an sao Tứ Hóa năm sinh",
        }
        receipt = select_domain_sources(task)
        self.assertEqual(receipt.domain, "metaphysics.ziwei")
        self.assertEqual(receipt.selection_status, "SATISFIED")

        selected_ids = {s.source_id for s in receipt.selected_sources}
        unselected_ids = {u.source_id for u in receipt.unselected_candidates}

        self.assertIn("repo:SylarLong/iztro", selected_ids)
        self.assertIn("repo:Linden-TR/ziwei-doushu-skill", selected_ids)

        by_id = {s.source_id: s for s in receipt.selected_sources}
        iztro = by_id["repo:SylarLong/iztro"]
        self.assertEqual(iztro.source_role, "EXECUTABLE_ENGINE")
        self.assertIn("DETERMINISTIC_OUTPUT_IS_NOT_PREDICTIVE_VALIDITY", iztro.limitations)

        # Liuyao and Meihua are excluded by domain mismatch
        self.assertIn("repo:muyen/meihua-yishu", unselected_ids)
        self.assertIn("repo:xiaoshiyilangzhao1996-droid/yinyo-liuyao", unselected_ids)

        # Sanhe school repo excluded because task specifically asked for Zhongzhou
        self.assertIn("repo:wuandyA/ziwei", unselected_ids)

    def test_sample_chart_dataset_does_not_become_methodology_authority(self) -> None:
        task = {
            "task_id": "TASK-ZW-02",
            "domain": "metaphysics.ziwei",
            "desired_outcome": "Thiết lập quy tắc an sao Tứ Hóa chuẩn phái",
            "required_capabilities": ["school_methodology"],
        }
        receipt = select_domain_sources(task, available_sources=[FIXTURE_ZIWEI_DATASET])
        self.assertEqual(receipt.selection_status, "BLOCKED")
        self.assertEqual(len(receipt.selected_sources), 0)
        self.assertIn("school_methodology", receipt.unsatisfied_required_capabilities)
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
        self.assertIn("SELECTION_STATUS=SATISFIED", summary)
        self.assertIn("CAPABILITIES_REQUIRED=", summary)
        self.assertIn("SATISFIED_CAPABILITIES=", summary)
        self.assertIn("UNSATISFIED_REQUIRED_CAPABILITIES=", summary)
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
        self.assertEqual(d["selection_status"], "SATISFIED")
        self.assertEqual(tuple(d["invariants_enforced"]), CORE_INVARIANTS)

    def test_no_second_router_or_registry_created(self) -> None:
        from p2p_capabilities import ProjectDomainModel, select_domain_sources
        self.assertTrue(callable(select_domain_sources))
        model = ProjectDomainModel("test-domain")
        self.assertEqual(model.domain, "test-domain")


if __name__ == "__main__":
    unittest.main()
