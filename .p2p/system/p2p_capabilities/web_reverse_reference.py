"""Pinned web/browser reverse-evidence reference for the P2P ``web.*`` family.

This module deliberately does NOT import or execute any upstream browser,
JavaScript-tracing, crawler, or archive tool. It is not a router, installer,
bootstrapper, MCP registrar, target executor, crawler service, traffic
database, or authority store. P2P remains the sole router and authorization
authority.

Its only job is to bind already-declared ``web.*`` capabilities to reviewed
upstream candidates at exact commits, to state each license boundary, and to
refuse to describe live external interaction as a bounded local class. Callers
look up a reference only *after* P2P has selected a capability; task text is
never classified here, so this cannot become a second router.

Import-time truthfulness rules (fail closed):

* every declared execution-class ceiling exists in the existing security
  contract vocabulary;
* a capability that can interact with an external target never declares a
  bounded local ceiling (``SAFE_READONLY`` / ``ANALYSIS_LOCAL``);
* every upstream candidate stays uninstalled, unactivated and unvendored in
  this task;
* a license-unresolved upstream is registered reference-only and cannot be
  adopted;
* the existing Reverse-Skill pin is reconciled as current upstream HEAD, never
  reported as drifted.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from .security_contract import (
    ACTIVE_TEST_AUTHORIZED,
    ANALYSIS_LOCAL,
    SAFE_READONLY,
    SECURITY_EXECUTION_CLASSES,
)


WEB_REVERSE_REFERENCE_SCHEMA = "p2p-web-reverse-reference/1"
WEB_REVERSE_REFERENCE_MODULE = ".p2p/system/p2p_capabilities/web_reverse_reference.py"
PIN_VERIFIED_AT = "2026-09-21"

# Declarative family order describing the escalation boundary between evidence
# sources. It is methodology metadata only: it never selects, ranks, or routes
# a capability, and the P2P router remains the single selection authority.
WEB_REVERSE_FAMILY_FLOW = (
    "web.browser.evidence",
    "web.js.reverse",
    "web.endpoint.discovery",
    "web.public.reconstruction",
)

BOUNDED_LOCAL_CLASSES = (SAFE_READONLY, ANALYSIS_LOCAL)
LIVE_TARGET_CEILING = ACTIVE_TEST_AUTHORIZED

LICENSE_BOUNDARIES: dict[str, str] = {
    "Apache-2.0": "PERMISSIVE_REFERENCE_ONLY_NOT_VENDORED_NOT_INSTALLED_IN_THIS_TASK",
    "MIT": "PERMISSIVE_REFERENCE_ONLY_NOT_VENDORED_NOT_INSTALLED_IN_THIS_TASK",
    "AGPL-3.0": "COPYLEFT_EXTERNAL_BACKEND_ONLY_NOT_VENDORED_NOT_LINKED_NOT_REDISTRIBUTED",
    "NO_SPDX": "LICENSE_UNRESOLVED_REFERENCE_ONLY_ADOPTION_PROHIBITED_UNTIL_RESOLVED",
}

# Reconciliation of the existing SEC01 security/reverse foundation. The
# Reverse-Skill bridge stays exactly as adopted and its pin still equals current
# upstream HEAD; no drift is claimed and no existing mapping is rewritten.
EXISTING_REVERSE_SKILL_PIN = "7e2097fd90d25c2f976f6eba26d6c00aa88051df"
EXISTING_REVERSE_SKILL_PIN_STATUS = "CURRENT_UPSTREAM_HEAD_AT_VERIFICATION"
EXISTING_REVERSE_SKILL_RECONCILIATION = "UNCHANGED_NO_DRIFT_CLAIMED"
EXISTING_REVERSE_SKILL_REFERENCE_MODULE = ".p2p/system/p2p_capabilities/reverse_skill_reference.py"

# Existing routes stay authoritative inside their own scopes. Each entry records
# the concrete reason it cannot express a web/browser evidence route, so the
# ``web.*`` family is an extension of the same foundation rather than a
# duplicate or a relabelled mobile/binary route.
EXISTING_ROUTE_RECONCILIATION: dict[str, dict[str, str]] = {
    "security.mobile.static.assess": {
        "existing_scope": "LOCAL_MOBILE_ARTIFACT_STATIC_ASSESSMENT",
        "not_sufficient_for": "LIVE_WEB_DOCUMENT_AND_NETWORK_EVIDENCE",
    },
    "android.protection.detect": {
        "existing_scope": "LOCAL_ANDROID_ARTIFACT_PROTECTION_IDENTIFICATION",
        "not_sufficient_for": "LIVE_WEB_DOCUMENT_AND_NETWORK_EVIDENCE",
    },
    "android.artifact.decode": {
        "existing_scope": "LOCAL_ANDROID_ARTIFACT_DECODING",
        "not_sufficient_for": "LIVE_WEB_DOCUMENT_AND_NETWORK_EVIDENCE",
    },
    "android.runtime.instrument": {
        "existing_scope": "AUTHORIZED_ANDROID_DEVICE_OR_EMULATOR_RUNTIME_INSTRUMENTATION",
        "not_sufficient_for": "BROWSER_JAVASCRIPT_RUNTIME_TRACING",
    },
    "android.network.inspect": {
        "existing_scope": "AUTHORIZED_ANDROID_DEVICE_OR_EMULATOR_TRAFFIC_INSPECTION",
        "not_sufficient_for": "BROWSER_DOCUMENT_AND_NETWORK_EVIDENCE",
    },
    "reverse.identify": {
        "existing_scope": "LOCAL_BINARY_MANAGED_OR_ARCHIVE_ARTIFACT_IDENTIFICATION",
        "not_sufficient_for": "WEB_ENDPOINT_DISCOVERY",
    },
    "reverse.decompile.managed": {
        "existing_scope": "LOCAL_MANAGED_CODE_DECOMPILATION",
        "not_sufficient_for": "BROWSER_JAVASCRIPT_RUNTIME_TRACING",
    },
    "reverse.decompile.native": {
        "existing_scope": "LOCAL_NATIVE_CODE_DECOMPILATION",
        "not_sufficient_for": "BROWSER_JAVASCRIPT_RUNTIME_TRACING",
    },
    "reverse.deobfuscate": {
        "existing_scope": "LOCAL_ARTIFACT_DEOBFUSCATION_ANALYSIS",
        "not_sufficient_for": "BROWSER_JAVASCRIPT_RUNTIME_TRACING",
    },
    "reverse.callgraph": {
        "existing_scope": "LOCAL_STATIC_CALL_GRAPH_ANALYSIS",
        "not_sufficient_for": "BROWSER_JAVASCRIPT_RUNTIME_TRACING",
    },
    "reverse.semantic_reconstruct": {
        "existing_scope": "LOCAL_ARTIFACT_SEMANTIC_RECONSTRUCTION",
        "not_sufficient_for": "PUBLIC_ARCHIVE_AND_INDEX_RECONSTRUCTION",
    },
}

# Reviewed upstream candidates. Exact commits were verified on PIN_VERIFIED_AT
# and each pin equalled upstream HEAD at that moment. None is installed,
# registered, executed, or vendored by this task.
_UPSTREAM_CANDIDATES: dict[str, dict[str, Any]] = {
    "chrome-devtools-mcp": {
        "repository": "https://github.com/ChromeDevTools/chrome-devtools-mcp",
        "commit": "61780c7498a447771127d1fd3b2454fc4ae4ba28",
        "license": "Apache-2.0",
        "role": "DEFAULT_BROWSER_EVIDENCE_BACKEND_CANDIDATE",
        "methodology_topics": [
            "live document and DOM inspection",
            "observed network request evidence",
            "console evidence",
            "screenshot evidence",
            "source-mapped debugging",
        ],
        "integration_position": "EXTERNAL_BACKEND_REQUIRES_SEPARATE_OWNER_ACTIVATION",
        "p2p_install": "DISABLED",
        "p2p_runtime_activation": "DISABLED",
        "mcp_registration": "NOT_PERFORMED",
        "vendored": False,
        "credentials": False,
    },
    "vmoranv-jshookmcp": {
        "repository": "https://github.com/vmoranv/jshookmcp",
        "commit": "33983e58cddc998af88a2ed46484364e5425cc86",
        "license": "AGPL-3.0",
        "role": "OPTIONAL_DEEP_RUNTIME_INSPECTION_BACKEND_CANDIDATE",
        "methodology_topics": [
            "runtime/source tracing only when document and network evidence is insufficient",
        ],
        "integration_position": "OPTIONAL_EXTERNAL_BACKEND_ONLY",
        "p2p_install": "DISABLED",
        "p2p_runtime_activation": "DISABLED",
        "mcp_registration": "NOT_PERFORMED",
        "vendored": False,
        "credentials": False,
        "agpl_boundary": {
            "copyleft": True,
            "vendoring_allowed": False,
            "linking_allowed": False,
            "redistribution_with_p2p_allowed": False,
            "network_use_of_modified_covered_work": "OPERATOR_RESPONSIBILITY_OUT_OF_TREE",
            "requirement_before_any_use": "SEPARATE_OWNER_ACTIVATION_AND_AGPL_COMPLIANCE_REVIEW",
        },
    },
    "projectdiscovery-katana": {
        "repository": "https://github.com/projectdiscovery/katana",
        "commit": "c1de26dbe69764a92dfa9a142eb64035e5d05a9d",
        "license": "MIT",
        "role": "ENDPOINT_DISCOVERY_BACKEND_CANDIDATE",
        "methodology_topics": [
            "standard crawling",
            "headless crawling",
            "client-side JavaScript endpoint parsing",
        ],
        "integration_position": "EXTERNAL_BACKEND_REQUIRES_SEPARATE_OWNER_ACTIVATION",
        "p2p_install": "DISABLED",
        "p2p_runtime_activation": "DISABLED",
        "mcp_registration": "NOT_PERFORMED",
        "vendored": False,
        "credentials": False,
    },
    "bishopfox-jsluice": {
        "repository": "https://github.com/BishopFox/jsluice",
        "commit": "0ddfab153e060a9eeaded4d8669233f7c071e7e4",
        "license": "MIT",
        "role": "SUBORDINATE_JAVASCRIPT_ENDPOINT_PARSER_REFERENCE",
        "methodology_topics": [
            "static JavaScript endpoint extraction reference",
        ],
        "integration_position": "SUBORDINATE_REFERENCE_UNDER_ENDPOINT_DISCOVERY_NOT_A_SEPARATE_P2P_AUTHORITY",
        "p2p_install": "DISABLED",
        "p2p_runtime_activation": "DISABLED",
        "mcp_registration": "NOT_PERFORMED",
        "vendored": False,
        "credentials": False,
    },
    "xnl-h4ck3r-waymore": {
        "repository": "https://github.com/xnl-h4ck3r/waymore",
        "commit": "4e02de512fd6b110be92dc8bffb3002edfebcb6c",
        "license": "MIT",
        "role": "PUBLIC_RECONSTRUCTION_BACKEND_CANDIDATE",
        "methodology_topics": [
            "public archive URL discovery",
            "public index response retrieval",
        ],
        "integration_position": "EXTERNAL_BACKEND_REQUIRES_SEPARATE_OWNER_ACTIVATION",
        "p2p_install": "DISABLED",
        "p2p_runtime_activation": "DISABLED",
        "mcp_registration": "NOT_PERFORMED",
        "vendored": False,
        "credentials": False,
    },
}

# Reviewed and deliberately NOT adopted in this task. These stay reference-only
# and must fail closed if a caller tries to treat them as adopted candidates.
NON_ADOPTED_UPSTREAMS: dict[str, dict[str, Any]] = {
    "mouseww-anything-analyzer": {
        "repository": "https://github.com/Mouseww/anything-analyzer",
        "commit": "1da6b5c9acc024e987d41e4b9c88676ffea0da0c",
        "license": "Apache-2.0",
        "reason_code": "DEFERRED_ALTERNATIVE_TRAFFIC_STACK",
        "reason": "A second parallel traffic-analysis stack is not adopted by default; benchmark or defer.",
    },
    "reqable-mcp-server": {
        "repository": "https://github.com/Reqable/reqable-mcp-server",
        "commit": "2df174f982e9ab481a457ab96e065aac22829a51",
        "license": "NO_SPDX",
        "reason_code": "LICENSE_UNRESOLVED",
        "reason": "Repository metadata exposes no SPDX license; reference only until the license is resolved.",
    },
}

_NON_ADOPTED_KEYS = frozenset(NON_ADOPTED_UPSTREAMS)

# Post-route methodology cross-reference. This maps *already-selected P2P
# capability IDs* to evidence roles and reviewed candidates; it never maps user
# text to a capability.
_CAPABILITY_REFERENCES: dict[str, dict[str, Any]] = {
    "web.browser.evidence": {
        "evidence_source_role": "FIRST_LINE_DOCUMENT_AND_NETWORK_TRUTH",
        "truth_source": "LIVE_OR_CAPTURED_PAGE_DOCUMENT_AND_OBSERVED_NETWORK_REQUESTS",
        "family_position": 1,
        "escalation_preconditions": [],
        "execution_class_ceiling": ACTIVE_TEST_AUTHORIZED,
        "local_artifact_floor": ANALYSIS_LOCAL,
        "external_interaction_possible": True,
        "answers_before_deeper_reverse": [
            "is this field client-hidden or server-redacted",
            "which requests actually produced the observed document state",
        ],
        "backend_candidates": ("chrome-devtools-mcp",),
        "non_adopted_candidates": (),
    },
    "web.js.reverse": {
        "evidence_source_role": "DEEP_RUNTIME_AND_SOURCE_TRACING_WHEN_DOCUMENT_AND_NETWORK_EVIDENCE_IS_INSUFFICIENT",
        "truth_source": "RUNTIME_FUNCTION_SOURCE_AND_BUNDLE_TRACING",
        "family_position": 2,
        "escalation_preconditions": ("web.browser.evidence",),
        "execution_class_ceiling": ACTIVE_TEST_AUTHORIZED,
        "local_artifact_floor": ANALYSIS_LOCAL,
        "external_interaction_possible": True,
        "answers_before_deeper_reverse": [
            "which client function produced an observed value",
            "which source-mapped path explains a runtime behaviour",
        ],
        "backend_candidates": ("vmoranv-jshookmcp",),
        "non_adopted_candidates": (),
    },
    "web.endpoint.discovery": {
        "evidence_source_role": "CLIENT_BUNDLE_STATIC_AND_HEADLESS_ENDPOINT_DISCOVERY",
        "truth_source": "CLIENT_BUNDLES_STATIC_ASSETS_AND_HEADLESS_CRAWL",
        "family_position": 3,
        "escalation_preconditions": (),
        "execution_class_ceiling": ACTIVE_TEST_AUTHORIZED,
        "local_artifact_floor": ANALYSIS_LOCAL,
        "external_interaction_possible": True,
        "answers_before_deeper_reverse": [
            "which endpoints exist for an authorized scope",
            "which client asset references an endpoint",
        ],
        "backend_candidates": ("projectdiscovery-katana", "bishopfox-jsluice"),
        "non_adopted_candidates": (),
    },
    "web.public.reconstruction": {
        "evidence_source_role": "PUBLIC_ARCHIVE_AND_INDEX_RECONSTRUCTION",
        "truth_source": "PUBLIC_ARCHIVE_INDEX_AND_SEARCH_SOURCES",
        "family_position": 4,
        "escalation_preconditions": (),
        "execution_class_ceiling": ACTIVE_TEST_AUTHORIZED,
        "local_artifact_floor": ANALYSIS_LOCAL,
        "external_interaction_possible": True,
        "answers_before_deeper_reverse": [
            "what a public page previously exposed",
            "which public URLs and responses existed historically",
        ],
        "backend_candidates": ("xnl-h4ck3r-waymore",),
        "non_adopted_candidates": ("mouseww-anything-analyzer", "reqable-mcp-server"),
        "distinct_from": (
            "web.browser.evidence",
            "web.js.reverse",
        ),
    },
}


class WebReverseReferenceError(ValueError):
    """Raised when a caller asks for an undeclared or non-adopted reference."""


def execution_class_is_truthful(execution_class: Any, *, external_interaction: bool) -> bool:
    """Return whether a class claim is truthful for the given interaction mode."""

    if execution_class not in SECURITY_EXECUTION_CLASSES:
        return False
    if external_interaction and execution_class in BOUNDED_LOCAL_CLASSES:
        return False
    return True


def validate_reference_declarations(
    references: Mapping[str, Mapping[str, Any]] | None = None,
    *,
    candidates: Mapping[str, Mapping[str, Any]] | None = None,
) -> None:
    """Fail closed when a declaration would misrepresent authority or risk."""

    table = _CAPABILITY_REFERENCES if references is None else references
    candidate_table = _UPSTREAM_CANDIDATES if candidates is None else candidates
    for capability_id, reference in table.items():
        ceiling = reference.get("execution_class_ceiling")
        external = bool(reference.get("external_interaction_possible"))
        if not execution_class_is_truthful(ceiling, external_interaction=external):
            raise WebReverseReferenceError(f"UNTRUTHFUL_EXECUTION_CLASS:{capability_id}:{ceiling}")
        for key in reference.get("backend_candidates", ()):
            if key not in candidate_table:
                raise WebReverseReferenceError(f"UNKNOWN_BACKEND_CANDIDATE:{capability_id}:{key}")
        for key in reference.get("non_adopted_candidates", ()):
            if key not in _NON_ADOPTED_KEYS:
                raise WebReverseReferenceError(f"UNKNOWN_NON_ADOPTED_CANDIDATE:{capability_id}:{key}")
    for key, candidate in candidate_table.items():
        license_kind = candidate.get("license")
        if license_kind not in LICENSE_BOUNDARIES:
            raise WebReverseReferenceError(f"UNKNOWN_LICENSE_KIND:{key}:{license_kind}")
        if candidate.get("vendored") or candidate.get("p2p_install") != "DISABLED":
            raise WebReverseReferenceError(f"CANDIDATE_MUST_STAY_DISABLED:{key}")
        if candidate.get("p2p_runtime_activation") != "DISABLED":
            raise WebReverseReferenceError(f"CANDIDATE_RUNTIME_MUST_STAY_DISABLED:{key}")
    if tuple(table) != WEB_REVERSE_FAMILY_FLOW:
        raise WebReverseReferenceError("FAMILY_FLOW_MISMATCH")


validate_reference_declarations()


def web_reverse_reference_ids() -> tuple[str, ...]:
    """Return the exact P2P capability IDs covered by this reference bridge."""

    return tuple(_CAPABILITY_REFERENCES)


def web_reverse_upstream_candidate(key: str) -> dict[str, Any]:
    """Return one adopted reference candidate, or fail closed."""

    normalized = str(key or "").strip()
    if normalized in _NON_ADOPTED_KEYS:
        raise WebReverseReferenceError(f"NON_ADOPTED_UPSTREAM:{normalized}")
    if normalized not in _UPSTREAM_CANDIDATES:
        raise WebReverseReferenceError(f"UNKNOWN_UPSTREAM_CANDIDATE:{normalized or 'EMPTY'}")
    candidate = deepcopy(_UPSTREAM_CANDIDATES[normalized])
    candidate["license_boundary"] = LICENSE_BOUNDARIES[candidate["license"]]
    candidate["pin_verified_at"] = PIN_VERIFIED_AT
    return candidate


def web_reverse_reference_for(capability_id: str) -> dict[str, Any]:
    """Return a defensive reference for an already-selected P2P capability.

    This function performs no task routing, filesystem access, subprocess call,
    network request, browser launch, installation, permission grant, or target
    interaction.
    """

    key = str(capability_id or "").strip()
    if key not in _CAPABILITY_REFERENCES:
        raise WebReverseReferenceError(f"UNMAPPED_P2P_CAPABILITY:{key or 'EMPTY'}")
    reference = deepcopy(_CAPABILITY_REFERENCES[key])
    candidates = [
        web_reverse_upstream_candidate(candidate_key)
        for candidate_key in reference["backend_candidates"]
    ]
    non_adopted = [deepcopy(NON_ADOPTED_UPSTREAMS[item]) for item in reference["non_adopted_candidates"]]
    return {
        "schema": WEB_REVERSE_REFERENCE_SCHEMA,
        "capability_id": key,
        "adoption_mode": "PINNED_REFERENCE_ONLY_RUNTIME_DISABLED",
        "p2p_router_authority": "SOLE",
        "upstream_router_authority": "NONE",
        "family_flow": list(WEB_REVERSE_FAMILY_FLOW),
        "reference": reference,
        "backend_candidates": candidates,
        "non_adopted_candidates": non_adopted,
        "existing_route_reconciliation": deepcopy(EXISTING_ROUTE_RECONCILIATION),
        "existing_reverse_skill": {
            "reference_module": EXISTING_REVERSE_SKILL_REFERENCE_MODULE,
            "pin": EXISTING_REVERSE_SKILL_PIN,
            "pin_status": EXISTING_REVERSE_SKILL_PIN_STATUS,
            "reconciliation": EXISTING_REVERSE_SKILL_RECONCILIATION,
        },
        "bootstrap_allowed": False,
        "auto_install_allowed": False,
        "mcp_registration_allowed": False,
        "browser_runtime_allowed": False,
        "network_runtime_allowed": False,
        "credential_use_allowed": False,
        "vendoring_allowed": False,
        "external_execution_authorized": False,
        "activation_requires_separate_bounded_task": True,
        "authorization_required_before_live_target_interaction": True,
    }


__all__ = [
    "BOUNDED_LOCAL_CLASSES",
    "EXISTING_REVERSE_SKILL_PIN",
    "EXISTING_REVERSE_SKILL_PIN_STATUS",
    "EXISTING_REVERSE_SKILL_RECONCILIATION",
    "EXISTING_REVERSE_SKILL_REFERENCE_MODULE",
    "EXISTING_ROUTE_RECONCILIATION",
    "LICENSE_BOUNDARIES",
    "LIVE_TARGET_CEILING",
    "NON_ADOPTED_UPSTREAMS",
    "PIN_VERIFIED_AT",
    "WEB_REVERSE_FAMILY_FLOW",
    "WEB_REVERSE_REFERENCE_MODULE",
    "WEB_REVERSE_REFERENCE_SCHEMA",
    "WebReverseReferenceError",
    "execution_class_is_truthful",
    "validate_reference_declarations",
    "web_reverse_reference_for",
    "web_reverse_reference_ids",
    "web_reverse_upstream_candidate",
]
