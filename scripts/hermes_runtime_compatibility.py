#!/usr/bin/env python3
"""Small compatibility gate for the pinned Hermes runtime used by P2P.

The gate proves only the interfaces P2P consumes:
- exact Hermes release identity;
- CLI flags used by the P2P adapter;
- read-only SQLite columns required by TokScale's Hermes parser.

It does not authenticate providers, start background services, mutate the
runtime database, enable Hindsight, or certify production deployment.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path

EXPECTED_HERMES_VERSION = "0.21.3"
EXPECTED_HERMES_IMAGE_TAG = "v2026.9.14"

REQUIRED_CLI_TOKENS = (
    "--oneshot",
    "--usage-file",
    "--model",
    "--provider",
    "--toolsets",
    "--in",
    "--ignore-rules",
)

TOKSCALE_SESSIONS_COLUMNS = frozenset(
    {
        "id",
        "model",
        "billing_provider",
        "started_at",
        "message_count",
        "input_tokens",
        "output_tokens",
        "cache_read_tokens",
        "cache_write_tokens",
        "reasoning_tokens",
        "actual_cost_usd",
        "estimated_cost_usd",
    }
)

TOKSCALE_MODEL_USAGE_COLUMNS = frozenset(
    {
        "session_id",
        "model",
        "billing_provider",
        "input_tokens",
        "output_tokens",
        "cache_read_tokens",
        "cache_write_tokens",
        "reasoning_tokens",
        "actual_cost_usd",
        "estimated_cost_usd",
    }
)


class CompatibilityError(RuntimeError):
    pass


def parse_hermes_version(text: str) -> str:
    match = re.search(r"(?:Hermes Agent\s+)?v?(\d+\.\d+\.\d+)", text or "")
    if not match:
        raise CompatibilityError("HERMES_VERSION_UNPARSEABLE")
    return match.group(1)


def validate_cli(version_text: str, help_text: str) -> dict[str, object]:
    observed = parse_hermes_version(version_text)
    if observed != EXPECTED_HERMES_VERSION:
        raise CompatibilityError(
            f"HERMES_VERSION_MISMATCH:{observed}!={EXPECTED_HERMES_VERSION}"
        )
    missing = [token for token in REQUIRED_CLI_TOKENS if token not in help_text]
    if missing:
        raise CompatibilityError("HERMES_CLI_SURFACE_MISSING:" + ",".join(missing))
    return {
        "status": "PASS",
        "observed_version": observed,
        "expected_version": EXPECTED_HERMES_VERSION,
        "required_cli_tokens": list(REQUIRED_CLI_TOKENS),
    }


def _columns(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
    return {str(row[1]) for row in rows}


def inspect_state_db(path: str | Path) -> dict[str, object]:
    db_path = Path(path).expanduser().resolve()
    if not db_path.is_file():
        raise CompatibilityError("HERMES_STATE_DB_MISSING")

    uri = f"file:{db_path.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        tables = {
            str(row[0])
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if "sessions" not in tables:
            raise CompatibilityError("HERMES_SESSIONS_TABLE_MISSING")

        session_columns = _columns(conn, "sessions")
        missing_sessions = sorted(TOKSCALE_SESSIONS_COLUMNS - session_columns)
        if missing_sessions:
            raise CompatibilityError(
                "TOKSCALE_SESSIONS_SCHEMA_MISSING:" + ",".join(missing_sessions)
            )

        model_usage_present = "session_model_usage" in tables
        missing_model_usage: list[str] = []
        if model_usage_present:
            model_usage_columns = _columns(conn, "session_model_usage")
            missing_model_usage = sorted(
                TOKSCALE_MODEL_USAGE_COLUMNS - model_usage_columns
            )

        # TokScale explicitly falls back to session totals when the optional
        # per-model query cannot run, so missing per-model columns are a
        # degradation signal, not a hard incompatibility.
        return {
            "status": "PASS",
            "database": str(db_path),
            "sessions_compatible": True,
            "session_model_usage_present": model_usage_present,
            "session_model_usage_compatible": (
                model_usage_present and not missing_model_usage
            ),
            "session_model_usage_missing_columns": missing_model_usage,
            "tokscale_mode": (
                "PER_MODEL" if model_usage_present and not missing_model_usage else "SESSION_TOTALS_FALLBACK"
            ),
            "read_only": True,
        }
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    cli = sub.add_parser("cli")
    cli.add_argument("--version-file", required=True)
    cli.add_argument("--help-file", required=True)

    state = sub.add_parser("state-db")
    state.add_argument("path")

    args = parser.parse_args()
    try:
        if args.command == "cli":
            result = validate_cli(
                Path(args.version_file).read_text(encoding="utf-8"),
                Path(args.help_file).read_text(encoding="utf-8"),
            )
        else:
            result = inspect_state_db(args.path)
    except CompatibilityError as exc:
        print(json.dumps({"status": "FAIL", "reason": str(exc)}, sort_keys=True))
        return 1

    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
