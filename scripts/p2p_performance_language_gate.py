#!/usr/bin/env python3
"""Development/runtime CLI for the P2P performance-language evidence gate."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass


def _load_runtime() -> None:
    here = Path(__file__).resolve()
    candidates = []
    for parent in here.parents:
        candidates.extend((parent / ".p2p" / "system", parent))
    for candidate in candidates:
        if (candidate / "p2p_capabilities" / "performance_language_gate.py").is_file():
            sys.path.insert(0, str(candidate))
            return
    raise RuntimeError("P2P native runtime was not found")


_load_runtime()

from p2p_capabilities.performance_language_gate import cli_main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(cli_main())
