#!/usr/bin/env python3
"""Minimal probe for disposable/free model providers.

No third-party dependencies. API keys are read only from environment variables
and are never printed. Chat Completions and Responses are tested separately so
a chat-only success is never mistaken for Codex/Responses compatibility.
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
    protocols: tuple[str, ...] = ("chat",)
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
        # Current free/promotional candidates. Order prefers models already
        # live-proven on the Owner account before documentation-only candidates.
        free_candidates=("mimo-v2.5", "hy3", "qwen3.8-flash"),
        protocols=("chat", "responses"),
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
    def __init__(self, message: str, http_status: int | None = None) -> None:
        super().__init__(message)
        self.http_status = http_status


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
        "User-Agent": "p2p-free-model-probe/0.2",
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
        raise ProbeError(f"HTTP {exc.code}: {detail}", http_status=exc.code) from exc
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


def candidate_models(
    preset: ProviderPreset,
    available_models: list[str] | None,
    env: dict[str, str] | None = None,
) -> list[str]:
    env = os.environ if env is None else env
    override = env.get(preset.model_env)

    if available_models:
        by_lower = {item.lower(): item for item in available_models}
        if override:
            matched = by_lower.get(override.lower())
            return [matched] if matched else []
        return [
            by_lower[candidate.lower()]
            for candidate in preset.free_candidates
            if candidate.lower() in by_lower
        ]

    if override:
        return [override]
    return list(preset.free_candidates)


def choose_model(
    preset: ProviderPreset,
    available_models: list[str] | None,
    env: dict[str, str] | None = None,
) -> str | None:
    candidates = candidate_models(preset, available_models, env)
    return candidates[0] if candidates else None


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


def extract_responses_text(payload: dict[str, Any]) -> str:
    output = payload.get("output")
    if not isinstance(output, list):
        return ""
    chunks: list[str] = []
    for item in output:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if (
                isinstance(block, dict)
                and block.get("type") == "output_text"
                and isinstance(block.get("text"), str)
            ):
                chunks.append(block["text"])
    return "".join(chunks)


def _live_call(
    preset: ProviderPreset,
    model: str,
    protocol: str,
    key: str,
    timeout: float,
) -> str:
    if protocol == "chat":
        payload = _request_json(
            "POST",
            f"{preset.base_url.rstrip('/')}/chat/completions",
            key,
            payload={
                "model": model,
                "messages": [
                    {"role": "user", "content": "Reply with exactly: P2P_PROBE_OK"}
                ],
                "temperature": 0,
                "max_tokens": 32,
                "stream": False,
            },
            timeout=timeout,
        )
        return extract_chat_text(payload).strip()

    if protocol == "responses":
        payload = _request_json(
            "POST",
            f"{preset.base_url.rstrip('/')}/responses",
            key,
            payload={
                "model": model,
                "input": "Reply with exactly: P2P_PROBE_OK",
                "max_output_tokens": 32,
                "stream": False,
            },
            timeout=timeout,
        )
        return extract_responses_text(payload).strip()

    raise ValueError(f"unknown protocol: {protocol}")


def probe_provider(
    preset: ProviderPreset,
    live: bool,
    timeout: float,
    protocol: str = "chat",
) -> dict[str, Any]:
    key = os.environ.get(preset.key_env)
    if not key:
        return {
            "provider": preset.name,
            "protocol": protocol,
            "status": "MISSING_KEY",
            "key_env": preset.key_env,
        }

    if protocol not in preset.protocols:
        return {
            "provider": preset.name,
            "protocol": protocol,
            "status": "UNSUPPORTED_PROTOCOL",
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
                "protocol": protocol,
                "status": "DISCOVERY_FAIL",
                "detail": str(exc),
                "elapsed_ms": round((time.monotonic() - started) * 1000),
            }

    models = candidate_models(preset, available_models)
    if not models:
        return {
            "provider": preset.name,
            "protocol": protocol,
            "status": "NO_ALLOWLISTED_MODEL",
            "discovery": discovery,
            "elapsed_ms": round((time.monotonic() - started) * 1000),
        }

    if not live:
        return {
            "provider": preset.name,
            "protocol": protocol,
            "status": "READY",
            "model": models[0],
            "candidates": models,
            "discovery": discovery,
            "elapsed_ms": round((time.monotonic() - started) * 1000),
        }

    explicit_override = bool(os.environ.get(preset.model_env))
    failures: list[dict[str, Any]] = []
    for index, model in enumerate(models):
        try:
            text = _live_call(preset, model, protocol, key, timeout)
            status = f"{protocol.upper()}_PASS" if text else "EMPTY_RESPONSE"
            return {
                "provider": preset.name,
                "protocol": protocol,
                "status": status,
                "model": model,
                "text": text[:120],
                "discovery": discovery,
                "attempts": index + 1,
                "elapsed_ms": round((time.monotonic() - started) * 1000),
            }
        except ProbeError as exc:
            failures.append(
                {"model": model, "http_status": exc.http_status, "detail": str(exc)}
            )
            # A 400 can be model-specific (quota, endpoint incompatibility, or
            # unsupported parameters). With no explicit override, try the next
            # allowlisted free candidate. Do not retry auth/network failures.
            if explicit_override or exc.http_status != 400:
                break

    return {
        "provider": preset.name,
        "protocol": protocol,
        "status": f"{protocol.upper()}_CALL_FAIL",
        "model": failures[-1]["model"] if failures else models[0],
        "failures": failures,
        "discovery": discovery,
        "attempts": len(failures),
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
        "--protocol",
        choices=("chat", "responses"),
        default="chat",
        help="Protocol to probe (default: chat). Responses is currently enabled for B.AI.",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Send one tiny model request. Without this flag only readiness is checked.",
    )
    parser.add_argument(
        "--require",
        type=int,
        default=2,
        help="Minimum READY/live-pass providers required for exit code 0 (default: 2).",
    )
    parser.add_argument("--timeout", type=float, default=25.0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    results = [
        probe_provider(
            PRESETS[name],
            live=args.live,
            timeout=args.timeout,
            protocol=args.protocol,
        )
        for name in args.providers
    ]
    for result in results:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))

    accepted = (
        {f"{args.protocol.upper()}_PASS"} if args.live else {"READY"}
    )
    passed = sum(result.get("status") in accepted for result in results)
    verdict = "PASS" if passed >= args.require else "BLOCKED"
    print(
        json.dumps(
            {
                "p2p_free_model_pool_01": verdict,
                "mode": f"{'live' if args.live else 'readiness'}:{args.protocol}",
                "passed": passed,
                "required": args.require,
            },
            sort_keys=True,
        )
    )
    return 0 if verdict == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
