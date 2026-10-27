import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class QiushiScopeContractTests(unittest.TestCase):
    def test_skill_guardrails(self):
        skill = (ROOT / ".agents/skills/p2p-scope/SKILL.md").read_text()
        for term in ("two or more material blockers", "Skip direct tasks",
                     "already-clear critical path", "For independent blockers",
                     "observable dependency evidence", "falsify", "Owner Gates"):
            with self.subTest(term=term):
                self.assertIn(term, skill)

    def test_mode_resolves_existing_scope_skill(self):
        mode_path = ROOT / ".agents/skills/p2p/references/modes.md"
        mode = mode_path.read_text()
        relative = "../../p2p-scope/SKILL.md"
        self.assertIn(relative, mode)
        self.assertEqual((mode_path.parent / relative).resolve(),
                         (ROOT / ".agents/skills/p2p-scope/SKILL.md").resolve())

    def test_frozen_cases(self):
        data = json.loads((ROOT / "tests/fixtures/p2p_qiushi_scope_cases.json").read_text())
        self.assertEqual(len(data["cases"]), 6)
        self.assertEqual(data["comparison"]["behavioral_status"], "NOT_RUN")


if __name__ == "__main__":
    unittest.main()
