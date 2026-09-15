"""Pinned Reverse-Skill methodology reference for the existing SEC01 surface.

This module deliberately does NOT import or execute upstream Reverse-Skill code.
It is not a router, installer, bootstrapper, MCP registrar, target executor, or
authority store. P2P remains the sole router and authorization authority.

The only job here is to bind selected P2P security/reverse capabilities to a
reviewed upstream methodology reference at an exact commit. Callers look up
methodology *after* P2P has already selected a capability; task text is never
classified here.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


REVERSE_SKILL_REFERENCE_SCHEMA = "p2p-reverse-skill-reference/1"
REVERSE_SKILL_REPOSITORY = "https://github.com/zhaoxuya520/reverse-skill"
REVERSE_SKILL_COMMIT = "7e2097fd90d25c2f976f6eba26d6c00aa88051df"
REVERSE_SKILL_LICENSE = "MIT"

# Exact upstream source surfaces reviewed for this adoption. They are provenance
# references, not executable P2P entrypoints.
REVIEWED_SOURCE_SURFACES = (
    "skills/config/routing.json",
    "skills/ops/scope-contract.md",
    "skills/ops/skill-supply-chain.md",
    "LICENSE",
)

# Intentionally excluded from automatic loading/execution because upstream
# contains host-mutating bootstrap instructions and offensive execution chains.
EXCLUDED_EXECUTION_SURFACES = (
    "README_AI.md",
    "RULES.md",
    "skills/scripts/",
    "kali/scripts/",
    "skills/attack-chain/",
    "skills/edr-bypass-re/",
    "skills/patch-diff-exploit/",
    "skills/pentest-tools/",
    "skills/pwn-chain/",
    "CTF-Sandbox-Orchestrator/",
)

# This is a post-route methodology cross-reference only. It maps *existing P2P
# capability IDs* to upstream route IDs/surfaces; it never maps user text to a
# capability and therefore cannot become a second router.
_CAPABILITY_REFERENCES: dict[str, dict[str, Any]] = {
    "android.protection.detect": {
        "upstream_route_ids": ["R1"],
        "methodology_topics": ["APK protection identification", "static Android triage"],
        "execution_class_ceiling": "SAFE_READONLY",
    },
    "android.artifact.decode": {
        "upstream_route_ids": ["R1"],
        "methodology_topics": ["APK decoding", "artifact structure inspection"],
        "execution_class_ceiling": "ANALYSIS_LOCAL",
    },
    "security.mobile.static.assess": {
        "upstream_route_ids": ["R1", "R2"],
        "methodology_topics": ["mobile static assessment", "evidence-led mobile triage"],
        "execution_class_ceiling": "ANALYSIS_LOCAL",
    },
    "android.runtime.instrument": {
        "upstream_route_ids": ["R1", "R2"],
        "methodology_topics": ["runtime instrumentation planning"],
        "execution_class_ceiling": "ACTIVE_TEST_AUTHORIZED",
    },
    "android.network.inspect": {
        "upstream_route_ids": ["R2", "R3"],
        "methodology_topics": ["authorized mobile traffic inspection"],
        "execution_class_ceiling": "ACTIVE_TEST_AUTHORIZED",
    },
    "reverse.identify": {
        "upstream_route_ids": ["R6", "R7", "R22"],
        "methodology_topics": ["binary identification", "static reconnaissance"],
        "execution_class_ceiling": "SAFE_READONLY",
    },
    "reverse.decompile.managed": {
        "upstream_route_ids": ["R5"],
        "methodology_topics": ["managed-code decompilation"],
        "execution_class_ceiling": "ANALYSIS_LOCAL",
    },
    "reverse.decompile.native": {
        "upstream_route_ids": ["R6", "R7", "R22"],
        "methodology_topics": ["native decompilation", "disassembly workflow"],
        "execution_class_ceiling": "ANALYSIS_LOCAL",
    },
    "reverse.deobfuscate": {
        "upstream_route_ids": ["R1", "R4", "R5", "R6"],
        "methodology_topics": ["deobfuscation analysis", "uncertainty-preserving reconstruction"],
        "execution_class_ceiling": "ANALYSIS_LOCAL",
    },
    "reverse.callgraph": {
        "upstream_route_ids": ["R6", "R22"],
        "methodology_topics": ["static call-graph analysis"],
        "execution_class_ceiling": "ANALYSIS_LOCAL",
    },
    "reverse.semantic_reconstruct": {
        "upstream_route_ids": ["R4", "R5", "R6", "R22"],
        "methodology_topics": ["semantic reconstruction from evidence"],
        "execution_class_ceiling": "ANALYSIS_LOCAL",
    },
}


class ReverseSkillReferenceError(ValueError):
    """Raised when a caller asks for an unknown P2P capability reference."""


def reverse_skill_reference_for(capability_id: str) -> dict[str, Any]:
    """Return a defensive methodology reference for an already-selected P2P capability.

    This function performs no task routing, filesystem access, subprocess call,
    network request, installation, permission grant, or target interaction.
    """

    key = str(capability_id or "").strip()
    if key not in _CAPABILITY_REFERENCES:
        raise ReverseSkillReferenceError(f"UNMAPPED_P2P_CAPABILITY:{key or 'EMPTY'}")
    return {
        "schema": REVERSE_SKILL_REFERENCE_SCHEMA,
        "source": {
            "repository": REVERSE_SKILL_REPOSITORY,
            "commit": REVERSE_SKILL_COMMIT,
            "license": REVERSE_SKILL_LICENSE,
            "reviewed_surfaces": list(REVIEWED_SOURCE_SURFACES),
        },
        "adoption_mode": "PINNED_METHODOLOGY_REFERENCE_ONLY",
        "p2p_router_authority": "SOLE",
        "upstream_router_authority": "NONE",
        "bootstrap_allowed": False,
        "auto_install_allowed": False,
        "mcp_registration_allowed": False,
        "network_runtime_allowed": False,
        "external_execution_authorized": False,
        "capability_id": key,
        "reference": deepcopy(_CAPABILITY_REFERENCES[key]),
        "excluded_execution_surfaces": list(EXCLUDED_EXECUTION_SURFACES),
    }


def reverse_skill_reference_ids() -> tuple[str, ...]:
    """Return the exact P2P capability IDs covered by the reference bridge."""

    return tuple(_CAPABILITY_REFERENCES)


__all__ = [
    "EXCLUDED_EXECUTION_SURFACES",
    "REVERSE_SKILL_COMMIT",
    "REVERSE_SKILL_LICENSE",
    "REVERSE_SKILL_REFERENCE_SCHEMA",
    "REVERSE_SKILL_REPOSITORY",
    "REVIEWED_SOURCE_SURFACES",
    "ReverseSkillReferenceError",
    "reverse_skill_reference_for",
    "reverse_skill_reference_ids",
]
