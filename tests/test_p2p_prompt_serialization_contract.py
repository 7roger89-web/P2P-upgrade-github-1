from pathlib import Path
import importlib.util
import re


def _flat(text: str) -> str:
    return re.sub(r"\\s+", " ", text).strip().lower()


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

    assert "Do not treat every negative answer as failure" in block
    assert "if the answer is weak or negative" not in block


def test_downstream_oe_guidance_matches_directional_canonical_semantics():
    root = Path(__file__).resolve().parents[1]
    agents = (root / "AGENTS.md").read_text(encoding="utf-8")
    runtime_init = (root / ".p2p/system/p2p_capabilities/__init__.py").read_text(encoding="utf-8")
    shield = (root / "docs/p2p-development/P2P-SHIELD-PLAN.md").read_text(encoding="utf-8")

    for text in (agents, runtime_init, shield):
        assert "weak or negative answer means" not in text
        assert "Any weak answer means" not in text

    assert "SIMPLER_PATH=YES" in agents
    assert "SMALLER_VERIFIABLE_SLICE=YES" in agents
    assert "MATERIAL_PROGRESS=NO" in agents
    assert "Do not treat every literal negative answer as failure" in agents

    assert "SIMPLER_PATH=YES or SMALLER_VERIFIABLE_SLICE=YES" in runtime_init
    assert "MATERIAL_PROGRESS=NO, NECESSITY=NO, or CORE_BEFORE_SUPPORT=NO" in runtime_init
    assert "Do not treat every negative answer as failure" in runtime_init

    assert "YES on questions 1 and 5 is a" in shield
    assert "Questions 2–4 require YES to proceed" in shield
    assert "Do not treat every literal negative answer as failure" in shield


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
