"""Focused A-T fixture tests for P2P-TMPGC01.

Every physical deletion in this module targets a disposable fixture below the
candidate's dedicated ``.tmp/p2p-tmpgc-test-*`` root.  No production or
historical workspace is used as a mutation target.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = ROOT / ".p2p" / "system"
sys.path.insert(0, str(SYSTEM_ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from p2p_capabilities import fw06_operational_resilience as fw06  # noqa: E402
from p2p_capabilities.task_state import TaskPlan, TaskStateStore  # noqa: E402
import p2p_live_certification as live_certification  # noqa: E402


NOW = "2026-08-29T00:00:00Z"
OLD = "2026-01-01T00:00:00Z"
FUTURE = "2026-12-31T00:00:00Z"
REJECTED_SHA = "59530007e80f42699e8e030d80783dfb6bf58cbf"
PRIOR_REVIEWED_SHA = "782d7f0be3107cf87c163c72ee20539304379562"
FW06_SOURCE = ".p2p/system/p2p_capabilities/fw06_operational_resilience.py"


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
def sandbox():
    root = ROOT / ".tmp" / f"p2p-tmpgc-test-{uuid.uuid4().hex}"
    (root / ".tmp").mkdir(parents=True)
    (root / ".p2p" / "state").mkdir(parents=True)
    (root / "reports").mkdir()
    (root / "archive").mkdir()
    (root / "governance").mkdir()
    (root / "governance" / "p2p-tmp-gc-policy.json").write_text(
        json.dumps(_policy(), indent=2, sort_keys=True), encoding="utf-8",
    )
    try:
        yield root
    finally:
        # This is the only broad removal in the suite and is confined to the
        # dedicated disposable fixture root created above.
        shutil.rmtree(root, ignore_errors=True)


def _git(path: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(path), *args],
        capture_output=True,
        text=True,
        check=check,
    )


def _task_state(root: Path, task_id: str, status: str = "CANCELLED") -> None:
    if (root / ".p2p" / "state" / "task-state.json").exists():
        return
    plan = TaskPlan.from_goal(
        {
            "goal_id": "goal-tmpgc-test",
            "scope": ["P2P-TMPGC01-FIXTURE"],
            "out_of_scope": [],
        },
        [{
            "task_id": task_id,
            "title": "TMPGC fixture task",
            "purpose": "exercise fail-closed disposal",
            "status": status,
            "scope": ["P2P-TMPGC01-FIXTURE"],
            "acceptance_requirements": ["fixture-only mutation"],
            "required_evidence": ["fixture evidence"],
        }],
        now=NOW,
    )
    TaskStateStore(root).initialize(plan, at=NOW)


def _make_git_workspace(root: Path, workspace_id: str,
                        *, extra_commit: bool = False) -> tuple[Path, str]:
    workspace = root / ".tmp" / workspace_id
    workspace.mkdir(parents=True)
    _git(workspace, "init", "-b", "main")
    _git(workspace, "config", "user.name", "P2P TMPGC fixture")
    _git(workspace, "config", "user.email", "tmpgc-fixture@example.invalid")
    (workspace / "payload.txt").write_text("base\n", encoding="utf-8")
    _git(workspace, "add", "payload.txt")
    _git(workspace, "commit", "-m", "fixture base")
    if extra_commit:
        (workspace / "payload.txt").write_text("unique local history\n", encoding="utf-8")
        _git(workspace, "add", "payload.txt")
        _git(workspace, "commit", "-m", "fixture unique local commit")
    head = _git(workspace, "rev-parse", "HEAD").stdout.strip()
    return workspace, head


def _durable_files(root: Path, workspace_id: str) -> tuple[Path, Path]:
    evidence = root / "reports" / f"{workspace_id}-evidence.json"
    handoff = root / "archive" / f"{workspace_id}-handoff.json"
    evidence.write_text('{"fixture":"evidence"}\n', encoding="utf-8")
    handoff.write_text('{"fixture":"handoff"}\n', encoding="utf-8")
    return evidence, handoff


def _bundle(root: Path, workspace: Path, workspace_id: str,
            head: str) -> tuple[Path, str]:
    archive = root / ".p2p" / "state" / f"{workspace_id}.bundle"
    _git(workspace, "bundle", "create", str(archive), "--all")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    return archive, digest


def _record(root: Path, workspace_id: str, *, task_id: str = "task-1",
            lifecycle: str = "COMPLETE", status: str = "QUIESCED",
            extra_commit: bool = False, archive: bool = True,
            disposable_after: str = OLD, **overrides) -> dict:
    _task_state(root, task_id, str(overrides.pop("task_status", "CANCELLED")))
    workspace, head = _make_git_workspace(
        root, workspace_id, extra_commit=extra_commit,
    )
    evidence, handoff = _durable_files(root, workspace_id)
    archive_path = ""
    archive_sha = ""
    if archive:
        archive_file, archive_sha = _bundle(root, workspace, workspace_id, head)
        archive_path = str(archive_file)
    record = {
        "workspace_id": workspace_id,
        "project_id": "p2p-tmpgc-test",
        "owner_goal_id": "goal-tmpgc-test",
        "owner_task_id": task_id,
        "task_id": task_id,
        "session_id": f"session-{workspace_id}",
        "root_path": str(workspace),
        "temp_root": str(root / ".tmp"),
        "base_revision": head,
        "head_revision": head,
        "created_at": OLD,
        "last_used_at": OLD,
        "completed_at": OLD,
        "disposable_after": disposable_after,
        "status": status,
        "lifecycle_state": lifecycle,
        "mutation_policy": "SYNTHETIC_ONLY",
        "conflict_group": "",
        "git_worktree": False,
        "workspace_type": "GIT_CLONE",
        "purpose": "P2P-TMPGC01 fixture",
        "creator": "focused-test",
        "branch": "main",
        "remote": "",
        "evidence_pointers": [str(evidence)],
        "evidence_status": "DURABLE",
        "handoff_status": "DURABLE",
        "handoff_ref": str(handoff),
        "dependencies": [],
        "owner_gate": False,
        "candidate": False,
        "rollback_required": False,
        "protection_reasons": [],
        "archive_path": archive_path,
        "archive_sha256": archive_sha,
        "archive_head": head if archive else "",
    }
    record.update(overrides)
    return fw06.register_workspace(root, record)


def _classify(root: Path, record: dict, *, pressure: dict | None = None,
              now: str = NOW) -> dict:
    return fw06.classify_tmp_workspace(
        root,
        record,
        policy=_policy(),
        pressure=pressure,
        now=now,
    )


def _latest(root: Path, workspace_id: str) -> dict:
    return next(
        row for row in fw06.list_all_workspaces(root)
        if row.get("workspace_id") == workspace_id
    )


def _load_rejected_fw06(root: Path, *, rejected_sha: str = REJECTED_SHA):
    source = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{rejected_sha}:{FW06_SOURCE}"],
        capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout
    module_path = root / "rejected-fw06.py"
    module_path.write_text(source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location(
        "rejected_fw06_tmpgc01", module_path,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _audit_row(*, workspace_id: str, path: str, status: str,
               deletion_time: str, prior_lifecycle: str = "COMPLETE",
               **overrides) -> dict:
    digest = "a" * 64
    row = {
        "schema": fw06.TMP_GC_SCHEMA,
        "workspace_id": workspace_id,
        "path": path,
        "task_id": "task-audit",
        "prior_lifecycle": prior_lifecycle,
        "deletion_time": deletion_time,
        "classification_evidence_digest": digest,
        "reclaimed_bytes": 1 if status == "DELETE_PHYSICAL_SUCCESS" else 0,
        "reason": "fixture audit evidence",
        "status": status,
        "delete_authorized": status in {
            "DELETE_INTENT", "DELETE_PHYSICAL_SUCCESS",
        },
        "final_revalidation_valid": status in {
            "DELETE_INTENT", "DELETE_PHYSICAL_SUCCESS",
        },
        "dry_run": False,
        "physical_deleted": status == "DELETE_PHYSICAL_SUCCESS",
        "authorized_path": path if status in {
            "DELETE_INTENT", "DELETE_PHYSICAL_SUCCESS",
        } else "",
        "physical_deleted_path": path
        if status == "DELETE_PHYSICAL_SUCCESS" else "",
        "protection_reasons": [],
        "active_lease": False,
        "active_lock": False,
        "active_dependency": False,
        "filesystem_operation": (
            "REMOVED" if status == "DELETE_PHYSICAL_SUCCESS"
            else "NOT_ATTEMPTED"
        ),
        "filesystem_result": {
            "operation": (
                "REMOVED" if status == "DELETE_PHYSICAL_SUCCESS"
                else "NOT_ATTEMPTED"
            ),
            "path": path,
            "before": (
                "PRESENT" if status == "DELETE_PHYSICAL_SUCCESS"
                else "UNKNOWN"
            ),
            "after": (
                "ABSENT" if status == "DELETE_PHYSICAL_SUCCESS"
                else "NOT_ATTEMPTED"
            ),
        },
        "lifecycle_from": prior_lifecycle,
        "lifecycle_to": (
            "DELETED" if status == "DELETE_PHYSICAL_SUCCESS"
            else prior_lifecycle
        ),
    }
    row.update(overrides)
    row["audit_id"] = fw06._classification_digest([
        "tmp-gc-audit", workspace_id, status, digest,
    ])
    return row


def _write_audit(root: Path, *rows: dict) -> None:
    path = root / ".p2p" / "state" / fw06.TMP_GC_AUDIT_PATH
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_A_registered_active_workspace_kept(sandbox):
    record = _record(sandbox, "a-active", lifecycle="ACTIVE", status="ACTIVE",
                     task_status="ACTIVE", archive=False)
    result = _classify(sandbox, record)
    assert result["final_action"] == "KEEP"
    assert "ACTIVE_SESSION" in result["protection_reasons"]


def test_A_active_execution_lease_keeps_terminal_workspace(sandbox):
    record = _record(sandbox, "a-lease")
    acquired = fw06.acquire_lease(
        sandbox,
        owner_process="tmpgc-fixture-owner",
        project_id=record["project_id"],
        task_id=record["task_id"],
        ttl_seconds=120,
    )
    assert acquired["acquired"] is True
    try:
        result = _classify(sandbox, record)
        assert result["final_action"] == "KEEP"
        assert "ACTIVE_SESSION" in result["protection_reasons"]
    finally:
        fw06.release_lease(sandbox, acquired["lease"]["lease_id"])


def test_lease_acquisition_is_single_writer_across_processes(sandbox):
    code_template = (
        "import json, sys; "
        "sys.path.insert(0, {system!r}); "
        "from p2p_capabilities import fw06_operational_resilience as f; "
        "result = f.acquire_lease({root!r}, owner_process={owner!r}, "
        "project_id='lease-race', goal_id='goal-race', "
        "task_id='task-race', ttl_seconds=120); "
        "print(json.dumps(result, sort_keys=True))"
    )
    processes = [
        subprocess.Popen(
            [sys.executable, "-B", "-c", code_template.format(
                system=str(SYSTEM_ROOT), root=str(sandbox), owner=owner,
            )],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        for owner in ("lease-race-a", "lease-race-b")
    ]
    results = []
    for process in processes:
        stdout, stderr = process.communicate(timeout=20)
        assert process.returncode == 0, stderr
        results.append(json.loads(stdout))
    assert sorted(bool(item.get("acquired")) for item in results) == [False, True]
    failures = [item.get("failure_class") for item in results
                if not item.get("acquired")]
    assert len(failures) == 1
    assert failures[0] in {"LEASE_CONFLICT", "LEASE_LOCK_UNAVAILABLE"}


def test_inventory_roots_relative_registry_paths_and_measures_payload(sandbox):
    target = sandbox / ".tmp" / "relative-fixture"
    target.mkdir()
    payload = target / "payload.txt"
    payload.write_text("payload", encoding="utf-8")
    row = {
        "workspace_id": "relative-fixture",
        "project_id": "p2p-tmpgc-test",
        "root_path": ".tmp/relative-fixture",
        "status": "QUIESCED",
        "lifecycle_state": "COMPLETE",
    }
    fw06._workspaces_path(sandbox, mkdirs=True).write_text(
        json.dumps(row, sort_keys=True) + "\n", encoding="utf-8",
    )
    result = fw06.inventory_tmp_gc(sandbox, policy=_policy(), now=NOW)
    item = next(entry for entry in result["workspaces"]
                if entry["workspace_id"] == "relative-fixture")
    assert Path(item["path"]).resolve() == target.resolve()
    assert item["size"] == payload.stat().st_size
    assert item["predicates"]["size_complete"] is True


def test_A_relevant_git_lock_keeps_terminal_workspace(sandbox):
    record = _record(sandbox, "a-lock")
    lock = Path(record["root_path"]) / ".git" / "index.lock"
    lock.write_text("fixture lock\n", encoding="utf-8")
    try:
        result = _classify(sandbox, record)
        assert result["final_action"] == "KEEP"
        assert "ACTIVE_SESSION" in result["protection_reasons"]
    finally:
        lock.unlink(missing_ok=True)


def test_A_central_registry_lock_keeps_terminal_workspace(sandbox):
    record = _record(sandbox, "a-central-lock")
    lock = sandbox / ".p2p" / "state" / "fw06-workspaces.jsonl.lock"
    lock.write_text("fixture lock\n", encoding="utf-8")
    try:
        result = _classify(sandbox, record)
        assert result["final_action"] == "KEEP"
        assert "ACTIVE_SESSION" in result["protection_reasons"]
    finally:
        lock.unlink(missing_ok=True)


def test_B_owner_gate_candidate_kept(sandbox):
    record = _record(sandbox, "b-owner", owner_gate=True,
                     protection_reasons=["OWNER_GATE", "CANDIDATE"])
    result = _classify(sandbox, record)
    assert result["final_action"] == "KEEP"
    assert {"OWNER_GATE", "CANDIDATE"} <= set(result["protection_reasons"])


def test_C_rollback_required_kept(sandbox):
    record = _record(sandbox, "c-rollback", rollback_required=True,
                     protection_reasons=["ROLLBACK_REQUIRED"])
    result = _classify(sandbox, record)
    assert result["final_action"] == "KEEP"
    assert "ROLLBACK_REQUIRED" in result["protection_reasons"]


def test_D_dirty_git_workspace_kept(sandbox):
    record = _record(sandbox, "d-dirty")
    Path(record["root_path"], "payload.txt").write_text("dirty\n", encoding="utf-8")
    result = _classify(sandbox, record)
    assert result["final_action"] == "KEEP"
    assert "DIRTY" in result["protection_reasons"]


def test_E_unique_unpushed_commit_without_archive_kept(sandbox):
    record = _record(sandbox, "e-unique", extra_commit=True, archive=False)
    result = _classify(sandbox, record)
    assert result["final_action"] == "KEEP"
    assert "UNIQUE_LOCAL_HISTORY" in result["protection_reasons"]


def test_F_verified_reusable_archive_allows_eligibility(sandbox):
    record = _record(sandbox, "f-archive", extra_commit=True, archive=True)
    result = _classify(sandbox, record)
    assert result["final_action"] == "DELETE_ELIGIBLE"
    inventory = fw06.inventory_tmp_gc(sandbox, policy=_policy(), now=NOW)
    applied = fw06.apply_tmp_gc(sandbox, inventory, policy=_policy(), now=NOW)
    assert applied["deleted_count"] == 1
    assert not Path(record["root_path"]).exists()


def test_G_unknown_metadata_kept(sandbox):
    record = _record(sandbox, "g-unknown")
    record.pop("owner_gate")
    result = _classify(sandbox, record)
    assert result["final_action"] == "KEEP"
    assert "UNKNOWN" in result["protection_reasons"]


def test_G_explicit_unknown_protection_reason_kept(sandbox):
    record = _record(sandbox, "g-explicit-unknown")
    fw06._workspace_state_update(
        sandbox,
        record["workspace_id"],
        protection_reasons=["UNKNOWN"],
        event_type="FIXTURE_UNKNOWN_PROTECTION",
    )
    current = _latest(sandbox, record["workspace_id"])
    result = _classify(sandbox, current)
    assert result["final_action"] == "KEEP"
    assert "UNKNOWN" in result["protection_reasons"]


def test_H_non_git_unknown_workspace_kept(sandbox):
    _task_state(sandbox, "task-1")
    workspace = sandbox / ".tmp" / "h-non-git"
    workspace.mkdir()
    (workspace / "payload.txt").write_text("unknown\n", encoding="utf-8")
    record = {
        "workspace_id": "h-non-git",
        "project_id": "p2p-tmpgc-test",
        "owner_goal_id": "goal-tmpgc-test",
        "owner_task_id": "task-1",
        "task_id": "task-1",
        "session_id": "session-h-non-git",
        "root_path": str(workspace),
        "lifecycle_state": "COMPLETE",
        "protection_reasons": [],
        "owner_gate": False,
        "candidate": False,
        "rollback_required": False,
        "dependencies": [],
        "evidence_pointers": [],
        "evidence_status": "UNKNOWN",
        "handoff_status": "UNKNOWN",
        "disposable_after": OLD,
    }
    result = _classify(sandbox, record)
    assert result["final_action"] == "KEEP"
    assert "UNKNOWN" in result["protection_reasons"]


def test_I_outside_allowlist_hard_reject(sandbox):
    record = _record(sandbox, "i-inside")
    outside = sandbox / "outside"
    outside.mkdir()
    record["root_path"] = str(outside)
    result = _classify(sandbox, record)
    assert result["final_action"] == "KEEP"
    assert result["hard_reject"] is True
    assert result["predicates"]["allowlisted_path"] is False


def test_J_canonical_checkout_path_hard_reject(sandbox):
    _task_state(sandbox, "task-1")
    record = {
        "workspace_id": "j-canonical",
        "project_id": "p2p-tmpgc-test",
        "task_id": "task-1",
        "owner_task_id": "task-1",
        "session_id": "session-j-canonical",
        "root_path": str(sandbox),
        "lifecycle_state": "COMPLETE",
    }
    result = _classify(sandbox, record)
    assert result["final_action"] == "KEEP"
    assert result["hard_reject"] is True
    assert result["predicates"]["allowlisted_path"] is False


def test_K_symlink_escape_hard_reject(sandbox):
    _task_state(sandbox, "task-1")
    outside = sandbox / "symlink-target"
    outside.mkdir()
    link = sandbox / ".tmp" / "k-link"
    try:
        os.symlink(str(outside), str(link), target_is_directory=True)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlink fixture unavailable: {exc}")
    record = {
        "workspace_id": "k-link",
        "project_id": "p2p-tmpgc-test",
        "task_id": "task-1",
        "owner_task_id": "task-1",
        "session_id": "session-k-link",
        "root_path": str(link),
        "lifecycle_state": "COMPLETE",
    }
    result = _classify(sandbox, record)
    assert result["final_action"] == "KEEP"
    assert result["hard_reject"] is True


def test_L_missing_handoff_evidence_kept(sandbox):
    record = _record(sandbox, "l-missing", handoff_status="MISSING",
                     handoff_ref="")
    result = _classify(sandbox, record)
    assert result["final_action"] == "KEEP"
    assert "EVIDENCE_NOT_DURABLE" in result["protection_reasons"]


def test_M_durable_handoff_with_owner_gate_kept(sandbox):
    record = _record(sandbox, "m-gated", owner_gate=True)
    result = _classify(sandbox, record)
    assert result["predicates"]["handoff_durable"] is True
    assert result["final_action"] == "KEEP"
    assert "OWNER_GATE" in result["protection_reasons"]


def test_N_disposable_grace_not_elapsed_kept(sandbox):
    record = _record(sandbox, "n-grace", disposable_after=FUTURE)
    result = _classify(sandbox, record)
    assert result["lifecycle"] == "DISPOSABLE"
    assert result["grace_status"] == "NOT_ELAPSED"
    assert result["final_action"] == "KEEP"


def test_O_disposable_grace_elapsed_fixture_delete_pass(sandbox):
    record = _record(sandbox, "o-delete")
    result = fw06.run_tmp_gc(sandbox, policy=_policy(), now=NOW)
    assert result["dry_run"] is True
    assert result["reclaimable_after_grace"] > 0
    assert Path(record["root_path"]).exists()
    applied = fw06.run_tmp_gc(sandbox, apply=True, policy=_policy(), now=NOW)
    assert applied["deleted_count"] == 1
    assert not Path(record["root_path"]).exists()
    assert _latest(sandbox, "o-delete")["lifecycle_state"] == "DELETED"


def test_P_pressure_only_shortens_proven_disposable_grace(sandbox):
    record = _record(sandbox, "p-pressure", disposable_after=FUTURE)
    normal = _classify(
        sandbox, record,
        pressure={"state": "NORMAL"},
    )
    low = _classify(
        sandbox, record,
        pressure={"state": "LOW"},
    )
    critical = _classify(
        sandbox, record,
        pressure={"state": "CRITICAL"},
    )
    assert normal["final_action"] == "KEEP"
    assert low["final_action"] == "DELETE_ELIGIBLE"
    assert critical["final_action"] == "DELETE_ELIGIBLE"
    protected = _record(sandbox, "p-protected", disposable_after=OLD,
                        owner_gate=True)
    protected_result = _classify(
        sandbox, protected,
        pressure={"state": "CRITICAL"},
    )
    assert protected_result["final_action"] == "KEEP"
    assert "OWNER_GATE" in protected_result["protection_reasons"]


def test_P_unknown_disk_measurement_keeps_even_at_critical(monkeypatch, sandbox):
    record = _record(sandbox, "p-pressure-unknown")

    def fail_disk_usage(_path):
        raise OSError("fixture disk usage unavailable")

    monkeypatch.setattr(fw06.shutil, "disk_usage", fail_disk_usage)
    result = _classify(sandbox, record)
    assert result["final_action"] == "KEEP"
    assert result["predicates"]["pressure_known"] is False
    assert "UNKNOWN" in result["protection_reasons"]


def test_P_unknown_disk_measurement_blocks_creation_preflight(monkeypatch,
                                                              sandbox):
    def fail_disk_usage(_path):
        raise OSError("fixture disk usage unavailable")

    monkeypatch.setattr(fw06.shutil, "disk_usage", fail_disk_usage)
    result = fw06.opportunistic_tmp_gc_before_workspace_creation(
        sandbox, policy=_policy(), now=NOW,
    )
    assert result["status"] == "UNKNOWN"
    assert result["pressure_state"] == "UNKNOWN"


def test_Q_apply_revalidates_state_changed_after_inventory(sandbox):
    record = _record(sandbox, "q-toctou")
    inventory = fw06.inventory_tmp_gc(sandbox, policy=_policy(), now=NOW)
    fw06._workspace_state_update(
        sandbox, record["workspace_id"], owner_gate=True,
        protection_reasons=["OWNER_GATE"], event_type="FIXTURE_OWNER_GATE",
    )
    applied = fw06.apply_tmp_gc(sandbox, inventory, policy=_policy(), now=NOW)
    assert applied["deleted_count"] == 0
    assert Path(record["root_path"]).exists()
    assert _latest(sandbox, "q-toctou")["lifecycle_state"] != "DELETED"


def test_Q_final_classifier_rechecks_active_lease_before_delete(sandbox):
    record = _record(sandbox, "q-final-lease")
    classification = _classify(sandbox, record)
    acquired = fw06.acquire_lease(
        sandbox,
        owner_process="tmpgc-final-revalidation-owner",
        project_id=record["project_id"],
        task_id=record["task_id"],
        ttl_seconds=120,
    )
    assert acquired["acquired"] is True
    try:
        outcome = fw06._delete_tmp_workspace(
            sandbox,
            record,
            classification,
            _policy(),
            now=NOW,
        )
    finally:
        fw06.release_lease(sandbox, acquired["lease"]["lease_id"])
    assert outcome["status"] == "DELETE_REVALIDATION_FAILED"
    assert Path(record["root_path"]).exists()


def test_TOCTOU_rejected_candidate_deletes_after_post_final_lease(
        sandbox):
    rejected_fw06 = _load_rejected_fw06(sandbox)
    record = _record(sandbox, "toctou-rejected-gap")
    classification = rejected_fw06.classify_tmp_workspace(
        sandbox, record, policy=_policy(), now=NOW,
    )
    probe = {}
    original = rejected_fw06.classify_tmp_workspace

    def final_then_acquire(*args, **kwargs):
        result = original(*args, **kwargs)
        probe.update(rejected_fw06.acquire_lease(
            sandbox,
            owner_process="rejected-gap-owner",
            project_id=record["project_id"],
            task_id=record["task_id"],
            ttl_seconds=120,
        ))
        return result

    rejected_fw06.classify_tmp_workspace = final_then_acquire
    outcome = rejected_fw06._delete_tmp_workspace(
        sandbox, record, classification, _policy(), now=NOW,
    )
    assert probe["acquired"] is True
    assert outcome["status"] == "DELETED"
    assert not Path(record["root_path"]).exists()


def test_TOCTOU_new_serialization_blocks_post_final_lease_mutation(
        sandbox, monkeypatch):
    record = _record(sandbox, "toctou-serialized-gap")
    classification = _classify(sandbox, record)
    probe = {}
    original = fw06.classify_tmp_workspace

    def final_then_acquire(*args, **kwargs):
        result = original(*args, **kwargs)
        probe.update(fw06.acquire_lease(
            sandbox,
            owner_process="serialized-gap-owner",
            project_id=record["project_id"],
            task_id=record["task_id"],
            ttl_seconds=120,
        ))
        return result

    monkeypatch.setattr(fw06, "classify_tmp_workspace", final_then_acquire)
    outcome = fw06._delete_tmp_workspace(
        sandbox, record, classification, _policy(), now=NOW,
    )
    assert probe["acquired"] is False
    assert probe["failure_class"] == "LEASE_LOCK_UNAVAILABLE"
    assert outcome["status"] == "DELETED"
    assert not any(
        row.get("status") == "ACTIVE"
        for row in fw06.read_leases(sandbox)
    )
    assert not Path(record["root_path"]).exists()


def test_DELETE_serialization_unavailable_keeps_workspace(sandbox):
    record = _record(sandbox, "delete-serialization-busy")
    classification = _classify(sandbox, record)
    with fw06._lease_writer_guard(sandbox):
        outcome = fw06._delete_tmp_workspace(
            sandbox, record, classification, _policy(), now=NOW,
        )
    assert outcome["status"] == "DELETE_REVALIDATION_FAILED"
    assert outcome["audit"]["reason"] == "DELETE_SERIALIZATION_UNAVAILABLE"
    assert outcome["workspace_removed"] is False
    assert Path(record["root_path"]).exists()


@pytest.mark.parametrize(
    "overrides",
    [
        {"delete_authorized": False},
        {"final_revalidation_valid": False},
        {"dry_run": True},
        {"physical_deleted": False},
        {"protection_reasons": ["OWNER_GATE"]},
        {"active_lease": True},
        {"active_lock": True},
        {"active_dependency": True},
        {"authorized_path": "C:/other-authorized-path"},
        {"physical_deleted_path": "C:/other-deleted-path"},
        {"filesystem_operation": "FAILED"},
        {"lifecycle_from": "ACTIVE"},
        {"lifecycle_to": "COMPLETE"},
        {"prior_lifecycle": "ACTIVE", "lifecycle_from": "COMPLETE"},
    ],
)
def test_AUDIT_contradictory_success_rows_are_rejected(sandbox, overrides):
    path = str(sandbox / ".tmp" / "audit-semantic")
    intent = _audit_row(
        workspace_id="audit-semantic",
        path=path,
        status="DELETE_INTENT",
        deletion_time="2026-08-29T00:00:00Z",
    )
    success = _audit_row(
        workspace_id="audit-semantic",
        path=path,
        status="DELETE_PHYSICAL_SUCCESS",
        deletion_time="2026-08-29T00:00:01Z",
        **overrides,
    )
    _write_audit(sandbox, intent, success)
    assert fw06._tmp_gc_audit_is_well_formed(sandbox) is False


def test_AUDIT_unknown_authorization_and_missing_intent_are_rejected(sandbox):
    path = str(sandbox / ".tmp" / "audit-unknown")
    unknown = _audit_row(
        workspace_id="audit-unknown",
        path=path,
        status="DELETE_PHYSICAL_SUCCESS",
        deletion_time="2026-08-29T00:00:00Z",
        prior_lifecycle="UNKNOWN",
        lifecycle_from="UNKNOWN",
    )
    _write_audit(sandbox, unknown)
    assert fw06._tmp_gc_audit_is_well_formed(sandbox) is False


@pytest.mark.parametrize(
    ("case", "status", "overrides", "target_exists"),
    [
        (
            "success_target_still_exists", "DELETE_PHYSICAL_SUCCESS", {}, True
        ),
        (
            "success_target_never_existed", "DELETE_PHYSICAL_SUCCESS",
            {"filesystem_result": {
                "operation": "REMOVED", "path": "PLACEHOLDER",
                "before": "ABSENT", "after": "ABSENT",
            }}, False,
        ),
        (
            "success_target_unremoved", "DELETE_PHYSICAL_SUCCESS",
            {"filesystem_result": {
                "operation": "REMOVED", "path": "PLACEHOLDER",
                "before": "PRESENT", "after": "PRESENT",
            }}, False,
        ),
        (
            "failure_dry_run_removed_evidence", "DELETE_FAILED",
            {"dry_run": True, "filesystem_operation": "REMOVED"}, False,
        ),
        (
            "failure_status_with_REMOVED", "DELETE_FAILED",
            {"filesystem_operation": "REMOVED"}, False,
        ),
        (
            "dry_run_with_physical_deleted", "DELETE_PHYSICAL_SUCCESS",
            {"dry_run": True}, False,
        ),
        (
            "physical_deleted_without_filesystem_result",
            "DELETE_PHYSICAL_SUCCESS", {"filesystem_result": None}, False,
        ),
        (
            "success_without_authorization", "DELETE_PHYSICAL_SUCCESS",
            {"delete_authorized": False}, False,
        ),
        (
            "success_without_final_revalidation", "DELETE_PHYSICAL_SUCCESS",
            {"final_revalidation_valid": False}, False,
        ),
    ],
    ids=lambda value: value if isinstance(value, str) else None,
)
def test_AUDIT_filesystem_proof_counterfactuals_are_rejected(
        sandbox, case, status, overrides, target_exists):
    path = str(sandbox / ".tmp" / f"audit-{case}")
    result_overrides = dict(overrides)
    filesystem_result = result_overrides.get("filesystem_result")
    if isinstance(filesystem_result, dict):
        result_overrides["filesystem_result"] = {
            **filesystem_result, "path": path,
        }
    if target_exists:
        Path(path).mkdir(parents=True)
    if status == "DELETE_PHYSICAL_SUCCESS":
        intent = _audit_row(
            workspace_id=case, path=path, status="DELETE_INTENT",
            deletion_time="2026-08-29T00:00:00Z",
        )
        success = _audit_row(
            workspace_id=case, path=path, status=status,
            deletion_time="2026-08-29T00:00:01Z", **result_overrides,
        )
        _write_audit(sandbox, intent, success)
    else:
        failure = _audit_row(
            workspace_id=case, path=path, status=status,
            deletion_time="2026-08-29T00:00:00Z", **result_overrides,
        )
        _write_audit(sandbox, failure)
    assert fw06._tmp_gc_audit_is_well_formed(sandbox) is False


def test_AUDIT_valid_intent_and_success_are_accepted(sandbox):
    path = str(sandbox / ".tmp" / "audit-valid")
    intent = _audit_row(
        workspace_id="audit-valid",
        path=path,
        status="DELETE_INTENT",
        deletion_time="2026-08-29T00:00:00Z",
    )
    success = _audit_row(
        workspace_id="audit-valid",
        path=path,
        status="DELETE_PHYSICAL_SUCCESS",
        deletion_time="2026-08-29T00:00:01Z",
    )
    _write_audit(sandbox, intent, success)
    assert fw06._tmp_gc_audit_is_well_formed(sandbox) is True


def test_AUDIT_lifecycle_identity_regression_fails_rejected_design(sandbox):
    rejected_fw06 = _load_rejected_fw06(
        sandbox, rejected_sha=PRIOR_REVIEWED_SHA,
    )
    path = str(sandbox / ".tmp" / "audit-lifecycle-mismatch")
    intent = _audit_row(
        workspace_id="audit-lifecycle-mismatch",
        path=path,
        status="DELETE_INTENT",
        deletion_time="2026-08-29T00:00:00Z",
        prior_lifecycle="ACTIVE",
        lifecycle_from="COMPLETE",
        lifecycle_to="COMPLETE",
    )
    success = _audit_row(
        workspace_id="audit-lifecycle-mismatch",
        path=path,
        status="DELETE_PHYSICAL_SUCCESS",
        deletion_time="2026-08-29T00:00:01Z",
        prior_lifecycle="ACTIVE",
        lifecycle_from="COMPLETE",
        lifecycle_to="DELETED",
    )
    intent.pop("filesystem_result")
    success.pop("filesystem_result")
    _write_audit(sandbox, intent, success)
    assert rejected_fw06._tmp_gc_audit_is_well_formed(sandbox) is True
    assert fw06._tmp_gc_audit_is_well_formed(sandbox) is False


def test_R_repeated_gc_is_idempotent(sandbox):
    record = _record(sandbox, "r-repeat")
    first = fw06.run_tmp_gc(sandbox, apply=True, policy=_policy(), now=NOW)
    second = fw06.run_tmp_gc(sandbox, apply=True, policy=_policy(), now=NOW)
    assert first["deleted_count"] == 1
    assert second["deleted_count"] == 0
    deleted_audits = [
        row for row in fw06.read_tmp_gc_audit(sandbox)
        if row.get("workspace_id") == record["workspace_id"]
        and row.get("status") == "DELETE_PHYSICAL_SUCCESS"
    ]
    assert len(deleted_audits) == 1


def test_S_deletion_audit_is_durable_and_bound(sandbox):
    record = _record(sandbox, "s-audit")
    result = fw06.run_tmp_gc(sandbox, apply=True, policy=_policy(), now=NOW)
    assert result["deleted_count"] == 1
    audit = next(
        row for row in fw06.read_tmp_gc_audit(sandbox)
        if row.get("workspace_id") == record["workspace_id"]
        and row.get("status") == "DELETE_PHYSICAL_SUCCESS"
    )
    assert audit["path"] == record["root_path"]
    assert audit["task_id"] == record["task_id"]
    assert audit["prior_lifecycle"] == "COMPLETE"
    assert len(audit["classification_evidence_digest"]) == 64
    assert audit["reclaimed_bytes"] > 0
    assert audit["filesystem_operation"] == "REMOVED"
    assert audit["filesystem_result"] == {
        "operation": "REMOVED",
        "path": record["root_path"],
        "before": "PRESENT",
        "after": "ABSENT",
    }


def test_T_failed_deletion_does_not_claim_deleted(sandbox, monkeypatch):
    record = _record(sandbox, "t-failed")

    def fail(*args, **kwargs):
        raise OSError("fixture deletion failure")

    monkeypatch.setattr(fw06.shutil, "rmtree", fail)
    result = fw06.run_tmp_gc(sandbox, apply=True, policy=_policy(), now=NOW)
    assert result["deleted_count"] == 0
    assert any(item["status"] == "DELETE_FAILED" for item in result["applied"])
    assert Path(record["root_path"]).exists()
    assert _latest(sandbox, "t-failed")["lifecycle_state"] != "DELETED"
    assert not any(
        row.get("workspace_id") == record["workspace_id"]
        and row.get("status") == "DELETE_PHYSICAL_SUCCESS"
        for row in fw06.read_tmp_gc_audit(sandbox)
    )


def test_T_state_update_failure_does_not_claim_deleted(sandbox, monkeypatch):
    record = _record(sandbox, "t-state-failed")
    original = fw06._workspace_state_update

    def fail_deleted_state(root, workspace_id, **kwargs):
        if kwargs.get("lifecycle_state") == "DELETED":
            raise OSError("fixture state storage failure")
        return original(root, workspace_id, **kwargs)

    monkeypatch.setattr(fw06, "_workspace_state_update", fail_deleted_state)
    result = fw06.run_tmp_gc(sandbox, apply=True, policy=_policy(), now=NOW)
    assert result["deleted_count"] == 0
    assert any(item["status"] == "STATE_UPDATE_FAILED"
               for item in result["applied"])
    assert not Path(record["root_path"]).exists()
    assert _latest(sandbox, record["workspace_id"])["lifecycle_state"] != "DELETED"
    assert any(
        row.get("workspace_id") == record["workspace_id"]
        and row.get("status") == "STATE_UPDATE_FAILED"
        for row in fw06.read_tmp_gc_audit(sandbox)
    )


def test_T_physical_delete_without_audit_does_not_claim_deleted(
        sandbox, monkeypatch):
    record = _record(sandbox, "t-audit-failed")
    original = fw06._append_tmp_gc_audit

    def fail_physical_audit(root, payload):
        if payload.get("status") == "DELETE_PHYSICAL_SUCCESS":
            raise OSError("fixture audit storage failure")
        return original(root, payload)

    monkeypatch.setattr(fw06, "_append_tmp_gc_audit", fail_physical_audit)
    result = fw06.run_tmp_gc(sandbox, apply=True, policy=_policy(), now=NOW)
    assert result["deleted_count"] == 0
    assert any(item["status"] == "DELETE_AUDIT_FAILED"
               for item in result["applied"])
    assert not Path(record["root_path"]).exists()
    assert _latest(sandbox, record["workspace_id"])["lifecycle_state"] == "COMPLETE"
    assert not any(
        row.get("workspace_id") == record["workspace_id"]
        and row.get("status") == "DELETE_PHYSICAL_SUCCESS"
        for row in fw06.read_tmp_gc_audit(sandbox)
    )


def test_T_malformed_audit_blocks_apply(sandbox):
    record = _record(sandbox, "t-audit-malformed")
    audit = sandbox / ".p2p" / "state" / fw06.TMP_GC_AUDIT_PATH
    audit.write_text("not-json\n", encoding="utf-8")
    result = fw06.run_tmp_gc(sandbox, apply=True, policy=_policy(), now=NOW)
    assert result["deleted_count"] == 0
    assert result["apply_status"] == "KEEP"
    assert result["apply_block_reason"] == "TMP_GC_AUDIT_MALFORMED"
    assert Path(record["root_path"]).exists()


def test_cli_default_is_dry_run_and_schedule_is_inactive(sandbox):
    cli = ROOT / "scripts" / "p2p_tmp_gc.py"
    dry = subprocess.run(
        [sys.executable, str(cli), "--root", str(sandbox), "gc"],
        capture_output=True, text=True, check=True,
    )
    dry_data = json.loads(dry.stdout)
    assert dry_data["dry_run"] is True
    assert dry_data["apply_requested"] is False
    assert dry_data["legacy_workspace_delete_count"] == 0
    schedule = subprocess.run(
        [sys.executable, str(cli), "--root", str(sandbox), "schedule"],
        capture_output=True, text=True, check=True,
    )
    schedule_data = json.loads(schedule.stdout)
    assert schedule_data["activated"] is False
    assert schedule_data["activation"] == "OWNER_GATED"
    apply_with_override = subprocess.run(
        [sys.executable, str(cli), "--root", str(sandbox), "gc",
         "--apply", "--now", NOW],
        capture_output=True, text=True,
    )
    blocked = json.loads(apply_with_override.stdout)
    assert apply_with_override.returncode == 2
    assert blocked["status"] == "BLOCKED"
    assert blocked["reason"] == "NOW_OVERRIDE_NOT_ALLOWED_IN_APPLY"


def test_creation_seam_runs_opportunistic_pressure_preflight(sandbox):
    repo = sandbox / "source-repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "P2P TMPGC fixture")
    _git(repo, "config", "user.email", "tmpgc-fixture@example.invalid")
    (repo / "payload.txt").write_text("source\n", encoding="utf-8")
    _git(repo, "add", "payload.txt")
    _git(repo, "commit", "-m", "source fixture")
    base = _git(repo, "rev-parse", "HEAD").stdout.strip()
    result = fw06.create_isolated_worktree(
        sandbox,
        repo_path=repo,
        workspace_id="u-preflight",
        base_revision=base,
        worktree_path=sandbox / ".tmp" / "u-preflight",
        project_id="p2p-tmpgc-test",
        task_id="task-1",
        session_id="session-u-preflight",
        creator="focused-test",
        tmp_gc_policy=_policy(),
    )
    assert result["tmp_gc_preflight"]["status"] == "PASS"
    assert _latest(sandbox, "u-preflight")["workspace_type"] == "GIT_WORKTREE"


def test_worktree_delete_does_not_prune_unrelated_admin_metadata(sandbox):
    repo = sandbox / "worktree-source"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.name", "P2P TMPGC fixture")
    _git(repo, "config", "user.email", "tmpgc-fixture@example.invalid")
    (repo / "payload.txt").write_text("source\n", encoding="utf-8")
    _git(repo, "add", "payload.txt")
    _git(repo, "commit", "-m", "source fixture")
    base = _git(repo, "rev-parse", "HEAD").stdout.strip()
    target = sandbox / ".tmp" / "worktree-target"
    stale = sandbox / ".tmp" / "worktree-stale"
    _git(repo, "worktree", "add", "--detach", str(target), base)
    _git(repo, "worktree", "add", "--detach", str(stale), base)

    def admin_path(worktree: Path) -> Path:
        marker = (worktree / ".git").read_text(encoding="utf-8")
        raw = next(line.split(":", 1)[1].strip()
                    for line in marker.splitlines()
                    if line.startswith("gitdir:"))
        path = Path(raw)
        return (worktree / ".git" / path).resolve() \
            if not path.is_absolute() else path.resolve()

    target_admin = admin_path(target)
    stale_admin = admin_path(stale)
    assert target_admin.exists()
    assert stale_admin.exists()
    shutil.rmtree(stale)
    assert stale_admin.exists()

    _task_state(sandbox, "task-1")
    evidence, handoff = _durable_files(sandbox, "worktree-target")
    archive = sandbox / ".p2p" / "state" / "worktree-target.bundle"
    _git(target, "bundle", "create", str(archive), "--all")
    archive_sha = hashlib.sha256(archive.read_bytes()).hexdigest()
    record = {
        "workspace_id": "worktree-target",
        "project_id": "p2p-tmpgc-test",
        "owner_goal_id": "goal-tmpgc-test",
        "owner_task_id": "task-1",
        "task_id": "task-1",
        "session_id": "session-worktree-target",
        "root_path": str(target),
        "temp_root": str(sandbox / ".tmp"),
        "base_revision": base,
        "head_revision": base,
        "created_at": OLD,
        "last_used_at": OLD,
        "completed_at": OLD,
        "disposable_after": OLD,
        "status": "QUIESCED",
        "lifecycle_state": "COMPLETE",
        "protection_reasons": [],
        "mutation_policy": "SYNTHETIC_ONLY",
        "conflict_group": "",
        "git_worktree": str(target),
        "repo_path": str(repo),
        "workspace_type": "GIT_WORKTREE",
        "purpose": "worktree prune boundary fixture",
        "creator": "focused-test",
        "evidence_pointers": [str(evidence)],
        "evidence_status": "DURABLE",
        "handoff_status": "DURABLE",
        "handoff_ref": str(handoff),
        "owner_gate": False,
        "candidate": False,
        "rollback_required": False,
        "dependencies": [],
        "archive_path": str(archive),
        "archive_sha256": archive_sha,
        "archive_head": base,
    }
    fw06.register_workspace(sandbox, record)
    applied = fw06.run_tmp_gc(sandbox, apply=True, policy=_policy(), now=NOW)
    assert applied["deleted_count"] == 1, applied
    assert not target.exists()
    assert not target_admin.exists()
    assert stale_admin.exists()


def test_duplicate_workspace_binding_is_dependency_keep(sandbox):
    first = _record(sandbox, "v-first")
    duplicate = dict(first)
    duplicate["workspace_id"] = "v-second"
    duplicate["session_id"] = "session-v-second"
    fw06.register_workspace(sandbox, duplicate)
    inventory = fw06.inventory_tmp_gc(sandbox, policy=_policy(), now=NOW)
    matches = [
        item for item in inventory["workspaces"]
        if item["path"] == first["root_path"]
    ]
    assert len(matches) == 2
    assert all(item["final_action"] == "KEEP" for item in matches)
    assert all("DEPENDENCY" in item["protection_reasons"] for item in matches)
    applied = fw06.apply_tmp_gc(
        sandbox,
        {"workspaces": [{"workspace_id": first["workspace_id"]}]},
        policy=_policy(),
        now=NOW,
    )
    assert applied["deleted_count"] == 0
    assert Path(first["root_path"]).exists()


def test_C27_reconcile_without_registry_keeps_workspace(sandbox):
    workspace = sandbox / ".tmp" / "c27-unregistered"
    workspace.mkdir()
    record = live_certification.build_record(
        prompt="fixture prompt",
        workspace=workspace,
        evidence={"external_execution_id": "fixture", "mutation_state": "KNOWN_NONE"},
        verification={"status": "PASS", "actual_sha256": "fixture"},
        project_id="p2p-tmpgc-test",
    )
    outcome = live_certification.reconcile(
        workspace,
        sandbox / "archive",
        record,
        {"status": "PASS"},
    )
    assert outcome["disposal"] == "KEEP"
    assert outcome["workspace_removed"] is False
    assert workspace.exists()


def test_C27_registered_outside_allowlist_keeps_before_lifecycle_change(sandbox):
    record = _record(sandbox, "c27-outside")
    outside = sandbox / "outside-c27"
    outside.mkdir()
    fw06._workspace_state_update(
        sandbox,
        record["workspace_id"],
        root_path=str(outside),
        lifecycle_state="ACTIVE",
        status="ACTIVE",
        event_type="FIXTURE_MOVE_OUTSIDE_ALLOWLIST",
    )
    live_record = live_certification.build_record(
        prompt="fixture outside prompt",
        workspace=outside,
        evidence={"external_execution_id": "fixture", "mutation_state": "KNOWN_NONE"},
        verification={"status": "PASS", "actual_sha256": "fixture"},
        project_id="p2p-tmpgc-test",
    )
    outcome = live_certification.reconcile(
        outside,
        sandbox / "archive",
        live_record,
        {"status": "PASS"},
        registry_root=sandbox,
    )
    assert outcome["disposal"] == "KEEP"
    assert outcome["workspace_removed"] is False
    assert _latest(sandbox, record["workspace_id"])["lifecycle_state"] == "ACTIVE"
    assert outside.exists()
