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
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parents[1]
STACK_DIR = REPO_ROOT / "deployments" / "hermes-essential-stack"
COMPOSE_PATH = STACK_DIR / "docker-compose.yml"
WORKSPACE_DOCKERFILE_PATH = STACK_DIR / "Dockerfile.workspace"
RUNTIME_DOCKERFILE_PATH = REPO_ROOT / "Dockerfile"
POST_BOOTSTRAP_PATH = REPO_ROOT / "deployments" / "hermes-dockhosting" / "p2p-post-bootstrap-main.sh"
ENV_EXAMPLE_PATH = STACK_DIR / ".env.example"
DEFAULT_ENV_PATH = STACK_DIR / ".env"

WORKSPACE_COMMIT = "15fa9cd706f5c04e4db288fb958e21d10fc776da"
WORKSPACE_PNPM = "9.15.9"
OPIK_VERSION = "2.2.59"
OPIK_CLOUD_URL = "https://www.comet.com/opik/api"
EXPECTED = {
    "hermes": "nousresearch/hermes-agent:v2026.9.14",
    "workspace": f"hermes-workspace:v2.3.0@{WORKSPACE_COMMIT}",
    "repomix": "repomix@1.18.0",
    "tokscale": "tokscale@4.16.0",
    "opik": f"opik=={OPIK_VERSION}",
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
GENIEX_LOCAL_HOSTS = {
    "127.0.0.1",
    "localhost",
    "::1",
    "host.docker.internal",
}
FALSE_VALUES = {"0", "false", "no", "off"}


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


def _validate_geniex_local_url(value: str) -> None:
    try:
        parsed = urlparse(value)
    except ValueError as exc:
        raise StackContractError("ENV_GENIEX_BASE_URL_INVALID") from exc
    if parsed.scheme != "http" or parsed.hostname not in GENIEX_LOCAL_HOSTS:
        raise StackContractError("ENV_GENIEX_BASE_URL_MUST_BE_LOCAL_HTTP")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise StackContractError("ENV_GENIEX_BASE_URL_INVALID")
    if parsed.path.rstrip("/") != "/v1":
        raise StackContractError("ENV_GENIEX_BASE_URL_MUST_END_IN_V1")


def _validate_opik(env: dict[str, str]) -> tuple[bool, bool]:
    gate = env.get("P2P_ENABLE_OPIK", "NO")
    capture = env.get("P2P_OPIK_CAPTURE_CONTENT", "NO")
    if gate not in {"NO", "YES"}:
        raise StackContractError("ENV_OPIK_GATE_INVALID")
    if capture not in {"NO", "YES"}:
        raise StackContractError("ENV_OPIK_CONTENT_GATE_INVALID")
    if capture == "YES" and gate != "YES":
        raise StackContractError("ENV_OPIK_CONTENT_CAPTURE_REQUIRES_ENABLE")

    analytics = env.get("OPIK_ANALYTICS_ENABLE", "false").strip().lower()
    if analytics not in FALSE_VALUES:
        raise StackContractError("ENV_OPIK_ANALYTICS_MUST_BE_DISABLED")

    if gate == "YES":
        if not env.get("OPIK_API_KEY", "").strip():
            raise StackContractError("ENV_OPIK_KEY_REQUIRED_WHEN_ENABLED")
        if not env.get("OPIK_WORKSPACE", "").strip():
            raise StackContractError("ENV_OPIK_WORKSPACE_REQUIRED_WHEN_ENABLED")
        if not env.get("OPIK_PROJECT_NAME", "").strip():
            raise StackContractError("ENV_OPIK_PROJECT_REQUIRED_WHEN_ENABLED")
        if not env.get("OPIK_ENVIRONMENT", "").strip():
            raise StackContractError("ENV_OPIK_ENVIRONMENT_REQUIRED_WHEN_ENABLED")
        url = env.get("OPIK_URL_OVERRIDE", OPIK_CLOUD_URL).rstrip("/")
        if url != OPIK_CLOUD_URL:
            raise StackContractError("ENV_OPIK_PILOT_URL_MUST_BE_COMET_CLOUD")
    return gate == "YES", capture == "YES"


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

    geniex_gate = env.get("P2P_ENABLE_GENIEX", "NO")
    if geniex_gate not in {"NO", "YES"}:
        raise StackContractError("ENV_GENIEX_GATE_INVALID")
    if geniex_gate == "YES":
        base_url = env.get("GENIEX_BASE_URL", "").strip()
        model = env.get("GENIEX_MODEL", "").strip()
        if not base_url:
            raise StackContractError("ENV_GENIEX_BASE_URL_REQUIRED_WHEN_ENABLED")
        if not model:
            raise StackContractError("ENV_GENIEX_MODEL_REQUIRED_WHEN_ENABLED")
        if any(ch.isspace() for ch in model):
            raise StackContractError("ENV_GENIEX_MODEL_INVALID")
        _validate_geniex_local_url(base_url)

    if env.get("P2P_ENABLE_HINDSIGHT", "NO") not in {"NO", "YES"}:
        raise StackContractError("ENV_HINDSIGHT_GATE_INVALID")
    if env.get("P2P_ENABLE_HINDSIGHT") == "YES" and not env.get("HINDSIGHT_API_KEY"):
        raise StackContractError("ENV_HINDSIGHT_KEY_REQUIRED_WHEN_ENABLED")

    opik_enabled, opik_capture_content = _validate_opik(env)

    budget = env.get("REPOMIX_TOKEN_BUDGET", "")
    try:
        budget_i = int(budget)
    except ValueError as exc:
        raise StackContractError("ENV_REPOMIX_BUDGET_INVALID") from exc
    if not 1_000 <= budget_i <= 1_000_000:
        raise StackContractError("ENV_REPOMIX_BUDGET_OUT_OF_RANGE")
    return {
        "status": "PASS",
        "geniex_enabled": geniex_gate == "YES",
        "hindsight_enabled": env.get("P2P_ENABLE_HINDSIGHT") == "YES",
        "opik_enabled": opik_enabled,
        "opik_capture_content": opik_capture_content,
        "repomix_token_budget": budget_i,
    }


def validate_compose(text: str) -> dict[str, object]:
    required_fragments = [
        "dockerfile: deployments/hermes-essential-stack/Dockerfile.workspace",
        f"WORKSPACE_COMMIT: {WORKSPACE_COMMIT}",
        "image: p2p-hermes-workspace:v2.3.0-15fa9cd",
        'P2P_INSTALL_OPIK: "1"',
        "./plugins/p2p-opik-observer:/opt/data/plugins/p2p-opik-observer:ro",
        "P2P_ENABLE_OPIK",
        "P2P_OPIK_CAPTURE_CONTENT",
        "OPIK_API_KEY",
        "OPIK_WORKSPACE",
        "OPIK_PROJECT_NAME",
        'OPIK_ANALYTICS_ENABLE: "false"',
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
        'geniex-register:',
        'profiles: ["geniex"]',
        'user: "hermes"',
        'host.docker.internal:host-gateway',
        'P2P_ENABLE_GENIEX',
        'GENIEX_CHAT_SMOKE=PASS',
        'providers.geniex.api',
        'providers.geniex.transport chat_completions',
        'providers.geniex.default_model',
        'providers.geniex.discover_models false',
        'main_model_unchanged=YES',
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
        'model.provider custom;',
        'model.default "$${GENIEX_MODEL}"',
        "clickhouse:",
        "mysql:",
        "redis:",
        "minio:",
    ]
    hit = [item for item in forbidden if item in text]
    if hit:
        raise StackContractError(f"COMPOSE_FORBIDDEN_FRAGMENT:{hit[0]}")

    return {
        "status": "PASS",
        "workspace": EXPECTED["workspace"],
        "repomix": EXPECTED["repomix"],
        "tokscale": EXPECTED["tokscale"],
        "opik": EXPECTED["opik"],
        "opik_cloud_only": True,
        "opik_second_control_plane": False,
        "geniex_named_provider_only": True,
        "geniex_registration_user": "hermes",
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


def validate_runtime_dockerfile(text: str) -> dict[str, object]:
    required = [
        "ARG P2P_INSTALL_OPIK=0",
        f"ARG OPIK_VERSION={OPIK_VERSION}",
        'if [ "$P2P_INSTALL_OPIK" = "1" ]; then',
        'uv pip install --python /opt/hermes/.venv/bin/python "opik==${OPIK_VERSION}"',
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise StackContractError(f"RUNTIME_DOCKERFILE_OPIK_FRAGMENT_MISSING:{missing[0]}")
    if "ARG P2P_INSTALL_OPIK=1" in text:
        raise StackContractError("RUNTIME_DOCKERFILE_OPIK_MUST_DEFAULT_OFF")
    return {
        "status": "PASS",
        "opik": EXPECTED["opik"],
        "default_installed": False,
    }


def validate_post_bootstrap(text: str) -> dict[str, object]:
    required = [
        'if [ "${P2P_ENABLE_OPIK:-NO}" = "YES" ]; then',
        "/opt/data/plugins/p2p-opik-observer/plugin.yaml",
        "hermes plugins enable p2p-opik-observer",
    ]
    missing = [item for item in required if item not in text]
    if missing:
        raise StackContractError(f"POST_BOOTSTRAP_OPIK_FRAGMENT_MISSING:{missing[0]}")
    return {
        "status": "PASS",
        "opik_explicit_gate": True,
    }


def validate_stack(*, env_path: Path | None = None, allow_placeholders: bool = False) -> dict[str, object]:
    compose_result = validate_compose(COMPOSE_PATH.read_text(encoding="utf-8"))
    workspace_build_result = validate_workspace_dockerfile(
        WORKSPACE_DOCKERFILE_PATH.read_text(encoding="utf-8")
    )
    runtime_build_result = validate_runtime_dockerfile(
        RUNTIME_DOCKERFILE_PATH.read_text(encoding="utf-8")
    )
    post_bootstrap_result = validate_post_bootstrap(
        POST_BOOTSTRAP_PATH.read_text(encoding="utf-8")
    )
    target_env = env_path or DEFAULT_ENV_PATH
    env_result = validate_env(target_env.read_text(encoding="utf-8"), allow_placeholders=allow_placeholders)
    return {
        "compose": compose_result,
        "workspace_build": workspace_build_result,
        "runtime_build": runtime_build_result,
        "post_bootstrap": post_bootstrap_result,
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
