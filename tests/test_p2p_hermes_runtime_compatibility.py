from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.hermes_runtime_compatibility import (
    CompatibilityError,
    EXPECTED_HERMES_VERSION,
    inspect_state_db,
    parse_hermes_version,
    validate_cli,
)


class TestHermesRuntimeCompatibility(unittest.TestCase):
    def test_version_parser_accepts_release_banner(self):
        self.assertEqual(
            parse_hermes_version("Hermes Agent v0.21.3 (2026.9.14)"),
            EXPECTED_HERMES_VERSION,
        )

    def test_cli_surface_passes(self):
        help_text = " ".join(
            [
                "--oneshot",
                "--usage-file",
                "--model",
                "--provider",
                "--toolsets",
                "--in",
                "--ignore-rules",
            ]
        )
        result = validate_cli("Hermes Agent v0.21.3", help_text)
        self.assertEqual(result["status"], "PASS")

    def test_version_mismatch_fails_closed(self):
        with self.assertRaisesRegex(CompatibilityError, "VERSION_MISMATCH"):
            validate_cli("Hermes Agent v0.20.2", "--oneshot --usage-file")

    def _make_db(self, path: Path, *, with_model_usage: bool = True) -> None:
        conn = sqlite3.connect(path)
        try:
            conn.execute(
                """
                CREATE TABLE sessions (
                    id TEXT PRIMARY KEY,
                    model TEXT,
                    billing_provider TEXT,
                    started_at REAL,
                    message_count INTEGER,
                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    cache_read_tokens INTEGER,
                    cache_write_tokens INTEGER,
                    reasoning_tokens INTEGER,
                    actual_cost_usd REAL,
                    estimated_cost_usd REAL
                )
                """
            )
            if with_model_usage:
                conn.execute(
                    """
                    CREATE TABLE session_model_usage (
                        session_id TEXT,
                        model TEXT,
                        billing_provider TEXT,
                        input_tokens INTEGER,
                        output_tokens INTEGER,
                        cache_read_tokens INTEGER,
                        cache_write_tokens INTEGER,
                        reasoning_tokens INTEGER,
                        actual_cost_usd REAL,
                        estimated_cost_usd REAL
                    )
                    """
                )
            conn.commit()
        finally:
            conn.close()

    def test_tokscale_full_schema_passes_readonly(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.db"
            self._make_db(path)
            result = inspect_state_db(path)
            self.assertTrue(result["read_only"])
            self.assertTrue(result["sessions_compatible"])
            self.assertEqual(result["tokscale_mode"], "PER_MODEL")

    def test_tokscale_session_fallback_is_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.db"
            self._make_db(path, with_model_usage=False)
            result = inspect_state_db(path)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["tokscale_mode"], "SESSION_TOTALS_FALLBACK")

    def test_missing_session_usage_column_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.db"
            conn = sqlite3.connect(path)
            try:
                conn.execute("CREATE TABLE sessions (id TEXT PRIMARY KEY, model TEXT)")
                conn.commit()
            finally:
                conn.close()
            with self.assertRaisesRegex(CompatibilityError, "TOKSCALE_SESSIONS_SCHEMA_MISSING"):
                inspect_state_db(path)


if __name__ == "__main__":
    unittest.main()
