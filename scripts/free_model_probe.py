#!/usr/bin/env python3
"""Minimal probe for disposable/free OpenAI-compatible model providers.

No third-party dependencies. API keys are read only from environment variables
and are never printed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProviderPreset:
    name: str
    base_url: str
    key_env: str
    model_env: str
    free_candidates: tuple[str, ...]
    supports_model_discovery: bool = True


PRESETS: dict[str, ProviderPreset] = {
    "cline": ProviderPreset(
        name="cline",
        base_url="https://api.cline.bot/api/v1",
        key_env="CLINE_API_KEY",
        model_env="CLINE_MODEL",
        free_candidates=("minimax/minimax-m2.5",),
        supports_model_discovery=False,
    ),
    "bai": ProviderPreset(
        name="bai",
        base_url="https://api.b.ai/v1",
        key_env="BAI_API_KEY",
        model_env="BAI_MODEL",
        free_candidates=("glm-5.3-flash", "mimo-v2.5", "hy3"),
    ),
    "amd": ProviderPreset(
        name="amd",
        base_url="https://developer.amd.com.cn/radeon/api/v1",
        key_env="RADEON_API_KEY",
        model_env="RADEON_MODEL",
        free_candidates=("DeepSeek-V4-Flash", "DeepSeek-V4-Flash-Vision-Exp"),
    ),
}


class ProbeError(RuntimeError):
    pass


def _request_json(
    method: str,
    url: str,
    api_key: str,
    payload: dict[str, Any] | None = None,
    timeout: float = 25.0,
) -> dict[str, Any]:
    data = None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
        "User-Agent": "p2p-free-model-probe/0.1",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(body)
        except json.JSONDecodeError:
            detail = body[:500]
        raise ProbeError(f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise ProbeError(f"network error: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise ProbeError("provider returned non-JSON response") from exc


def extract_model_ids(payload: dict[str, Any]) -> list[str]:
    data = payload.get("data")
    if not isinstance(data, list):
        return []
    ids: list[str] = []
    for item in data:
        if isinstance(item, dict) and isinstance(item.get("id"), str):
            ids.append(item["id"])
    return ids


def choose_model(
    preset: ProviderPreset,
    available_models: list[str] | None,
    env: dict[str, str] | None = None,
) -> str | None:
    env = os.environ if env is None else env
    override = env.get(preset.model_env)
    if override:
        if available_models:
            by_lower = {item.lower(): item for item in available_models}
            return by_lower.get(override.lower())
        return override

    if available_models:
        by_lower = {item.lower(): item for item in available_models}
        for candidate in preset.free_candidates:
            if candidate.lower() in by_lower:
                return by_lower[candidate.lower()]
        return None

    return preset.free_candidates[0] if preset.free_candidates else None


def extract_chat_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0]
    if not isinstance(first, dict):
        return ""
    message = first.get("message")
    if not isinstance(message, dict):
        return ""
    content = message.get("content")
    return content if isinstance(content, str) else ""


def probe_provider(preset: ProviderPreset, live: bool, timeout: float) -> dict[str, Any]:
    key = os.environ.get(preset.key_env)
    if not key:
        return {
            "provider": preset.name,
            "status": "MISSING_KEY",
            "key_env": preset.key_env,
        }

    started = time.monotonic()
    available_models: list[str] | None = None
    discovery = "SKIPPED"

    if preset.supports_model_discovery:
        try:
            model_payload = _request_json(
                "GET", f"{preset.base_url.rstrip('/')}/models", key, timeout=timeout
            )
            available_models = extract_model_ids(model_payload)
            discovery = f"OK:{len(available_models)}"
        except ProbeError as exc:
            return {
                "provider": preset.name,
                "status": "DISCOVERY_FAIL",
                "detail": str(exc),
                "elapsed_ms": round((time.monotonic() - started) * 1000),
            }

    model = choose_model(preset, available_models)
    if not model:
        return {
            "provider": preset.name,
            "status": "NO_ALLOWLISTED_MODEL",
            "discovery": discovery,
            "elapsed_ms": round((time.monotonic() - started) * 1000),
        }

    if not live:
        return {
            "provider": preset.name,
            "status": "READY",
            "model": model,
            "discovery": discovery,
            "elapsed_ms": round((time.monotonic() - started) * 1000),
        }

    try:
        payload = _request_json(
            "POST",
            f"{preset.base_url.rstrip('/')}/chat/completions",
            key,
            payload={
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": "Reply with exactly: P2P_PROBE_OK",
                    }
                ],
                "temperature": 0,
                "max_tokens": 32,
                "stream": False,
            },
            timeout=timeout,
        )
        text = extract_chat_text(payload).strip()
        return {
            "provider": preset.name,
            "status": "PASS" if text else "EMPTY_RESPONSE",
            "model": model,
            "text": text[:120],
            "discovery": discovery,
            "elapsed_ms": round((time.monotonic() - started) * 1000),
        }
    except ProbeError as exc:
        return {
            "provider": preset.name,
            "status": "CALL_FAIL",
            "model": model,
            "detail": str(exc),
            "discovery": discovery,
            "elapsed_ms": round((time.monotonic() - started) * 1000),
        }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Probe Cline, B.AI and AMD Radeon free-model endpoints."
    )
    parser.add_argument(
        "--providers",
        nargs="+",
        choices=sorted(PRESETS),
        default=sorted(PRESETS),
        help="Providers to probe (default: all).",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help=(
            "Send one tiny chat completion. Without this flag only "
            "auth/model readiness is checked."
        ),
    )
    parser.add_argument(
        "--require",
        type=int,
        default=2,
        help="Minimum READY/PASS providers required for exit code 0 (default: 2).",
    )
    parser.add_argument("--timeout", type=float, default=25.0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    results = [
        probe_provider(PRESETS[name], live=args.live, timeout=args.timeout)
        for name in args.providers
    ]
    for result in results:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))

    accepted = {"PASS"} if args.live else {"READY"}
    passed = sum(result.get("status") in accepted for result in results)
    verdict = "PASS" if passed >= args.require else "BLOCKED"
    print(
        json.dumps(
            {
                "p2p_free_model_pool_01": verdict,
                "mode": "live" if args.live else "readiness",
                "passed": passed,
                "required": args.require,
            },
            sort_keys=True,
        )
    )
    return 0 if verdict == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
