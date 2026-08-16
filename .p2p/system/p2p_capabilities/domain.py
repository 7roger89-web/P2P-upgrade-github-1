"""Optional project-domain vocabulary; never an authority or persistence layer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ProjectDomainModel:
    domain: str
    users: tuple[str, ...] = field(default_factory=tuple)
    workflows: tuple[str, ...] = field(default_factory=tuple)
    vocabulary: tuple[str, ...] = field(default_factory=tuple)
    constraints: tuple[str, ...] = field(default_factory=tuple)
    provenance: str = "OWNER"

    def as_context(self) -> dict[str, Any]:
        value = asdict(self)
        value.update({"content_class": "CONTENT", "grants_permissions": False, "changes_quorum": False, "persistent": False})
        return value
