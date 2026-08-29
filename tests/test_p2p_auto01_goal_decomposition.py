"""Focused behavior tests for P2P-AUTO01 automatic goal decomposition."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TMP_ROOT = REPO_ROOT / ".tmp"
if str(REPO_ROOT / ".p2p" / "system") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / ".p2p" / "system"))
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from p2p_capabilities.beginner_gateway import (  # noqa: E402
    AUTO_DECOMPOSITION_SCHEMA,
    beginner_projection,
    derive_charter,
    task_specs_for_charter,
)
from p2p_capabilities.evidence import EvidenceClaim  # noqa: E402
from p2p_capabilities.task_state import TaskStateStore  # noqa: E402
from p2p_workflow import beginner_entrypoint, beginner_public_result  # noqa: E402


class P2PAUTO01GoalDecompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        TMP_ROOT.mkdir(parents=True, exist_ok=True)

    def _root(self, prefix: str):
        return tempfile.TemporaryDirectory(dir=TMP_ROOT, prefix=prefix)

    def _run(self, root: Path, request: str) -> dict[str, object]:
        return beginner_entrypoint(root, request, package_hint=str(REPO_ROOT))

    def test_vietnamese_genealogy_request_derives_small_goal_and_startable_action(self) -> None:
        request = "Tôi muốn làm một app gia phả dễ dùng cho người lớn tuổi."
        direct = derive_charter(request)
        auto = direct["auto_decomposition"]
        self.assertEqual(direct["project_state"], "NEW_PROJECT")
        self.assertEqual(direct["project_type"], "Ứng dụng gia phả")
        self.assertEqual(len(auto["workstreams"]), 3)
        self.assertEqual(auto["schema_version"], AUTO_DECOMPOSITION_SCHEMA)
        self.assertEqual(auto["now_startable"], ["scope"])
        self.assertTrue(auto["dependency_model"]["real_dependencies_only"])
        self.assertEqual(auto["dependency_model"]["topological_order"], ["scope", "core", "verify"])
        self.assertIsNone(direct["question"])

        with self._root("p2p-auto01-new-") as raw:
            result = self._run(Path(raw), request)
            public = beginner_public_result(result)
            plan = TaskStateStore(Path(raw)).load()
            self.assertEqual(result["persistence"]["status"], "CREATED")
            self.assertEqual(result["persistence"]["workstream_count"], 3)
            self.assertEqual(len(plan.tasks), 3)
            self.assertEqual(plan.topological_order(), ("beginner-gateway-next", "beginner-gateway-next-2", "beginner-gateway-next-3"))
            self.assertEqual(public["project_state"], "NEW_PROJECT")
            self.assertIn("người lớn tuổi", public["intended_outcome"])
            self.assertTrue(any("Chữ rõ" in item for item in public["important_constraints"]))
            self.assertTrue(public["progress_summary"]["next"].startswith("Bắt đầu phần nhỏ nhất"))
            self.assertTrue(public["safe_next_action"])

    def test_existing_logistics_continuation_reuses_goal_and_plan(self) -> None:
        with self._root("p2p-auto01-continuation-") as raw:
            root = Path(raw)
            first = self._run(root, "Tôi muốn làm app logistics để theo dõi giao hàng.")
            first_plan_hash = first["persistence"]["plan_hash"]
            first_goal_id = first["persistence"]["goal_id"]
            continuation = self._run(root, "Hãy tiếp tục hoàn thiện app logistics của tôi.")
            repeated = self._run(root, "Hãy tiếp tục hoàn thiện app logistics của tôi.")
            public = beginner_public_result(continuation)
            contract = json.loads((root / ".p2p" / "state" / "goal-contract.json").read_text(encoding="utf-8"))
            events = [
                json.loads(line)
                for line in (root / ".p2p" / "state" / "execution-ledger.jsonl").read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            self.assertEqual(continuation["persistence"]["status"], "REUSED")
            self.assertEqual(repeated["persistence"]["status"], "REUSED")
            self.assertEqual(continuation["persistence"]["goal_id"], first_goal_id)
            self.assertEqual(continuation["persistence"]["plan_hash"], first_plan_hash)
            self.assertEqual(public["project_state"], "EXISTING_PROJECT")
            self.assertEqual(public["project_type"], "Phần mềm vận hành hàng hóa")
            self.assertIsNone(public["question"])
            self.assertEqual(len(TaskStateStore(root).load().tasks), 3)
            self.assertEqual(len(contract["beginner_request_history"]), 1)
            self.assertEqual(contract["beginner_gateway"]["request"], first["charter"]["request"])
            self.assertEqual(contract["beginner_continuation_projection"]["request"], continuation["charter"]["request"])
            self.assertEqual(sum(item.get("event") == "beginner_gateway_continuation_bound" for item in events), 1)

    def test_simple_request_stays_small_and_complex_request_adds_only_real_edges(self) -> None:
        simple = derive_charter("I want to build a small app.")
        self.assertLessEqual(simple["auto_decomposition"]["workstream_count"], 3)
        self.assertEqual(simple["auto_decomposition"]["dependency_model"]["edges"], [
            {"from": "scope", "to": "core"},
            {"from": "core", "to": "verify"},
        ])

        complex_request = "Tôi muốn làm app logistics, nhập dữ liệu tồn kho và chia sẻ an toàn."
        complex_charter = derive_charter(complex_request)
        complex_auto = complex_charter["auto_decomposition"]
        self.assertEqual(complex_auto["workstream_count"], 5)
        self.assertEqual(complex_auto["dependency_model"]["topological_order"], ["scope", "data", "safety", "core", "verify"])
        self.assertEqual(
            complex_auto["dependency_model"]["edges"],
            [
                {"from": "scope", "to": "data"},
                {"from": "scope", "to": "safety"},
                {"from": "data", "to": "core"},
                {"from": "safety", "to": "core"},
                {"from": "core", "to": "verify"},
            ],
        )
        self.assertTrue(all(edge["from"] in complex_auto["dependency_model"]["topological_order"] for edge in complex_auto["dependency_model"]["edges"]))

    def test_only_material_ambiguity_asks_and_technical_choice_does_not(self) -> None:
        technical = derive_charter("I want to build an app using Python and React.")
        self.assertIsNone(technical["question"])
        self.assertFalse(technical["auto_decomposition"]["owner_decisions"])

        material = derive_charter("I want to build and improve this app.")
        self.assertEqual(material["project_state"], "NEEDS_DECISION")
        self.assertTrue(material["question"])
        self.assertEqual(len(material["auto_decomposition"]["owner_decisions"]), 1)
        self.assertFalse(material["auto_decomposition"]["now_startable"])

        protected = derive_charter("Please deploy this app to production.")
        self.assertTrue(protected["question"])
        self.assertEqual(protected["internal"]["safety"]["production_protection"], "FAIL_CLOSED")

    def test_continuity_projects_completed_active_and_blocked_state_without_recreation(self) -> None:
        request = "I want to build a genealogy app for older adults."
        with self._root("p2p-auto01-continuity-") as raw:
            root = Path(raw)
            self._run(root, request)
            store = TaskStateStore(root)
            plan = store.load()
            first = plan.tasks["beginner-gateway-next"]
            store.transition(first.task_id, "ACTIVE", now="2026-08-29T04:00:00+00:00")
            active_result = self._run(root, request)
            self.assertEqual(active_result["beginner_projection"]["progress_summary"]["status"], "Đang làm")
            self.assertEqual(len(active_result["beginner_projection"]["progress_summary"]["active"]), 1)

            current = store.load()
            active_task = current.tasks[first.task_id]
            claims = [
                EvidenceClaim(
                    claim="The AUTO01 workstream was independently checked.",
                    required_evidence=(reference,),
                    actual_evidence=(
                        {
                            "source": "tests/test_p2p_auto01_goal_decomposition.py",
                            "evidence_ref": reference,
                            "origin": "RUNTIME_EVIDENCE",
                            "observed_at": "2026-08-29T04:01:00+00:00",
                            "freshness": "CURRENT",
                            "scope": ["p2p-auto01"],
                            "source_binding": "focused-test",
                            "fingerprint": "a" * 64,
                        },
                    ),
                    status="VERIFIED",
                )
                for reference in active_task.required_evidence
            ]
            store.complete(first.task_id, claims, {"observed": "auto01"}, now="2026-08-29T04:02:00+00:00")
            refreshed = store.load().refresh_ready(now="2026-08-29T04:03:00+00:00")
            store.save(refreshed, event_name="auto01_dependency_refresh", at="2026-08-29T04:03:00+00:00")
            store.transition("beginner-gateway-next-2", "ACTIVE", now="2026-08-29T04:04:00+00:00")
            completed_active = self._run(root, request)
            progress = completed_active["beginner_projection"]["progress_summary"]
            self.assertEqual(len(progress["completed"]), 1)
            self.assertEqual(len(progress["active"]), 1)
            self.assertEqual(len(TaskStateStore(root).load().tasks), 3)

            store.transition(
                "beginner-gateway-next-2",
                "BLOCKED",
                blocker={"reason": "Waiting for a bounded project input."},
                now="2026-08-29T04:05:00+00:00",
            )
            blocked_result = self._run(root, request)
            blocked_progress = blocked_result["beginner_projection"]["progress_summary"]
            self.assertEqual(blocked_progress["status"], "Đang bị chặn")
            self.assertTrue(blocked_progress["blocked"])
            self.assertIn("Giải quyết phần đang bị chặn", blocked_result["beginner_projection"]["safe_next_action"])

    def test_state_binding_and_beginner_projection_do_not_create_a_second_store(self) -> None:
        with self._root("p2p-auto01-state-") as raw:
            root = Path(raw)
            result = self._run(root, "Tôi muốn làm một app gia phả dễ dùng cho người lớn tuổi.")
            contract = json.loads((root / ".p2p" / "state" / "goal-contract.json").read_text(encoding="utf-8"))
            state = json.loads((root / ".p2p" / "state" / "task-state.json").read_text(encoding="utf-8"))
            public = beginner_public_result(result)
            advanced = beginner_public_result(result, advanced=True)
            self.assertEqual(contract["auto_decomposition"]["schema_version"], AUTO_DECOMPOSITION_SCHEMA)
            self.assertEqual(contract["beginner_gateway"]["auto_decomposition"]["schema_version"], AUTO_DECOMPOSITION_SCHEMA)
            self.assertEqual(state["plan_hash"], result["persistence"]["plan_hash"])
            self.assertTrue((root / ".p2p" / "state" / "execution-ledger.jsonl").is_file())
            self.assertNotIn("auto_decomposition", public)
            self.assertNotIn("internal", public)
            self.assertNotIn("plan_hash", json.dumps(public, ensure_ascii=False))
            self.assertIn("auto_decomposition", advanced["advanced"])
            self.assertFalse(result["safety"]["execution_started"])
            self.assertFalse(result["recovery"]["automatic_start"])
            state_files = {path.name for path in (root / ".p2p" / "state").iterdir() if path.is_file()}
            self.assertNotIn("auto-plan.json", state_files)

    def test_material_conflict_preserves_existing_state_and_safe_next_action(self) -> None:
        with self._root("p2p-auto01-conflict-") as raw:
            root = Path(raw)
            first = self._run(root, "I want to build a genealogy app for older adults.")
            before = json.loads((root / ".p2p" / "state" / "goal-contract.json").read_text(encoding="utf-8"))
            result = self._run(root, "Please improve the current app navigation.")
            public = beginner_public_result(result)
            after = json.loads((root / ".p2p" / "state" / "goal-contract.json").read_text(encoding="utf-8"))
            self.assertEqual(result["persistence"]["status"], "BLOCKED")
            self.assertEqual(public["status"], "CẦN BẠN QUYẾT ĐỊNH")
            self.assertIn("một việc chưa xong", public["question"])
            self.assertEqual(public["safe_next_action"], "Chờ bạn trả lời câu hỏi trên; chưa bắt đầu thay đổi nào.")
            self.assertEqual(after["goal_id"], before["goal_id"])
            self.assertEqual(after["request"], before["request"])
            self.assertEqual(result["persistence"].get("existing_goal_id"), first["persistence"]["goal_id"])


if __name__ == "__main__":
    unittest.main()
