#!/usr/bin/env python3
"""Namespaced adapter for the UI/UX evaluator in a full P2P install."""

import importlib.util
import runpy
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent


def _load_alias(name: str, preferred: Path, fallback: Path) -> None:
    target = preferred if preferred.exists() else fallback
    spec = importlib.util.spec_from_file_location(name, target)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load UI/UX evaluator dependency: {target}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)


if __name__ == "__main__":
    _load_alias("doctor", HERE / "p2p_uiux_doctor.py", HERE / "doctor.py")
    _load_alias("drift_check", HERE / "p2p_uiux_drift_check.py", HERE / "drift_check.py")
    implementation = HERE / "p2p_uiux_eval_impl.py"
    if not implementation.exists():
        implementation = HERE / "p2p_eval.py"
    runpy.run_path(str(implementation), run_name="__main__")
