"""C35 Synthetic multi-target proof harness — deterministic fake
ExecutionTargets.

Identities: fake-manus / fake-codex / fake-claude / fake-grok /
fake-deepseek / fake-gemini / fake-hermes.

These identities are DELIBERATELY synthetic: they carry no real
certification claim, no live auth, and the honest historical/current
metadata reflects that. They exist so the SAME role specification and
role contract semantics can run through multiple materially different
target identities while core role behavior remains invariant (only
adapter/target identity differs).

NO LIVE BACKEND CALL: every execution passes through the existing C34
deterministic backend bridge; external API budget spend is zero.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping

from .backend_contract import BackendCapabilityCertification, BackendAdapterIdentity
from .role_contract import target_fingerprint_from_profile
from .role_eligibility import TargetCertificationRecord, certification_for_scope

FAKE_TARGET_IDS = (
    "fake-manus",
    "fake-codex",
    "fake-claude",
    "fake-grok",
    "fake-deepseek",
    "fake-gemini",
    "fake-hermes",
)

FAKE_TARGET_SCHEMA = "p2p-fake-execution-target/1"


def fake_target_identity(target_id: str) -> dict[str, Any]:
    """Explicit synthetic target identity. Never implies real certification."""
    if target_id not in FAKE_TARGET_IDS:
        raise ValueError("FAKE_TARGET_ID_INVALID:" + str(target_id))
    return {
        "schema": FAKE_TARGET_SCHEMA,
        "target_id": target_id,
        "synthetic": True,
        "real_certification_claimed": False,
        "harness": _harness_for(target_id),
        "provider": _provider_for(target_id),
        "model": f"{_provider_for(target_id)}-model-deterministic",
        "current_auth_state": "NO_CREDENTIALS",
        "environment_binding": "LOCAL_PROJECT",
    }


def _harness_for(target_id: str) -> str:
    mapping = {
        "fake-manus": "manus", "fake-codex": "codex", "fake-claude": "claude-code",
        "fake-grok": "grok", "fake-deepseek": "deepseek",
        "fake-gemini": "gemini", "fake-hermes": "hermes",
    }
    return mapping.get(target_id, "unknown")


def _provider_for(target_id: str) -> str:
    mapping = {
        "fake-manus": "manus", "fake-codex": "openai", "fake-claude": "anthropic",
        "fake-grok": "xai", "fake-deepseek": "deepseek",
        "fake-gemini": "google", "fake-hermes": "hermes",
    }
    return mapping.get(target_id, "unknown")


def fake_target_certification_record(
    target_id: str,
    *,
    certified_scopes: tuple[str, ...] = (),
    historical_certification: bool = False,
    current_auth_state: str = "NO_CREDENTIALS",
    environment_binding: str = "LOCAL_PROJECT",
) -> TargetCertificationRecord:
    """Build a synthetic certification record with honest metadata.

    Each scope listed in certified_scopes gets a LIVE_CERTIFIED_FOR_CAPABILITY
    record ONLY for testing the eligibility machinery — it never implies
    a real backend was certified. Unknown scopes remain UNKNOWN (fail closed)."""
    if target_id not in FAKE_TARGET_IDS:
        raise ValueError("FAKE_TARGET_ID_INVALID:" + str(target_id))
    adapter_id = f"adapter-{target_id}"
    certs = []
    for scope in certified_scopes:
        certs.append(BackendCapabilityCertification(
            adapter_id=adapter_id,
            scope=scope,
            status="LIVE_CERTIFIED_FOR_CAPABILITY",
            evidence_pointers=(f"synthetic-evidence:{target_id}:{scope}",),
            certified_at="2026-01-01T00:00:00+00:00",
        ))
    return TargetCertificationRecord(
        target_id=target_id,
        adapter_id=adapter_id,
        scope_certifications=tuple(certs),
        historical_certification=bool(historical_certification),
        current_auth_state=current_auth_state,
        environment_binding=environment_binding,
    )


def fake_target_adapter_identity(target_id: str) -> BackendAdapterIdentity:
    """Synthetic adapter identity registered behind the existing adapter
    boundary (C34 reuse). Vendor behavior stays behind that boundary."""
    identity = fake_target_identity(target_id)
    return BackendAdapterIdentity(
        adapter_id=f"adapter-{target_id}",
        adapter_version="1",
        adapter_state="ADAPTER_IMPLEMENTED",
        harness_identity=identity["harness"],
        provider_identity=identity["provider"],
        model_identity=identity["model"],
        protocol="synthetic-deterministic",
        toolset_capabilities=("synthetic-text-execution", "read-only-context"),
        workspace_binding="synthetic-workspace",
        environment_binding="LOCAL_PROJECT",
    )


def register_fake_targets(
    registry: Any,
    *,
    target_ids: tuple[str, ...] = FAKE_TARGET_IDS,
    auth_state: str = "NO_CREDENTIALS",
) -> list[dict[str, Any]]:
    """Register synthetic fake targets through the existing C34 registry
    surface (role_bridge.register_explicit_adapter reuse). No live auth,
    no secrets, no live backend call."""
    from .role_bridge import register_explicit_adapter
    registrations: list[dict[str, Any]] = []
    for target_id in target_ids:
        identity = fake_target_identity(target_id)
        registrations.append(register_explicit_adapter(
            registry,
            adapter_id=f"adapter-{target_id}",
            harness=identity["harness"],
            provider=identity["provider"],
            model=identity["model"],
            live_certified=False,
            auth_state=auth_state,
            synthetic=True,
        ))
    return registrations


def fake_target_fingerprint(target_id: str) -> str:
    identity = fake_target_identity(target_id)
    return target_fingerprint_from_profile(identity)
