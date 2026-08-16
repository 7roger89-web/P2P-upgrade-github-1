"""Technical guard for capability tests and temporary evaluation targets."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable


class IsolationViolation(ValueError):
    """Raised when an evaluation target is a preserve-only path."""


def assert_isolated_target(target: str | Path, protected_roots: Iterable[str | Path]) -> Path:
    candidate = Path(target).expanduser().resolve()
    for raw_root in protected_roots:
        root = Path(raw_root).expanduser().resolve()
        try:
            candidate.relative_to(root)
        except ValueError:
            continue
        raise IsolationViolation(f"evaluation target is inside preserve-only root: {candidate}")
    return candidate
