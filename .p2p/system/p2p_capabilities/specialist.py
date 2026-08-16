"""Optional-specialist validation without simulated execution."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import tomllib


def validate_optional_specialist(
    profile_path: str | Path,
    *,
    execute_verified: bool = False,
    health_verified: bool = False,
) -> dict[str, Any]:
    path = Path(profile_path)
    if not path.is_file():
        return {"status": "PROFILE_UNAVAILABLE", "identity_verified": False, "simulated": False, "reason": "PROFILE_MISSING"}
    text = path.read_text(encoding="utf-8")
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        return {
            "status": "PROFILE_INVALID",
            "identity_verified": False,
            "profile_resolved": False,
            "execute_verified": False,
            "health_verified": False,
            "simulated": False,
            "reason": f"PROFILE_TOML_INVALID: {exc}",
        }
    required = {
        "identity": data.get("name") == "p2p_aesthetica",
        "description": bool(data.get("description")),
        "developer_instructions": bool(data.get("developer_instructions")),
        "sandbox_mode": data.get("sandbox_mode") == "read-only",
    }
    profile_ok = all(required.values())
    execution_ok = profile_ok and bool(execute_verified)
    health_ok = execution_ok and bool(health_verified)
    return {
        "status": "HEALTHY" if health_ok else "EXECUTABLE" if execution_ok else "RESOLVED" if profile_ok else "PROFILE_INVALID",
        "identity_verified": execution_ok,
        "profile_resolved": profile_ok,
        "execute_verified": execution_ok,
        "health_verified": health_ok,
        "simulated": False,
        "required": required,
        "readiness_chain": [
            "SOURCE_EXISTS" if path.exists() else "SOURCE_MISSING",
            "PACKAGE_CONTAINS" if path.is_file() else "PACKAGE_MISSING",
            "INSTALLER_INSTALLS" if path.is_file() else "INSTALLER_UNKNOWN",
            "RUNTIME_DISCOVERS" if profile_ok else "RUNTIME_NOT_DISCOVERED",
            "PROFILE_RESOLVES" if profile_ok else "PROFILE_UNRESOLVED",
            "AGENT_EXECUTES" if execution_ok else "AGENT_EXECUTION_NOT_PROVEN",
            "IDENTITY_VERIFIED" if execution_ok else "IDENTITY_NOT_VERIFIED",
        ],
    }
