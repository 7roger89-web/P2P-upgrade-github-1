from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
APPENDIX = ROOT / "docs" / "p2p-development" / "GITHUB-RESEARCH-APPENDIX.md"
BRIDGE = ROOT / ".p2p" / "system" / "p2p_capabilities" / "code_intelligence_bridge.py"
NATIVE_QUALITY = ROOT / ".p2p" / "system" / "p2p_capabilities" / "quality_intelligence.py"
NATIVE_REALPATH = ROOT / ".p2p" / "system" / "p2p_capabilities" / "native_code_impact.py"


class GithubResearchAppendixTests(unittest.TestCase):
    def test_appendix_reconciles_already_implemented_research(self) -> None:
        text = APPENDIX.read_text(encoding="utf-8")
        for durable_marker in (
            "PR #169",
            "PR #170",
            "PR #171",
            "PR #175",
            "PR #173",
            "PR #153",
            "PR #159",
            "PR #152",
            "PR #162",
            "PR #178",
            "PR #182",
            "PR #185",
        ):
            with self.subTest(durable_marker=durable_marker):
                self.assertIn(durable_marker, text)

    def test_appendix_does_not_promote_research_inbox_to_authority(self) -> None:
        text = APPENDIX.read_text(encoding="utf-8")
        self.assertIn("discovery inbox, not an adoption ledger", text)
        self.assertIn("durable GitHub state wins", text)
        self.assertIn("not a replacement ledger", text)
        self.assertIn("second router", text)
        self.assertIn("second truth", text)

    def test_appendix_reconciles_external_graph_against_proven_native_code_impact(self) -> None:
        text = APPENDIX.read_text(encoding="utf-8")
        native = NATIVE_QUALITY.read_text(encoding="utf-8")
        realpath = NATIVE_REALPATH.read_text(encoding="utf-8")
        self.assertIn("NATIVE_CAPABILITY_FIRST=YES", text)
        self.assertIn("NATIVE_CODE_IMPACT_REALPATH_PROVEN=YES", text)
        self.assertIn("EXTERNAL_CODE_INTELLIGENCE_ROLE=OPTIONAL_EXTENSION", text)
        self.assertIn(
            "NEXT_CORE_SLICE=NO_NEW_CODE_INTELLIGENCE_INFRASTRUCTURE_UNTIL_NATIVE_GAP_OBSERVED",
            text,
        )
        self.assertIn("DeusData/codebase-memory-mcp", text)
        self.assertIn("v0.11.0", text)
        self.assertIn("8972ea69c6ad94b1ef1d4ffbf0a92d78d2db1798", text)
        self.assertIn("Code-impact evidence contract", native)
        self.assertIn("def affected_surface", native)
        self.assertIn("impact_unknown", native)
        self.assertIn("BASELINE_UNION_CURRENT_NATIVE_AST", realpath)
        self.assertIn("external_extension_recommended", realpath)

    def test_code_intelligence_bridge_keeps_external_graph_native_first_non_authoritative(self) -> None:
        text = BRIDGE.read_text(encoding="utf-8")
        self.assertIn("NATIVE_FIRST_FALLBACK", text)
        self.assertIn("native_gap_reason", text)
        self.assertIn("NON_AUTHORITATIVE_STRUCTURAL_EVIDENCE", text)
        self.assertIn("index_repository", text)
        self.assertIn("manage_adr", text)
        self.assertIn("standing_process_started_by_bridge", text)
        self.assertIn("index_created_by_bridge", text)


if __name__ == "__main__":
    unittest.main()
