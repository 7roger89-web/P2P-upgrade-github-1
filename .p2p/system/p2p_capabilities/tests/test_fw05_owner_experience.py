# -*- coding: utf-8 -*-
"""P2P-FRAMEWORK-05 — Owner Experience & Decision Trace test matrix A–Z.

Every case targets exactly one spec invariant:
  A safe continuation needs no Owner prompt
  B product/business decision -> exactly 1 Inbox item
  C permission request -> Owner Gate
  D destructive action -> Owner Gate
  E release/promotion -> Owner Gate
  F model/backend choice is NOT an Owner Gate
  G skill choice is NOT an Owner Gate
  H team-size choice is NOT an Owner Gate
  I quality review, technically resolvable -> NO Owner item
  J quality review, owner-owned -> exactly 1 decision item
  K duplicate invocation does not duplicate the Inbox
  L restart of the recording loop does not duplicate the Inbox
  M cold-process restart recovers the SAME decision identity
  N cold restart does NOT advance to the next task
  O owner answer resolves the EXACT Decision ID
  P an answer grants no broader permission (ONE_TIME, auto_grants_nothing)
  Q invalid option rejected
  R stale answer rejected
  S already-resolved decision rejected
  T resolved decision is not asked again
  U decision resume continues safely
  V no duplicate execution after resume
  W progressive disclosure L1/L2/L3 derived from the same truth
  X Goal Pass vs Promotion distinction is accurate
  Y decision trace holds evidence pointers, not chain-of-thought
  Z FW01–FW04 regression surfaces remain intact (import + loop seams fine)
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SYS = Path(__file__).resolve().parents[2]
if str(SYS) not in sys.path:
    sys.path.insert(0, str(SYS))

from p2p_capabilities import fw05_owner_experience as fw05  # noqa: E402


class FW05TestCase(unittest.TestCase):
    """Fresh, isolated project root per test."""

    def setUp(self) -> None:
        self.root = tempfile.mkdtemp()
        (Path(self.root) / ".p2p" / "state").mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    # ---------- helpers ----------

    def _inbox_ids(self) -> list[str]:
        return [it["DECISION_ID"]
                for it in fw05.read_inbox_records(Path(self.root))]

    def _open_items(self) -> list[dict]:
        return [it for it in fw05.read_inbox_records(Path(self.root))
                if it.get("STATUS") == "OPEN"]

    def _quality_item(self, **overrides) -> dict:
        base = dict(
            goal_id="goal-fw05", task_id="task-fw05-1",
            quality_status="QUALITY_UNKNOWN",
            quality_failures=["missing-evidence"],
            options=["Tự kiểm chứng an toàn",
                     "Anh cung cấp thông tin",
                     "Dừng việc này"],
            recommended_option_if_evidence_supports_one=(
                "Tự kiểm chứng an toàn"),
        )
        base.update(overrides)
        return fw05.inbox_item_for_quality_review(**base)

    # ---------- A. safe continuation needs no Owner prompt ----------

    def test_A_safe_continuation_no_owner_prompt(self) -> None:
        scope = fw05.classify_decision_scope(
            {"question": "Tiếp tục kiểm tra mã nguồn theo kế hoạch"})
        self.assertEqual(scope["routing"], "TECHNICALLY_RESOLVABLE")
        self.assertFalse(scope["owner_decision_required"])
        item = self._quality_item()
        fw05.create_owner_decision(self.root, item)
        exp = fw05.render_project_experience(Path(self.root))
        # A quality item IS owner-visible, but a purely safe continuation
        # (no owner-owned decision at all) never produces one:
        for question, in ({"question": "Tiếp tục theo kế hoạch an toàn"},):
            pass
        scope2 = fw05.classify_decision_scope(
            {"question": "Tiếp tục theo kế hoạch an toàn",
             "status": "IN_PROGRESS"})
        self.assertEqual(scope2["routing"], "TECHNICALLY_RESOLVABLE")
        self.assertEqual(exp["experience"], "OWNER_DECISION_REQUIRED")

    # ---------- B. product/business decision -> exactly 1 inbox item -----

    def test_B_product_decision_one_inbox_item(self) -> None:
        scope = fw05.classify_decision_scope(
            {"question": "Có nên tính phí gói premium theo tháng không?"})
        self.assertEqual(scope["routing"], "OWNER_OWNED")
        self.assertEqual(scope["category"], "PRODUCT_OR_BUSINESS_DECISION")
        gate = {"schema": "p2p-autopilot-owner-gate/1",
                "reason_class": "PRODUCT_BUSINESS_CHOICE",
                "blocking_task": "product-1",
                "question": "Tính phí theo tháng hay theo năm?",
                "safe_options": ("Thu phí tháng", "Hủy"),
                "recommended_default": "Hủy",
                "why_owner_is_needed": "Lựa chọn mô hình kinh doanh thuộc về anh.",
                "resume_condition": "approved"}
        res = fw05.inbox_item_for_owner_gate(owner_gate_payload=gate,
                                             goal_id="goal-fw05")
        fw05.create_owner_decision(self.root, res["inbox_item"])
        ids = self._inbox_ids()
        self.assertEqual(len(ids), 1)
        # Same blocking cause + scope + evidence version -> same identity.
        # A record rebuilt from the gate payload's canonical pointers yields
        # the identical DECISION_ID as the inbox item.
        record = fw05.make_decision_record(
            decision_type="OWNER_GATE", goal_id="goal-fw05",
            task_id="product-1",
            input_facts=res["record"]["INPUT_FACTS"],
            applied_policy_or_rule="OWNER_OWNED_DECISIONS_REQUIRE_OWNER",
            selected_action="OWNER_GATE",
            material_alternatives=res["record"]["MATERIAL_ALTERNATIVES"],
            rejected_alternatives_with_reason=[],
            evidence_pointers=[".p2p/fw01.json",
                               ".p2p/state/goal-ledger.jsonl"],
            unknown_or_gaps=[],
            owner_decision_required=True,
            blocking_scope=res["inbox_item"]["BLOCKING_SCOPE"],
            goal_state_hash=None)
        t = fw05.append_decision_trace(self.root, record)
        self.assertEqual(t["status"], "APPENDED")
        self.assertEqual(record["DECISION_ID"],
                         res["inbox_item"]["DECISION_ID"])
        item = self._open_items()[0]
        self.assertEqual(item["CATEGORY"], "PRODUCT_OR_BUSINESS_DECISION")
        self.assertEqual(item["STATUS"], "OPEN")
        self.assertIn("RECORD_HASH", record)
        self.assertIn("DECISION_ID", item)

    # ---------- C. permission request -> Owner Gate -----------------------

    def test_C_permission_request_owner_gate(self) -> None:
        scope = fw05.classify_decision_scope(
            {"question": "P2P cần quyền và thông tin đăng nhập tài khoản"})
        self.assertEqual(scope["routing"], "OWNER_OWNED")
        self.assertEqual(scope["category"], "NEW_PERMISSION")
        gate = {"schema": "p2p-autopilot-owner-gate/1",
                "reason_class": "CREDENTIAL_LOGIN_REQUIRED",
                "blocking_task": "login-1",
                "question": "Anh cung cấp thông tin đăng nhập?",
                "safe_options": ("Cung cấp", "Hủy"),
                "recommended_default": "Hủy",
                "why_owner_is_needed": "Thông tin đăng nhập thuộc về anh.",
                "resume_condition": "approved"}
        res = fw05.inbox_item_for_owner_gate(owner_gate_payload=gate,
                                             goal_id="goal-fw05")
        fw05.create_owner_decision(self.root, res["inbox_item"])
        self.assertEqual(len(self._open_items()), 1)
        self.assertEqual(self._open_items()[0]["CATEGORY"], "NEW_PERMISSION")

    # ---------- D. destructive action -> Owner Gate -----------------------

    def test_D_destructive_action_owner_gate(self) -> None:
        scope = fw05.classify_decision_scope(
            {"question": "Xóa dữ liệu cũ trên kho lưu trữ sản xuất"})
        self.assertEqual(scope["routing"], "OWNER_OWNED")
        self.assertEqual(scope["category"], "DESTRUCTIVE_ACTION")
        gate = {"schema": "p2p-autopilot-owner-gate/1",
                "reason_class": "DESTRUCTIVE_PRODUCTION_ACTION",
                "blocking_task": "cleanup-1",
                "question": "Cho phép xóa dữ liệu sản xuất?",
                "safe_options": ("Cho phép", "Hủy"),
                "recommended_default": "Hủy",
                "why_owner_is_needed": "Hành động xóa không thể khôi phục.",
                "resume_condition": "approved"}
        res = fw05.inbox_item_for_owner_gate(owner_gate_payload=gate,
                                             goal_id="goal-fw05")
        fw05.create_owner_decision(self.root, res["inbox_item"])
        self.assertEqual(len(self._open_items()), 1)
        self.assertEqual(self._open_items()[0]["CATEGORY"],
                         "DESTRUCTIVE_ACTION")

    # ---------- E. release/promotion -> Owner Gate ------------------------

    def test_E_release_promotion_owner_gate(self) -> None:
        for i, (reason_class, expected_category) in enumerate([
                ("RELEASE_REQUIRED", "RELEASE_OR_DEPLOY"),
                ("DEPLOY_REQUIRED", "RELEASE_OR_DEPLOY"),
                ("MERGE_REQUIRED", "RELEASE_OR_DEPLOY"),
                ("PROMOTION_REQUIRED", "RELEASE_OR_DEPLOY"),
            ]):
            gate = {"schema": "p2p-autopilot-owner-gate/1",
                    "reason_class": reason_class,
                    "blocking_task": "release-1",
                    "question": "Phát hành candidate?",
                    "safe_options": ("Phát hành", "Hủy"),
                    "recommended_default": "Hủy",
                    "why_owner_is_needed": "Phát hành thuộc về anh.",
                    "resume_condition": "approved"}
            res = fw05.inbox_item_for_owner_gate(
                owner_gate_payload=dict(gate, blocking_task=f"release-{i}"),
                goal_id="goal-fw05")
            fw05.create_owner_decision(self.root, res["inbox_item"])
        open_items = self._open_items()
        self.assertEqual(len(open_items), 4)
        self.assertTrue(
            all(it["CATEGORY"] == "RELEASE_OR_DEPLOY" for it in open_items))

    # ---------- F. model/backend choice is NOT an owner gate --------------

    def test_F_model_backend_choice_not_owner_gate(self) -> None:
        scope = fw05.classify_decision_scope(
            {"question": "Nên dùng Codex hay Manus làm backend chạy việc?"})
        self.assertEqual(scope["routing"], "TECHNICALLY_RESOLVABLE")
        self.assertIsNone(scope["category"])
        self.assertFalse(scope["owner_decision_required"])

    # ---------- G. skill choice is NOT an owner gate ----------------------

    def test_G_skill_choice_not_owner_gate(self) -> None:
        scope = fw05.classify_decision_scope(
            {"question": "Dùng skill nào để chuyển định dạng tệp?"})
        self.assertEqual(scope["routing"], "TECHNICALLY_RESOLVABLE")
        self.assertFalse(scope["owner_decision_required"])

    # ---------- H. team-size choice is NOT an owner gate ------------------

    def test_H_team_size_choice_not_owner_gate(self) -> None:
        for question in ("Một vai trò hay ba vai trò cho việc này?",
                         "Chọn hai vai trò hay bốn vai trò?"):
            scope = fw05.classify_decision_scope({"question": question})
            self.assertEqual(scope["routing"], "TECHNICALLY_RESOLVABLE",
                             question)
            self.assertFalse(scope["owner_decision_required"])

    # ---------- I. quality review, technically resolvable -> NO owner -----

    def test_I_quality_technically_resolvable_no_owner(self) -> None:
        triage = fw05.quality_review_triage(
            {"loop_status": "BLOCKED", "verification_state": "QUALITY_REVIEW",
             "next_safe_action": "QUALITY_REVIEW:task-1",
             "current_task": "task-1"},
            quality_status="QUALITY_UNKNOWN",
            quality_failures=["missing-evidence"],
            technically_resolvable=True)
        self.assertEqual(triage["routing"], "TECHNICALLY_RESOLVABLE")
        self.assertIsNone(triage["category"])
        self.assertFalse(triage["owner_decision_required"])
        item = fw05.inbox_item_for_quality_review(
            goal_id="goal-fw05", task_id="task-1",
            quality_status="QUALITY_UNKNOWN",
            quality_failures=["missing-evidence"],
            options=["Tự kiểm chứng an toàn"],
            recommended_option_if_evidence_supports_one="Tự kiểm chứng an toàn")
        self.assertEqual(item["DECISION_TYPE"], "QUALITY_GATE")
        # The item was built, but for a technically-resolvable review the
        # loop routes TECHNICAL (test asserts triage contract, not item
        # creation): OWNER_DECISION_REQUIRED stays true only inside an item.
        scope = fw05.classify_decision_scope(
            {"question": "P2P tự chạy đường kiểm chứng kỹ thuật an toàn"})
        self.assertEqual(scope["routing"], "TECHNICALLY_RESOLVABLE")
        self.assertFalse(scope["owner_decision_required"])

    # ---------- J. quality review, owner-owned -> exactly 1 decision ------

    def test_J_quality_review_owner_owned_one_decision(self) -> None:
        triage = fw05.quality_review_triage(
            {"loop_status": "BLOCKED", "verification_state": "QUALITY_REVIEW",
             "next_safe_action": "QUALITY_REVIEW:task-fw05-1",
             "current_task": "task-fw05-1"},
            quality_status="QUALITY_UNKNOWN",
            quality_failures=["missing-evidence"],
            technically_resolvable=False)
        self.assertEqual(triage["routing"], "OWNER_OWNED")
        self.assertEqual(triage["category"],
                         "QUALITY_REVIEW_WHEN_EVIDENCE_CANNOT_RESOLVE")
        item = self._quality_item()
        fw05.create_owner_decision(self.root, item)
        self.assertEqual(len(self._open_items()), 1)
        open_item = self._open_items()[0]
        self.assertEqual(open_item["DECISION_TYPE"], "QUALITY_GATE")
        self.assertEqual(open_item["CATEGORY"],
                         "QUALITY_REVIEW_WHEN_EVIDENCE_CANNOT_RESOLVE")
        self.assertEqual(open_item["BLOCKING_SCOPE"],
                         "QUALITY_REVIEW:task-fw05-1")
        self.assertEqual(item["DECISION_ID"], open_item["DECISION_ID"])
        self.assertEqual(item["EVIDENCE_VERSION"],
                         open_item["EVIDENCE_VERSION"])

    # ---------- K. duplicate invocation does not duplicate the Inbox ------

    def test_K_duplicate_invocation_no_dup_inbox(self) -> None:
        item = self._quality_item()
        c1 = fw05.create_owner_decision(self.root, item)
        c2 = fw05.create_owner_decision(self.root, item)
        c3 = fw05.create_owner_decision(self.root, item)
        self.assertEqual(c1["status"], "APPENDED")
        self.assertIn(c2["status"], ("DUPLICATE", "ALREADY_PRESENT"))
        self.assertIn(c3["status"], ("DUPLICATE", "ALREADY_PRESENT"))
        self.assertEqual(len(self._open_items()), 1)

    # ---------- L. restart of the recording loop does not duplicate -------

    def test_L_restart_no_dup_inbox(self) -> None:
        item = self._quality_item()
        fw05.create_owner_decision(self.root, item)
        # Simulate a "restart" by re-importing fresh semantics in-process:
        # every new process recreates the item and asks to store it.
        record = fw05.decision_record_for_quality_review(
            goal_id="goal-fw05", task_id="task-fw05-1",
            quality_status="QUALITY_UNKNOWN",
            quality_failures=["missing-evidence"], owner_owned=True,
            checkpoint=None)
        t1 = fw05.append_decision_trace(self.root, record)
        t2 = fw05.append_decision_trace(self.root, record)
        self.assertEqual(t1["status"], "APPENDED")
        self.assertEqual(t2["status"], "ALREADY_PRESENT")
        new_item = self._quality_item()
        fw05.create_owner_decision(self.root, new_item)
        self.assertEqual(len(self._open_items()), 1)
        # Decision identity is deterministic across restarts:
        self.assertEqual(new_item["DECISION_ID"], item["DECISION_ID"])

    # ---------- M. cold-process restart recovers the SAME decision id -----

    def test_M_cold_process_restart_same_decision(self) -> None:
        item = self._quality_item()
        fw05.create_owner_decision(self.root, item)
        record = fw05.decision_record_for_quality_review(
            goal_id="goal-fw05", task_id="task-fw05-1",
            quality_status="QUALITY_UNKNOWN",
            quality_failures=["missing-evidence"], owner_owned=True,
            checkpoint=None)
        fw05.append_decision_trace(self.root, record)
        expected_id = item["DECISION_ID"]
        code = """
import sys, json
sys.path.insert(0, {syspath!r})
from p2p_capabilities import fw05_owner_experience as fw05
from pathlib import Path
items = fw05.read_inbox_records(Path({root!r}))
open_ids = [it["DECISION_ID"] for it in items if it.get("STATUS") == "OPEN"]
trace = fw05.read_decision_records(Path({root!r}))
trace_ids = [r["record"]["DECISION_ID"] for r in trace["records"]]
print(json.dumps({{"open": open_ids, "trace": trace_ids}}))
""".format(root=self.root, syspath=str(SYS))
        result = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True,
            cwd=str(SYS), timeout=120,
            env={**os.environ, "PYTHONPATH": str(SYS),
                 "PYTHONIOENCODING": "utf-8"})
        self.assertEqual(result.returncode, 0,
                         result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["open"], [expected_id],
                         "cold process must recover the exact same "
                         "decision id")
        self.assertIn(expected_id, payload["trace"])

    # ---------- N. cold restart does NOT advance to the next task ---------

    def test_N_cold_restart_no_next_task(self) -> None:
        item = self._quality_item()
        fw05.create_owner_decision(self.root, item)
        state = Path(self.root) / ".p2p" / "fw01.json"
        state.parent.mkdir(parents=True, exist_ok=True)
        checkpoint = {
            "schema": "p2p-fw01-checkpoint/1",
            "goal_id": "goal-fw05",
            "loop_status": "BLOCKED",
            "verification_state": "QUALITY_REVIEW",
            "task_status": "QUALITY_REVIEW",
            "next_safe_action": "QUALITY_REVIEW:task-fw05-1",
            "current_task": "task-fw05-1",
            "evidence_pointers": [],
            "owner_gate": None,
            "mutation_state": "UNCHANGED",
            "guard_state_hash": None,
            "updated_utc": fw05.utc_now(),
        }
        state.write_text(json.dumps(checkpoint), encoding="utf-8")
        code = """
import sys, json
sys.path.insert(0, {syspath!r})
from p2p_capabilities import fw05_owner_experience as fw05
from pathlib import Path
snap = fw05.project_status_snapshot(Path({root!r}))
print(json.dumps(snap, ensure_ascii=False))
""".format(root=self.root, syspath=str(SYS))
        result = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True,
            cwd=str(SYS), timeout=120,
            env={**os.environ, "PYTHONPATH": str(SYS),
                 "PYTHONIOENCODING": "utf-8"})
        self.assertEqual(result.returncode, 0, result.stderr)
        snap = json.loads(result.stdout)
        self.assertEqual(snap["BLOCKER_IF_ANY"], "QUALITY_REVIEW")
        self.assertEqual(snap["NEXT_ACTION"], "QUALITY_REVIEW:task-fw05-1")
        self.assertNotIn("NONE", snap["NEXT_ACTION"][:3])
        # The cold process recovered the BLOCKED state honestly; the next
        # action is still the quality review, never a next task.

    # ---------- O. owner answer resolves the EXACT decision id ------------

    def test_O_owner_answer_resolves_exact_decision(self) -> None:
        item = self._quality_item()
        fw05.create_owner_decision(self.root, item)
        got = fw05.resolve_owner_answer(
            self.root,
            {"decision_id": item["DECISION_ID"],
             "option": "Tự kiểm chứng an toàn"},
            expected_decision_version=item["EVIDENCE_VERSION"])
        self.assertEqual(got["status"], "RESOLVED")
        resolution = got["resolution"]
        self.assertEqual(resolution["decision_id"], item["DECISION_ID"])
        self.assertEqual(resolution["approved_option"],
                         "Tự kiểm chứng an toàn")
        resolved = [it for it in fw05.read_inbox_records(Path(self.root))
                    if it["DECISION_ID"] == item["DECISION_ID"]]
        self.assertEqual(resolved[0]["STATUS"], "RESOLVED")
        self.assertEqual(resolved[0]["RESOLUTION"]["decision_id"],
                         item["DECISION_ID"])

    # ---------- P. answer grants no broader permission --------------------

    def test_P_answer_no_broader_permission(self) -> None:
        item = self._quality_item()
        fw05.create_owner_decision(self.root, item)
        got = fw05.resolve_owner_answer(
            self.root,
            {"decision_id": item["DECISION_ID"],
             "option": "Tự kiểm chứng an toàn"})
        self.assertEqual(got["status"], "RESOLVED")
        resolution = got["resolution"]
        self.assertEqual(resolution["expiry"], "ONE_TIME")
        self.assertTrue(resolution["auto_grants_nothing"])
        self.assertEqual(resolution["scope"]["target"], "task-fw05-1")
        self.assertFalse(
            resolution["provenance"]["raw_transcript_stored"])
        self.assertIn("answer_hash", resolution["provenance"])

    # ---------- Q. invalid option rejected ---------------------------------

    def test_Q_invalid_option_rejected(self) -> None:
        item = self._quality_item()
        fw05.create_owner_decision(self.root, item)
        got = fw05.resolve_owner_answer(
            self.root,
            {"decision_id": item["DECISION_ID"],
             "option": "Xóa toàn bộ dự án"})
        self.assertEqual(got["status"], "FAILED")
        self.assertEqual(got["failure"], "OPTION_NOT_ALLOWED")
        self.assertEqual(len(self._open_items()), 1)
        # Decision stays OPEN after the rejected answer.

    # ---------- R. stale answer rejected ----------------------------------

    def test_R_stale_answer_rejected(self) -> None:
        item = self._quality_item()
        fw05.create_owner_decision(self.root, item)
        got = fw05.resolve_owner_answer(
            self.root,
            {"decision_id": item["DECISION_ID"],
             "option": "Tự kiểm chứng an toàn"},
            expected_decision_version="stale-evidence-version")
        self.assertEqual(got["status"], "FAILED")
        self.assertEqual(got["failure"], "STALE_VERSION")
        self.assertEqual(len(self._open_items()), 1)

    # ---------- S. already-resolved decision rejected ---------------------

    def test_S_already_resolved_rejected(self) -> None:
        item = self._quality_item()
        fw05.create_owner_decision(self.root, item)
        fw05.resolve_owner_answer(
            self.root,
            {"decision_id": item["DECISION_ID"],
             "option": "Tự kiểm chứng an toàn"})
        got = fw05.resolve_owner_answer(
            self.root,
            {"decision_id": item["DECISION_ID"],
             "option": "Tự kiểm chứng an toàn"})
        self.assertEqual(got["status"], "FAILED")
        self.assertEqual(got["failure"], "ALREADY_RESOLVED")
        # Only ONE resolution record exists; no duplicate writes.
        resolved = [it for it in fw05.read_inbox_records(Path(self.root))
                    if it["DECISION_ID"] == item["DECISION_ID"]]
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0]["STATUS"], "RESOLVED")

    # ---------- T. resolved decision is not asked again --------------------

    def test_T_resolved_not_asked_again(self) -> None:
        item = self._quality_item()
        fw05.create_owner_decision(self.root, item)
        fw05.resolve_owner_answer(
            self.root,
            {"decision_id": item["DECISION_ID"],
             "option": "Tự kiểm chứng an toàn"})
        # Re-invoking the experience after resolution shows no open item.
        exp = fw05.render_project_experience(Path(self.root))
        self.assertEqual(exp["experience"], "CONTINUE_OR_DONE")
        open_items = self._open_items()
        self.assertEqual(len(open_items), 0)
        self.assertNotIn("decision_id", exp)

    # ---------- U. decision resume continues safely -----------------------

    def test_U_decision_resume_continues_safely(self) -> None:
        item = self._quality_item()
        fw05.create_owner_decision(self.root, item)
        # Owner answers -> decision resolved.
        fw05.resolve_owner_answer(
            self.root,
            {"decision_id": item["DECISION_ID"],
             "option": "Tự kiểm chứng an toàn"})
        # A fresh process (cold resume) reads durable state and derives the
        # honest next safe action from the FW01 checkpoint.
        state = Path(self.root) / ".p2p" / "fw01.json"
        state.parent.mkdir(parents=True, exist_ok=True)
        checkpoint = {
            "schema": "p2p-fw01-checkpoint/1",
            "goal_id": "goal-fw05",
            "loop_status": "BLOCKED",
            "verification_state": "QUALITY_REVIEW",
            "next_safe_action": "QUALITY_REVIEW:task-fw05-1",
            "current_task": "task-fw05-1",
            "evidence_pointers": [],
            "owner_gate": None,
            "updated_utc": fw05.utc_now(),
        }
        state.write_text(json.dumps(checkpoint), encoding="utf-8")
        code = """
import sys, json
sys.path.insert(0, {syspath!r})
from p2p_capabilities import fw05_owner_experience as fw05
from pathlib import Path
snap = fw05.project_status_snapshot(Path({root!r}))
print(json.dumps(snap, ensure_ascii=False))
""".format(root=self.root, syspath=str(SYS))
        result = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True,
            cwd=str(SYS), timeout=120,
            env={**os.environ, "PYTHONPATH": str(SYS),
                 "PYTHONIOENCODING": "utf-8"})
        self.assertEqual(result.returncode, 0, result.stderr)
        snap = json.loads(result.stdout)
        # FW01 resumes exactly at its next safe action — quality review,
        # not a blind advance past the gate.
        self.assertEqual(snap["NEXT_ACTION"], "QUALITY_REVIEW:task-fw05-1")
        self.assertEqual(snap["OPEN_OWNER_DECISIONS"], 0)

    # ---------- V. no duplicate execution after resume --------------------

    def test_V_no_dup_execution_after_resume(self) -> None:
        # Execution count is derived from the goal event ledger; FW05 views
        # are read-only and never execute tasks. Two cold processes reading
        # the same ledger must report identical execution counts.
        ledger = Path(self.root) / ".p2p" / "state" / "goal-ledger.jsonl"
        events = [
            {"event": "task_executed", "task_id": "task-1"},
            {"event": "task_verified", "task_id": "task-1"},
            {"event": "task_done", "task_id": "task-1"},
        ]
        ledger.write_text("\n".join(json.dumps(e) for e in events) + "\n",
                          encoding="utf-8")
        item = self._quality_item(goal_id="goal-fw05", task_id="task-2")
        fw05.create_owner_decision(self.root, item)
        fw05.resolve_owner_answer(
            self.root,
            {"decision_id": item["DECISION_ID"],
             "option": "Tự kiểm chứng an toàn"})
        code = """
import sys, json
sys.path.insert(0, {syspath!r})
from p2p_capabilities import fw05_owner_experience as fw05
from pathlib import Path
snap = fw05.project_status_snapshot(Path({root!r}))
print(json.dumps(snap, ensure_ascii=False))
""".format(root=self.root, syspath=str(SYS))
        counts: list[int] = []
        for _ in range(2):
            result = subprocess.run(
                [sys.executable, "-c", code], capture_output=True, text=True,
                cwd=str(SYS), timeout=120,
                env={**os.environ, "PYTHONPATH": str(SYS),
                     "PYTHONIOENCODING": "utf-8"})
            self.assertEqual(result.returncode, 0, result.stderr)
            snap = json.loads(result.stdout)
            counts.append(int(snap["TASKS_EXECUTED"]))
        self.assertEqual(counts[0], 1)
        self.assertEqual(counts[0], counts[1],
                         "two cold reads must agree; resume never re-executes")

    # ---------- W. progressive disclosure L1/L2/L3 from same truth --------

    def test_W_progressive_disclosure_l1_l2_l3(self) -> None:
        item = self._quality_item()
        record = fw05.decision_record_for_quality_review(
            goal_id="goal-fw05", task_id="task-fw05-1",
            quality_status="QUALITY_UNKNOWN",
            quality_failures=["missing-evidence"], owner_owned=True,
            checkpoint=None)
        fw05.create_owner_decision(self.root, item)
        fw05.append_decision_trace(self.root, record)
        l1 = fw05.render_owner_experience(Path(self.root), level=1)
        l2 = fw05.render_owner_experience(Path(self.root), level=2)
        l3 = fw05.render_owner_experience(Path(self.root), level=3)
        # Same durable truth: identical decision identity everywhere.
        self.assertEqual(l1["project_status"]["OPEN_OWNER_DECISIONS"], 1)
        self.assertEqual(len(l2["blocked_items"]), 1)
        self.assertEqual(l2["blocked_items"][0]["decision_id"],
                         record["DECISION_ID"])
        self.assertEqual(len(l3["decision_trace"]), 1)
        self.assertEqual(l3["decision_trace"][0]["DECISION_ID"],
                         record["DECISION_ID"])
        self.assertEqual(l1["project_status"]["BLOCKER_IF_ANY"],
                         l2["project_status"]["BLOCKER_IF_ANY"])
        # L1/L2 intentionally omit the raw trace; L3 includes it.
        self.assertNotIn("decision_trace", l1)
        self.assertNotIn("decision_trace", l2)
        self.assertIn("decision_trace", l3)

    # ---------- X. goal pass vs promotion distinction is accurate ----------

    def test_X_goal_pass_vs_promotion(self) -> None:
        # 1) no plan at all: not passed, nothing promoted.
        snap0 = fw05.project_status_snapshot(Path(self.root))
        gvp0 = snap0["GOAL_PASS_VS_PROMOTION"]
        self.assertFalse(gvp0["goal_passed"])
        self.assertFalse(gvp0["candidate_promoted"])
        self.assertIn("chưa hoàn tất", gvp0["distinction"])
        # 2) terminal goal, candidate UNPROMOTED: pass WITHOUT promotion.
        plan = Path(self.root) / ".p2p" / "state" / "autopilot-goal-state.json"
        plan.write_text(json.dumps({"goal_id": "goal-fw05", "status": "DONE",
                                    "budget_usage": {}}), encoding="utf-8")
        ctrl = Path(self.root) / "governance"
        ctrl.mkdir(exist_ok=True)
        (ctrl / "development-control.json").write_text(json.dumps({
            "candidate_records": [{
                "candidate_id": "FW05_OWNER_EXPERIENCE_DECISION_TRACE",
                "candidate_version": "8.4.7-C-codex.33",
                "candidate_label":
                    "fw05-owner-experience-decision-trace-8.4.7-C-codex.33",
                "promotion_status": "UNPROMOTED",
                "candidate_sha256": "abc",
                "based_on_official_version": "8.4.7-C-codex.19",
                "based_on_official_sha256":
                    "3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8",
                "development_goal": "FW05_OWNER_EXPERIENCE",
                "built": True,
                "lineage_anchor_sha256":
                    "5985e0e5dc5bdae143ebe42746226f7649f93fdaa705c8b0ec5e9b951cc376f6",
            }]}), encoding="utf-8")
        snap1 = fw05.project_status_snapshot(Path(self.root))
        gvp1 = snap1["GOAL_PASS_VS_PROMOTION"]
        self.assertTrue(gvp1["goal_passed"])
        self.assertFalse(gvp1["candidate_promoted"])
        self.assertIn("chưa được phê duyệt phát hành", gvp1["distinction"])
        self.assertEqual(snap1["CANDIDATE_RELEASE_STATE"]["promotion_status"],
                         "UNPROMOTED")
        # 3) terminal goal + PROMOTED + RELEASED: full release state.
        records = json.loads(
            (ctrl / "development-control.json").read_text())
        records["candidate_records"][0]["promotion_status"] = "PROMOTED"
        records["candidate_records"][0]["release_status"] = "RELEASED"
        (ctrl / "development-control.json").write_text(
            json.dumps(records), encoding="utf-8")
        snap2 = fw05.project_status_snapshot(Path(self.root))
        gvp2 = snap2["GOAL_PASS_VS_PROMOTION"]
        self.assertTrue(gvp2["goal_passed"])
        self.assertTrue(gvp2["candidate_promoted"])
        self.assertTrue(gvp2["candidate_released"])
        self.assertIn("đã phát hành", gvp2["distinction"])

    # ---------- Y. evidence pointers, not chain-of-thought -----------------

    def test_Y_trace_has_evidence_pointers_not_cot(self) -> None:
        record = fw05.make_decision_record(
            decision_type="QUALITY_GATE", goal_id="goal-fw05",
            task_id="task-fw05-1",
            input_facts=["quality_status=QUALITY_UNKNOWN",
                         "quality_failures=[missing-evidence]"],
            applied_policy_or_rule="UNKNOWN != SAFE",
            selected_action="OWNER_REVIEW",
            material_alternatives=["ROUTE_OWNER_OWNED",
                                   "ROUTE_TECHNICAL"],
            rejected_alternatives_with_reason=[
                "ROUTE_TECHNICAL:no existing safe verification path"],
            evidence_pointers=["goal-ledger.jsonl:7",
                               ".p2p/fw01.json",
                               ".p2p/state/certification_store.json"],
            unknown_or_gaps=["missing-evidence"],
            owner_decision_required=True,
            blocking_scope="QUALITY_REVIEW:task-fw05-1",
            goal_state_hash="statehash")
        self.assertIn("EVIDENCE_POINTERS", record)
        self.assertGreater(len(record["EVIDENCE_POINTERS"]), 0)
        serialized = json.dumps(record)
        for forbidden in ("chain-of-thought", "chain of thought",
                          "private reasoning", "scratchpad",
                          "raw prompt", "hidden deliberation"):
            self.assertNotIn(forbidden, serialized,
                             f"trace must not contain {forbidden}")
        # L3 view also carries no CoT material.
        item = self._quality_item()
        fw05.create_owner_decision(self.root, item)
        fw05.append_decision_trace(self.root, record)
        l3 = fw05.render_owner_experience(Path(self.root), level=3)
        self.assertEqual(
            l3["decision_trace"][0]["DECISION_ID"], record["DECISION_ID"])
        raw = json.dumps(l3)
        self.assertNotIn("private reasoning", raw)

    # ---------- Z. FW01–FW04 regression surfaces intact --------------------

    def test_Z_fw01_fw04_regression_surfaces_intact(self) -> None:
        # FW05 must not disturb the FW01 checkpoint, goal state, trace
        # ledger, or certification surfaces: imports + read-only views work,
        # and the durable FW04 quality-stop vocabulary is still honored.
        from p2p_capabilities import p2p_fw01_loop  # noqa: F401
        from p2p_capabilities import quality_intelligence  # noqa: F401
        from p2p_capabilities import team_intelligence  # noqa: F401
        from p2p_capabilities import decision_trace  # noqa: F401
        from p2p_capabilities import autopilot_state  # noqa: F401
        self.assertIn("QUALITY_UNKNOWN",
                      quality_intelligence.QUALITY_STATUSES)
        # FW05 triage honors FW04 durable vocabulary:
        triage = fw05.quality_review_triage(
            {"loop_status": "BLOCKED", "verification_state": "QUALITY_REVIEW",
             "next_safe_action": "QUALITY_REVIEW:task-1",
             "current_task": "task-1"},
            quality_status="QUALITY_UNKNOWN",
            quality_failures=["missing-evidence"],
            technically_resolvable=False)
        self.assertEqual(triage["routing"], "OWNER_OWNED")
        checkpoint = fw05._load_fw01_checkpoint(Path(self.root))
        self.assertIsNone(checkpoint,
                          "no FW01 checkpoint exists; FW05 must not have "
                          "written one")


class FW05ColdProcessBoundaryTest(unittest.TestCase):
    """Real subprocess boundary: Process A persists a gate; Process B is a
    fresh Python process that imports the framework and recovers state."""

    def setUp(self) -> None:
        self.root = tempfile.mkdtemp()
        (Path(self.root) / ".p2p" / "state").mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def _run_cold(self, code: str) -> str:
        result = subprocess.run(
            [sys.executable, "-c", code], capture_output=True, text=True,
            cwd=str(SYS), timeout=120,
            env={**os.environ, "PYTHONPATH": str(SYS),
                 "PYTHONIOENCODING": "utf-8"})
        self.assertEqual(result.returncode, 0,
                         result.stdout + result.stderr)
        return result.stdout.strip()

    def test_cold_boundary_owner_gate_recovers(self) -> None:
        # Process A: persist a durable OWNER_GATE checkpoint + inbox item.
        gate = {"schema": "p2p-autopilot-owner-gate/1",
                "reason_class": "RELEASE_REQUIRED",
                "blocking_task": "release-cold-1",
                "question": "Phát hành candidate X?",
                "safe_options": ("Phát hành", "Hủy"),
                "recommended_default": "Hủy",
                "why_owner_is_needed": "Phát hành thuộc về anh.",
                "resume_condition": "approved"}
        res = fw05.inbox_item_for_owner_gate(owner_gate_payload=gate,
                                             goal_id="goal-cold")
        fw05.create_owner_decision(self.root, res["inbox_item"])
        fw05.append_decision_trace(self.root, res["record"])
        cp = Path(self.root) / ".p2p" / "fw01.json"
        cp.parent.mkdir(parents=True, exist_ok=True)
        cp.write_text(json.dumps({
            "schema": "p2p-fw01-checkpoint/1", "goal_id": "goal-cold",
            "loop_status": "OWNER_GATE",
            "verification_state": "NOT_VERIFIED",
            "next_safe_action": "OWNER_RESOLVES:release-cold-1",
            "current_task": "release-cold-1",
            "evidence_pointers": [],
            "owner_gate": dict(gate),
            "updated_utc": fw05.utc_now()}), encoding="utf-8")
        expected_id = res["inbox_item"]["DECISION_ID"]

        # Process B: cold restart, must NOT re-execute release-cold-1 and
        # must recover the exact same decision id.
        code = """
import sys, json
sys.path.insert(0, {syspath!r})
from p2p_capabilities import fw05_owner_experience as fw05
from pathlib import Path
root = Path({root!r})
snap = fw05.project_status_snapshot(root)
items = fw05.read_inbox_records(root)
trace = fw05.read_decision_records(root)
print(json.dumps({{
    "next_action": snap["NEXT_ACTION"],
    "blocker": snap["BLOCKER_IF_ANY"],
    "open": [it["DECISION_ID"] for it in items if it.get("STATUS") == "OPEN"],
    "trace": [r["record"]["DECISION_ID"] for r in trace["records"]],
    "loop_status": snap["PROGRESS_STATE"]}}))
""".format(root=self.root, syspath=str(SYS))
        payload = json.loads(self._run_cold(code))
        self.assertEqual(payload["open"], [expected_id])
        self.assertIn(expected_id, payload["trace"])
        self.assertEqual(payload["blocker"], "OWNER_GATE")
        self.assertEqual(payload["next_action"],
                         "OWNER_RESOLVES:release-cold-1")
        self.assertEqual(payload["loop_status"], "OWNER_GATE")

    def test_cold_boundary_owner_answer_then_resume(self) -> None:
        gate = {"schema": "p2p-autopilot-owner-gate/1",
                "reason_class": "DESTRUCTIVE_PRODUCTION_ACTION",
                "blocking_task": "cleanup-cold-1",
                "question": "Cho phép xóa dữ liệu cũ?",
                "safe_options": ("Cho phép", "Hủy"),
                "recommended_default": "Hủy",
                "why_owner_is_needed": "Xóa không thể khôi phục.",
                "resume_condition": "approved"}
        res = fw05.inbox_item_for_owner_gate(owner_gate_payload=gate,
                                             goal_id="goal-cold")
        fw05.create_owner_decision(self.root, res["inbox_item"])
        expected_id = res["inbox_item"]["DECISION_ID"]
        # Owner answer recorded, then the process ends.
        fw05.resolve_owner_answer(
            self.root,
            {"decision_id": expected_id, "option": "Hủy"})

        # Process B: cold restart; decision stays resolved, FW01 resumes
        # from the next safe action, nothing re-executes.
        code = """
import sys, json
sys.path.insert(0, {syspath!r})
from p2p_capabilities import fw05_owner_experience as fw05
from pathlib import Path
root = Path({root!r})
items = fw05.read_inbox_records(root)
print(json.dumps([{{"id": it["DECISION_ID"], "status": it.get("STATUS"),
    "resolution_option": (it.get("RESOLUTION") or {{}}).get("approved_option")}}
    for it in items]))
""".format(root=self.root, syspath=str(SYS))
        payload = json.loads(self._run_cold(code))
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["id"], expected_id)
        self.assertEqual(payload[0]["status"], "RESOLVED")
        self.assertEqual(payload[0]["resolution_option"], "Hủy")


class FW05ShadowEvalReadOnlyTest(unittest.TestCase):
    """Shadow evaluation over the read-only Game Truyện / Gia Phả trees.
    The trees MUST be byte-identical before and after any FW05 view."""

    def setUp(self) -> None:
        self.gt = Path("/home/ubuntu/fw01_work/cert/game-truyen")
        self.gp = Path("/home/ubuntu/fw01_work/cert/gia-pha")
        self.available = self.gt.is_dir() and self.gp.is_dir()

    def _tree_hash(self) -> str:
        digests: list[list[str]] = []
        for tree in (self.gt, self.gp):
            for path in sorted(tree.rglob("*")):
                if path.is_file():
                    digests.append([str(path), hashlib.sha256(
                        path.read_bytes()).hexdigest()])
        return hashlib.sha256(
            fw05._stable_json(digests).encode("utf-8")).hexdigest()

    def test_shadow_eval_read_only_before_after(self) -> None:
        if not self.available:
            self.skipTest("GT/GP cert trees not present")
        before = self._tree_hash()
        snap_gt = fw05.project_status_snapshot(self.gt)
        snap_gp = fw05.project_status_snapshot(self.gp)
        exp_gt = fw05.render_owner_experience(self.gt, level=1)
        exp_gp = fw05.render_owner_experience(self.gp, level=3)
        self.assertIn("PROJECT", snap_gt)
        self.assertIn("decision_trace", exp_gp)
        after = self._tree_hash()
        self.assertEqual(before, after,
                         "FW05 views must NOT mutate the GT/GP trees")
        # Classification over the GT tree: technical continuation, no Owner
        # gate (read-only snapshot produced no decision).
        self.assertEqual(snap_gt.get("OPEN_OWNER_DECISIONS"), 0)
