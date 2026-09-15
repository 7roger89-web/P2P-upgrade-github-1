#!/usr/bin/env python3
"""Fail-closed guard and beginner bootstrap for the P2P Hermes essential stack.

This module does not deploy anything by itself. It creates a local .env with
random secrets and validates the pinned, localhost-only compose contract.
"""

from __future__ import annotations

import argparse
import json
import secrets
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
STACK_DIR = REPO_ROOT / "deployments" / "hermes-essential-stack"
COMPOSE_PATH = STACK_DIR / "docker-compose.yml"
WORKSPACE_DOCKERFILE_PATH = STACK_DIR / "Dockerfile.workspace"
ENV_EXAMPLE_PATH = STACK_DIR / ".env.example"
DEFAULT_ENV_PATH = STACK_DIR / ".env"

WORKSPACE_COMMIT = "15fa9cd706f5c04e4db288fb958e21d10fc776da"
WORKSPACE_PNPM = "9.15.9"
EXPECTED = {
    "hermes": "nousresearch/hermes-agent:v2026.9.14",
    "workspace": f"hermes-workspace:v2.3.0@{WORKSPACE_COMMIT}",
    "repomix": "repomix@1.18.0",
    "tokscale": "tokscale@4.16.0",
}
SECRET_KEYS = (
    "API_SERVER_KEY",
    "HERMES_DASHBOARD_BASIC_AUTH_PASSWORD",
    "HERMES_DASHBOARD_BASIC_AUTH_SECRET",
    "HERMES_PASSWORD",
)
PLACEHOLDERS = {
    "__GENERATE_API_SERVER_KEY__",
    "__GENERATE_DASHBOARD_PASSWORD__",
    "__GENERATE_DASHBOARD_SECRET__",
    "__GENERATE_WORKSPACE_PASSWORD__",
}


class StackContractError(RuntimeError):
    pass


def parse_env(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def _secret() -> str:
    return secrets.token_urlsafe(48)


def render_env(example_text: str) -> str:
    replacements = {
        "__GENERATE_API_SERVER_KEY__": _secret(),
        "__GENERATE_DASHBOARD_PASSWORD__": _secret(),
        "__GENERATE_DASHBOARD_SECRET__": _secret(),
        "__GENERATE_WORKSPACE_PASSWORD__": _secret(),
    }
    rendered = example_text
    for token, value in replacements.items():
        rendered = rendered.replace(token, value)
    return rendered


def validate_env(text: str, *, allow_placeholders: bool = False) -> dict[str, object]:
    env = parse_env(text)
    missing = [key for key in SECRET_KEYS if key not in env]
    if missing:
        raise StackContractError(f"ENV_MISSING_KEYS:{','.join(missing)}")
    if env.get("HERMES_DASHBOARD_BASIC_AUTH_USERNAME", "").strip() == "":
        raise StackContractError("ENV_DASHBOARD_USERNAME_REQUIRED")

    values = [env[key] for key in SECRET_KEYS]
    if allow_placeholders:
        bad = [value for value in values if not value]
    else:
        bad = [value for value in values if not value or value in PLACEHOLDERS or len(value) < 32]
    if bad:
        raise StackContractError("ENV_SECRET_NOT_READY")
    if not allow_placeholders and len(set(values)) != len(values):
        raise StackContractError("ENV_SECRETS_MUST_BE_DISTINCT")
    if env.get("P2P_ENABLE_HINDSIGHT", "NO") not in {"NO", "YES"}:
        raise StackContractError("ENV_HINDSIGHT_GATE_INVALID")
    if env.get("P2P_ENABLE_HINDSIGHT") == "YES" and not env.get("HINDSIGHT_API_KEY"):
        raise StackContractError("ENV_HINDSIGHT_KEY_REQUIRED_WHEN_ENABLED")
    budget = env.get("REPOMIX_TOKEN_BUDGET", "")
    try:
        budget_i = int(budget)
    except ValueError as exc:
        raise StackContractError("ENV_REPOMIX_BUDGET_INVALID") from exc
    if not 1_000 <= budget_i <= 1_000_000:
        raise StackContractError("ENV_REPOMIX_BUDGET_OUT_OF_RANGE")
    return {
        "status": "PASS",
        "hindsight_enabled": env.get("P2P_ENABLE_HINDSIGHT") == "YES",
        "repomix_token_budget": budget_i,
    }


def validate_compose(text: str) -> dict[str, object]:
    required_fragments = [
        "dockerfile: deployments/hermes-essential-stack/Dockerfile.workspace",
        f"WORKSPACE_COMMIT: {WORKSPACE_COMMIT}",
        "image: p2p-hermes-workspace:v2.3.0-15fa9cd",
        "repomix@1.18.0",
        "tokscale@4.16.0",
        '127.0.0.1:3000:3000',
        '127.0.0.1:8642:8642',
        '127.0.0.1:9119:9119',
        'HERMES_DASHBOARD: "1"',
        'VITE_HERMESWORLD_ENABLED: "0"',
        'P2P_ENABLE_HINDSIGHT',
        'profiles: ["hindsight"]',
        'profiles: ["tools"]',
        '/opt/data:ro',
    ]
    missing = [item for item in required_fragments if item not in text]
    if missing:
        raise StackContractError(f"COMPOSE_REQUIRED_FRAGMENT_MISSING:{missing[0]}")

    forbidden = [
        ":latest",
        "ghcr.io/outsourc-e/hermes-workspace",
        "tokscale@latest",
        "repomix@latest",
        "tokscale@4.16.0 submit",
        '"submit"',
        "builderz-labs/mission-control",
        "mission-control:",
        '0.0.0.0:3000:3000',
        '0.0.0.0:8642:8642',
        '0.0.0.0:9119:9119',
    ]
    hit = [item for item in forbidden if item in text]
    if hit:
        raise StackContractError(f"COMPOSE_FORBIDDEN_FRAGMENT:{hit[0]}")

    return {
        "status": "PASS",
        "workspace": EXPECTED["workspace"],
        "repomix": EXPECTED["repomix"],
        "tokscale": EXPECTED["tokscale"],
        "mission_control_authority": False,
    }


def validate_workspace_dockerfile(text: str) -> dict[str, object]:
    required = [
        f"ARG WORKSPACE_COMMIT={WORKSPACE_COMMIT}",
        f"corepack prepare pnpm@{WORKSPACE_PNPM} --activate",
        'git remote add origin https://github.com/outsourc-e/hermes-workspace.git',
        'git fetch --depth=1 origin "${WORKSPACE_COMMIT}"',
        'test "$(git rev-parse HEAD)" = "${WORKSPACE_COMMIT}"',
        "pnpm install --frozen-lockfile",
        "pnpm build",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise StackContractError(f"WORKSPACE_DOCKERFILE_REQUIRED_FRAGMENT_MISSING:{missing[0]}")
    forbidden = [
        "git checkout main",
        "git checkout master",
        "pnpm@latest",
        "ghcr.io/outsourc-e/hermes-workspace",
    ]
    hit = [item for item in forbidden if item in text]
    if hit:
        raise StackContractError(f"WORKSPACE_DOCKERFILE_FORBIDDEN_FRAGMENT:{hit[0]}")
    return {
        "status": "PASS",
        "commit": WORKSPACE_COMMIT,
        "pnpm": WORKSPACE_PNPM,
    }


def validate_stack(*, env_path: Path | None = None, allow_placeholders: bool = False) -> dict[str, object]:
    compose_result = validate_compose(COMPOSE_PATH.read_text(encoding="utf-8"))
    workspace_build_result = validate_workspace_dockerfile(
        WORKSPACE_DOCKERFILE_PATH.read_text(encoding="utf-8")
    )
    target_env = env_path or DEFAULT_ENV_PATH
    env_result = validate_env(target_env.read_text(encoding="utf-8"), allow_placeholders=allow_placeholders)
    return {
        "compose": compose_result,
        "workspace_build": workspace_build_result,
        "env": env_result,
    }


def init_env(output: Path, *, force: bool = False) -> dict[str, object]:
    if output.exists() and not force:
        raise StackContractError(f"ENV_ALREADY_EXISTS:{output}")
    rendered = render_env(ENV_EXAMPLE_PATH.read_text(encoding="utf-8"))
    validate_env(rendered)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
    try:
        output.chmod(0o600)
    except OSError:
        pass
    return {"status": "CREATED", "path": str(output)}


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    init_p = sub.add_parser("init", help="create a local .env with random secrets")
    init_p.add_argument("--output", type=Path, default=DEFAULT_ENV_PATH)
    init_p.add_argument("--force", action="store_true")

    val_p = sub.add_parser("validate", help="validate compose and env invariants")
    val_p.add_argument("--env", type=Path, default=DEFAULT_ENV_PATH)
    val_p.add_argument("--allow-placeholders", action="store_true")

    args = parser.parse_args()
    try:
        if args.command == "init":
            result = init_env(args.output, force=args.force)
        else:
            result = validate_stack(env_path=args.env, allow_placeholders=args.allow_placeholders)
    except (OSError, StackContractError) as exc:
        print(json.dumps({"status": "FAIL", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
