"""Focused tests for P2P-CLEANUP-INSPECTION-AUTHORITY-01.

Proves, over the existing FW06/TMPGC seams (no new authority framework):

1. READ_ONLY cleanup inspection collects enough evidence to classify
   (SAFE_DISPOSABLE_CANDIDATE / KEEP / UNKNOWN);
2. filesystem/state mutations attempted under inspection authority are denied;
3. lifecycle restore without explicit Owner authorization is denied;
4. lifecycle restore with incomplete/ambiguous evidence is denied;
5. an exact proven binding + explicit Owner authorization is representable;
6. lifecycle restore never grants DELETE (delete stays separately authorized);
7. UNKNOWN => KEEP remains unchanged.

Every fixture lives below the disposable ``.tmp/p2p-authority-test-*`` root.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = ROOT / ".p2p" / "system"
sys.path.insert(0, str(SYSTEM_ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from p2p_capabilities import fw06_operational_resilience as fw06  # noqa: E402
from p2p_capabilities import authority_chain_registry as acr  # noqa: E402

OWNER_AUTH = "owner-cleanup-inspection-authority-01"
BASE_REVISION = "b" * 40
BINDING_EVIDENCE_SCHEMA = fw06.LIFECYCLE_BINDING_EVIDENCE_SCHEMA


def _policy() -> dict:
    return {
        "schema": fw06.TMP_GC_POLICY_SCHEMA,
        "allowlisted_temp_roots": [".tmp"],
        "protected_roots": [],
        "owner_roots": [],
        "authoritative_roots": [],
        "durable_roots": [".p2p/state", "reports", "archive"],
        "grace_days": {
            "NORMAL": 7,
            "WARNING": 3,
            "LOW": 1,
            "CRITICAL": 0,
        },
        "pressure": {
            "warning_percent_free": 0,
            "warning_absolute_free_bytes": 0,
            "low_percent_free": 0,
            "low_absolute_free_bytes": 0,
            "critical_percent_free": 0,
            "critical_absolute_free_bytes": 0,
        },
        "schedule": {
            "daily_local_time": "03:00",
            "activation": "OWNER_GATED",
        },
        "largest_consumers_limit": 10,
    }


@pytest.fixture()
def sandbox(monkeypatch):
    root = ROOT / ".tmp" / f"p2p-authority-test-{uuid.uuid4().hex}"
    (root / ".tmp").mkdir(parents=True)
    (root / ".p2p" / "state").mkdir(parents=True)
    (root / "reports").mkdir()
    (root / "archive").mkdir()
    (root / "governance").mkdir()
    (root / "governance" / "p2p-tmp-gc-policy.json").write_text(
        json.dumps(_policy(), indent=2, sort_keys=True), encoding="utf-8",
    )
    # Isolate the existing authority-chain certification ledger per fixture.
    monkeypatch.setenv("P2P_STATE_DIR", str(root / ".p2p" / "state"))
    acr.clear_authority_chain_registry_for_tests()
    yield root
    acr.clear_authority_chain_registry_for_tests()


def _register(root: Path, *, workspace_id: str, workspace_path: Path,
              project_id: str = "project-alpha", task_id: str = "task-alpha",
              session_id: str = "session-alpha",
              evidence_pointers: list[str] | tuple[str, ...] = (),
              **extra) -> dict:
    workspace_path.mkdir(parents=True, exist_ok=True)
    record = fw06.register_managed_workspace(
        root,
        workspace_id=workspace_id,
        project_id=project_id,
        task_id=task_id,
        session_id=session_id,
        root_path=str(workspace_path.relative_to(root)),
        base_revision=BASE_REVISION,
        workspace_type="GIT_WORKTREE",
        purpose="inspection_fixture",
        creator="fixture",
        temp_root=".tmp",
        git_worktree=False,
        evidence_pointers=list(evidence_pointers),
        **extra,
    )
    return record


def _raw_row(root: Path, *, workspace_id: str, workspace_path: Path,
             project_id: str = "project-alpha", task_id: str = "task-alpha",
             session_id: str = "session-alpha",
             omit_identity: tuple[str, ...] = (),
             include_lifecycle: bool = False) -> dict:
    """A registry row with a MISSING lifecycle record (the restore subject).

    ``omit_identity`` removes durable identity fields so a partial-registry
    scenario can be constructed; the caller may still supply the missing
    value and must NOT have it accepted as proof.
    """
    workspace_path.mkdir(parents=True, exist_ok=True)
    row = {
        "workspace_id": workspace_id,
        "project_id": project_id,
        "owner_goal_id": "",
        "owner_task_id": task_id,
        "task_id": task_id,
        "session_id": session_id,
        "root_path": str(workspace_path.relative_to(root)),
        "temp_root": ".tmp",
        "base_revision": BASE_REVISION,
        "created_at": "2026-08-01T00:00:00Z",
        "last_used_at": "2026-08-01T00:00:00Z",
        "status": "ACTIVE",
        "mutation_policy": "SYNTHETIC_ONLY",
        "conflict_group": "",
        "git_worktree": False,
        "evidence_pointers": [],
        "workspace_type": "GIT_WORKTREE",
        "purpose": "inspection_fixture",
        "creator": "fixture",
        "branch": "",
        "remote": "",
    }
    for field in omit_identity:
        row.pop(field, None)
    if include_lifecycle:
        row["lifecycle_state"] = "ACTIVE"
        row["protection_reasons"] = ["ACTIVE_SESSION"]
    ledger = root / ".p2p" / "state" / fw06.WORKSPACE_PATH
    with ledger.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, sort_keys=True) + "\n")
    return row


def _binding_evidence(root: Path, *, name: str, workspace_id: str,
                      project_id: str = "project-alpha",
                      task_id: str = "task-alpha",
                      session_id: str = "session-alpha",
                      root_path: str,
                      base_revision: str = BASE_REVISION) -> Path:
    path = root / "reports" / name
    path.write_text(json.dumps({
        "schema": BINDING_EVIDENCE_SCHEMA,
        "workspace_id": workspace_id,
        "project_id": project_id,
        "task_id": task_id,
        "session_id": session_id,
        "root_path": root_path,
        "base_revision": base_revision,
        "source": "durable-canonical-fixture",
    }, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _write_workspace_files(workspace_path: Path) -> bytes:
    workspace_path.mkdir(parents=True, exist_ok=True)
    payload = b"inspection-payload-v1"
    (workspace_path / "payload.txt").write_bytes(payload)
    (workspace_path / "nested").mkdir()
    (workspace_path / "nested" / "data.bin").write_bytes(b"\x00\x01\x02")
    return payload


def _registry_lifecycle(root: Path, workspace_id: str) -> str:
    rows = []
    ledger = root / ".p2p" / "state" / fw06.WORKSPACE_PATH
    if ledger.exists():
        for line in ledger.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row.get("workspace_id") == workspace_id:
                rows.append(row)
    return str(rows[-1].get("lifecycle_state", "")).strip().upper() if rows else ""


def _path_key_for_test(path: Path) -> str:
    return os.path.normcase(os.path.abspath(os.path.normpath(str(path))))


# ---------------------------------------------------------------- acceptance 1
def test_inspection_collects_evidence_and_classifies(sandbox):
    ws_path = sandbox / ".tmp" / "ws-inspect"
    payload = _write_workspace_files(ws_path)
    receipt = sandbox / "reports" / "receipt-inspect.json"
    receipt.write_text(json.dumps({
        "return_packet": "ok", "workspace_id": "ws-inspect",
    }, indent=2), encoding="utf-8")
    _register(sandbox, workspace_id="ws-inspect", workspace_path=ws_path,
              evidence_pointers=["reports/receipt-inspect.json"],
              evidence_status="DURABLE",
              handoff_status="DURABLE",
              handoff_ref="reports/receipt-inspect.json",
              completed_at="2026-08-29T00:00:00Z",
              disposable_after="2026-08-30T00:00:00Z")

    report = fw06.inspect_cleanup_scope(
        sandbox, authority=fw06.CLEANUP_INSPECTION_AUTHORITY,
        policy=_policy(),
    )

    assert report["authority"] == fw06.CLEANUP_INSPECTION_AUTHORITY
    assert report["read_only"] is True
    assert report["mutation_authorized"] is False
    assert report["disposal_authorized"] is False
    assert report["registry_well_formed"] is True
    assert report["audit_well_formed"] is True
    # files/directory list, size/timestamps, hashes
    entries = report["scope_listing"]["entries"]
    listed = {entry["path"]: entry for entry in entries}
    assert ".tmp/ws-inspect/payload.txt" in listed
    assert listed[".tmp/ws-inspect/payload.txt"]["size"] == len(payload)
    assert listed[".tmp/ws-inspect/payload.txt"]["sha256"] == (
        hashlib.sha256(payload).hexdigest()
    )
    assert listed[".tmp/ws-inspect/payload.txt"]["mtime_utc"]
    # reports / receipts / return packets read with durable hash
    docs = {entry["relative_path"]: entry
            for entry in report["durable_documents"]}
    assert "reports/receipt-inspect.json" in docs
    assert docs["reports/receipt-inspect.json"]["durable"] is True
    assert docs["reports/receipt-inspect.json"]["sha256"] == (
        hashlib.sha256(receipt.read_bytes()).hexdigest()
    )
    # per-workspace evidence: git metadata, history, registry, audit, pointers
    by_id = {item["workspace_id"]: item for item in report["workspaces"]}
    assert "ws-inspect" in by_id
    item = by_id["ws-inspect"]
    assert item["registry_row"]["project_id"] == "project-alpha"
    assert item["history"]["history_preserved_or_reachable"] is False
    assert item["evidence_pointers"][0]["durable"] is True
    assert item["classification"] in fw06.CLEANUP_INSPECTION_CLASSIFICATIONS
    assert item["disposal_authorized"] is False
    assert item["final_action"] == "KEEP"

    # Wrong authority is refused
    with pytest.raises(fw06.InspectionAuthorityError):
        fw06.inspect_cleanup_scope(
            sandbox, authority=fw06.LIFECYCLE_BINDING_RESTORE_AUTHORITY,
            policy=_policy(),
        )


# ---------------------------------------------------------------- acceptance 2
def test_mutation_denied_under_inspection(sandbox):
    ws_path = sandbox / ".tmp" / "ws-inspect"
    _write_workspace_files(ws_path)
    _register(sandbox, workspace_id="ws-inspect", workspace_path=ws_path)

    authority = fw06.CleanupInspectionAuthority(sandbox, policy=_policy())
    assert authority.snapshot()["read_only"] is True
    with pytest.raises(fw06.InspectionAuthorityError,
                       match="MUTATION_DENIED_UNDER_INSPECTION"):
        authority.mutate("DELETE", ws_path)
    with pytest.raises(fw06.InspectionAuthorityError,
                       match="MUTATION_DENIED_UNDER_INSPECTION"):
        fw06.cleanup_workspace(
            sandbox, "ws-inspect",
            authority=fw06.CLEANUP_INSPECTION_AUTHORITY,
            mutation_state_known=True, evidence_committed=True,
            result_reconciled=True, owner_decision_resolved=True,
        )
    with pytest.raises(fw06.InspectionAuthorityError,
                       match="MUTATION_DENIED_UNDER_INSPECTION"):
        fw06.run_tmp_gc(sandbox, apply=True,
                        authority=fw06.CLEANUP_INSPECTION_AUTHORITY,
                        policy=_policy())
    # Nothing was moved, renamed, reset, stashed, or lifecycle-written.
    assert (ws_path / "payload.txt").exists()
    latest = fw06.list_all_workspaces(sandbox)[-1]
    assert latest["status"] == "ACTIVE"
    assert latest["lifecycle_state"] == "ACTIVE"


# ---------------------------------------------------------------- acceptance 3
def test_restore_without_owner_authorization_denied(sandbox):
    ws_path = sandbox / ".tmp" / "ws-restore"
    _raw_row(sandbox, workspace_id="ws-restore", workspace_path=ws_path)
    _binding_evidence(
        sandbox, name="binding-restore-evidence.json", workspace_id="ws-restore",
        root_path=str(ws_path.relative_to(sandbox)),
    )
    log = sandbox / ".p2p" / "state" / fw06.LIFECYCLE_RESTORE_LEDGER

    result = fw06.restore_workspace_lifecycle_binding(
        sandbox,
        authority=fw06.LIFECYCLE_BINDING_RESTORE_AUTHORITY,
        owner_authorization_id="",
        restored_lifecycle="COMPLETE",
        identity={
            "workspace_id": "ws-restore",
            "project_id": "project-alpha",
            "task_id": "task-alpha",
            "session_id": "session-alpha",
            "root_path": str(ws_path.relative_to(sandbox)),
            "base_revision": BASE_REVISION,
        },
        evidence_pointers=["reports/binding-restore-evidence.json"],
        policy=_policy(),
    )

    assert result["status"] == "BLOCKED"
    assert result["final_action"] == "KEEP"
    assert result["reason"] == "OWNER_AUTHORIZATION_REQUIRED"
    assert result["delete_authorized"] is False
    assert _registry_lifecycle(sandbox, "ws-restore") == ""
    assert not log.exists()


# ---------------------------------------------------------------- acceptance 4
def test_restore_incomplete_evidence_denied(sandbox):
    ws_path = sandbox / ".tmp" / "ws-incomplete"
    _raw_row(sandbox, workspace_id="ws-incomplete", workspace_path=ws_path)
    # Evidence document missing required session_id field -> unprovable.
    (sandbox / "reports" / "incomplete-evidence.json").write_text(
        json.dumps({
            "schema": BINDING_EVIDENCE_SCHEMA,
            "workspace_id": "ws-incomplete",
            "project_id": "project-alpha",
            "task_id": "task-alpha",
            "root_path": str(ws_path.relative_to(sandbox)),
            "base_revision": BASE_REVISION,
        }), encoding="utf-8")

    result = fw06.restore_workspace_lifecycle_binding(
        sandbox,
        authority=fw06.LIFECYCLE_BINDING_RESTORE_AUTHORITY,
        owner_authorization_id=OWNER_AUTH,
        restored_lifecycle="COMPLETE",
        identity={
            "workspace_id": "ws-incomplete",
            "project_id": "project-alpha",
            "task_id": "task-alpha",
            "session_id": "session-alpha",
            "root_path": str(ws_path.relative_to(sandbox)),
            "base_revision": BASE_REVISION,
        },
        evidence_pointers=["reports/incomplete-evidence.json"],
        policy=_policy(),
    )

    assert result["status"] == "BLOCKED"
    assert result["final_action"] == "KEEP"
    assert result["reason"] == "EVIDENCE_DOCUMENT_UNREADABLE_OR_INCOMPLETE"
    assert _registry_lifecycle(sandbox, "ws-incomplete") == ""


def test_restore_ambiguous_evidence_denied(sandbox):
    ws_path = sandbox / ".tmp" / "ws-ambiguous"
    _raw_row(sandbox, workspace_id="ws-ambiguous", workspace_path=ws_path)
    root_rel = str(ws_path.relative_to(sandbox))
    _binding_evidence(sandbox, name="binding-a.json", workspace_id="ws-ambiguous",
                      project_id="project-alpha", root_path=root_rel)
    _binding_evidence(sandbox, name="binding-b.json", workspace_id="ws-ambiguous",
                      project_id="project-beta", root_path=root_rel)

    result = fw06.restore_workspace_lifecycle_binding(
        sandbox,
        authority=fw06.LIFECYCLE_BINDING_RESTORE_AUTHORITY,
        owner_authorization_id=OWNER_AUTH,
        restored_lifecycle="COMPLETE",
        identity={
            "workspace_id": "ws-ambiguous",
            "project_id": "project-alpha",
            "task_id": "task-alpha",
            "session_id": "session-alpha",
            "root_path": root_rel,
            "base_revision": BASE_REVISION,
        },
        evidence_pointers=[
            "reports/binding-a.json", "reports/binding-b.json",
        ],
        policy=_policy(),
    )

    assert result["status"] == "BLOCKED"
    assert result["final_action"] == "KEEP"
    assert result["reason"] == "AMBIGUOUS_BINDING_FAIL_CLOSED"
    assert _registry_lifecycle(sandbox, "ws-ambiguous") == ""


# ---------------------------------------------------------------- acceptance 5
def test_exact_proven_binding_and_owner_authorization_restored(sandbox):
    ws_path = sandbox / ".tmp" / "ws-restore"
    _write_workspace_files(ws_path)
    _raw_row(sandbox, workspace_id="ws-restore", workspace_path=ws_path)
    root_rel = str(ws_path.relative_to(sandbox))
    _binding_evidence(sandbox, name="binding-restore.json",
                      workspace_id="ws-restore", root_path=root_rel)

    result = fw06.restore_workspace_lifecycle_binding(
        sandbox,
        authority=fw06.LIFECYCLE_BINDING_RESTORE_AUTHORITY,
        owner_authorization_id=OWNER_AUTH,
        restored_lifecycle="COMPLETE",
        identity={
            "workspace_id": "ws-restore",
            "project_id": "project-alpha",
            "task_id": "task-alpha",
            "session_id": "session-alpha",
            "root_path": root_rel,
            "base_revision": BASE_REVISION,
        },
        evidence_pointers=["reports/binding-restore.json"],
        policy=_policy(),
    )

    assert result["status"] == "RESTORED"
    assert result["final_action"] == "KEEP"
    assert result["delete_authorized"] is False
    receipt = result["restore_receipt"]
    assert receipt["owner_authorization_id"] == OWNER_AUTH
    assert receipt["workspace_id"] == "ws-restore"
    assert receipt["project_id"] == "project-alpha"
    assert receipt["task_id"] == "task-alpha"
    assert receipt["session_id"] == "session-alpha"
    assert receipt["root_path"] == root_rel
    assert receipt["base_revision"] == BASE_REVISION
    assert receipt["restored_lifecycle"] == "COMPLETE"
    assert receipt["binding_proof"]["directory_name_inference_used"] is False
    assert result["authority_model"]["owner_authorization_id"] == OWNER_AUTH
    assert _registry_lifecycle(sandbox, "ws-restore") == "COMPLETE"
    ledger = sandbox / ".p2p" / "state" / fw06.LIFECYCLE_RESTORE_LEDGER
    assert ledger.exists()
    assert json.loads(ledger.read_text(encoding="utf-8").splitlines()[-1])[
        "owner_authorization_id"] == OWNER_AUTH
    # The existing authority-chain model can represent the exact binding.
    certificate = acr.append_lifecycle_binding_restore_certification(
        role_id="p2p-owner-delegate",
        owner_authorization_id=OWNER_AUTH,
        workspace_id="ws-restore",
        project_id="project-alpha",
        task_id="task-alpha",
        session_id="session-alpha",
        root_path=root_rel,
        base_revision=BASE_REVISION,
        restored_lifecycle="COMPLETE",
        evidence_pointers=["reports/binding-restore.json"],
    )
    assert certificate["delete_authorized"] is False
    latest = acr.latest_lifecycle_binding_restore_certification(
        "ws-restore", OWNER_AUTH,
    )
    assert latest is not None
    assert latest["project_id"] == "project-alpha"
    assert latest["root_path"] == root_rel
    assert latest["permission_grant"] == acr.CANONICAL_RESTORE_GRANT


# ---------------------------------------------------------------- acceptance 6
def test_restore_authority_does_not_grant_delete(sandbox):
    ws_path = sandbox / ".tmp" / "ws-restore"
    _write_workspace_files(ws_path)
    _raw_row(sandbox, workspace_id="ws-restore", workspace_path=ws_path)
    root_rel = str(ws_path.relative_to(sandbox))
    _binding_evidence(sandbox, name="binding-restore.json",
                      workspace_id="ws-restore", root_path=root_rel)
    restored = fw06.restore_workspace_lifecycle_binding(
        sandbox,
        authority=fw06.LIFECYCLE_BINDING_RESTORE_AUTHORITY,
        owner_authorization_id=OWNER_AUTH,
        restored_lifecycle="COMPLETE",
        identity={
            "workspace_id": "ws-restore",
            "project_id": "project-alpha",
            "task_id": "task-alpha",
            "session_id": "session-alpha",
            "root_path": root_rel,
            "base_revision": BASE_REVISION,
        },
        evidence_pointers=["reports/binding-restore.json"],
        policy=_policy(),
    )
    assert restored["status"] == "RESTORED"

    with pytest.raises(fw06.InspectionAuthorityError,
                       match="DELETE_NOT_GRANTED_TO_LIFECYCLE_RESTORE"):
        fw06.cleanup_workspace(
            sandbox, "ws-restore",
            authority=fw06.LIFECYCLE_BINDING_RESTORE_AUTHORITY,
            mutation_state_known=True, evidence_committed=True,
            result_reconciled=True, owner_decision_resolved=True,
        )
    with pytest.raises(fw06.InspectionAuthorityError,
                       match="DELETE_NOT_GRANTED_TO_LIFECYCLE_RESTORE"):
        fw06.run_tmp_gc(sandbox, apply=True,
                        authority=fw06.LIFECYCLE_BINDING_RESTORE_AUTHORITY,
                        policy=_policy())
    assert (ws_path / "payload.txt").exists()
    assert _registry_lifecycle(sandbox, "ws-restore") == "COMPLETE"


# ---------------------------------------------------------------- acceptance 7
def test_unknown_keep_invariant_preserved(sandbox):
    known = sandbox / ".tmp" / "ws-known"
    _write_workspace_files(known)
    _register(sandbox, workspace_id="ws-known", workspace_path=known)
    unknown = sandbox / ".tmp" / "ws-unknown"
    unknown.mkdir(parents=True)
    (unknown / "orphan.txt").write_text("orphan", encoding="utf-8")

    report = fw06.inspect_cleanup_scope(
        sandbox, authority=fw06.CLEANUP_INSPECTION_AUTHORITY,
        policy=_policy(),
    )
    by_id = {item["workspace_id"]: item for item in report["workspaces"]}
    orphan = next(item for item in report["workspaces"]
                  if item["workspace_id"].startswith("UNREGISTERED-"))
    assert orphan["classification"] == "UNKNOWN"
    assert orphan["final_action"] == "KEEP"
    assert orphan["keep_invariant"] is True
    assert report["summary"]["unknown_keep_invariant_preserved"] is True
    assert report["summary"]["delete_authorized"] is False
    # No authority in this workstream ever granted DELETE.
    assert report["disposal_authorized"] is False
    assert by_id["ws-known"]["classification"] != "SAFE_DISPOSABLE_CANDIDATE"


# ---------------------------------------------- Supervisor fail-open regression
def _restore_identity(workspace_id: str, root_path: str,
                      session_id: str = "session-alpha",
                      project_id: str = "project-alpha",
                      task_id: str = "task-alpha") -> dict:
    return {
        "workspace_id": workspace_id,
        "project_id": project_id,
        "task_id": task_id,
        "session_id": session_id,
        "root_path": root_path,
        "base_revision": BASE_REVISION,
    }


def _last_lifecycle(root: Path, workspace_id: str) -> str:
    rows = fw06.list_all_workspaces(root)
    for row in reversed(rows):
        if row.get("workspace_id") == workspace_id:
            return str(row.get("lifecycle_state", "")).strip().upper()
    return ""


def test_restore_complete_durable_registry_allowed(sandbox):
    """1. Complete durable registry => allowed subject to the Owner gate."""
    ws_path = sandbox / ".tmp" / "ws-complete"
    _raw_row(sandbox, workspace_id="ws-complete", workspace_path=ws_path)
    root_rel = str(ws_path.relative_to(sandbox))

    result = fw06.restore_workspace_lifecycle_binding(
        sandbox,
        authority=fw06.LIFECYCLE_BINDING_RESTORE_AUTHORITY,
        owner_authorization_id=OWNER_AUTH,
        restored_lifecycle="COMPLETE",
        identity=_restore_identity("ws-complete", root_rel),
        evidence_pointers=[],
        policy=_policy(),
    )

    assert result["status"] == "RESTORED"
    assert result["final_action"] == "KEEP"
    assert result["delete_authorized"] is False
    assert result["binding_proof"]["registry_complete"] is True
    assert result["binding_proof"]["proven"] is True
    assert result["binding_proof"]["evidence_documents"] == []
    assert _last_lifecycle(sandbox, "ws-complete") == "COMPLETE"


def test_restore_partial_registry_without_docs_blocked(sandbox):
    """2. Partial registry + no evidence docs => BLOCKED, even though the
    caller supplies the missing field (caller value is never proof)."""
    ws_path = sandbox / ".tmp" / "ws-partial"
    _raw_row(sandbox, workspace_id="ws-partial", workspace_path=ws_path,
             omit_identity=("session_id",))
    root_rel = str(ws_path.relative_to(sandbox))
    ledger = sandbox / ".p2p" / "state" / fw06.LIFECYCLE_RESTORE_LEDGER

    result = fw06.restore_workspace_lifecycle_binding(
        sandbox,
        authority=fw06.LIFECYCLE_BINDING_RESTORE_AUTHORITY,
        owner_authorization_id=OWNER_AUTH,
        restored_lifecycle="COMPLETE",
        identity=_restore_identity("ws-partial", root_rel,
                                   session_id="CALLER-SUPPLIED"),
        evidence_pointers=[],
        policy=_policy(),
    )

    assert result["status"] == "BLOCKED"
    assert result["final_action"] == "KEEP"
    assert result["reason"] == "INCOMPLETE_REGISTRY_FAIL_CLOSED"
    proof = result["binding_proof"]
    assert proof["proven"] is False
    assert proof["registry_complete"] is False
    assert proof["missing_dur_proof"] == ["session_id"]
    assert proof["caller_value_accepted_as_proof"] is False
    assert proof["evidence_documents"] == []
    assert _last_lifecycle(sandbox, "ws-partial") == ""
    assert not ledger.exists()


def test_restore_partial_registry_with_durable_docs_allowed(sandbox):
    """3. Partial registry + durable evidence proving every missing field
    => allowed, subject to the Owner gate."""
    ws_path = sandbox / ".tmp" / "ws-partial-doc"
    _raw_row(sandbox, workspace_id="ws-partial-doc", workspace_path=ws_path,
             omit_identity=("session_id",))
    root_rel = str(ws_path.relative_to(sandbox))
    _binding_evidence(sandbox, name="binding-partial-doc.json",
                      workspace_id="ws-partial-doc", root_path=root_rel)

    result = fw06.restore_workspace_lifecycle_binding(
        sandbox,
        authority=fw06.LIFECYCLE_BINDING_RESTORE_AUTHORITY,
        owner_authorization_id=OWNER_AUTH,
        restored_lifecycle="COMPLETE",
        identity=_restore_identity("ws-partial-doc", root_rel,
                                   session_id="session-alpha"),
        evidence_pointers=["reports/binding-partial-doc.json"],
        policy=_policy(),
    )

    assert result["status"] == "RESTORED"
    assert result["final_action"] == "KEEP"
    assert result["delete_authorized"] is False
    proof = result["binding_proof"]
    assert proof["proven"] is True
    assert proof["registry_complete"] is False
    assert len(proof["evidence_documents"]) == 1
    assert proof["registry_source"] == {
        "workspace_id": "ws-partial-doc",
        "project_id": "project-alpha",
        "task_id": "task-alpha",
        "root_path": _path_key_for_test(sandbox / ".tmp" / "ws-partial-doc"),
        "base_revision": BASE_REVISION,
    }
    assert _last_lifecycle(sandbox, "ws-partial-doc") == "COMPLETE"


def test_restore_caller_value_never_proof_without_durable_source(sandbox):
    """4. Caller supplies a missing/unproven field with no durable source
    => BLOCKED. Caller-provided values are claims, never evidence."""
    ws_path = sandbox / ".tmp" / "ws-caller-only"
    _raw_row(sandbox, workspace_id="ws-caller-only", workspace_path=ws_path,
             omit_identity=("session_id", "task_id", "owner_task_id"))
    root_rel = str(ws_path.relative_to(sandbox))
    ledger = sandbox / ".p2p" / "state" / fw06.LIFECYCLE_RESTORE_LEDGER

    result = fw06.restore_workspace_lifecycle_binding(
        sandbox,
        authority=fw06.LIFECYCLE_BINDING_RESTORE_AUTHORITY,
        owner_authorization_id=OWNER_AUTH,
        restored_lifecycle="COMPLETE",
        identity=_restore_identity("ws-caller-only", root_rel,
                                   session_id="CALLER-SUPPLIED",
                                   task_id="CALLER-TASK"),
        evidence_pointers=[],
        policy=_policy(),
    )

    assert result["status"] == "BLOCKED"
    assert result["final_action"] == "KEEP"
    assert result["reason"] == "INCOMPLETE_REGISTRY_FAIL_CLOSED"
    proof = result["binding_proof"]
    assert proof["proven"] is False
    assert set(proof["missing_dur_proof"]) == {"session_id", "task_id"}
    assert proof["caller_value_accepted_as_proof"] is False
    assert _last_lifecycle(sandbox, "ws-caller-only") == ""
    assert not ledger.exists()


def test_restore_contradictory_durable_evidence_blocked(sandbox):
    """5. Contradictory evidence (doc disagrees with the durable registry)
    => BLOCKED / KEEP."""
    ws_path = sandbox / ".tmp" / "ws-contradict"
    _raw_row(sandbox, workspace_id="ws-contradict", workspace_path=ws_path)
    root_rel = str(ws_path.relative_to(sandbox))
    # Complete durable doc, but project_id disagrees with the registry.
    _binding_evidence(sandbox, name="binding-contradict.json",
                      workspace_id="ws-contradict", root_path=root_rel,
                      project_id="project-BETA")

    result = fw06.restore_workspace_lifecycle_binding(
        sandbox,
        authority=fw06.LIFECYCLE_BINDING_RESTORE_AUTHORITY,
        owner_authorization_id=OWNER_AUTH,
        restored_lifecycle="COMPLETE",
        identity=_restore_identity("ws-contradict", root_rel,
                                   project_id="project-BETA"),
        evidence_pointers=["reports/binding-contradict.json"],
        policy=_policy(),
    )

    assert result["status"] == "BLOCKED"
    assert result["final_action"] == "KEEP"
    assert result["reason"] == "BINDING_CONTRADICTS_DURABLE_REGISTRY"
    assert result["binding_proof"]["proven"] is False
    assert result["binding_proof"]["conflicting_field"] == "project_id"
    assert _last_lifecycle(sandbox, "ws-contradict") == ""
