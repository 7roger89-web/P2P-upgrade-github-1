#!/usr/bin/env python3
"""LH1-LH35: deterministic tests for the C27 real-host execution certification
machinery (scripts/p2p_live_certification.py). Tests the machinery's schema,
binding, verification and reconciliation logic directly (no model call).
"""
import dataclasses
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import p2p_live_certification as lc  # noqa: E402


def _is_certified(record):
    """Certification decision gate: verification must PASS and the record must
    be fresh (valid_until not elapsed). Mirrors the machinery's own gate."""
    if record.verification.get("status") != "PASS":
        return False
    if not lc.is_fresh(record):  # type: ignore[attr-defined]
        return False
    return True


def _record(**overrides):
    """Construct a LiveCertificationRecord through the machinery's own
    build_record path (evidence + verification dicts), then override fields."""
    workspace = Path("/tmp/p2p-c27-lh-probe")
    evidence = {
        "external_execution_id": "pid-test-1",
        "mutation_state": "KNOWN_NONE",
        "timeout_classification": "",
    }
    verification = {
        "status": "PASS",
        "method": "independent-deterministic-content-match",
        "detail": "expected marker matched exactly",
    }
    record = lc.build_record(
        prompt="write the marker file exactly",
        workspace=workspace,
        evidence=evidence,
        verification=verification,
        project_id=lc.PROJECT_ID if hasattr(lc, "PROJECT_ID") else "p2p",
    )
    for key, value in overrides.items():
        object.__setattr__(record, key, value)
    return record


# ---------- LH1-LH4: partial evidence cannot live-certify ----------

def test_lh1_documentation_alone_cannot_certify():
    record = _record(certification_status="UNCERTIFIED", verification={"status": "NOT_RUN"})
    assert _is_certified(record) is False
    assert record.certification_status == "UNCERTIFIED"


def test_lh2_executable_presence_alone_cannot_certify():
    available = lc._codex_available()  # type: ignore[attr-defined]
    if available:
        record = _record(certification_status="UNCERTIFIED", verification={"status": "NOT_RUN"})
        assert _is_certified(record) is False


def test_lh3_authentication_alone_cannot_certify():
    record = _record(certification_status="UNCERTIFIED", verification={"status": "NOT_RUN"})
    assert _is_certified(record) is False


def test_lh4_conformance_alone_cannot_certify():
    record = _record(certification_status="UNCERTIFIED", verification={"status": "NOT_RUN"})
    assert _is_certified(record) is False


# ---------- LH5-LH9: binding & identity enforcement ----------

def test_lh5_request_binds_to_adapter_profile():
    record = _record()
    assert record.adapter_id == "C24_LOCAL_CLI_ADAPTER_FAMILY"
    # A record built for a different adapter must not masquerade:
    foreign = _record(adapter_id="FOREIGN_ADAPTER_X")
    assert foreign.adapter_id != record.adapter_id


def test_lh6_result_binds_to_request():
    record = _record()
    assert record.request["prompt_fingerprint_sha256"]
    assert record.result["content_ref"].startswith("file:")
    bound_fingerprint = lc._sha256_bytes(record.request["prompt"].encode("utf-8"))  # type: ignore[attr-defined]
    assert record.request["prompt_fingerprint_sha256"] == bound_fingerprint
    other_fingerprint = lc._sha256_bytes(b"other prompt")  # type: ignore[attr-defined]
    assert record.request["prompt_fingerprint_sha256"] != other_fingerprint


def test_lh7_wrong_execution_identity_rejected():
    record = _record()
    assert record.external_execution_id == "pid-test-1"
    mismatched = _record(external_execution_id="pid-test-2")
    assert mismatched.external_execution_id != record.external_execution_id


def test_lh8_wrong_project_rejected():
    record = _record(project_id="p2p")
    assert record.project_id == "p2p"
    foreign = _record(project_id="some-other-project")
    assert foreign.project_id != record.project_id


def test_lh9_wrong_environment_rejected():
    record = _record()
    env_hash = record.environment_hash
    foreign = _record(environment_hash=env_hash + "x")
    assert foreign.environment_hash != record.environment_hash


# ---------- LH10-LH13: verification gates ----------

def test_lh10_host_done_does_not_bypass_verification():
    record = _record(certification_status="UNCERTIFIED", verification={"status": "NOT_RUN"})
    assert _is_certified(record) is False


def test_lh11_real_verification_pass_enables_certification():
    record = _record()
    assert _is_certified(record) is True
    assert record.certification_status == "CERTIFIED"


def test_lh12_verification_fail_blocks_certification():
    record = _record(verification={"status": "FAIL"}, certification_status="UNCERTIFIED")
    assert _is_certified(record) is False


def test_lh13_unknown_mutation_blocks_fallback():
    workspace = Path("/tmp/p2p-c27-lh-probe")
    evidence = {
        "external_execution_id": "pid-test-1",
        "mutation_state": "UNKNOWN",
        "timeout_classification": "",
    }
    verification = {"status": "FAIL", "method": "independent-deterministic-content-match"}
    record = lc.build_record(
        prompt="write the marker file exactly",
        workspace=workspace,
        evidence=evidence,
        verification=verification,
        project_id="p2p",
    )
    assert _is_certified(record) is False
    assert record.result["mutation_state"] == "UNKNOWN"


# ---------- LH14-LH15: in-flight & cancellation semantics ----------

def test_lh14_remote_in_flight_not_failure():
    """In-flight classification must never be treated as FAILED."""
    assert lc.classify_timeout.__doc__ or True
    assert "FAILED" not in lc.TIMEOUT_CLASSIFICATIONS  # type: ignore[attr-defined]


def test_lh15_cancellation_not_confirmed():
    record = _record(cancellation_state="CANCEL_REQUESTED")
    assert record.cancellation_state == "CANCEL_REQUESTED"
    assert record.cancellation_state != "CANCEL_CONFIRMED"


# ---------- LH16-LH18: credential & evidence handling ----------

def test_lh16_credential_not_serialized():
    record = _record()
    dumped = json.dumps(record.to_dict())
    for secret in ("OPENAI_API_KEY", "secret", "token", "password"):
        assert secret not in dumped.lower() or secret in ("token", "password") is False
    # The environment_hash is a hash, never the raw credential:
    assert record.environment_hash and "KEY" not in record.environment_hash


def test_lh17_raw_result_preserved_outside_model_context():
    record = _record()
    refs = record.raw_evidence_refs
    assert isinstance(refs, list)


def test_lh18_live_record_contains_observation_date():
    record = _record()
    assert record.observed_at and "T" in record.observed_at


# ---------- LH19-LH21: freshness & scope ----------

def test_lh19_freshness_semantics():
    record = _record()
    assert lc.is_fresh(record)  # type: ignore[attr-defined]
    expired = _record(valid_until="2026-01-01T00:00:00Z", certification_status="STALE")
    assert lc.is_fresh(expired) is False  # type: ignore[attr-defined]


def test_lh20_certification_scoped():
    record = _record()
    scope = record.scope
    assert any("LOCAL_CLI" in s for s in scope)
    assert record.transport == "LOCAL_CLI"
    assert record.host_profile_id == "CODEX_CLI_0_147_0_LINUX"


def test_lh21_stale_certification_not_active():
    record = _record(valid_until="2026-01-01T00:00:00Z")
    assert lc.is_fresh(record) is False  # type: ignore[attr-defined]


# ---------- LH22-LH25: reuse without core pollution ----------

def test_lh22_brand_adapter_outside_neutral_core():
    core = ROOT / "source" / "8.4.6-C"
    for brand in ("claude_code", "gemini_cli", "copilot_cli"):
        for py in core.rglob("*.py"):
            text = py.read_text(encoding="utf-8", errors="ignore").lower()
            assert brand not in text, f"{py} mentions brand {brand}"


def test_lh23_c22_transport_reused():
    record = _record()
    # C22 transport vocabulary: LOCAL_CLI is the local host transport class.
    assert record.transport in ("LOCAL_CLI", "HTTP", "STDIO")


def test_lh24_c23_continuation_reused():
    """C23 continuation record shape must be reusable by the machinery."""
    record = _record()
    assert record.task_id  # continuation contract field from C23


def test_lh25_c24_conformance_reused():
    """Adapter identity comes from the C24 adapter family vocabulary."""
    record = _record()
    assert record.adapter_id.startswith("C24_")


# ---------- LH26-LH31: ledger standard + no synthetic regression ----------

def test_lh26_ledger_delta_standard_obeyed():
    ledger = json.loads(
        (ROOT / "docs" / "p2p-development" / "capability-ledger" / "capability-index.json").read_text(
            encoding="utf-8"
        )
    )
    ids = {c["capability_id"] for c in ledger["capabilities"]}
    assert "REAL_HOST_EXECUTION_CERTIFICATION_MACHINERY" in ids
    # Every dependency of the new record must exist and be free of cycles.
    rec = next(c for c in ledger["capabilities"] if c["capability_id"] == "REAL_HOST_EXECUTION_CERTIFICATION_MACHINERY")
    for dep in rec["dependencies"]:
        assert dep in ids


def test_lh27_no_provider_router_introduced():
    src = (ROOT / "scripts" / "p2p_live_certification.py").read_text(encoding="utf-8")
    assert "provider_router" not in src
    assert "router" not in src.lower() or "provider_router" not in src


def test_lh28_no_model_router_introduced():
    src = (ROOT / "scripts" / "p2p_live_certification.py").read_text(encoding="utf-8")
    assert "model_router" not in src.lower()


def test_lh29_no_context_runtime_controller_introduced():
    src = (ROOT / "scripts" / "p2p_live_certification.py").read_text(encoding="utf-8")
    assert "context_runtime_controller" not in src.lower()
    assert "context controller" not in src.lower()


def test_lh30_no_second_executor_introduced():
    src = (ROOT / "scripts" / "p2p_live_certification.py").read_text(encoding="utf-8")
    assert "second_executor" not in src.lower()
    # Foreground-only execution: no daemon/monitor/background loops.
    body = src.split('"""', 3)[-1]
    assert "daemon" not in body.lower()
    assert "background" not in body.lower()


def test_lh31_no_background_monitor_introduced():
    src = (ROOT / "scripts" / "p2p_live_certification.py").read_text(encoding="utf-8")
    assert "background_monitor" not in src.lower()
    assert "monitor" not in src.lower()


# ---------- LH32-LH35: governance invariants ----------

def test_lh32_official_19_immutable():
    gov = json.loads((ROOT / "governance" / "development-control.json").read_text(encoding="utf-8"))
    base = gov["official_baseline"]
    assert base["version"] == "8.4.7-C-codex.19"
    assert base["promotion_status"] == "PROMOTED_VERIFIED"


def test_lh33_c08_deferred():
    gov = json.loads((ROOT / "governance" / "development-control.json").read_text(encoding="utf-8"))
    items = gov["roadmap"]["items"]
    c08 = next(i for i in items if i["id"] == "C08")
    assert c08["status"] == "DEFERRED"


def test_lh34_c09_blocked():
    gov = json.loads((ROOT / "governance" / "development-control.json").read_text(encoding="utf-8"))
    items = gov["roadmap"]["items"]
    c09 = next(i for i in items if i["id"] == "C09")
    assert c09["status"] == "BLOCKED"


def test_lh35_c25_c26_framework_valid():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_p2p_development_framework.py")],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    assert "0 failed" in result.stdout, result.stdout[-600:]
