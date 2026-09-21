"""Pinned web/browser reverse methodology references for the SEC01-extended web family.

This module deliberately does NOT import or execute any upstream web tool code.
It is not a router, installer, bootstrapper, MCP registrar, crawler, browser
farm, traffic database, target executor, or authority store. P2P remains the
sole router and authorization authority.

The only job here is to bind the four P2P web reverse capability IDs to
reviewed upstream methodology references at exact commits. Callers look up
methodology *after* P2P has already selected a capability; task text is never
classified here.

Boundary notes recorded by this module (not granted by it):

- The existing Reverse-Skill pin
  (``zhaoxuya520/reverse-skill@7e2097fd90d25c2f976f6eba26d6c00aa88051df``)
  is unchanged by this foundation; that pin equals current upstream HEAD, so
  no drift is claimed and nothing here re-pins or extends that bridge.
- ``vmoranv/jshookmcp`` is AGPL-3.0 and is an optional external backend only:
  no vendor snapshot, no linking, no import, no install, and no runtime
  activation in this foundation.
- ``BishopFox/jsluice`` is a subordinate parser reference under endpoint
  discovery, not a separate P2P authority.
- Traffic-analysis stacks are benchmark-or-defer: neither
  ``Mouseww/anything-analyzer`` nor ``Reqable/reqable-mcp-server`` is adopted
  by this foundation. Reqable additionally exposes no SPDX license in its
  repository metadata, so it stays a reference/external candidate only until
  that license is resolved.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


WEB_REVERSE_REFERENCE_SCHEMA = "p2p-web-reverse-reference/1"

# Behaviors this foundation explicitly denies for every mapped capability.
# They are deny-list metadata, not granted permissions.
EXCLUDED_RUNTIME_BEHAVIORS = (
    "tool-installation",
    "mcp-auto-registration",
    "global-host-configuration",
    "credential-or-authenticated-session-use",
    "unscoped-live-target-interaction",
    "bypass-or-exploit-execution",
)

# Traffic-analysis candidates verified 2026-09-21 and explicitly NOT adopted.
# Neither entry maps to a P2P capability ID.
DEFERRED_TRAFFIC_CANDIDATES: tuple[dict[str, Any], ...] = (
    {
        "repository": "https://github.com/Mouseww/anything-analyzer",
        "commit": "1da6b5c9acc024e987d41e4b9c88676ffea0da0c",
        "license": "Apache-2.0",
        "status": "DEFERRED_NOT_ADOPTED",
        "reason": "BENCHMARK_OR_DEFER: do not adopt a traffic stack by default",
    },
    {
        "repository": "https://github.com/Reqable/reqable-mcp-server",
        "commit": "2df174f982e9ab481a457ab96e065aac22829a51",
        "license": "UNRESOLVED_NO_SPDX_IN_REPOSITORY_METADATA",
        "status": "NOT_ADOPTED_LICENSE_UNRESOLVED",
        "reason": "REFERENCE_OR_EXTERNAL_CANDIDATE_ONLY_UNTIL_LICENSE_RESOLVED",
    },
)

# This is a post-route methodology cross-reference only. It maps *existing P2P
# web capability IDs* (selected by the sole P2P router) to upstream backend
# references; it never maps user text to a capability and therefore cannot
# become a second router.
_CAPABILITY_REFERENCES: dict[str, dict[str, Any]] = {
    "web.browser.evidence": {
        "upstream_repository": "https://github.com/ChromeDevTools/chrome-devtools-mcp",
        "upstream_commit": "61780c7498a447771127d1fd3b2454fc4ae4ba28",
        "license": "Apache-2.0",
        "backend_role": "CANDIDATE_DEFAULT_BROWSER_EVIDENCE_BACKEND",
        "methodology_topics": [
            "first-line DOM truth",
            "served-document truth",
            "observed network truth",
            "client-hidden vs server-redacted separation",
        ],
        "execution_class_ceiling": "ACTIVE_TEST_AUTHORIZED",
        "ceiling_note": (
            "Local-document analysis stays SAFE_READONLY/ANALYSIS_LOCAL under "
            "the existing gates; the ceiling covers only a future live-browser "
            "adapter, which remains authorization-gated and disabled here."
        ),
    },
    "web.js.reverse": {
        "upstream_repository": "https://github.com/vmoranv/jshookmcp",
        "upstream_commit": "33983e58cddc998af88a2ed46484364e5425cc86",
        "license": "AGPL-3.0",
        "license_boundary": (
            "AGPL-3.0_EXTERNAL_ONLY: no vendor snapshot, no linking, "
            "no import, no install, no runtime activation in this foundation"
        ),
        "backend_role": "OPTIONAL_EXTERNAL_DEEP_INSPECTION_BACKEND",
        "methodology_topics": [
            "JS runtime/source tracing only when first-line evidence is insufficient",
        ],
        "execution_class_ceiling": "ACTIVE_TEST_AUTHORIZED",
    },
    "web.endpoint.discover": {
        "upstream_repository": "https://github.com/projectdiscovery/katana",
        "upstream_commit": "c1de26dbe69764a92dfa9a142eb64035e5d05a9d",
        "license": "MIT",
        "backend_role": "CANDIDATE_ENDPOINT_DISCOVERY_BACKEND",
        "subordinate_reference": {
            "repository": "https://github.com/BishopFox/jsluice",
            "commit": "0ddfab153e060a9eeaded4d8669233f7c071e7e4",
            "license": "MIT",
            "role": "SUBORDINATE_PARSER_REFERENCE_NOT_A_SEPARATE_P2P_AUTHORITY",
        },
        "methodology_topics": [
            "JS endpoint parsing",
            "static endpoint discovery",
            "headless endpoint discovery for an explicitly scoped target",
        ],
        "execution_class_ceiling": "ACTIVE_TEST_AUTHORIZED",
    },
    "web.public.reconstruct": {
        "upstream_repository": "https://github.com/xnl-h4ck3r/waymore",
        "upstream_commit": "4e02de512fd6b110be92dc8bffb3002edfebcb6c",
        "license": "MIT",
        "backend_role": "CANDIDATE_PUBLIC_RECONSTRUCTION_BACKEND",
        "methodology_topics": [
            "historical/public URL discovery",
            "public archive/index/search reconstruction",
        ],
        "execution_class_ceiling": "ANALYSIS_LOCAL",
        "ceiling_note": (
            "Public archive/index sources only; archive output is never "
            "presented as live-target truth."
        ),
    },
}


class WebReverseReferenceError(ValueError):
    """Raised when a caller asks for an unknown P2P web capability reference."""


def web_reverse_reference_for(capability_id: str) -> dict[str, Any]:
    """Return a defensive methodology reference for an already-selected capability.

    This function performs no task routing, filesystem access, subprocess call,
    network interaction, installation, permission grant, or target interaction.
    """

    key = str(capability_id or "").strip()
    if key not in _CAPABILITY_REFERENCES:
        raise WebReverseReferenceError(f"UNMAPPED_P2P_CAPABILITY:{key or 'EMPTY'}")
    return {
        "schema": WEB_REVERSE_REFERENCE_SCHEMA,
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
        "excluded_runtime_behaviors": list(EXCLUDED_RUNTIME_BEHAVIORS),
        "deferred_traffic_candidates": deepcopy(DEFERRED_TRAFFIC_CANDIDATES),
    }


def web_reverse_reference_ids() -> tuple[str, ...]:
    """Return the exact P2P web capability IDs covered by the reference bridge."""

    return tuple(_CAPABILITY_REFERENCES)


__all__ = [
    "DEFERRED_TRAFFIC_CANDIDATES",
    "EXCLUDED_RUNTIME_BEHAVIORS",
    "WEB_REVERSE_REFERENCE_SCHEMA",
    "WebReverseReferenceError",
    "web_reverse_reference_for",
    "web_reverse_reference_ids",
]
