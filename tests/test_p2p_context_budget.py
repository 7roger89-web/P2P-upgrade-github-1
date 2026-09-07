import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities.context_budget import (  # noqa: E402
    CAPABILITY_ID,
    ContextBudgetError,
    audit_context_budget,
    main,
)


def _view(*, total_bytes: int = 9000, include_optional: bool = True) -> dict[str, object]:
    documentation = []
    if include_optional:
        documentation.append(
            {
                "item_id": "docs-large",
                "value": "RAW_BODY_SHOULD_NOT_LEAK" * 200,
                "required": False,
                "category": "documentation",
            }
        )
    return {
        "schema": "p2p-context-view/1",
        "context_mode": "CONTEXT_EFFICIENT_V1",
        "preloaded": {
            "relevant_facts": [
                {
                    "item_id": "fact-main",
                    "value": "current authoritative fact",
                    "required": False,
                    "category": "relevant_facts",
                }
            ],
            "documentation": documentation,
        },
        "deferred_or_omitted": [
            {
                "category": "history",
                "item_id": "history-old",
                "pointer_id": "pointer-history",
                "source_binding": "history",
            }
        ],
        "serialized_size": {
            "label": "LOCAL_SERIALIZATION_PROXY",
            "bytes": total_bytes,
        },
    }


class ContextBudgetTests(unittest.TestCase):
    def test_classifies_required_optional_and_on_demand(self) -> None:
        report = audit_context_budget(_view(), host="codex", budget_bytes=10000)
        self.assertEqual(report["capability_id"], CAPABILITY_ID)
        self.assertEqual(report["host"], "CODEX")
        self.assertEqual(report["measurement"]["budget_status"], "PASS")
        self.assertEqual(report["classification"]["MUST_LOAD"]["count"], 1)
        self.assertEqual(report["classification"]["PRELOADED_OPTIONAL"]["count"], 1)
        self.assertEqual(report["classification"]["ON_DEMAND"]["count"], 1)
        self.assertEqual(report["classification"]["DO_NOT_LOAD"]["count"], 0)

    def test_over_budget_prioritizes_optional_bloat_without_raw_content(self) -> None:
        report = audit_context_budget(_view(total_bytes=12000), budget_bytes=8000)
        self.assertEqual(report["measurement"]["budget_status"], "OVER_BUDGET")
        self.assertEqual(report["recommendation"], "REVIEW_PRELOADED_OPTIONAL_FIRST")
        self.assertEqual(report["top_bloat"][0]["item_id"], "docs-large")
        self.assertEqual(report["top_bloat"][0]["classification"], "PRELOADED_OPTIONAL")
        self.assertNotIn("RAW_BODY_SHOULD_NOT_LEAK", json.dumps(report))
        self.assertFalse(report["safety"]["drops_context"])

    def test_required_only_over_budget_never_recommends_dropping_authority(self) -> None:
        report = audit_context_budget(_view(total_bytes=12000, include_optional=False), budget_bytes=8000)
        self.assertEqual(report["measurement"]["budget_status"], "OVER_BUDGET")
        self.assertEqual(report["recommendation"], "REQUIRED_CONTEXT_EXCEEDS_BUDGET_DO_NOT_DROP_AUTHORITY")

    def test_missing_budget_is_unbounded_not_silently_invented(self) -> None:
        report = audit_context_budget(_view(), host="arena")
        self.assertEqual(report["host"], "ARENA")
        self.assertEqual(report["measurement"]["budget_status"], "UNBOUNDED")
        self.assertIsNone(report["measurement"]["budget_bytes"])
        self.assertIsNone(report["measurement"]["headroom_bytes"])

    def test_invalid_view_fails_closed(self) -> None:
        with self.assertRaises(ContextBudgetError):
            audit_context_budget({"schema": "wrong"})
        with self.assertRaises(ContextBudgetError):
            audit_context_budget(_view(), budget_bytes=0)
        with self.assertRaises(ContextBudgetError):
            audit_context_budget(_view(), top_n=0)

    def test_cli_outputs_json_without_mutating_input(self) -> None:
        payload = _view(total_bytes=7000)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "view.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            before = path.read_bytes()
            self.assertEqual(main([str(path), "--host", "codex", "--budget-bytes", "8000"]), 0)
            self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
