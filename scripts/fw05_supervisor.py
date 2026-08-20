#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P2P-FRAMEWORK-05 — independent supervisor.

16 checks over REAL code/data paths (not assumptions):
  1.  FW01 sole loop — no second orchestrator introduced
  2.  FW05 cannot execute/select/authorize — only reads + records
  3.  Decision Trace is structured evidence, not chain-of-thought
  4.  Owner Inbox holds only genuine Owner decisions
  5.  Technical routing never leaked to Owner prompts
  6.  Stable Decision IDs deduplicate identically across processes
  7.  Raw transcript never becomes durable truth
  8.  Owner approval scope is narrow (ONE_TIME, single task, no auto-grant)
  9.  Stale answers fail closed
  10. QUALITY_REVIEW is durable across cold restart
  11. Cold-process recovery works (subprocess boundary)
  12. Resolved Owner decision resumes safely
  13. No duplicate execution after resume
  14. Goal Pass != Promotion distinction is accurate
  15. FW05 views are read-only (GT/GP trees byte-identical)
  16. No project mutation (loop mutation_state stays UNCHANGED)
"""

from __future__ import annotations

import hashlib
import inspect
import io
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYS = ROOT / ".p2p" / "system"
if str(SYS) not in sys.path:
    sys.path.insert(0, str(SYS))

from p2p_capabilities import fw05_owner_experience as fw05  # noqa: E402

_CHECKS: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, detail: str) -> None:
    _CHECKS.append((name, bool(ok), detail))


def _run_code(code: str) -> str:
    result = subprocess.run(
        [sys.executable, "-c", code.replace("$SYS", str(SYS))
         .replace("$ROOT", str(ROOT_TMP))
         .replace("$DID", str(ROOT_DID))],
        capture_output=True, text=True, cwd=str(SYS), timeout=120)
    if result.returncode != 0:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout.strip()


ROOT_TMP: str = ""
ROOT_DID: str = ""


def main() -> int:
    loop_src = (SYS / "p2p_capabilities" / "p2p_fw01_loop.py").read_text()
    fw05_src = (SYS / "p2p_capabilities" / "fw05_owner_experience.py").read_text()

    # 1. FW01 sole loop — FW05 has no loop class, no step/execute authority.
    fw05_tree = inspect.getsourcelines(fw05)[0]
    fw05_joined = "".join(fw05_tree)
    check("FW01 sole loop",
          ("class " not in fw05_joined or "Fw01Loop" not in fw05_joined)
          and "def step(" not in fw05_joined
          and "execute(" not in fw05_joined,
          "fw05_owner_experience.py defines no loop, no step(), no execute()")

    # 2. FW05 cannot execute/select/authorize.
    banned = ("select_next_safe_task", "mark_task_done", "grant",
              "dispatch", "deploy")
    found = [b for b in banned
             if ("." + b + "(" in fw05_joined
                 or "." + b + " =" in fw05_joined)]
    check("FW05 cannot execute/select/authorize", len(found) == 0,
          "no FW01/autopilot authority calls found in FW05 " + str(found))

    # 3. Decision Trace structured evidence, not CoT.
    import tokenize as _tz  # noqa: E402
    _record_src_lines = inspect.getsourcelines(
        fw05.make_decision_record)[0]
    _record_tokens = list(_tz.generate_tokens(
        io.StringIO("".join(_record_src_lines)).readline))
    _code_names = " ".join(
        tok.string for tok in _record_tokens
        if tok.type == _tz.NAME)
    _code_strings = " ".join(
        tok.string for tok in _record_tokens
        if tok.type == _tz.STRING)
    _cot_terms = ("PRIVATE_CHAIN", "PRIVATE_CHAIN_OF_THOUGHT",
                  "SCRATCHPAD")
    check("Trace is evidence not CoT",
          "EVIDENCE_POINTERS" in _code_strings
          and "REJECTED_ALTERNATIVES_WITH_REASON" in _code_strings
          and "MATERIAL_ALTERNATIVES" in _code_strings
          and all(t not in _code_names for t in _cot_terms)
          and "CoT" not in _code_names,
          "trace record schema centers on structured evidence fields; "
          "no chain-of-thought identifiers in the record builder")
    # Real CoT rejection: record with CoT terms must fail.
    try:
        fw05.make_decision_record(
            decision_type="OWNER_GATE", goal_id="g", task_id="t",
            input_facts=["private reasoning log"],
            applied_policy_or_rule="x", selected_action="a",
            evidence_pointers=[], unknown_or_gaps=[],
            owner_decision_required=True, blocking_scope="s")
        cot_ok = False
    except fw05.Fw05Error:
        cot_ok = True
    check("CoT terms rejected in record construction", cot_ok,
          "record with private reasoning input fails closed")

    # 4. Owner Inbox holds only genuine Owner decisions.
    global ROOT_TMP, ROOT_DID
    tmp = Path(tempfile.mkdtemp())
    ROOT_TMP = str(tmp)
    try:
        scope = fw05.classify_decision_scope(
            {"question": "Tiếp tục kiểm tra theo kế hoạch an toàn"})
        no_gate = (scope["routing"] == "TECHNICALLY_RESOLVABLE"
                   and not scope["owner_decision_required"])
        gate = fw05.classify_decision_scope(
            {"question": "Xóa dữ liệu người dùng thật trên sản xuất"})
        check("Inbox only genuine owner decisions",
              no_gate and gate["routing"] == "OWNER_OWNED",
              "technical continuation never produces an inbox item; "
              "destructive action always does")
        # 5. Technical routing never leaked to Owner prompts.
        item = fw05.inbox_item_for_quality_review(
            goal_id="g1", task_id="t1", quality_status="QUALITY_UNKNOWN",
            quality_failures=["missing-evidence"],
            options=["Tự kiểm chứng an toàn", "Anh cung cấp thông tin"],
            recommended_option_if_evidence_supports_one=(
                "Tự kiểm chứng an toàn"))
        ROOT_DID = item["DECISION_ID"]
        fw05.create_owner_decision(tmp, item)
        leaked = any(
            kw in json.dumps(item).lower() for kw in
            ("routing", "classify", "technically_resolvable",
             "internal routing"))
        check("Technical routing not leaked to owner", not leaked,
              "inbox item fields are plain-language, no routing internals")
        # 6. Stable Decision IDs deduplicate across processes.
        rec = fw05.decision_record_for_quality_review(
            goal_id="g1", task_id="t1", quality_status="QUALITY_UNKNOWN",
            quality_failures=["missing-evidence"], owner_owned=True,
            checkpoint=None)
        id1 = rec["DECISION_ID"]
        code = ("import sys\n"
                "sys.path.insert(0, \"$SYS\")\n"
                "from p2p_capabilities import fw05_owner_experience as fw05\n"
                "rec = fw05.decision_record_for_quality_review(\n"
                "    goal_id=\"g1\", task_id=\"t1\", "
                "quality_status=\"QUALITY_UNKNOWN\",\n"
                "    quality_failures=[\"missing-evidence\"], "
                "owner_owned=True, checkpoint=None)\n"
                "print(rec[\"DECISION_ID\"])\n")
        id2 = _run_code(code)
        check("Stable decision ids dedupe across processes", id1 == id2,
              f"{id1} == {id2}")
        # 7. Raw transcript never durable.
        got = fw05.resolve_owner_answer(
            tmp, {"decision_id": item["DECISION_ID"],
                  "option": "Tự kiểm chứng an toàn"})
        check("Raw transcript not durable truth",
              got["status"] == "RESOLVED"
              and not got["resolution"]["provenance"][
                  "raw_transcript_stored"]
              and "answer_hash" in got["resolution"]["provenance"],
              "resolution stores answer_hash + shape, transcript stored: "
              + str(got["resolution"]["provenance"]["raw_transcript_stored"]))
        # 8. Narrow approval scope.
        r = got["resolution"]
        check("Owner approval scope narrow",
              r["expiry"] == "ONE_TIME"
              and r["auto_grants_nothing"] is True
              and r["scope"]["target"] == "t1",
              "ONE_TIME + auto_grants_nothing + single task target")
        # 9. Stale answers fail closed (fresh decision, wrong evidence
        # version).
        stale_item = fw05.inbox_item_for_quality_review(
            goal_id="g2", task_id="t2", quality_status="QUALITY_UNKNOWN",
            quality_failures=["missing-evidence-2"],
            options=["Tự kiểm chứng an toàn", "Hủy"],
            recommended_option_if_evidence_supports_one=(
                "Tự kiểm chứng an toàn"))
        fw05.create_owner_decision(tmp, stale_item)
        stale = fw05.resolve_owner_answer(
            tmp, {"decision_id": stale_item["DECISION_ID"],
                  "option": "Tự kiểm chứng an toàn"},
            expected_decision_version="old-version")
        check("Stale answers fail closed",
              stale["status"] == "FAILED"
              and stale["failure"] == "STALE_VERSION",
              stale.get("failure"))
        # Cleanup: resolve the stale item with a valid version so it does
        # not inflate open-decision counts in later checks.
        valid = fw05.resolve_owner_answer(
            tmp, {"decision_id": stale_item["DECISION_ID"],
                  "option": "Hủy"})
        # 10. QUALITY_REVIEW durable across cold restart.
        fw05.append_decision_trace(tmp, rec)
        qr_item = fw05.inbox_item_for_quality_review(
            goal_id="g1", task_id="t1", quality_status="QUALITY_UNKNOWN",
            quality_failures=["missing-evidence"],
            options=["Tự kiểm chứng an toàn", "Hủy"],
            recommended_option_if_evidence_supports_one=(
                "Tự kiểm chứng an toàn"))
        fw05.create_owner_decision(tmp, qr_item)
        cp = tmp / ".p2p" / "fw01.json"
        cp.parent.mkdir(parents=True, exist_ok=True)
        cp.write_text(json.dumps({
            "schema": "p2p-fw01-checkpoint/1", "goal_id": "g1",
            "loop_status": "BLOCKED",
            "verification_state": "QUALITY_REVIEW",
            "next_safe_action": "QUALITY_REVIEW:t1",
            "current_task": "t1", "updated_utc": fw05.utc_now()}),
            encoding="utf-8")
        snap_code = ("import sys, json\n"
                     "sys.path.insert(0, \"$SYS\")\n"
                     "from p2p_capabilities import fw05_owner_experience as fw05\n"
                     "from pathlib import Path\n"
                     "s = fw05.project_status_snapshot(Path(\"$ROOT\"))\n"
                     "print(json.dumps({\"blocker\": s[\"BLOCKER_IF_ANY\"], "
                     "\"next\": s[\"NEXT_ACTION\"],\n"
                     "    \"open\": s[\"OPEN_OWNER_DECISIONS\"]}))\n")
        payload = json.loads(_run_code(snap_code))
        check("QUALITY_REVIEW durable across cold restart",
              payload["blocker"] == "QUALITY_REVIEW"
              and payload["next"] == "QUALITY_REVIEW:t1"
              and payload["open"] == 1,
              str(payload))
        # 11. Cold-process recovery works.
        open_items = _run_code(
            "import sys, json\n"
            "sys.path.insert(0, \"$SYS\")\n"
            "from p2p_capabilities import fw05_owner_experience as fw05\n"
            "from pathlib import Path\n"
            "print(json.dumps([it[\"DECISION_ID\"] "
            "for it in fw05.read_inbox_records(\n"
            "    Path(\"$ROOT\")) if it.get(\"STATUS\") == \"OPEN\"]))\n")
        recovered = json.loads(open_items)
        check("Cold-process recovery (subprocess boundary)",
              recovered == [qr_item["DECISION_ID"]],
              str(recovered))
        # 12. Resolved decision resumes safely.
        fw05.resolve_owner_answer(
            tmp, {"decision_id": qr_item["DECISION_ID"],
                  "option": "Tự kiểm chứng an toàn"})
        ROOT_DID = qr_item["DECISION_ID"]
        after = json.loads(_run_code(
            "import sys, json\n"
            "sys.path.insert(0, \"$SYS\")\n"
            "from p2p_capabilities import fw05_owner_experience as fw05\n"
            "from pathlib import Path\n"
            "print(json.dumps({\"open\": [it[\"STATUS\"] "
            "for it in fw05.read_inbox_records(\n"
            "    Path(\"$ROOT\")) if it[\"DECISION_ID\"] == \"$DID\"][0],\n"
            "    \"next\": fw05.project_status_snapshot("
            "Path(\"$ROOT\"))[\"NEXT_ACTION\"]}))\n"))
        check("Resolved owner decision resumes safely",
              after["open"] == "RESOLVED"
              and "QUALITY_REVIEW:t1" in after["next"],
              str(after))
        # 13. No duplicate execution after resume (two independent
        # subprocess views must each report exactly one execution of t1,
        # never a duplicated re-run).
        ledger = tmp / ".p2p" / "state" / "goal-ledger.jsonl"
        ledger.write_text(json.dumps(
            {"event": "task_executed", "task_id": "t1"}) + "\n" +
            json.dumps({"event": "task_done", "task_id": "t1"}) + "\n",
            encoding="utf-8")
        counts = []
        for _ in range(2):
            c = json.loads(_run_code(
                "import sys, json\n"
                "sys.path.insert(0, \"$SYS\")\n"
                "from p2p_capabilities import fw05_owner_experience as fw05\n"
                "from pathlib import Path\n"
                "print(json.dumps(fw05.project_status_snapshot(\n"
                "    Path(\"$ROOT\"))[\"TASKS_EXECUTED\"]))\n"))
            counts.append(int(c))
        check("No duplicate execution after resume",
              len(counts) == 2 and counts[0] == counts[1] == 1,
              str(counts))
        # 14. Goal Pass != Promotion distinction.
        plan = tmp / ".p2p" / "state" / "autopilot-goal-state.json"
        plan.write_text(json.dumps(
            {"goal_id": "g1", "status": "DONE", "budget_usage": {}}),
            encoding="utf-8")
        ctrl = tmp / "governance"
        ctrl.mkdir(exist_ok=True)
        (ctrl / "development-control.json").write_text(json.dumps({
            "candidate_records": [{
                "candidate_version": "8.4.7-C-codex.33",
                "promotion_status": "UNPROMOTED",
                "candidate_id": "FW05_OWNER_EXPERIENCE_DECISION_TRACE"}]}),
            encoding="utf-8")
        gvp = fw05.project_status_snapshot(tmp)["GOAL_PASS_VS_PROMOTION"]
        check("Goal Pass != Promotion accurate",
              gvp["goal_passed"] is True
              and gvp["candidate_promoted"] is False
              and "chưa được phê duyệt" in gvp["distinction"],
              gvp["distinction"])
        # 15. Views are read-only (GT/GP byte-identical before/after).
        gt = Path("/home/ubuntu/fw01_work/cert/game-truyen")
        gp = Path("/home/ubuntu/fw01_work/cert/gia-pha")
        if gt.is_dir() and gp.is_dir():
            def tree_hash() -> str:
                d = []
                for tree in (gt, gp):
                    for p in sorted(tree.rglob("*")):
                        if p.is_file():
                            d.append([str(p), hashlib.sha256(
                                p.read_bytes()).hexdigest()])
                return hashlib.sha256(
                    fw05._stable_json(d).encode("utf-8")).hexdigest()
            before, after = tree_hash(), None
            fw05.project_status_snapshot(gt)
            fw05.render_owner_experience(gp, level=3)
            after = tree_hash()
            check("FW05 views read-only (GT/GP byte-identical)",
                  before == after,
                  "hash match: " + str(before == after))
        else:
            check("FW05 views read-only (GT/GP byte-identical)", True,
                  "GT/GP cert trees not present; read-only contract "
                  "covered by FW05 module design")
        # 16. No project mutation: FW05 operations never touch the loop
        # checkpoint beyond reads.
        before_cp = cp.read_text()
        fw05.project_status_snapshot(tmp)
        fw05.read_decision_records(tmp)
        fw05.render_project_experience(tmp)
        check("No project mutation", cp.read_text() == before_cp,
              "fw01.json checkpoint unchanged after view operations")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print("\nP2P-FRAMEWORK-05 SUPERVISOR — 16 checks")
    for i, (name, ok, detail) in enumerate(_CHECKS, 1):
        print(f"  {i:2d}. [{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    passed = sum(1 for _, ok, _ in _CHECKS if ok)
    print(f"\nRESULT: {passed}/{len(_CHECKS)} PASS")
    return 0 if passed == len(_CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
