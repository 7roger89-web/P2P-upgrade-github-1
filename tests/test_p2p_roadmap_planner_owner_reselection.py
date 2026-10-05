from __future__ import annotations

import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLANNER_ROOT = REPO_ROOT / "scripts"
if str(PLANNER_ROOT) not in sys.path:
    sys.path.insert(0, str(PLANNER_ROOT))

import p2p_roadmap_planner as planner  # noqa: E402


class PlannerOwnerReselectionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.input_model = planner.build_input_model(str(REPO_ROOT), [])

    def _set_status(self, roadmap_id: str, status: str) -> None:
        self.input_model["STATUS"][roadmap_id] = status
        for item in self.input_model["ROADMAP_ITEMS"]:
            if item["roadmap_id"] == roadmap_id:
                item["status"] = status
                break
        else:  # pragma: no cover - canonical fixture must contain the item
            self.fail(f"missing roadmap item {roadmap_id}")

    def test_deferred_owner_reselection_gate_blocks_orca(self) -> None:
        self._set_status("RM-C08", "DEFERRED")
        graph = planner.classify_dependencies(self.input_model)
        self.assertEqual(
            self.input_model["OWNER_RESELECTION_DEPENDENCIES"]["RM-PRIORITY-ORCA-EXT"],
            ["RM-C08"],
        )
        self.assertEqual(graph["RM-PRIORITY-ORCA-EXT"]["class"], "OWNER_DEFERRED")
        self.assertIn("re-selection unresolved", graph["RM-PRIORITY-ORCA-EXT"]["reason"])
        self.assertNotEqual(graph["RM-PRIORITY-ORCA-EXT"]["class"], "READY_NOW")

    def test_active_unpromoted_reselection_clears_owner_gate_without_done(self) -> None:
        self._set_status("RM-C08", "ACTIVE_UNPROMOTED")
        graph = planner.classify_dependencies(self.input_model)
        self.assertEqual(self.input_model["STATUS"]["RM-C08"], "ACTIVE_UNPROMOTED")
        self.assertNotIn("ACTIVE_UNPROMOTED", planner.TERMINAL_STATUSES)
        self.assertEqual(graph["RM-PRIORITY-ORCA-EXT"]["class"], "READY_NOW")

    def test_active_unpromoted_is_known_nonterminal_continuation_state(self) -> None:
        self._set_status("RM-C08", "ACTIVE_UNPROMOTED")
        self.assertIn("ACTIVE_UNPROMOTED", planner.ALLOWED_ROADMAP_ITEM_STATUS)
        graph = planner.classify_dependencies(self.input_model)
        self.assertEqual(graph["RM-C08"]["class"], "READY_NOW")
        self.assertNotEqual(graph["RM-C08"]["class"], "UNKNOWN")
        self.assertIn("active unpromoted", graph["RM-C08"]["reason"])

    def test_ordinary_dependency_still_requires_terminal_completion(self) -> None:
        self._set_status("RM-C08", "ACTIVE_UNPROMOTED")
        graph = planner.classify_dependencies(self.input_model)
        large_goal = graph["RM-PRIORITY-LARGE-GOAL"]
        self.assertEqual(large_goal["class"], "BLOCKED_BY_DEPENDENCY")
        self.assertIn("RM-C08", large_goal["reason"])
        self.assertIn("not terminal", large_goal["reason"])
        self.assertEqual(graph["RM-PRIORITY-ORCA-EXT"]["class"], "READY_NOW")


if __name__ == "__main__":
    unittest.main()
