from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APPENDIX = ROOT / "docs" / "p2p-development" / "GITHUB-RESEARCH-APPENDIX.md"
BRIDGE = ROOT / ".p2p" / "system" / "p2p_capabilities" / "code_intelligence_bridge.py"


def test_appendix_reconciles_already_implemented_research() -> None:
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
    ):
        assert durable_marker in text


def test_appendix_does_not_promote_research_inbox_to_authority() -> None:
    text = APPENDIX.read_text(encoding="utf-8")
    assert "discovery inbox, not an adoption ledger" in text
    assert "durable GitHub state wins" in text
    assert "not a replacement ledger" in text
    assert "second router" in text
    assert "second truth" in text


def test_appendix_prioritizes_only_remaining_gap() -> None:
    text = APPENDIX.read_text(encoding="utf-8")
    assert "NEXT_CORE_SLICE=CODE_INTELLIGENCE_STRUCTURAL_EVIDENCE" in text
    assert "DeusData/codebase-memory-mcp" in text
    assert "v0.11.0" in text
    assert "8972ea69c6ad94b1ef1d4ffbf0a92d78d2db1798" in text


def test_code_intelligence_bridge_keeps_external_graph_non_authoritative() -> None:
    text = BRIDGE.read_text(encoding="utf-8")
    assert "NON_AUTHORITATIVE_STRUCTURAL_EVIDENCE" in text
    assert "index_repository" in text
    assert "manage_adr" in text
    assert "standing_process_started_by_bridge" in text
    assert "index_created_by_bridge" in text
