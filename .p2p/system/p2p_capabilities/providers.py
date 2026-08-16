"""Provider seams only; no external provider implementation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


PROVIDER_ROLES = ("P2P_PROVENANCE_PROVIDER", "P2P_CODE_INTELLIGENCE_PROVIDER")
PROVIDER_IMPLEMENTATIONS = ("P2P_NATIVE", "SEMANTICA", "ANVIEN")
TRUST_LEVELS = ("PURE_DATA", "HOST_CODE", "EXTERNAL_SERVICE")


@dataclass(frozen=True)
class ProviderDeclaration:
    role: str
    implementation: str
    trust_level: str
    input_scope: tuple[str, ...]
    output_schema: str
    provenance: str
    freshness: str

    def __post_init__(self) -> None:
        if self.role not in PROVIDER_ROLES:
            raise ValueError("PROVIDER_ROLE_INVALID")
        if self.implementation not in PROVIDER_IMPLEMENTATIONS:
            raise ValueError("PROVIDER_IMPLEMENTATION_INVALID")
        if self.trust_level not in TRUST_LEVELS:
            raise ValueError("PROVIDER_TRUST_LEVEL_INVALID")

    def contract(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.update({"can_change_governance": False, "can_grant_permissions": False, "provider_installed": False})
        return payload


def native_provider_state(role: str) -> dict[str, Any]:
    if role not in PROVIDER_ROLES:
        return {"status": "UNKNOWN", "reason": "PROVIDER_ROLE_INVALID"}
    return {"role": role, "implementation": "P2P_NATIVE", "status": "NOT_APPLICABLE", "provider_installed": False, "core_usable": True}
