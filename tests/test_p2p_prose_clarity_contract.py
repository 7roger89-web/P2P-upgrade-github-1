from __future__ import annotations

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL = REPO_ROOT / ".agents" / "skills" / "p2p" / "SKILL.md"
REFERENCE = REPO_ROOT / ".agents" / "skills" / "p2p" / "references" / "prose-clarity.md"
MODULE_INDEX = REPO_ROOT / ".agents" / "skills" / "p2p" / "references" / "module-index.md"
INTAKE = REPO_ROOT / "docs" / "p2p-development" / "research" / "diataxis-writer-intake-20260918.md"


def _word_count(text: str) -> int:
    return len(re.findall(r"\b\w+[\w./:=|-]*\b", text, flags=re.UNICODE))


def _long_sentence_count(text: str, limit: int = 25) -> int:
    sentences = [part.strip() for part in re.split(r"[.!?]+", text) if part.strip()]
    return sum(_word_count(sentence) > limit for sentence in sentences)


class P2PProseClarityContractTests(unittest.TestCase):
    def test_live_skill_wires_one_bounded_clarity_pass(self) -> None:
        skill = SKILL.read_text(encoding="utf-8")
        self.assertIn("references/prose-clarity.md", skill)
        self.assertIn("one bounded clarity pass", skill)
        self.assertIn("Do not run a second rewrite loop", skill)

    def test_guard_preserves_meaning_before_brevity(self) -> None:
        ref = REFERENCE.read_text(encoding="utf-8")
        for required in (
            "acceptance criteria",
            "Owner Gates",
            "evidence status",
            "rollback",
            "exact commands",
            "If shortening conflicts with protected meaning, keep the meaning.",
        ):
            self.assertIn(required, ref)

    def test_diataxis_is_optional_and_documentation_only(self) -> None:
        skill = SKILL.read_text(encoding="utf-8")
        ref = REFERENCE.read_text(encoding="utf-8")
        self.assertIn("only for actual documentation", skill)
        self.assertIn("Do not force this taxonomy onto executor prompts", ref)
        self.assertIn("prose-clarity.md", MODULE_INDEX.read_text(encoding="utf-8"))

    def test_upstream_is_reference_only_without_vendor_copy(self) -> None:
        intake = INTAKE.read_text(encoding="utf-8")
        ref = REFERENCE.read_text(encoding="utf-8")
        self.assertIn("REFERENCE_ONLY", intake)
        self.assertIn("license metadata: `null`", intake)
        self.assertIn("integration mode: `REFERENCE_ONLY`", ref)
        self.assertFalse((REPO_ROOT / ".p2p" / "vendor" / "skill" / "diataxis-writer").exists())

    def test_ab_fixture_gets_shorter_without_losing_protected_tokens(self) -> None:
        before = (
            "It is important to note that the executor should, in order to complete "
            "the task safely and correctly, first confirm P2P_LAW_SOURCE=LOCAL_PORTABLE, "
            "while also remembering that OWNER_GATE=REQUIRED applies before deployment, "
            "and after that it should run the relevant checks so that TEST_RESULTS=27/27 "
            "is recorded, with rollback=REQUIRED preserved in case the protected action "
            "cannot be completed as expected."
        )
        after = (
            "Confirm P2P_LAW_SOURCE=LOCAL_PORTABLE before execution. "
            "OWNER_GATE=REQUIRED applies before deployment. "
            "Record TEST_RESULTS=27/27 after the relevant checks. "
            "Keep rollback=REQUIRED for the protected action."
        )
        protected = (
            "P2P_LAW_SOURCE=LOCAL_PORTABLE",
            "OWNER_GATE=REQUIRED",
            "TEST_RESULTS=27/27",
            "rollback=REQUIRED",
        )
        self.assertLess(_word_count(after), _word_count(before))
        self.assertLessEqual(_long_sentence_count(after), _long_sentence_count(before))
        for token in protected:
            self.assertIn(token, before)
            self.assertIn(token, after)


if __name__ == "__main__":
    unittest.main()
