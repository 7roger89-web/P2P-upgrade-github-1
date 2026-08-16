#!/usr/bin/env python3
"""Installed-project CLI for the P2P-native decision trace."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


runtime = Path(__file__).resolve().parents[1]
if str(runtime) not in sys.path:
    sys.path.insert(0, str(runtime))

from p2p_capabilities.decision_trace import cli_main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(cli_main())
