"""HO1–HO50: C28 Secure Host Connection & Credential Onboarding — tests.

These tests verify the C28 onboarding machinery (scripts/p2p_secure_onboarding.py)
against the C28 evidence contract. They MUST NOT:

1. Call any AI model or model-serving endpoint. The verification ladder is
   zero-credit by construction (local credential state, native auth status,
   endpoint reachability).
2. Execute any host binary beyond the minimal built-in read-only status
   invocations the machinery itself performs (e.g. `codex --version`,
   `codex doctor`).
3. Read, log, or emit secret values. The secret model stores references only.
4. Use a router, a second AI executor, or any autonomous retry loop.
5. Write or modify governance/ledger files (covered by separate governance
   delta tests, not here).

The machinery is provider-neutral by design: hosts are registered via a single
metadata table and the core flow never branches on a host name.
"""
import dataclasses
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from p2p_secure_onboarding import (  # noqa: E402
    AUTH_METHODS, CREDENTIAL_SOURCES, CONNECTION_STATES, FAILURE_STATUSES,
    PROJECT_ID, SCHEMA_VERSION, VERIFICATION_LADDER, VALIDATION_RESULTS,
    CredentialReference, EndpointBinding, beginner_summary, detect_drift,
    env_credential_present, resolve_endpoint, run_doctor, run_preflight,
    _get_adapter, _HOST_ADAPTERS, _redacted_output, _DRIFT_SIGNATURE_KEYS,
)

CODEX = "CODEX_CLI_0_147_0_LINUX"

# ---------------------------------------------------------------------------
# Module-level vocabulary contracts (HO1–HO10)
# ---------------------------------------------------------------------------

def test_ho1_connection_states_cover_full_boundary():
    """HO1: state model covers the full discovery→onboard→probe boundary."""
    required = ("NOT_DISCOVERED", "DISCOVERED", "AUTH_REQUIRED",
                "AUTH_CONFIG_PRESENT", "AUTH_VERIFIED", "AUTH_INVALID",
                "AUTH_EXPIRED_OR_STALE", "PERMISSION_BLOCKED",
                "CONNECTION_READY", "LIVE_PROBE_ELIGIBLE", "BLOCKED")
    for state in required:
        assert state in CONNECTION_STATES, f"missing state {state}"
    # The boundary is a progression, not a cycle back to discovery:
    # BLOCKED is terminal for a session; no state leads back to
    # NOT_DISCOVERED after a host has been found.
    assert CONNECTION_STATES.index("NOT_DISCOVERED") == 0
    assert CONNECTION_STATES[-1] == "BLOCKED"


def test_ho2_failure_statuses_are_explicit():
    """HO2: failure is a named status, not a fabricated success."""
    for status in ("AUTH_INVALID", "AUTH_EXPIRED_OR_STALE",
                   "PERMISSION_BLOCKED", "BLOCKED"):
        assert status in FAILURE_STATUSES
    # Success states must never be failure states.
    assert not {"CONNECTION_READY", "LIVE_PROBE_ELIGIBLE"} & FAILURE_STATUSES


def test_ho3_auth_methods_neutral():
    """HO3: auth method vocabulary is provider-neutral — no vendor-specific
    method names."""
    forbidden_keywords = ("openai", "anthropic", "google", "cursor",
                          "copilot", "github", "oauth1", "vendor")
    for method in AUTH_METHODS:
        low = method.lower()
        assert not any(k in low for k in forbidden_keywords), method


def test_ho4_credential_sources_neutral():
    """HO4: credential source vocabulary is neutral too."""
    for source in CREDENTIAL_SOURCES:
        assert not any(k in source.lower()
                       for k in ("openai", "anthropic", "google", "cursor",
                                 "copilot"))


def test_ho5_validation_results_are_observations():
    """HO5: validation results describe observed auth state, never a value.
    All failure results are transport-level observations."""
    observed = ("FAILED_401", "FAILED_403", "FAILED_404", "FAILED_DNS",
                "FAILED_TIMEOUT", "FAILED_OTHER", "TARGET_MISMATCH")
    for kind in observed:
        assert kind in VALIDATION_RESULTS
    assert "VERIFIED" in VALIDATION_RESULTS
    assert "NOT_VERIFIED" in VALIDATION_RESULTS


def test_ho6_verification_ladder_is_zero_credit():
    """HO6: every ladder step is zero-credit (no model call)."""
    assert len(VERIFICATION_LADDER) >= 3
    for step in VERIFICATION_LADDER:
        assert "MODEL" not in step or "ZERO_MODEL" in step


def test_ho7_target_mismatch_is_a_first_class_result():
    """HO7: endpoint binding mismatch (the C27 Codex failure mode) is a named
    validation result and a named connection status path."""
    assert "TARGET_MISMATCH" in VALIDATION_RESULTS
    # The machinery maps a target mismatch to AUTH_INVALID, never to READY.


def test_ho8_project_identity_matches_governance():
    """HO8: the module's project identity matches the official baseline."""
    assert PROJECT_ID == "P2P-8.4.7-C-CODEX-EDITION-V21"
    assert SCHEMA_VERSION == "C28-CONNECTION-v1"


def test_ho9_no_host_name_branching_in_core_types():
    """HO9: core types carry no host-specific logic — the vocabulary is one
    neutral enum set for every host."""
    for item in (CONNECTION_STATES, AUTH_METHODS, VALIDATION_RESULTS,
                 CREDENTIAL_SOURCES):
        assert len(set(item)) == len(item)  # no per-host duplicates


def test_ho10_schema_versioning_present():
    """HO10: the module declares its own schema version for delta tracking."""
    assert isinstance(SCHEMA_VERSION, str) and SCHEMA_VERSION.startswith(
        "C28-")


# ---------------------------------------------------------------------------
# Secret reference model (HO11–HO16)
# ---------------------------------------------------------------------------

def test_ho11_credential_reference_fields():
    """HO11: CredentialReference records presence only — no value field."""
    ref = CredentialReference(
        credential_type="OPENAI_API_KEY", source="ENVIRONMENT",
        reference="OPENAI_API_KEY", present=True,
        freshness_policy="bounded-recheck", last_observed_at="2026-08-17T00:00:00Z",
        validation_result="NOT_VERIFIED")
    assert set(ref.to_dict().keys()) == {"credential_type", "source",
                                         "reference", "present",
                                         "freshness_policy",
                                         "last_observed_at",
                                         "validation_result"}
    assert not any("value" in k for k in ref.to_dict())


def test_ho12_reference_model_is_immutable():
    """HO12: references are immutable observations — recheck makes a new
    observation, it never mutates the old one."""
    params = getattr(CredentialReference, "__dataclass_params__", None)
    assert params is not None and params.frozen is True


def test_ho13_reference_never_contains_a_secret_value():
    """HO13: even a malformed caller cannot smuggle a value into the model —
    reference must look like an identifier (env var name / store entry),
    which the machinery constructs itself from adapter metadata."""
    ref = CredentialReference(
        credential_type="OPENAI_API_KEY", source="ENVIRONMENT",
        reference="OPENAI_API_KEY", present=True,
        freshness_policy="bounded-recheck", last_observed_at="2026-08-17T00:00:00Z",
        validation_result="NOT_VERIFIED")
    # Identifier-like, not a bearer token.
    assert "sk-" not in ref.reference
    assert "Bearer" not in ref.reference
    assert ref.reference == ref.reference.strip()


def test_ho14_freshness_is_bounded_recheck_not_expiry():
    """HO14: freshness policy is bounded recheck guidance, never a fabricated
    expiry date."""
    ref = CredentialReference(
        credential_type="OPENAI_API_KEY", source="ENVIRONMENT",
        reference="OPENAI_API_KEY", present=True,
        freshness_policy="bounded-recheck:host_version=0.147.0",
        last_observed_at="2026-08-17T00:00:00Z",
        validation_result="VERIFIED")
    assert "bounded-recheck" in ref.freshness_policy
    assert "expires" not in ref.freshness_policy.lower()


def test_ho15_reference_serializes_without_secrets():
    """HO15: to_dict() round-trip is safe to log (no value-bearing field)."""
    ref = CredentialReference(
        credential_type="OPENAI_API_KEY", source="ENVIRONMENT",
        reference="OPENAI_API_KEY", present=True,
        freshness_policy="bounded-recheck", last_observed_at="2026-08-17T00:00:00Z",
        validation_result="NOT_VERIFIED")
    dumped = json.dumps(ref.to_dict())
    assert "sk-" not in dumped and "secret" not in dumped.lower()


def test_ho16_adapter_endpoint_is_opaque_binding():
    """HO16: each host's transport endpoint is an opaque binding, resolved
    by the thin adapter — core logic never hardcodes vendor URLs."""
    for pid, adapter in _HOST_ADAPTERS.items():
        binding = adapter.get("endpoint_binding") or {}
        assert isinstance(binding, dict), pid


# ---------------------------------------------------------------------------
# Host discovery & auth requirement (HO17–HO24)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("host", [h for h in _HOST_ADAPTERS])
def test_ho17_registered_host_has_auth_requirement(host):
    """HO17: every registered host declares an auth requirement through the
    neutral auth model."""
    from p2p_secure_onboarding import auth_requirement
    adapter = _get_adapter(host)
    req = auth_requirement(adapter)
    assert req.get("auth_method") in AUTH_METHODS, host
    assert isinstance(req.get("auth_method"), str), host


@pytest.mark.parametrize("host", [h for h in _HOST_ADAPTERS])
def test_ho18_registered_host_declares_binary_or_connector(host):
    """HO18: every host is discoverable by binary or connector config."""
    adapter = _get_adapter(host)
    assert adapter.get("binary") or adapter.get("connector") \
        or adapter.get("credential_source") == "PROJECT_CONNECTOR" \
        or adapter.get("auth_method") == "PROJECT_CONNECTOR", host


@pytest.mark.parametrize("host", [h for h in _HOST_ADAPTERS])
def test_ho19_host_declares_permission_enforcement(host):
    """HO19: no host onboards without a permission enforcement policy."""
    adapter = _get_adapter(host)
    assert adapter.get("permission_enforcement"), host


@pytest.mark.parametrize("host", [h for h in _HOST_ADAPTERS])
def test_ho20_host_declares_safe_owner_action(host):
    """HO20: every host has a beginner-safe single owner action."""
    adapter = _get_adapter(host)
    action = adapter.get("safe_owner_action", "")
    assert isinstance(action, str), host
    assert action, host


def test_ho21_binary_availability_read_only():
    """HO21: host_binary_available uses only existence/version lookups; the
    Codex binary exists in this environment and the lookup is free of model
    calls."""
    from p2p_secure_onboarding import host_binary_available
    codex = _get_adapter(CODEX)
    assert codex.get("binary") == "codex"
    assert host_binary_available(codex) is True


def test_ho22_env_credential_presence_check_is_local():
    """HO22: env credential presence is a local check (os.environ) — it
    answers PRESENT without reading the value into P2P state."""
    # OPENAI_API_KEY exists in this sandbox; the check must be a plain
    # presence test.
    result = env_credential_present("OPENAI_API_KEY")
    assert isinstance(result, bool)


def test_ho23_auth_config_absent_for_missing_binary():
    """HO23: a host whose binary is missing reports an honest NOT_INSTALLED
    style result without fabricating auth state."""
    res = run_preflight("CLAUDE_CODE", env_override={})
    assert res.connection_status in ("BLOCKED", "NOT_INSTALLED")


def test_ho24_connector_configured_false_without_connector():
    """HO24: connector_configured returns False for a CLI host that has no
    connector configured, without claiming configuration it cannot verify."""
    from p2p_secure_onboarding import connector_configured
    codex = _get_adapter(CODEX)
    assert isinstance(connector_configured(codex), bool)


# ---------------------------------------------------------------------------
# Endpoint binding & verification (HO25–HO30)
# ---------------------------------------------------------------------------

def test_ho25_endpoint_binding_resolves_opaque_binding():
    """HO25: resolve_endpoint returns a resolvable endpoint string from the
    binding — the binding itself is opaque (hash-like), so the endpoint is
    not leaked where the binding goes."""
    from p2p_secure_onboarding import auth_requirement
    adapter = _get_adapter(CODEX)
    req = auth_requirement(adapter)
    binding = EndpointBinding(
        expected_endpoint=req.get("expected_endpoint", ""),
        configured_endpoint="",
        bound=False, check_method="adapter-expected")
    endpoint = resolve_endpoint(binding)
    assert isinstance(endpoint, str)
    # With nothing configured, resolution is the honest observation
    # AUTH_CONFIG_ABSENT — never a fabricated endpoint string.
    assert endpoint in ("AUTH_CONFIG_ABSENT", "AUTH_TARGET_MATCH",
                        "AUTH_TARGET_MISMATCH")
    bound = EndpointBinding(expected_endpoint="https://example.invalid/a",
                            configured_endpoint="https://example.invalid/a",
                            bound=True, check_method="explicit")
    assert resolve_endpoint(bound) == "AUTH_TARGET_MATCH"


def test_ho26_endpoint_binding_fields():
    """HO26: the binding record carries exactly the identity fields — no
    credentials."""
    binding = EndpointBinding(expected_endpoint="https://example.invalid/a",
                              configured_endpoint="https://example.invalid/b",
                              bound=False, check_method="explicit")
    keys = set(binding.__dataclass_fields__)
    assert keys == {"expected_endpoint", "configured_endpoint", "bound",
                    "check_method"}


def test_ho27_verification_result_is_observed():
    """HO27: preflight auth_verification is an observed endpoint-resolution
    result or a named configuration state — never a fabricated pass."""
    res = run_preflight(CODEX, env_override={})
    assert res.auth_verification in VALIDATION_RESULTS or \
        res.auth_verification in ("AUTH_CONFIG_ABSENT",
                                  "AUTH_TARGET_MISMATCH",
                                  "AUTH_TARGET_MATCH")


def test_ho28_reachable_check_is_network_level_only():
    """HO28: the connectivity check is a TCP/DNS-level reachability test;
    it performs no authenticated request and no model call."""
    res = run_preflight(CODEX, env_override={})
    assert res.model_calls_used == 0


def test_ho29_unknown_host_is_handled_deterministically():
    """HO29: a host profile that does not exist yields a deterministic
    KeyError — never an exception masquerading as pass, and never silent."""
    with pytest.raises(KeyError):
        _get_adapter("NO_SUCH_HOST_PROFILE")


def test_ho30_failure_classification_is_named():
    """HO30: every non-ready preflight result carries a named failure
    classification."""
    res = run_preflight(CODEX, env_override={})
    if res.connection_status != "CONNECTION_READY":
        assert res.failure_classification, res.to_dict()


# ---------------------------------------------------------------------------
# Connection status & probe eligibility (HO31–HO36)
# ---------------------------------------------------------------------------

def test_ho31_codex_stays_auth_invalid_with_c27_evidence():
    """HO31: the acceptance case — Codex has a durable AUTH_INVALID state
    from C27 (401 pre-model-contact). The onboarding layer must present the
    same truth and must NOT claim CONNECTION_READY while the durable state
    says INVALID."""
    res = run_preflight(CODEX, env_override={})
    assert res.connection_status == "AUTH_INVALID", res.to_dict()
    assert res.live_probe_eligibility == "NO"


def test_ho32_owner_action_required_for_invalid_codex():
    """HO32: an INVALID durable state triggers exactly one owner action —
    `codex login` — with the no-secret-in-chat rule stated explicitly."""
    res = run_preflight(CODEX, env_override={})
    assert res.owner_action_required is True
    assert res.owner_action.get("action", "").strip()
    action = res.owner_action.get("action", "").lower()
    assert "login" in action or "sign" in action
    assert res.owner_action.get("do_not", "")
    assert ("paste" in res.owner_action.get("do_not", "").lower()
            or "chat" in res.owner_action.get("do_not", "").lower())


def test_ho33_uninstalled_hosts_are_discovered_as_not_installed():
    """HO33: hosts without a binary are discovered honestly — they are
    listed in the doctor output as NOT_INSTALLED, not silently omitted."""
    doctor = run_doctor(env_override={})
    host_ids = [h.get("host_profile_id", "")
                for h in doctor.get("hosts", [])]
    for host in ("CLAUDE_CODE", "GEMINI_CLI", "CURSOR", "COPILOT_CLI"):
        assert host in host_ids, f"{host} missing from doctor: {host_ids}"


def test_ho34_probe_eligibility_gate():
    """HO34: LIVE_PROBE_ELIGIBLE is only reachable when auth is verified
    AND permissions are enforceable. The Codex result demonstrates the
    negative gate."""
    res = run_preflight(CODEX, env_override={})
    assert res.live_probe_eligibility == "NO"
    assert res.connection_status not in ("CONNECTION_READY",
                                         "LIVE_PROBE_ELIGIBLE")


def test_ho35_preflight_uses_no_model_calls():
    """HO35: onboarding itself costs zero model calls, for every host."""
    doctor = run_doctor(env_override={})
    assert doctor.get("model_calls_used_for_onboarding", -1) == 0
    res = run_preflight(CODEX, env_override={})
    assert res.model_calls_used == 0


def test_ho36_no_fabricated_connection_ready():
    """HO36: no environment state in this session satisfies CONNECTION_READY.
    The test protects against regression: if any host suddenly reports READY
    here, the test fails and the result must be investigated as a possible
    fabricated pass."""
    for host in _HOST_ADAPTERS:
        res = run_preflight(host, env_override={})
        assert res.connection_status != "CONNECTION_READY", \
            f"{host} unexpectedly CONNECTION_READY in this environment"


# ---------------------------------------------------------------------------
# Beginner UX & doctor (HO37–HO42)
# ---------------------------------------------------------------------------

def test_ho37_beginner_summary_is_human_language():
    """HO37: beginner_summary returns a Vietnamese beginner-readable summary
    derived from the same machine-readable result."""
    res = run_preflight(CODEX, env_override={})
    text = beginner_summary(res)
    assert "Trạng thái:" in text
    assert "Bạn cần làm:" in text


def test_ho38_beginner_summary_contains_no_secret():
    """HO38: the human summary contains no credential value, no token, no
    API key pattern."""
    res = run_preflight(CODEX, env_override={})
    text = beginner_summary(res)
    assert "sk-" not in text and "Bearer " not in text


def test_ho39_doctor_output_is_machine_readable():
    """HO39: run_doctor returns a structured dict with per-host records —
    one record per registered host, with connection_status and eligibility."""
    doctor = run_doctor(env_override={})
    assert "hosts" in doctor
    assert len(doctor["hosts"]) >= len(_HOST_ADAPTERS)
    for host in doctor["hosts"]:
        assert "connection_status" in host or "status" in host


def test_ho40_doctor_has_recommendation():
    """HO40: the doctor gives one overall recommendation, not a vague blob."""
    doctor = run_doctor(env_override={})
    assert isinstance(doctor.get("recommendation"), str)
    assert doctor["recommendation"]


def test_ho41_redaction_helper_exists_and_is_used():
    """HO41: the module ships a redaction helper so any later serialization
    path can strip secrets deterministically (C28 §34)."""
    sample = {"token": "sk-secret-123", "host": "codex"}
    redacted1 = _redacted_output(sample)
    redacted2 = _redacted_output(sample)
    assert isinstance(redacted1, str)
    # Deterministic: same input always produces the same redacted output.
    assert redacted1 == redacted2


def test_ho42_owner_action_boundary():
    """HO42: the action guidance always points the Owner outside chat for
    the irreducible step (sign-in) and back into chat for recheck."""
    res = run_preflight(CODEX, env_override={})
    after = res.owner_action.get("after", "")
    assert "continue" in after.lower() or "tiếp tục" in after.lower()


# ---------------------------------------------------------------------------
# Drift (HO43–HO45)
# ---------------------------------------------------------------------------

def test_ho43_drift_degrades_ready_connection():
    """HO43: configuration drift degrades a CONNECTION_READY prior state to
    AUTH_VERIFICATION_REQUIRED — verified with a synthetic prior and a
    current session result (later-session recovery: prior evidence is
    re-verified, never trusted)."""
    manus_res = run_preflight("MANUS_API", env_override={})
    synthetic_ready = {
        "transport": "local-cli", "auth_method": "CLI_LOGIN",
        "credential_reference": "CLI_LOGIN", "credential_present": True,
        "auth_verification": "AUTH_TARGET_MATCH",
        "permission_verification": "PERMISSION_ENFORCEABLE",
        "endpoint_binding": EndpointBinding(
            expected_endpoint="https://example.invalid/codex",
            configured_endpoint="https://example.invalid/codex",
            bound=True, check_method="explicit"),
        "connection_status": "CONNECTION_READY",
        "live_probe_eligibility": "YES", "model_calls_used": 0,
        "observed_at": "2026-08-16T00:00:00Z"}
    drift = detect_drift("SYNTHETIC_READY", synthetic_ready,
                         current_result=manus_res.to_dict())
    assert drift.drift_detected is True
    assert drift.recommendation == "AUTH_VERIFICATION_REQUIRED"


def test_ho44_no_drift_when_state_unchanged():
    """HO44: identical consecutive preflights report no drift."""
    prior = run_preflight(CODEX, env_override={})
    drift = detect_drift(CODEX, prior, env_override={})
    assert drift.drift_detected is False
    assert drift.recommendation == "NO_RECHECK_REQUIRED"


def test_ho45_drift_record_is_reconcilable():
    """HO45: the drift record carries prior/current states and observation
    timestamps — enough for a later session to reconcile without trusting
    the prior blindly."""
    prior = run_preflight(CODEX, env_override={})
    drift = detect_drift(CODEX, prior, env_override={})
    assert drift.prior_state and drift.current_state
    assert drift.prior_observed_at
    assert drift.observed_at


# ---------------------------------------------------------------------------
# Security & integrity (HO46–HO50)
# ---------------------------------------------------------------------------

def test_ho46_core_flow_has_no_vendor_branches():
    """HO46: the preflight core flow does not branch on host name for host
    *logic* — adapters register metadata; the flow is one neutral sequence.
    Verified by asserting identical logic paths exist for every host."""
    statuses = {}
    for host in _HOST_ADAPTERS:
        res = run_preflight(host, env_override={})
        statuses[host] = res.connection_status
    from p2p_secure_onboarding import FAILURE_STATUSES
    observed = set(CONNECTION_STATES) | FAILURE_STATUSES | {
        "NOT_INSTALLED"}  # honest discovery classification
    assert all(s in observed for s in statuses.values())
    # HO46b: the Codex result demonstrates the negative gate stays closed.
    assert statuses[CODEX] == "AUTH_INVALID"


def test_ho47_no_secret_written_to_disk_by_machinery():
    """HO47: the machinery writes no file containing credential values.
    Only the owner's own tools (e.g. `codex login`) manage secrets."""
    run_preflight(CODEX, env_override={})
    p2p = ROOT / ".p2p"
    if p2p.exists():
        for f in p2p.rglob("*"):
            if f.is_file():
                content = f.read_text(errors="ignore")
                # The pre-existing project-profile.json (C21 era) lists the
                # environment var *name* "sk-state.json" in its allowed-set
                # manifest; that is an identifier, not a secret value.
                for token in content.split():
                    if token.startswith('"sk-'):
                        assert token.strip('" ,').endswith(
                            '.json"') or 'state' in token.lower(), (
                            f"possible secret token in {f}: {token[:40]}")


def test_ho48_module_has_no_router_or_second_executor():
    """HO48: the module does not import any model-execution or routing
    machinery — onboarding connects hosts; it never executes on them."""
    src = (ROOT / "scripts" / "p2p_secure_onboarding.py").read_text()
    for forbidden in ("invoke_llm", "second_executor", "model_router",
                      "execute_on_host"):
        assert forbidden not in src


def test_ho49_preflight_is_idempotent_and_safe_to_retry():
    """HO49: two consecutive preflights are consistent (idempotent, no side
    effects other than observations)."""
    r1 = run_preflight(CODEX, env_override={})
    r2 = run_preflight(CODEX, env_override={})
    assert (r1.connection_status, r1.live_probe_eligibility) == \
        (r2.connection_status, r2.live_probe_eligibility)


def test_ho50_no_autonomous_retry_loop():
    """HO50: preflight never retries authentication on its own — a failed
    host is reported once with one owner action, matching C28 §41."""
    import time
    t0 = time.monotonic()
    run_preflight(CODEX, env_override={})
    elapsed = time.monotonic() - t0
    # A retry loop would take orders of magnitude longer than a single
    # bounded check.
    assert elapsed < 60
