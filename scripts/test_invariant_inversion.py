"""Negative proof that proposal/bootstrap state cannot authorize mutation."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".p2p" / "system"))

from p2p_capabilities.project_context import ProjectContextBootstrap, ProjectContextError, enforce_map_before_work


def run() -> None:
    root = Path(tempfile.mkdtemp(prefix="invariant-inversion-", dir=str(ROOT / ".tmp")))
    try:
        bootstrap = ProjectContextBootstrap(root)
        assert bootstrap.is_ready() is False
        bootstrap.bootstrap_new_project("test proposal")
        assert not (root / ".p2p" / "project-pin.json").exists()
        try:
            enforce_map_before_work(root, mutation_intent=True)
        except ProjectContextError:
            pass
        else:
            raise AssertionError("proposal/bootstrap state authorized mutation")
        (root / ".p2p" / "project-pin.json").write_text(json.dumps({"verification_status": "VERIFIED", "doctor_result": "HEALTHY"}), encoding="utf-8")
        assert ProjectContextBootstrap(root).is_ready() is False
        print(json.dumps({"status": "PASS", "proposal_pin": "NOT_CREATED", "malformed_pin": "BLOCKED"}))
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    run()
