from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / ".p2p" / "system" / "p2p_capabilities" / "fcc_local_bus.py"
SPEC = importlib.util.spec_from_file_location("fcc_local_bus", MODULE_PATH)
assert SPEC and SPEC.loader
bus = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = bus
SPEC.loader.exec_module(bus)


def _admin(*, fallbacks=None, ollama="http://localhost:11434",
           lmstudio="http://localhost:1234/v1",
           llamacpp="http://localhost:8080/v1"):
    return {
        "fields": [
            {"key": "MODEL_FALLBACKS", "value": fallbacks},
            {"key": "OLLAMA_BASE_URL", "value": ollama},
            {"key": "LM_STUDIO_BASE_URL", "value": lmstudio},
            {"key": "LLAMACPP_BASE_URL", "value": llamacpp},
        ]
    }


def test_ollama_payload_becomes_prefixed_candidate():
    payload = {"models": [{"name": "qwen2.5-coder:7b"}, {"model": "llama3.2:3b"}]}
    models = bus._models_from_payload("ollama", payload, "http://127.0.0.1:11434")
    assert [item.model_ref for item in models] == [
        "ollama/qwen2.5-coder:7b",
        "ollama/llama3.2:3b",
    ]
    assert models[0].score > models[1].score


def test_openai_compatible_payload_becomes_candidates():
    payload = {"data": [{"id": "deepseek-coder"}, {"id": "generic"}]}
    lm = bus._models_from_payload("lmstudio", payload, "http://localhost:1234/v1")
    cpp = bus._models_from_payload("llamacpp", payload, "http://localhost:8080/v1")
    assert lm[0].model_ref == "lmstudio/deepseek-coder"
    assert cpp[0].model_ref == "llamacpp/deepseek-coder"


def test_non_loopback_provider_url_is_rejected():
    gate = bus.assess_local_only_runtime(
        selected_model_ref="ollama/qwen",
        admin_payload=_admin(ollama="https://ollama.example.com"),
    )
    assert gate.safe is False
    assert gate.status == "FCC_LOCAL_PROVIDER_URL_NOT_LOOPBACK"


def test_cloud_fallback_blocks_local_lane():
    gate = bus.assess_local_only_runtime(
        selected_model_ref="ollama/qwen",
        admin_payload=_admin(fallbacks="open_router/free"),
    )
    assert gate.safe is False
    assert gate.status == "FCC_FALLBACK_EGRESS_UNSAFE"


def test_all_local_fallbacks_are_allowed_when_urls_loopback():
    gate = bus.assess_local_only_runtime(
        selected_model_ref="ollama/qwen",
        admin_payload=_admin(fallbacks="lmstudio/devstral,llamacpp/qwen"),
    )
    assert gate.safe is True
    assert gate.status == "LOCAL_ONLY_RUNTIME_SAFE"
    assert gate.fallbacks == ("lmstudio/devstral", "llamacpp/qwen")


def test_missing_runtime_fallback_field_fails_closed():
    gate = bus.assess_local_only_runtime(
        selected_model_ref="ollama/qwen",
        admin_payload={"fields": [{"key": "OLLAMA_BASE_URL", "value": "http://localhost:11434"}]},
    )
    assert gate.safe is False
    assert gate.status == "FCC_RUNTIME_CONFIG_UNVERIFIED"


def test_blank_fallback_is_equivalent_to_no_fallback():
    gate = bus.assess_local_only_runtime(
        selected_model_ref="lmstudio/devstral",
        admin_payload=_admin(fallbacks=""),
    )
    assert gate.safe is True
    assert gate.fallbacks == ()


def test_model_ranking_pushes_obvious_cloud_label_down():
    local = bus._candidate("ollama", "qwen2.5-coder:7b", "http://localhost:11434")
    cloud = bus._candidate("ollama", "qwen-coder-cloud", "http://localhost:11434")
    assert local.score > cloud.score


def test_local_ref_validation():
    assert bus.is_local_model_ref("ollama/qwen")
    assert bus.is_local_model_ref("lmstudio/devstral")
    assert bus.is_local_model_ref("llamacpp/qwen")
    assert not bus.is_local_model_ref("open_router/free")
    assert not bus.is_local_model_ref("ollama/")


def test_dotenv_port_resolution(monkeypatch, tmp_path):
    env_file = tmp_path / "fcc.env"
    env_file.write_text("PORT=9123\n", encoding="utf-8")
    monkeypatch.setenv("FCC_ENV_FILE", str(env_file))
    monkeypatch.delenv("PORT", raising=False)
    assert bus.configured_fcc_port() == 9123
    monkeypatch.setenv("PORT", "9456")
    assert bus.configured_fcc_port() == 9456
