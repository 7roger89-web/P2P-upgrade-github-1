from pathlib import Path
import importlib.util


def _load_projector():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "p2p_portable_law_projection.py"
    spec = importlib.util.spec_from_file_location("p2p_portable_law_projection", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_projected_agents_serialize_law_and_oe_gates():
    projector = _load_projector()
    block = projector._agents_block()

    required = (
        "Mandatory prompt serialization contract",
        "ARENA_CHAT_TITLE_FIRST_LINE_V1",
        "<PROJECT> — <bounded task/outcome>",
        "GỬI CHO:",
        "CHAT_TITLE",
        "P2P_LAW_PREFLIGHT",
        "P2P_LAW_SOURCE=<actual source>",
        "OE_GATE",
        "Không bị over engineering chứ?",
        "SIMPLER_PATH",
        "MATERIAL_PROGRESS",
        "NECESSITY",
        "CORE_BEFORE_SUPPORT",
        "SMALLER_VERIFIABLE_SLICE",
        "OE_VERDICT=DO_IT|SKIP_IT|DEFER_UNTIL_NEEDED",
        "NEW_CHAT",
        "SAME_CHAT",
    )
    for marker in required:
        assert marker in block


def test_projector_keeps_full_notebook_and_source_content_sha():
    projector = _load_projector()
    source = Path(__file__).resolve().parents[1] / projector.SOURCE_REL
    text = source.read_text(encoding="utf-8")
    projection = projector._projection_text(Path(__file__).resolve().parents[1])

    assert "SOURCE_CONTENT_SHA256=" in projection
    assert "P2P_SUPREME_OPERATING_LAW_V1" in projection
    assert "RULE 14 — OVER_ENGINEERING_CHECK" in projection
    assert "Không bị over engineering chứ?" in projection
    assert text.lstrip("\ufeff") in projection
