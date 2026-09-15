"""Strict loopback local-model discovery and FCC runtime safety gate.

This module is intentionally small and stdlib-only.  It does NOT introduce a
new P2P router.  It discovers model servers on loopback and verifies the
*running* Free Claude Code server's effective fallback configuration before a
P2P task may use a local-only lane.

Why the runtime gate exists:
FCC direct provider/model references still inherit MODEL_FALLBACKS.  A request
that starts at ``ollama/foo`` can therefore fall through to another configured
provider.  P2P must not call a lane "local-only" unless every reachable FCC
fallback target is also a loopback-backed local provider.

The accepted local providers in this slice are:
- Ollama      -> ollama/<tag>
- LM Studio   -> lmstudio/<model>
- llama.cpp   -> llamacpp/<model>

No LAN discovery, cloud provider discovery, credential reads, config mutation,
or silent fallback is performed here.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import ProxyHandler, Request, build_opener

LOCAL_PROVIDER_PREFIXES = ("ollama", "lmstudio", "llamacpp")
LOCAL_PROVIDER_CONFIG_KEYS = {
    "ollama": "OLLAMA_BASE_URL",
    "lmstudio": "LM_STUDIO_BASE_URL",
    "llamacpp": "LLAMACPP_BASE_URL",
}
LOCAL_PROVIDER_DEFAULTS = {
    "ollama": "http://127.0.0.1:11434",
    "lmstudio": "http://127.0.0.1:1234/v1",
    "llamacpp": "http://127.0.0.1:8080/v1",
}
FCC_DEFAULT_PORT = 8082
FCC_ADMIN_CONFIG_PATH = "/admin/api/config"
FCC_ENV_FILENAME = ".env"

# Prefer coding-specialized families. This is only a deterministic tie-breaker;
# availability and privacy gates are stronger than the ranking.
_MODEL_KEYWORDS = (
    ("coder", 60),
    ("codestral", 55),
    ("devstral", 55),
    ("code", 50),
    ("qwen", 35),
    ("deepseek", 35),
    ("glm", 25),
    ("llama", 20),
    ("mistral", 15),
)


@dataclass(frozen=True)
class LocalModelCandidate:
    provider: str
    model: str
    model_ref: str
    base_url: str
    score: int


@dataclass(frozen=True)
class LocalOnlyGate:
    safe: bool
    status: str
    selected_model_ref: str | None
    fallbacks: tuple[str, ...] = ()
    checked_provider_urls: tuple[str, ...] = ()
    detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "safe": self.safe,
            "status": self.status,
            "selected_model_ref": self.selected_model_ref,
            "fallbacks": list(self.fallbacks),
            "checked_provider_urls": list(self.checked_provider_urls),
            "detail": self.detail,
        }


def _loopback_url(url: str) -> bool:
    try:
        parsed = urlparse(str(url).strip())
    except ValueError:
        return False
    return (
        parsed.scheme in ("http", "https")
        and parsed.hostname in ("127.0.0.1", "localhost", "::1")
    )


def _json_get(url: str, *, timeout: float) -> Any:
    """GET JSON without inheriting HTTP(S)_PROXY.

    The local-bus probe must never escape through a corporate/user proxy just
    because the target loopback service is down.
    """
    if not _loopback_url(url):
        raise ValueError("NON_LOOPBACK_URL")
    opener = build_opener(ProxyHandler({}))
    request = Request(url, headers={"Accept": "application/json", "User-Agent": "P2P-FCC-Local-Bus/1"})
    with opener.open(request, timeout=timeout) as response:
        data = response.read(2_000_000)
    return json.loads(data.decode("utf-8"))


def _clean_model_id(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    model = value.strip()
    if not model or len(model) > 512 or any(ch in model for ch in "\r\n\x00"):
        return None
    return model


def _score_model(model: str) -> int:
    lowered = model.casefold()
    score = 0
    for keyword, weight in _MODEL_KEYWORDS:
        if keyword in lowered:
            score += weight
    # Obvious remote/cloud labels lose the tie. This is not a proof of local
    # compute; the hard guarantee in this slice is loopback transport.
    if "cloud" in lowered or "remote" in lowered:
        score -= 100
    return score


def _candidate(provider: str, model: str, base_url: str) -> LocalModelCandidate:
    return LocalModelCandidate(
        provider=provider,
        model=model,
        model_ref=f"{provider}/{model}",
        base_url=base_url,
        score=_score_model(model),
    )


def _models_from_payload(provider: str, payload: Any, base_url: str) -> list[LocalModelCandidate]:
    models: list[str] = []
    if provider == "ollama" and isinstance(payload, Mapping):
        raw = payload.get("models")
        if isinstance(raw, list):
            for entry in raw:
                if not isinstance(entry, Mapping):
                    continue
                model = _clean_model_id(entry.get("name") or entry.get("model"))
                if model:
                    models.append(model)
    elif provider in ("lmstudio", "llamacpp") and isinstance(payload, Mapping):
        raw = payload.get("data")
        if isinstance(raw, list):
            for entry in raw:
                if not isinstance(entry, Mapping):
                    continue
                model = _clean_model_id(entry.get("id"))
                if model:
                    models.append(model)

    unique = list(dict.fromkeys(models))
    return [_candidate(provider, model, base_url) for model in unique]


def _model_endpoint(provider: str, base_url: str) -> str:
    root = base_url.rstrip("/")
    if provider == "ollama":
        return f"{root}/api/tags"
    return f"{root}/models"


def discover_local_models(
    *,
    provider_urls: Mapping[str, str] | None = None,
    timeout: float = 1.5,
) -> tuple[list[LocalModelCandidate], list[dict[str, Any]]]:
    """Probe loopback model servers and return ranked models plus observations."""
    urls = dict(LOCAL_PROVIDER_DEFAULTS)
    if provider_urls:
        urls.update({str(k): str(v) for k, v in provider_urls.items()})

    candidates: list[LocalModelCandidate] = []
    observations: list[dict[str, Any]] = []
    for provider in LOCAL_PROVIDER_PREFIXES:
        base_url = urls.get(provider, "").strip()
        if not _loopback_url(base_url):
            observations.append(
                {
                    "provider": provider,
                    "status": "BLOCKED_NON_LOOPBACK_URL",
                    "base_url": base_url,
                    "models": 0,
                }
            )
            continue
        endpoint = _model_endpoint(provider, base_url)
        try:
            payload = _json_get(endpoint, timeout=timeout)
            found = _models_from_payload(provider, payload, base_url)
        except (OSError, HTTPError, URLError, ValueError, json.JSONDecodeError) as exc:
            observations.append(
                {
                    "provider": provider,
                    "status": "UNAVAILABLE",
                    "base_url": base_url,
                    "models": 0,
                    "detail": type(exc).__name__,
                }
            )
            continue
        candidates.extend(found)
        observations.append(
            {
                "provider": provider,
                "status": "READY" if found else "NO_MODELS",
                "base_url": base_url,
                "models": len(found),
            }
        )

    candidates.sort(key=lambda item: (-item.score, item.provider, item.model.casefold()))
    return candidates, observations


def select_best_local_model(candidates: list[LocalModelCandidate]) -> LocalModelCandidate | None:
    return candidates[0] if candidates else None


def is_local_model_ref(model_ref: str) -> bool:
    provider, sep, model = str(model_ref or "").strip().partition("/")
    return bool(sep and model.strip() and provider in LOCAL_PROVIDER_PREFIXES)


def parse_fallbacks(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return tuple(part.strip() for part in value.split(",") if part.strip())
    if isinstance(value, (tuple, list)):
        return tuple(str(part).strip() for part in value if str(part).strip())
    return (str(value).strip(),) if str(value).strip() else ()


def _admin_field(payload: Mapping[str, Any], key: str) -> tuple[bool, object]:
    fields = payload.get("fields")
    if not isinstance(fields, list):
        return False, None
    for item in fields:
        if isinstance(item, Mapping) and item.get("key") == key:
            return True, item.get("value")
    return False, None


def provider_urls_from_admin(payload: Mapping[str, Any]) -> dict[str, str]:
    result: dict[str, str] = {}
    for provider, key in LOCAL_PROVIDER_CONFIG_KEYS.items():
        present, value = _admin_field(payload, key)
        if present and isinstance(value, str) and value.strip():
            result[provider] = value.strip()
        else:
            result[provider] = LOCAL_PROVIDER_DEFAULTS[provider]
    return result


def assess_local_only_runtime(
    *,
    selected_model_ref: str,
    admin_payload: Mapping[str, Any],
) -> LocalOnlyGate:
    """Fail closed unless the running FCC config can only fall back to loopback locals."""
    if not is_local_model_ref(selected_model_ref):
        return LocalOnlyGate(False, "PRIMARY_NOT_LOCAL", selected_model_ref)

    present, fallback_value = _admin_field(admin_payload, "MODEL_FALLBACKS")
    if not present:
        return LocalOnlyGate(
            False,
            "FCC_RUNTIME_CONFIG_UNVERIFIED",
            selected_model_ref,
            detail="MODEL_FALLBACKS missing from running FCC admin config",
        )

    fallbacks = parse_fallbacks(fallback_value)
    routes = (selected_model_ref, *fallbacks)
    nonlocal_refs = tuple(ref for ref in routes if not is_local_model_ref(ref))
    if nonlocal_refs:
        return LocalOnlyGate(
            False,
            "FCC_FALLBACK_EGRESS_UNSAFE",
            selected_model_ref,
            fallbacks=fallbacks,
            detail="non-local model refs: " + ", ".join(nonlocal_refs),
        )

    urls = provider_urls_from_admin(admin_payload)
    providers = tuple(dict.fromkeys(ref.split("/", 1)[0] for ref in routes))
    checked_urls: list[str] = []
    for provider in providers:
        url = urls.get(provider, "")
        checked_urls.append(f"{provider}={url}")
        if not _loopback_url(url):
            return LocalOnlyGate(
                False,
                "FCC_LOCAL_PROVIDER_URL_NOT_LOOPBACK",
                selected_model_ref,
                fallbacks=fallbacks,
                checked_provider_urls=tuple(checked_urls),
                detail=f"{provider} resolves to {url}",
            )

    return LocalOnlyGate(
        True,
        "LOCAL_ONLY_RUNTIME_SAFE",
        selected_model_ref,
        fallbacks=fallbacks,
        checked_provider_urls=tuple(checked_urls),
    )


def _dotenv_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return values
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        values[key] = value
    return values


def managed_env_path(environ: Mapping[str, str] | None = None) -> Path:
    env = os.environ if environ is None else environ
    override = str(env.get("FCC_ENV_FILE", "")).strip()
    if override:
        return Path(override).expanduser()
    return Path.home() / ".fcc" / FCC_ENV_FILENAME


def configured_fcc_port(environ: Mapping[str, str] | None = None) -> int:
    env = os.environ if environ is None else environ
    process_value = str(env.get("PORT", "")).strip()
    file_value = _dotenv_values(managed_env_path(env)).get("PORT", "").strip()
    raw = process_value or file_value or str(FCC_DEFAULT_PORT)
    try:
        port = int(raw)
    except ValueError as exc:
        raise ValueError("FCC_PORT_INVALID") from exc
    if port < 1 or port > 65535:
        raise ValueError("FCC_PORT_INVALID")
    return port


def fetch_running_fcc_admin_config(*, port: int | None = None, timeout: float = 2.0) -> dict[str, Any]:
    resolved_port = configured_fcc_port() if port is None else int(port)
    payload = _json_get(
        f"http://127.0.0.1:{resolved_port}{FCC_ADMIN_CONFIG_PATH}",
        timeout=timeout,
    )
    if not isinstance(payload, dict):
        raise ValueError("FCC_ADMIN_CONFIG_INVALID")
    # The runtime API must expose the field manifest; otherwise we cannot prove
    # the effective fallback policy and must fail closed.
    if not isinstance(payload.get("fields"), list):
        raise ValueError("FCC_ADMIN_CONFIG_INVALID")
    return payload
