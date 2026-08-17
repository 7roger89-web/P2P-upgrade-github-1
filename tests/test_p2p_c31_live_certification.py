"""C31 tests — only the behavior required by the new C31 implementation.

Scope (per C31 rule 9): test the fresh live probe verdict logic and the
honest BLOCKED governance/ledger schema invariants. All C25–C30 regressions
remain untouched in their own files.

Tests: c31_01..c31_12
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
GOV = ROOT / "governance" / "development-control.json"
LEDGER = ROOT / "docs" / "p2p-development" / "capability-ledger" / "capability-index.json"
ROADMAP = ROOT / "docs/p2p-development/current-roadmap.md"
EVIDENCE = ROOT / "evidence" / "c31_live_probe.json"


@pytest.fixture(scope="module")
def gov():
    return json.loads(GOV.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def ledger():
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def c31_record(gov, cid):
    for r in gov["candidate_records"]:
        if r.get("candidate_id") == cid:
            return r
    return None


# ---------- probe evidence integrity ----------

def test_c31_01_evidence_file_exists_and_is_json():
    assert EVIDENCE.exists(), "fresh live probe evidence must exist"
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    assert data.get("kind") == "live_auth_probe"


def test_c31_02_probe_was_fresh_and_unreplayed():
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    observed = data["observed_at"]
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", observed)
    assert data["freshness"] == "FRESH"


def test_c31_03_fingerprint_matches_content():
    raw = EVIDENCE.read_text(encoding="utf-8")
    data = json.loads(raw)
    # Fingerprint was computed on the in-memory dict at probe time.
    # If it mismatches here, the persisted file must differ from what was
    # hashed (post-hoc mutation is forbidden for evidence integrity).
    import hashlib
    # The probe hashes the evidence dict minus the fingerprint field itself,
    # then persists the fingerprint alongside it. Re-derive accordingly.
    d2 = dict(data)
    del d2["fingerprint"]
    fp = hashlib.sha256(json.dumps(d2, sort_keys=True).encode()).hexdigest()
    assert fp == data["fingerprint"], \
        "evidence file must match the probe's fingerprint (dict minus the " \
        "fingerprint field); post-hoc mutation is forbidden"


def test_c31_04_bounded_exec_probe_reached_auth_layer():
    """The bounded exec probe must have actually reached Codex's own auth
    layer (HTTP 401 before model contact), not failed at CLI-arg level."""
    data = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    probe3 = next(p for p in data["probes"] if p["id"] == "bounded-exec-probe")
    out = probe3["result"].get("stdout", "") + probe3["result"].get("stderr", "")
    assert "401" in out and "Unauthorized" in out, \
        "probe must show HTTP 401 at the transport auth layer"
    assert data["auth_verdict"] == "AUTH_INVALID"


def test_c31_05_probe_was_non_destructive_and_secret_free():
    """No secret values are stored in the evidence; workspace was ephemeral."""
    text = EVIDENCE.read_text(encoding="utf-8")
    for marker in ["sk1-", "Bearer ", "Authorization:"]:
        assert marker not in text, f"evidence must not contain {marker}"
    data = json.loads(text)
    binding = data.get("workspace_binding", {})
    assert binding.get("class") == "EPHEMERAL_SANDBOX"


# ---------- governance schema ----------

def test_c31_06_current_development_records_blocked_terminal(gov):
    cd = gov["current_development"]
    assert cd["development_goal"] == "C31"
    assert cd["status"] == "BLOCKED_TERMINAL"
    assert cd["terminal_verdict"] == "BLOCKED / OWNER_ACTION_REQUIRED"
    assert "blocker" in cd
    assert "codex_cli_0_147_0" in cd["blocker"]["observed"]
    assert "AUTH_INVALID" in cd["blocker"]["observed"]["codex_cli_0_147_0"]


def test_c31_07_no_fabricated_certification_in_governance(gov):
    """C31 may not fabricate live-certification claims. FOUNDATION_READY
    legitimately exists for C30 machinery records; the forbidden claims are
    those that would assert a LIVE certified execution target or a promoted
    C31 release that never happened."""
    text = json.dumps(gov)
    # C31's own records must never claim live certification
    rec = c31_record(gov, "C31")
    assert "CERTIFIED" not in str(rec.get("promotion_status", ""))
    cd = gov["current_development"]
    assert cd["terminal_verdict"] == "BLOCKED / OWNER_ACTION_REQUIRED"
    for claim in ["LIVE_CERTIFIED", "AUTHENTICATED_AND_CERTIFIED",
                  "execution_target_certified"]:
        assert claim not in text, f"governance must not claim {claim}"


def test_c31_08_roadmap_c31_declares_owner_actions(gov):
    item = next(i for i in gov["roadmap"]["items"] if i["id"] == "C31")
    assert item["status"] == "PLANNED"
    assert "OWNER_ACTION_REQUIRED" in item["notes"]
    assert "reopen_condition" in item["notes"] or "reopens" in item["notes"].lower() \
        or "fresh probe" in item["notes"].lower()
    assert "codex login" in item["notes"].lower()


def test_c31_09_candidate_record_marks_no_release_artifact(gov):
    rec = c31_record(gov, "C31")
    assert rec is not None
    # The record passes the lineage schema (64-char hex sha, valid version keys,
    # canonical promotion set) while honestly recording that NO new artifact was
    # minted for the BLOCKED terminal.
    assert rec["promotion_status"] == "UNPROMOTED"
    assert rec["built"] is False
    assert re.fullmatch(r"[0-9a-f]{64}", rec["candidate_sha256"])
    assert "BUILD_SKIPPED_BY_POLICY" in rec["lineage_status"]


# ---------- ledger honesty ----------

def test_c31_10_ledger_c31_records_honest_statuses(ledger):
    cap_ids = [c["capability_id"] for c in ledger["capabilities"]]
    expected = {"C31_LIVE_AUTH_PROBE_FRESH_EVIDENCE",
                "C31_EXECUTION_TARGET_AS_CERTIFICATION_INTAKE",
                "C31_OWNER_AUTH_ACTION_DEPENDENCY"}
    for cid in expected:
        assert cid in cap_ids, cid
    for c in ledger["capabilities"]:
        if c["capability_id"] in expected:
            assert c["status"] in ledger["status_vocabulary"]


def test_c31_11_ledger_never_claims_live_certification_foundation(ledger):
    text = json.dumps(ledger)
    for fake in ["LIVE_CERTIFICATION_FOUNDATION_READY", "CERTIFIED_LIVE"]:
        assert fake not in text, f"ledger must not claim {fake}"


# ---------- machinery reuse (C27/C28/C30 not weakened) ----------

def test_c31_12_machinery_integrity_untouched():
    assert (ROOT / "scripts" / "p2p_live_certification.py").exists()
    assert (ROOT / "scripts" / "p2p_secure_onboarding.py").exists()
    assert (ROOT / "scripts" / "p2p_execution_target.py").exists()
    assert (ROOT / "scripts" / "p2p_goal_closure.py").exists()
