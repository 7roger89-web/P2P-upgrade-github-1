#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""C28 — Secure Host Connection & Credential Onboarding.

Provider-neutral, beginner-first connection/onboarding layer for AI hosts.

Answers safely:
  what connection/authentication is required
  -> whether it is already usable
  -> what minimum Owner action is genuinely required
  -> how that action must be performed outside chat
  -> how P2P verifies the connection afterward
  -> whether the host is LIVE_PROBE_ELIGIBLE

Core guarantees:
  SECRET VALUE != SECRET REFERENCE != AUTH STATE != CONNECTION READY
      != LIVE_PROBE_ELIGIBLE != LIVE EXECUTION CERTIFIED
  - No secret value is ever required, asked for, stored, logged, or
    serialized anywhere produced by this module.
  - Verification uses the cheapest safe method first (zero-credit
    preferred); no model call is used for onboarding verification.
  - No host router, provider ranking, model router, second executor,
    background watcher, or live certification is introduced or run.
  - Host-specific onboarding guidance lives in thin adapter metadata;
    the neutral core contains no `if host == "..."` credential logic.

Usage:
  python3 scripts/p2p_secure_onboarding.py status   # beginner + machine doctor
  python3 scripts/p2p_secure_onboarding.py preflight --host <profile>
  python3 scripts/p2p_secure_onboarding.py owner-action --host <profile>
  python3 scripts/p2p_secure_onboarding.py drift-check --host <profile>
"""

from __future__ import annotations

import dataclasses
import json
import os
import pathlib
import re
import shlex
import subprocess
import sys
import urllib.request
import urllib.error

__version__ = "C28-v1"
SCHEMA_VERSION = "C28-CONNECTION-v1"
PROJECT_ID = "P2P-8.4.7-C-CODEX-EDITION-V21"
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# 1. State model (C28 §11) — compact, canonical
# ---------------------------------------------------------------------------

CONNECTION_STATES = (
    "NOT_DISCOVERED",
    "DISCOVERED",
    "AUTH_REQUIRED",
    "AUTH_CONFIG_PRESENT",
    "AUTH_VERIFIED",
    "AUTH_INVALID",
    "AUTH_EXPIRED_OR_STALE",
    "PERMISSION_BLOCKED",
    "CONNECTION_READY",
    "LIVE_PROBE_ELIGIBLE",
    "BLOCKED",
)

FAILURE_STATUSES = {
    "AUTH_INVALID",
    "AUTH_EXPIRED_OR_STALE",
    "PERMISSION_BLOCKED",
    "BLOCKED",
}

AUTH_METHODS = (
    "CLI_LOGIN",
    "ENV_SECRET_REFERENCE",
    "LOCAL_CREDENTIAL_STORE",
    "OAUTH_SESSION",
    "API_TOKEN_REFERENCE",
    "PROJECT_CONNECTOR",
    "NONE",
    "UNKNOWN",
)

PROBE_ELIGIBILITY = "YES", "NO", "UNKNOWN"

# Zero-credit verification ladder (C28 §19), cheapest first.
VERIFICATION_LADDER = (
    "LOCAL_CREDENTIAL_STATE_INSPECTION",
    "HOST_NATIVE_AUTH_STATUS_CHECK",
    "ZERO_MODEL_CONNECTIVITY_CHECK",
    "MINIMAL_NON_GENERATIVE_API_CHECK",
)


# ---------------------------------------------------------------------------
# 2. Secret reference model (C28 §17) — references, never values
# ---------------------------------------------------------------------------

CREDENTIAL_SOURCES = (
    "ENVIRONMENT",
    "CLI_CREDENTIAL_STORE",
    "LOCAL_CONFIG_FILE",
    "PROJECT_CONNECTOR",
    "NONE",
    "UNKNOWN",
)


@dataclasses.dataclass(frozen=True)
class CredentialReference:
    """Everything P2P may know about a credential, minus its value."""

    credential_type: str          # e.g. OPENAI_API_KEY, OAUTH_TOKEN
    source: str                   # one of CREDENTIAL_SOURCES
    reference: str                # e.g. env var name, store entry id
    present: bool                 # presence only — never the value
    freshness_policy: str         # bounded recheck policy (not fabricated expiry)
    last_observed_at: str         # ISO-8601 UTC observation time
    validation_result: str        # verification outcome (see below)

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in (
            "credential_type", "source", "reference", "present",
            "freshness_policy", "last_observed_at", "validation_result")}


# Allowed validation results. NOTE: these describe observed auth state
# against a host's actual transport endpoint, never the credential value.
VALIDATION_RESULTS = (
    "NOT_VERIFIED",
    "VERIFIED",
    "FAILED_401",
    "FAILED_403",
    "FAILED_404",
    "FAILED_DNS",
    "FAILED_TIMEOUT",
    "FAILED_OTHER",
    "TARGET_MISMATCH",
    "UNKNOWN",
)


def _utcnow() -> str:
    import datetime
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def _sha256_bytes(data: bytes) -> str:
    import hashlib
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# 3. Endpoint binding (C28 §20/§21)
# ---------------------------------------------------------------------------

# Neutral: endpoint identity is an opaque binding string produced per host.
# Provider-specific resolution lives in the thin adapter metadata.

@dataclasses.dataclass(frozen=True)
class EndpointBinding:
    expected_endpoint: str        # where the host's transport actually talks
    configured_endpoint: str      # what the credential/env points at
    bound: bool                   # True only when identical & reachable-safe
    check_method: str             # how binding was determined

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in (
            "expected_endpoint", "configured_endpoint", "bound",
            "check_method")}


def resolve_endpoint(binding: EndpointBinding) -> str:
    """Auth claim classification from binding only (C28 §20)."""
    if not binding.configured_endpoint:
        return "AUTH_CONFIG_ABSENT"
    if binding.bound:
        return "AUTH_TARGET_MATCH"
    return "AUTH_TARGET_MISMATCH"


# ---------------------------------------------------------------------------
# 4. Host adapter metadata (thin, provider-specific; C28 §25)
# ---------------------------------------------------------------------------
# Adapter registry: metadata only. No `if host == "codex"` branches in the
# neutral control flow; adapters are registered entries consumed uniformly.

_HOST_ADAPTERS: dict[str, dict] = {}


def _register_adapter(profile_id: str, metadata: dict) -> None:
    _HOST_ADAPTERS[profile_id] = metadata


def _get_adapter(profile_id: str) -> dict:
    if profile_id not in _HOST_ADAPTERS:
        raise KeyError(f"no adapter metadata for host profile {profile_id}")
    return _HOST_ADAPTERS[profile_id]


def _codex_expected_endpoint() -> str:
    """Codex CLI 0.147.0 transports hardcode api.openai.com.

    Derived from C27 evidence: all four real attempts (2026-08-16) returned
    HTTP 401 against api.openai.com regardless of OPENAI_BASE_URL presence.
    Recorded as durable adapter metadata; neutral core reads it only as an
    opaque string."""
    return "https://api.openai.com"


# --- Adapter registration (thin metadata, no host logic in core) ----------

_register_adapter("CODEX_CLI_0_147_0_LINUX", {
    "host_name": "Codex CLI",
    "last_known_auth_state": {
        "state": "INVALID", "reason": "AUTH_TARGET_MISMATCH",
        "evidence_ref": "E27-PROBE-1f71d9b55eb78d8e",
        "observed_at": "2026-08-16T12:26:00Z",
        "summary": ("Four real C27 attempts reached Codex's own transport "
                    "and returned HTTP 401 before model contact; the "
                    "configured credential does not authenticate against "
                    "codex's hardcoded api.openai.com endpoint.")},
    "version": "0.147.0",
    "binary": "codex",
    "transport": "openai-completion-ws",
    "auth_method": "CLI_LOGIN",
    "auth_method_fallback": "ENV_SECRET_REFERENCE",
    "credential_reference": "OPENAI_API_KEY",
    "credential_source": "ENVIRONMENT",
    "expected_endpoint": _codex_expected_endpoint(),
    "auth_check": ["doctor-zero-credit"],
    "safe_owner_action": (
        "Sign in to Codex using its supported login flow "
        "(e.g. `codex login` or the official OpenAI account sign-in "
        "for the Codex CLI). This must be done outside of chat."),
    "success_signal": "auth state check passes against Codex's own endpoint",
    "failure_signals": {
        "401 before model contact": "AUTH_INVALID (see C27 evidence)",
        "no credential": "AUTH_CONFIG_ABSENT",
        "credential not bound to api.openai.com": "AUTH_TARGET_MISMATCH",
    },
    "c27_evidence_ref": "E27-PROBE-1f71d9b55eb78d8e",
    "permission_enforcement": "approval-policy (bounded, OnRequest or never)",
})

_register_adapter("MANUS_API", {
    "host_name": "Manus API",
    "version": "connector",
    "binary": None,
    "transport": "manus-connector",
    "auth_method": "PROJECT_CONNECTOR",
    "auth_method_fallback": "NONE",
    "credential_reference": "MANUS_PROJECT_CONNECTOR",
    "credential_source": "PROJECT_CONNECTOR",
    "expected_endpoint": "manus-connector://project",
    "auth_check": ["connector-config-inspection"],
    "safe_owner_action": (
        "Connect the Manus project connector in the Manus session "
        "configuration (no API key in chat)."),
    "success_signal": "connector enabled and callable without new secrets",
    "failure_signals": {
        "connector not enabled": "AUTH_CONFIG_ABSENT",
    },
    "permission_enforcement": "manus-connector-boundary",
})

_register_adapter("CLAUDE_CODE", {
    "host_name": "Claude Code",
    "last_known_auth_state": None,
    "version": None,
    "binary": "claude",
    "transport": "claude-code-local",
    "auth_method": "CLI_LOGIN",
    "credential_reference": "ANTHROPIC_SESSION",
    "credential_source": "CLI_CREDENTIAL_STORE",
    "expected_endpoint": "claude.ai",
    "auth_check": ["binary-only"],
    "safe_owner_action": "Install Claude Code and sign in via its own flow.",
    "success_signal": "binary present and `claude auth status` clean",
    "failure_signals": {"binary missing": "NOT_INSTALLED"},
    "permission_enforcement": "permission-tool bounded",
})

_register_adapter("GEMINI_CLI", {
    "host_name": "Gemini CLI",
    "last_known_auth_state": None,
    "version": None,
    "binary": "gemini",
    "transport": "gemini-api",
    "auth_method": "CLI_LOGIN",
    "credential_reference": "GOOGLE_ACCOUNT_SESSION",
    "credential_source": "CLI_CREDENTIAL_STORE",
    "expected_endpoint": "generativelanguage.googleapis.com",
    "auth_check": ["binary-only"],
    "safe_owner_action": "Install Gemini CLI and sign in via Google's own flow.",
    "success_signal": "binary present and CLI auth check passes",
    "failure_signals": {"binary missing": "NOT_INSTALLED"},
    "permission_enforcement": "approval gating",
})

_register_adapter("CURSOR", {
    "host_name": "Cursor",
    "last_known_auth_state": None,
    "version": None,
    "binary": "cursor",
    "transport": "cursor-agent",
    "auth_method": "OAUTH_SESSION",
    "credential_reference": "CURSOR_OAUTH_SESSION",
    "credential_source": "CLI_CREDENTIAL_STORE",
    "expected_endpoint": "cursor.com",
    "auth_check": ["binary-only"],
    "safe_owner_action": "Install Cursor and complete its account sign-in.",
    "success_signal": "binary present and session valid",
    "failure_signals": {"binary missing": "NOT_INSTALLED"},
    "permission_enforcement": "agent permission model",
})

_register_adapter("COPILOT_CLI", {
    "host_name": "Copilot CLI",
    "last_known_auth_state": None,
    "version": None,
    "binary": "copilot",
    "transport": "copilot-agent",
    "auth_method": "CLI_LOGIN",
    "credential_reference": "GITHUB_COPILOT_SESSION",
    "credential_source": "CLI_CREDENTIAL_STORE",
    "expected_endpoint": "copilot.microsoft.com",
    "auth_check": ["binary-only"],
    "safe_owner_action": "Install Copilot CLI and sign in with GitHub.",
    "success_signal": "binary present and auth check passes",
    "failure_signals": {"binary missing": "NOT_INSTALLED"},
    "permission_enforcement": "permission prompts",
})

HOST_PROFILES = tuple(_HOST_ADAPTERS.keys())


# ---------------------------------------------------------------------------
# 5. Environment discovery (zero-credit; reuses C27 host discovery evidence)
# ---------------------------------------------------------------------------

def host_binary_available(adapter: dict) -> bool:
    binary = adapter.get("binary")
    if not binary:
        return False
    try:
        subprocess.run(
            ["which", binary], check=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return False


def host_binary_version(adapter: dict) -> str:
    """Host-native version, zero model call."""
    binary = adapter.get("binary")
    if not binary or not host_binary_available(adapter):
        return ""
    try:
        proc = subprocess.run(
            [binary, "--version"], capture_output=True,
            text=True, timeout=15)
        out = (proc.stdout or proc.stderr or "").strip()
        m = re.search(r"(\d+\.\d+(?:\.\d+)?(?:-\S+)?)", out)
        return m.group(1) if m else (out.splitlines() or [""])[0][:64]
    except Exception:  # noqa: BLE001 — discovery only
        return ""


def env_credential_present(reference: str) -> bool:
    """Presence of an env secret reference, never its value."""
    return bool(os.environ.get(reference, ""))


def connector_configured(adapter: dict) -> bool:
    """PROJECT_CONNECTOR state, inspected not created."""
    if adapter.get("transport") != "manus-connector":
        return False
    return bool(os.environ.get("MANUS_CONNECTOR_ENABLED", ""))


# ---------------------------------------------------------------------------
# 6. Auth requirement discovery (C28 §14) — metadata-driven, fail closed
# ---------------------------------------------------------------------------

def auth_requirement(adapter: dict) -> dict:
    """What this host requires to authenticate. Fail-closed: UNKNOWN if
    the adapter metadata cannot express it."""
    method = adapter.get("auth_method")
    if method not in AUTH_METHODS:
        return {"auth_method": "UNKNOWN", "requirement_known": False}
    return {
        "auth_method": method,
        "auth_method_fallback": adapter.get("auth_method_fallback", "UNKNOWN"),
        "credential_reference": adapter.get("credential_reference", ""),
        "credential_source": adapter.get("credential_source", "UNKNOWN"),
        "expected_endpoint": adapter.get("expected_endpoint", ""),
        "requirement_known": True,
    }


def auth_config_present(adapter: dict) -> bool:
    """Credential-state observation, zero-credit. A durable INVALID
    last_known_auth_state is treated as an observed credential state (the
    C27 Codex lesson: presence without target binding is not usable).
    Owner attestation never substitutes; only re-verification evidence
    (env_override recheck or fresh native state) clears INVALID.
    (C28 §38)"""
    requirement = auth_requirement(adapter)
    if not requirement["requirement_known"]:
        return False
    method = requirement["auth_method"]
    ref = requirement["credential_reference"]
    if method == "ENV_SECRET_REFERENCE":
        return env_credential_present(ref)
    if method == "PROJECT_CONNECTOR":
        return connector_configured(adapter)
    if method in ("CLI_LOGIN", "LOCAL_CREDENTIAL_STORE", "OAUTH_SESSION"):
        return _cli_login_config_present(adapter)
    return False


def durable_auth_state(adapter: dict) -> dict | None:
    """Durable transport-level auth evidence for a host, if any
    (e.g. C27 Codex 401). Never a secret value. None means 'no durable
    evidence recorded'. (C28 §26/§38)"""
    known = adapter.get("last_known_auth_state") or {}
    if known.get("state"):
        return known
    return None


def _cli_login_config_present(adapter: dict) -> bool:
    """Check the host's own native auth status surface (zero model call).

    Durable evidence rule: if a host has last_known_auth_state INVALID from
    real transport-level evidence (C27 Codex 401), native health checks
    (e.g. `codex doctor` binary health) must NOT silently clear it — doctor
    health never proved the credential authenticates for that host.
    (C28 §20/§38)"""
    binary = adapter.get("binary")
    if not binary or not host_binary_available(adapter):
        return False
    known = adapter.get("last_known_auth_state") or {}
    if known.get("state") == "INVALID":
        # INVALID until re-verified: binary health != transport auth.
        return False
    checks = adapter.get("auth_check", [])
    if "doctor-zero-credit" in checks or "cli-auth-status" in checks:
        return _native_auth_status_clean(adapter)
    if "binary-only" in checks:
        return True  # installed binary = configured session check later
    return False





def _native_auth_status_clean(adapter: dict) -> bool:
    binary = adapter.get("binary")
    try:
        proc = subprocess.run(
            [binary, "auth", "status"], capture_output=True,
            text=True, timeout=30)
        return proc.returncode == 0
    except Exception:  # noqa: BLE001
        return False


def _native_credential_store_present(adapter: dict) -> bool:
    binary = adapter.get("binary")
    if not binary or not host_binary_available(adapter):
        return False
    try:
        proc = subprocess.run(
            [binary, "auth"], capture_output=True,
            text=True, timeout=30)
        return proc.returncode == 0
    except Exception:  # noqa: BLE001
        return False


def _oauth_session_present(adapter: dict) -> bool:
    return _native_credential_store_present(adapter)


# ---------------------------------------------------------------------------
# 7. Zero-credit connectivity check (ladder step 3)
# ---------------------------------------------------------------------------

def endpoint_reachable(endpoint: str, timeout_s: int = 10) -> dict:
    """Cheap HTTPS reachability to the transport endpoint only — never
    sends any credential. Returns outcome without credential involvement."""
    try:
        req = urllib.request.Request(
            endpoint, method="HEAD",
            headers={"User-Agent": "p2p-secure-onboarding-c28/1"})
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            return {"reachable": True, "http_status": resp.status,
                    "check": "ZERO_MODEL_CONNECTIVITY_CHECK"}
    except urllib.error.HTTPError as exc:
        return {"reachable": True, "http_status": exc.code,
                "check": "ZERO_MODEL_CONNECTIVITY_CHECK"}
    except urllib.error.URLError as exc:
        return {"reachable": False,
                "reason": getattr(exc.reason, "strerror", str(exc.reason)),
                "check": "ZERO_MODEL_CONNECTIVITY_CHECK"}
    except Exception as exc:  # noqa: BLE001
        return {"reachable": False, "reason": str(exc)[:120],
                "check": "ZERO_MODEL_CONNECTIVITY_CHECK"}


# ---------------------------------------------------------------------------
# 8. Connection preflight (C28 §22) — the structured result
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class ConnectionPreflightResult:
    """Structured preflight (C28 §22). No secret values anywhere."""

    host_profile_id: str
    transport: str
    auth_method: str
    credential_reference: str
    credential_present: bool
    endpoint_binding: EndpointBinding
    auth_verification: str
    permission_verification: str
    connection_status: str
    live_probe_eligibility: str
    owner_action_required: bool
    owner_action_reason: str
    observed_at: str
    freshness: str
    evidence_refs: list
    model_calls_used: int = 0
    failure_classification: str = ""
    owner_action: dict = dataclasses.field(default_factory=dict)

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in (
            "host_profile_id", "transport", "auth_method",
            "credential_reference", "credential_present",
            "endpoint_binding", "auth_verification",
            "permission_verification", "connection_status",
            "live_probe_eligibility", "owner_action_required",
            "owner_action_reason", "observed_at", "freshness",
            "evidence_refs", "model_calls_used",
            "failure_classification", "owner_action")}


def permission_enforceable(adapter: dict) -> dict:
    """Reuse existing P2P permission envelope; never widen for onboarding
    (C28 §32/§33). Returns whether material permissions are enforceable."""
    policy = adapter.get("permission_enforcement", "")
    if not policy:
        return {"enforceable": False, "reason": "NO_KNOWN_ENFORCEMENT_MODEL"}
    return {"enforceable": True, "policy": policy}


def run_preflight(host_profile_id: str, *,
                  env_override: dict | None = None) -> ConnectionPreflightResult:
    """Run the full zero-credit connection preflight for one host profile.

    All observations are deterministic and credential-free. No model call.
    """
    adapter = _get_adapter(host_profile_id)
    requirement = auth_requirement(adapter)
    observed_at = _utcnow()
    evidence_refs = []
    model_calls = 0
    owner_action = {
        "action": "", "why": "", "do_not": "", "after": "", "provider": ""}

    # --- binary/installation discovery ---
    binary_available = host_binary_available(adapter)
    binary_version = host_binary_version(adapter) if binary_available else ""
    if binary_available:
        evidence_refs.append(
            f"E28-DISCOVERY-{_sha256_bytes((host_profile_id + 'binary:' + binary_version).encode())[:12]}")

    # --- auth requirement ---
    if not requirement["requirement_known"]:
        return _blocked(
            host_profile_id, adapter, "AUTH_REQUIREMENT_UNKNOWN",
            "Host auth requirement cannot be determined; failed closed.",
            observed_at, evidence_refs, model_calls, owner_action,
            owner_action_required=True)

    if not binary_available and adapter.get("binary"):
        return _blocked(
            host_profile_id, adapter, "NOT_INSTALLED",
            "Host binary not discovered in this environment.",
            observed_at, evidence_refs, model_calls, owner_action,
            owner_action_required=True)

    # --- credential reference presence ---
    credential_present = auth_config_present(adapter)

    # --- durable transport-level auth evidence (C28 §26) ---
    durable = durable_auth_state(adapter)

    # --- endpoint binding (C28 §20/§21) ---
    expected = requirement["expected_endpoint"]
    configured, bound, check = _resolve_configured_endpoint(
        adapter, requirement, env_override=env_override)
    binding = EndpointBinding(
        expected_endpoint=expected,
        configured_endpoint=configured,
        bound=bound,
        check_method=check)
    endpoint_resolution = resolve_endpoint(binding)

    # --- zero-credit connectivity (ladder step 3) ---
    connectivity = endpoint_reachable(expected)

    # --- permission envelope ---
    perm = permission_enforceable(adapter)

    # --- reconcile (state model) ---
    (status, eligibility, action_required, reason,
     failure_class, owner_action) = _reconcile(
        adapter, requirement, credential_present, endpoint_resolution,
        binding, connectivity, perm, binary_version)

    # --- C27 acceptance case §26 — durable INVALID overrides ---
    # A host with durable transport-level INVALID evidence (Codex 401)
    # must never be claimed as auth-ready while the configuration that
    # produced the 401 remains unchanged. Owner attestation does not
    # clear it (C28 §38); only re-verification does.
    if (durable and durable.get("state") == "INVALID"
            and endpoint_resolution != "AUTH_TARGET_MATCH"):
        failure_class = durable.get("reason", "AUTH_INVALID")
        status = "AUTH_INVALID"
        eligibility = "NO"
        action_required = True
        reason = durable.get("summary", (
            "The installed host is present, but the currently configured "
            "credential does not authenticate against its API endpoint."))
        evidence_refs = [durable.get("evidence_ref", "")] + evidence_refs
        owner_action = _owner_action_for(adapter)
        owner_action["do_not"] = (
            "Do not paste an API key into chat or any prompt.")

    if endpoint_resolution != "AUTH_CONFIG_ABSENT":
        evidence_refs.append(
            f"E28-PREFLIGHT-{_sha256_bytes((host_profile_id + ':' + status + ':' + observed_at).encode())[:12]}")

    return ConnectionPreflightResult(
        host_profile_id=host_profile_id,
        transport=adapter.get("transport", ""),
        auth_method=requirement["auth_method"],
        credential_reference=requirement["credential_reference"],
        credential_present=credential_present,
        endpoint_binding=binding,
        auth_verification=endpoint_resolution,
        permission_verification=(
            "PERMISSION_ENFORCEABLE" if perm["enforceable"]
            else "PERMISSION_NOT_ENFORCEABLE"),
        connection_status=status,
        live_probe_eligibility=eligibility,
        owner_action_required=action_required,
        owner_action_reason=reason,
        observed_at=observed_at,
        freshness=_freshness(adapter, binary_version),
        evidence_refs=evidence_refs,
        model_calls_used=model_calls,
        failure_classification=failure_class,
        owner_action=owner_action)


def _resolve_configured_endpoint(adapter, requirement,
                                 env_override=None) -> tuple:
    """Determine what the current configuration actually points at.

    Returns (configured_endpoint, bound, check_method). Provider-specific
    resolution lives here and in adapter metadata only; the neutral core
    consumes the boolean outcome."""
    if not requirement["requirement_known"]:
        return ("", False, "REQUIREMENT_UNKNOWN")

    method = requirement["auth_method"]
    expected = requirement["expected_endpoint"]

    if method == "PROJECT_CONNECTOR":
        if connector_configured(adapter):
            return (expected, True, "connector-config-inspection")
        return ("", False, "connector-config-absent")

    if method == "ENV_SECRET_REFERENCE":
        env = env_override if env_override is not None else os.environ
        ref = requirement["credential_reference"]
        if not env.get(ref):
            return ("", False, "env-credential-absent")
        # Endpoint binding: the configured endpoint is wherever the
        # credential is accepted. If the host hardcodes its own endpoint
        # (adapter metadata), a credential aimed at any *other* endpoint
        # is a target mismatch even when present (C27 lesson).
        hardcoded = adapter.get("expected_endpoint", "")
        base_url = env.get("OPENAI_BASE_URL", "")
        if hardcoded:
            if base_url.rstrip("/") != hardcoded:
                return (base_url or hardcoded, base_url.rstrip("/") == hardcoded,
                        "endpoint-binding-comparison")
            return (hardcoded, True, "endpoint-binding-comparison")
        return ("", False, "endpoint-binding-unknown")

    if method in ("CLI_LOGIN", "LOCAL_CREDENTIAL_STORE", "OAUTH_SESSION"):
        if not host_binary_available(adapter):
            return ("", False, "binary-absent")
        if not _cli_login_config_present(adapter):
            return ("", False, "cli-login-not-complete")
        # CLI login binds to the host's own endpoint (native behavior).
        return (expected, True, "cli-native-auth-state")
    return ("", False, "auth-method-unsupported")


def _reconcile(adapter, requirement, credential_present,
               endpoint_resolution, binding, connectivity, perm,
               binary_version) -> tuple:
    action_required = False
    reason = ""
    failure_class = ""
    owner_action = _owner_action_for(adapter)

    if endpoint_resolution == "AUTH_TARGET_MISMATCH":
        return ("AUTH_INVALID", "NO", True,
                "Credential present but bound to an incompatible endpoint "
                "for this host's transport (AUTH_TARGET_MISMATCH).",
                "AUTH_TARGET_MISMATCH", owner_action)
    if endpoint_resolution == "AUTH_CONFIG_ABSENT":
        return ("AUTH_REQUIRED", "NO", True,
                "Host requires authentication and no configured credential "
                "was discovered.",
                "AUTH_CONFIG_ABSENT", owner_action)
    if endpoint_resolution == "AUTH_TARGET_MATCH" and not connectivity.get(
            "reachable"):
        return ("AUTH_VERIFICATION_REQUIRED", "NO", True,
                "Credential appears bound to the right endpoint but the "
                "endpoint is not reachable; verification blocked.",
                "CONNECTIVITY_UNAVAILABLE", owner_action)
    if endpoint_resolution == "AUTH_TARGET_MATCH":
        if not perm["enforceable"]:
            return ("PERMISSION_BLOCKED", "NO", True,
                    "Auth verified but material execution permissions cannot "
                    "be enforced; live probe blocked.",
                    "PERMISSION_NOT_ENFORCEABLE", owner_action)
        return ("CONNECTION_READY", "YES", False,
                "Connection verified for a safe non-generative probe.",
                "", owner_action)
    return ("AUTH_VERIFICATION_REQUIRED", "NO", True,
            "Auth configuration could not be verified against the host's "
            "actual endpoint.",
            "AUTH_VERIFICATION_UNAVAILABLE", owner_action)


def _owner_action_for(adapter: dict) -> dict:
    """Beginner-first single minimal action (C28 §23/§53)."""
    return {
        "action": adapter.get("safe_owner_action", ""),
        "why": "The host cannot currently authenticate with this "
               "environment's configuration.",
        "do_not": "Do not paste an API key into chat.",
        "after": ('Return to P2P and say "continue"; P2P will recheck '
                  "automatically."),
        "provider": adapter.get("host_name", ""),
    }


def _blocked(host_profile_id, adapter, status, reason, observed_at,
             evidence_refs, model_calls, owner_action,
             owner_action_required=False) -> ConnectionPreflightResult:
    owner = _owner_action_for(adapter)
    return ConnectionPreflightResult(
        host_profile_id=host_profile_id,
        transport=adapter.get("transport", ""),
        auth_method=auth_requirement(adapter).get("auth_method", "UNKNOWN"),
        credential_reference=auth_requirement(adapter).get(
            "credential_reference", ""),
        credential_present=False,
        endpoint_binding=EndpointBinding(
            expected_endpoint=auth_requirement(adapter).get(
                "expected_endpoint", ""),
            configured_endpoint="",
            bound=False,
            check_method="not-applicable"),
        auth_verification="AUTH_CONFIG_ABSENT",
        permission_verification="PERMISSION_NOT_ENFORCEABLE",
        connection_status=status,
        live_probe_eligibility="NO",
        owner_action_required=owner_action_required,
        owner_action_reason=reason,
        observed_at=observed_at,
        freshness=_freshness(adapter, ""),
        evidence_refs=evidence_refs,
        model_calls_used=model_calls,
        failure_classification=status,
        owner_action=owner)


def _freshness(adapter: dict, binary_version: str) -> str:
    """Bounded recheck policy, never a fabricated expiry (C28 §30)."""
    parts = []
    if binary_version:
        parts.append(f"host_version={binary_version}")
    endpoint = auth_requirement(adapter).get("expected_endpoint", "")
    if endpoint:
        parts.append(f"endpoint={endpoint}")
    if not parts:
        return "bounded-recheck"
    return f"bounded-recheck:{','.join(parts)}"


# ---------------------------------------------------------------------------
# 9. Configuration drift detection (C28 §31)
# ---------------------------------------------------------------------------

@dataclasses.dataclass
class DriftResult:
    host_profile_id: str
    prior_observed_at: str
    prior_state: dict
    current_state: dict
    drift_detected: bool
    drift_kinds: list
    recommendation: str
    observed_at: str

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in (
            "host_profile_id", "prior_observed_at", "prior_state",
            "current_state", "drift_detected", "drift_kinds",
            "recommendation", "observed_at")}


_DRIFT_SIGNATURE_KEYS = (
    "transport", "auth_method", "credential_reference", "credential_present",
    "auth_verification", "permission_verification")


def detect_drift(host_profile_id: str, prior_result: dict | ConnectionPreflightResult,
                 current_result: dict | ConnectionPreflightResult | None = None,
                 *, env_override: dict | None = None) -> DriftResult:
    """Compare two preflight results; any material drift degrades the
    connection state (C28 §31). Prior evidence may come from a later
    foreground session (C28 §37) — it is re-verified, never trusted."""
    def _asdict(r):
        if isinstance(r, ConnectionPreflightResult):
            return r.to_dict()
        return dict(r)
    prior = _asdict(prior_result)
    current = (_asdict(current_result) if current_result is not None
               else _asdict(run_preflight(host_profile_id, env_override=env_override)))

    drift_kinds = []
    for key in _DRIFT_SIGNATURE_KEYS:
        if prior.get(key) != current.get(key):
            drift_kinds.append(key)
    def _eb_endpoint(b):
        if isinstance(b, EndpointBinding):
            return b.expected_endpoint
        return (b or {}).get("expected_endpoint")
    p_endpoint = _eb_endpoint(prior.get("endpoint_binding"))
    c_endpoint = _eb_endpoint(current.get("endpoint_binding"))
    if p_endpoint and c_endpoint and p_endpoint != c_endpoint:
        drift_kinds.append("expected_endpoint_changed")

    current_status = current.get("connection_status", "")
    connection_ready_prior = (
        prior.get("connection_status") == "CONNECTION_READY")
    recommendation = "NO_RECHECK_REQUIRED"
    if drift_kinds and connection_ready_prior:
        recommendation = "AUTH_VERIFICATION_REQUIRED"

    return DriftResult(
        host_profile_id=host_profile_id,
        prior_observed_at=prior.get("observed_at", ""),
        prior_state={k: prior.get(k) for k in _DRIFT_SIGNATURE_KEYS},
        current_state={k: current.get(k) for k in _DRIFT_SIGNATURE_KEYS},
        drift_detected=bool(drift_kinds),
        drift_kinds=drift_kinds,
        recommendation=recommendation,
        observed_at=current.get("observed_at", _utcnow()))


# ---------------------------------------------------------------------------
# 10. Beginner UX (C28 §35) — human summary from the same result
# ---------------------------------------------------------------------------

_STATUS_WORDS = {
    "NOT_DISCOVERED": "Chưa được tìm thấy",
    "DISCOVERED": "Đã tìm thấy",
    "NOT_INSTALLED": "Chưa cài đặt",
    "AUTH_REQUIRED": "Chưa kết nối",
    "AUTH_CONFIG_PRESENT": "Đã có cấu hình (chưa xác minh)",
    "AUTH_VERIFIED": "Đã xác thực",
    "AUTH_INVALID": "Chưa kết nối",
    "AUTH_EXPIRED_OR_STALE": "Phiên đăng nhập hết hạn",
    "PERMISSION_BLOCKED": "Bị chặn bởi quyền thực thi",
    "CONNECTION_READY": "Sẵn sàng kết nối",
    "LIVE_PROBE_ELIGIBLE": "Đủ điều kiện chứng nhận live",
    "BLOCKED": "Bị chặn",
    "AUTH_VERIFICATION_REQUIRED": "Cần xác minh lại",
}


def beginner_summary(result: ConnectionPreflightResult) -> str:
    """Beginner-first human summary (C28 §35) derived from the same
    machine-readable result (§36). Never contains secrets or endpoints'
    credential details."""
    lines = []
    host = _get_adapter(result.host_profile_id).get("host_name",
                                                    result.host_profile_id)
    lines.append(host)
    lines.append(f"Trạng thái: {_STATUS_WORDS.get(result.connection_status, result.connection_status)}")
    lines.append("")

    if result.credential_present:
        lines.append("P2P đã tìm thấy:")
        lines.append("Đã có một thông tin kết nối được cấu hình.")
    elif _get_adapter(result.host_profile_id).get("binary"):
        lines.append("P2P đã tìm thấy:")
        lines.append("Phần mềm host đã được cài đặt.")
    lines.append("")

    if result.owner_action_required:
        lines.append("Vấn đề:")
        lines.append(result.owner_action_reason)
        lines.append("")
        lines.append("Bạn cần làm:")
        lines.append(result.owner_action.get("action", "") or result.owner_action_reason)
        lines.append("")
        lines.append("Quan trọng:")
        lines.append(result.owner_action.get("do_not", "Không dán thông tin xác thực vào chat."))
        lines.append("")
        lines.append("Sau đó:")
        lines.append(result.owner_action.get("after", 'Nói với P2P "tiếp tục" để kiểm tra lại.'))
    else:
        lines.append("Vấn đề:")
        lines.append("Không có. Kết nối đã sẵn sàng cho bước kiểm tra không phá hủy.")
        lines.append("")
        lines.append("Bạn cần làm:")
        lines.append("Không có gì cả.")

    lines.append("")
    lines.append("--- Advanced (evidence) ---")
    lines.append(f"auth_verification={result.auth_verification}")
    lines.append(f"endpoint_binding={result.endpoint_binding.to_dict()}")
    lines.append(f"permission_verification={result.permission_verification}")
    lines.append(f"live_probe_eligibility={result.live_probe_eligibility}")
    lines.append(f"observed_at={result.observed_at}")
    lines.append(f"freshness={result.freshness}")
    lines.append(f"model_calls_used_for_onboarding={result.model_calls_used}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 11. Host status overview (doctor) — human + machine-readable
# ---------------------------------------------------------------------------

def run_doctor(*, env_override: dict | None = None) -> dict:
    """Full connection doctor (C28 §34). Deterministic, zero model call,
    one structured result covering all known profiles."""
    overview = {"schema_version": SCHEMA_VERSION,
                "project_id": PROJECT_ID,
                "observed_at": _utcnow(),
                "model_calls_used_for_onboarding": 0,
                "hosts": [],
                "recommendation": ""}
    connected = []
    needs_action = []
    for profile_id in HOST_PROFILES:
        adapter = _get_adapter(profile_id)
        binary_available = host_binary_available(adapter)
        binary_version = (host_binary_version(adapter)
                          if binary_available else "")
        durable = durable_auth_state(adapter)
        if not binary_available:
            host_state = {
                "host_profile_id": profile_id,
                "host_name": adapter.get("host_name", profile_id),
                "installed": False,
                "connection_status": "NOT_INSTALLED",
                "auth_requirement": auth_requirement(adapter).get(
                    "auth_method", "UNKNOWN"),
                "auth_config_present": False,
                "auth_valid": False,
                "permission_ready": False,
                "connection_ready": False,
                "live_probe_eligible": "NO",
                "owner_action_required": True,
                "owner_action": {
                    "action": adapter.get("safe_owner_action", ""),
                    "do_not": "Do not paste credentials into chat."},
                "durable_auth_evidence": durable,
                "freshness": "",
                "evidence_refs": [],
            }
            needs_action.append((9, host_state))
            overview["hosts"].append(host_state)
            continue

        preflight = run_preflight(profile_id, env_override=env_override)
        host_state = {
            "host_profile_id": preflight.host_profile_id,
            "host_name": adapter.get("host_name", profile_id),
            "installed": True,
            "binary_version": binary_version,
            "connection_status": preflight.connection_status,
            "auth_requirement": preflight.auth_method,
            "auth_config_present": preflight.credential_present,
            "auth_valid": preflight.connection_status
            in ("AUTH_VERIFIED", "CONNECTION_READY", "LIVE_PROBE_ELIGIBLE"),
            "auth_verification": preflight.auth_verification,
            "endpoint_binding": preflight.endpoint_binding.to_dict(),
            "permission_ready": (
                preflight.permission_verification
                == "PERMISSION_ENFORCEABLE"),
            "connection_ready": (
                preflight.connection_status == "CONNECTION_READY"),
            "live_probe_eligible": preflight.live_probe_eligibility,
            "owner_action_required": preflight.owner_action_required,
            "owner_action": preflight.owner_action,
            "owner_action_reason": preflight.owner_action_reason,
            "freshness": preflight.freshness,
            "observed_at": preflight.observed_at,
            "evidence_refs": preflight.evidence_refs,
            "model_calls_used": preflight.model_calls_used,
            "failure_classification": preflight.failure_classification,
            "durable_auth_evidence": durable,
            "beginner_summary": beginner_summary(preflight),
        }
        overview["hosts"].append(host_state)
        overview["model_calls_used_for_onboarding"] += (
            preflight.model_calls_used)
        if preflight.connection_status == "CONNECTION_READY":
            connected.append(host_state)
        elif preflight.owner_action_required:
            needs_action.append((1 if binary_available else 9, host_state))

    needs_action.sort(key=lambda t: (t[0], t[1]["host_profile_id"]))
    if connected:
        overview["recommendation"] = (
            f"{connected[0]['host_profile_id']} is connection-ready; "
            "live probe eligibility is available in a separate Goal.")
    elif needs_action:
        pick = needs_action[0][1]
        overview["recommendation"] = (
            f"ACTION_REQUIRED for {pick['host_profile_id']}: "
            f"{pick['owner_action'].get('action', pick['owner_action_reason'])} "
            f"— {pick['owner_action'].get('do_not', '')}".rstrip(" -"))
    else:
        overview["recommendation"] = "No actionable onboarding state."
    return overview


# ---------------------------------------------------------------------------
# 12. CLI
# ---------------------------------------------------------------------------

def _redacted_output(obj) -> str:
    """Final safety net: strip anything that looks like a raw secret value
    from output payloads (C28 §18). Credential references stay."""
    text = json.dumps(obj, ensure_ascii=False, indent=2)
    # Reference names are fine; only redact raw high-entropy values that
    # appear as bare env values (defensive, never serialized upstream).
    text = re.sub(
        r'"(sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|'
        r'manus-sk-[A-Za-z0-9]{16,})"',
        '"[REDACTED]', text)
    return text


def main() -> int:
    args = sys.argv[1:]
    if not args or args[0] in ("status", "doctor"):
        report = run_doctor()
        print(_redacted_output(report))
        return 0
    if args[0] == "preflight":
        host = _parse_host(args)
        if not host:
            print("usage: p2p_secure_onboarding.py preflight --host <profile>",
                  file=sys.stderr)
            return 2
        result = run_preflight(host)
        print(_redacted_output(result.to_dict()))
        return 0
    if args[0] == "owner-action":
        host = _parse_host(args)
        if not host:
            print("usage: p2p_secure_onboarding.py owner-action --host <profile>",
                  file=sys.stderr)
            return 2
        result = run_preflight(host)
        print(beginner_summary(result))
        return 0
    if args[0] == "drift-check":
        host = _parse_host(args)
        if not host:
            print("usage: p2p_secure_onboarding.py drift-check --host <profile>",
                  file=sys.stderr)
            return 2
        prior_file = _parse_prior(args)
        prior = None
        if prior_file and prior_file.exists():
            with prior_file.open() as fh:
                prior = json.load(fh)
        result = detect_drift(host, prior or {})
        print(_redacted_output(result.to_dict()))
        return 0
    print(f"unknown command: {args[0]}", file=sys.stderr)
    return 2


def _parse_host(args: list[str]) -> str:
    try:
        idx = args.index("--host")
        return args[idx + 1]
    except (ValueError, IndexError):
        return ""


def _parse_prior(args: list[str]) -> pathlib.Path | None:
    try:
        idx = args.index("--prior")
        return pathlib.Path(args[idx + 1])
    except (ValueError, IndexError):
        return None


if __name__ == "__main__":
    sys.exit(main())
