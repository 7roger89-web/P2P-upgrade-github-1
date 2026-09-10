"""Focused deterministic checks for the single reusable prompt artifact
(P2P-PROMPT-ARTIFACT-01).

These tests prove artifact CONTRACT and STRUCTURE only. They do NOT assert that
any language model produced a specific message: subjective model quality cannot
be proven by static fixtures. Model-output samples, when produced, are kept
separate as clearly-labeled evidence, never as deterministic assertions.

Covered acceptance conditions (deterministic slice):
  A. DISCOVERY     — searching by stable ID finds exactly the one artifact.
  B. DOMAIN        — a natural logistics/shipment search term finds the artifact.
  3. STRUCTURE     — exactly one reusable prompt artifact; minimal metadata only.
  7. NO-FABRICATION— explicit contract forbids inventing operational facts.
  8. MISSING DATA  — missing ETA / status / fee is omitted or disclosed, never guessed.
  9. NO SIDE EFFECT— no external send / contact / mutation / provider call.
 10. NO GATEWAY    — no OpenRouter / model gateway / API-key handling.
  2/4. VERSIONING  — Git is the version-history mechanism; no version DB/service.
"""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = REPO_ROOT / "docs" / "p2p-development" / "prompt-artifacts"
ARTIFACT_PATH = ARTIFACT_DIR / "logistics.customer-shipment-update.md"
PROMPT_ID = "logistics.customer-shipment-update"

# Operational facts the prompt must never invent (substring check on the
# artifact's no-fabrication contract).
FORBIDDEN_FABRICATIONS = (
    "shipment status",
    "eta",
    "dates",
    "prices",
    "additional fees",
    "customs status",
    "vehicle",
    "weight",
    "quantity",
    "route",
    "border gate",
    "documents",
    "customer information",
    "factory information",
    "payment status",
)


def _tracked_md_files() -> list[str]:
    """All Markdown files tracked by Git, as raw relative paths (-z avoids
    pathname quoting for non-ASCII / special characters)."""
    result = subprocess.run(
        ["git", "ls-files", "-z", "*.md"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [p for p in result.stdout.split("\0") if p.strip()]


def _read_rel(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8", errors="replace")


def _artifact_text() -> str:
    return ARTIFACT_PATH.read_text(encoding="utf-8")


class ReusablePromptArtifactTests(unittest.TestCase):
    def test_01_artifact_exists_at_canonical_path(self) -> None:
        self.assertTrue(ARTIFACT_PATH.is_file(), f"missing {ARTIFACT_PATH}")

    def test_02_exactly_one_reusable_prompt_artifact_no_framework(self) -> None:
        # The product is ONE prompt. The directory must contain exactly this
        # one Markdown artifact: no registry, index, router, or service files.
        files = sorted(p.name for p in ARTIFACT_DIR.iterdir() if p.suffix == ".md")
        self.assertEqual(files, ["logistics.customer-shipment-update.md"])

    def test_03_discovery_by_stable_id_finds_exactly_the_artifact(self) -> None:
        # CASE A — search by stable ID. The ID is *declared* in exactly one
        # tracked file (this artifact); no other file declares it as a prompt.
        declared = [
            rel for rel in _tracked_md_files() if f"ID: {PROMPT_ID}" in _read_rel(rel)
        ]
        self.assertEqual(declared, [str(ARTIFACT_PATH.relative_to(REPO_ROOT))])

    def test_04_domain_discovery_finds_artifact(self) -> None:
        # CASE B — a natural Logistics/customer-update search term locates the
        # artifact without any new index.
        text = _artifact_text().lower()
        self.assertIn("logistics", text)
        self.assertIn("shipment", text)
        self.assertIn("customer update", text)
        self.assertIn("shipment status", text)
        found = [
            rel
            for rel in _tracked_md_files()
            if "customer shipment update" in _read_rel(rel).lower()
        ]
        self.assertIn(str(ARTIFACT_PATH.relative_to(REPO_ROOT)), found)

    def test_05_minimal_metadata_fields_present(self) -> None:
        text = _artifact_text()
        for field in ("ID:", "DOMAIN:", "CAPABILITY:", "USE_WHEN:", "DO_NOT_USE_WHEN:"):
            with self.subTest(field=field):
                self.assertIn(field, text)
        self.assertIn(f"ID: {PROMPT_ID}", text)

    def test_06_no_fabrication_contract_is_explicit(self) -> None:
        text = _artifact_text().lower()
        for fact in FORBIDDEN_FABRICATIONS:
            with self.subTest(forbidden=fact):
                self.assertIn(fact, text)
        self.assertIn("never invent", text)
        self.assertIn("never guess", text)

    def test_07_missing_data_is_omitted_or_disclosed_never_guessed(self) -> None:
        text = _artifact_text().lower()
        self.assertIn("omit", text)
        self.assertIn("not currently available", text)
        self.assertIn("never guess a missing value", text)
        self.assertIn("never invent a date, status, fee, or price", text)

    def test_08_no_external_send_or_action_side_effect(self) -> None:
        text = _artifact_text()
        # The prompt explicitly forbids sending/contacting/mutating/calling a provider.
        for prohibition in (
            "Do not send Telegram, email, or Zalo messages",
            "do not contact the customer",
            "do not mutate Logistics data",
            "do not call an external AI provider directly",
        ):
            with self.subTest(prohibition=prohibition):
                self.assertIn(prohibition, text)
        # No active instruction to perform any of those side effects.
        lowered = text.lower()
        for marker in (
            "smtplib",
            "requests.post",
            "requests.get",
            "send_telegram",
            "telegram-send",
            "send_email",
        ):
            with self.subTest(active_marker=marker):
                self.assertNotIn(marker, lowered)

    def test_09_no_openrouter_or_model_gateway_introduced(self) -> None:
        text = _artifact_text()
        for marker in ("OpenRouter", "model gateway", "provider routing", "api_key", "API key"):
            with self.subTest(marker=marker):
                self.assertNotIn(marker, text)

    def test_10_git_is_version_history_and_no_version_database(self) -> None:
        text = _artifact_text()
        self.assertIn("Git", text)
        self.assertIn("version history", text)
        self.assertIn("git log", text)
        # The artifact explicitly states it has NO version database/API/service.
        self.assertIn("There is no prompt version database", text)
        self.assertIn("no version API", text)
        # No active version-infrastructure signals were introduced.
        lowered = text.lower()
        for marker in ("version table", "migrations", "prompt_history", "version_number"):
            with self.subTest(marker=marker):
                self.assertNotIn(marker, lowered)

    def test_11_artifact_is_tracked_by_git(self) -> None:
        # Durability: the artifact is committed and tracked by the existing
        # repository (Git is the version-history mechanism).
        rel = str(ARTIFACT_PATH.relative_to(REPO_ROOT))
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", rel],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
