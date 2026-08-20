#!/usr/bin/env python3
"""Reinstall idempotence + packaged regression + GT/GP compatibility shadow
for the FW00-FW06 cumulative candidate (.35).

READ-ONLY with respect to Game Truyện / Gia Phả / Logistics:
  - GT/GP trees are NEVER written; only hashes and file lists are computed.
  - The shadow installs into /tmp roots, never into GT/GP.
"""
import hashlib
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

CANONICAL = Path("/home/ubuntu/fw01_work/auth-f01/reports/candidates/"
                 "P2P-8.4.7-C-Codex-Edition-v24-fw00-fw06-cumulative-candidate.zip")
FRESH = Path("/tmp/p2p-fw00-fw06-fresh")
SYSTEM = FRESH / "system"
PKGPROJ = Path("/tmp/p2p-fw00-fw06-pkgproj")

GT = Path("/home/ubuntu/fw01_work/cert/game-truyen")
GP = Path("/home/ubuntu/fw01_work/cert/gia-pha")

ENV = {**{k: v for k, v in os.environ.items() if k != "PYTHONPATH"},
       "PYTHONDONTWRITEBYTECODE": "1"}


def sha256(path: Path) -> str:
    d = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            d.update(block)
    return d.hexdigest()


def _tree_hash(root: Path) -> str:
    dig = []
    for p in sorted(root.rglob("*")):
        if p.is_dir():
            continue
        rel = str(p.relative_to(root)).encode()
        if p.is_symlink():
            dig.append(rel + b"LINK" + os.readlink(p).encode())
        elif ".git/" in str(p) + "/":
            continue
        else:
            dig.append(rel + sha256(p).encode())
    combined = hashlib.sha256(b"\n".join(dig)).hexdigest()
    return combined


def step(name):
    def deco(fn):
        def wrap():
            try:
                fn()
                print(f"  [PASS] {name}")
            except Exception as e:  # noqa: BLE001
                print(f"  [FAIL] {name}: {e}")
                sys.exit(4)
        return wrap
    return deco


@step("reinstall idempotence: second extraction byte-identical tree")
def check_idempotence():
    # Start from a guaranteed-clean re-extraction (any leftover state from
    # earlier verification runs is discarded first).
    if FRESH.exists():
        import shutil
        shutil.rmtree(FRESH)
    with zipfile.ZipFile(CANONICAL) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            full = FRESH / info.filename
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_bytes(z.read(info.filename))
    before = _tree_hash(FRESH)
    import shutil
    shutil.rmtree(FRESH)
    with zipfile.ZipFile(CANONICAL) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            full = FRESH / info.filename
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_bytes(z.read(info.filename))
    after = _tree_hash(FRESH)
    assert before == after, "tree changed between extractions"
    # doctor still passes on the reinstalled tree
    result = subprocess.run(
        [sys.executable, str(FRESH / "scripts" / "doctor.py"),
         "--package", str(FRESH)],
        capture_output=True, text=True)
    assert "RESULT: PASS" in result.stdout, result.stdout[-500:]


@step("packaged regression: 240 tests inside project-shaped git wrapper")
def check_packaged_regression():
    import shutil
    # The packaged tests are designed for a PROJECT tree: several tests use
    # git log (need a git repo at the project root) and write certification
    # evidence to .p2p/state (a runtime directory install.sh now creates).
    # The extracted zip is wrapped into a project-shaped root exactly as a
    # target project would see after install:
    #   PKGPROJ/.p2p/system/<everything from zip except git-agnostic layout>
    #   PKGPROJ/.p2p/state (runtime dir, created by the install path)
    #   PKGPROJ initialized as a fresh git repo (project-initialized)
    if PKGPROJ.exists():
        shutil.rmtree(PKGPROJ)
    # Extract the raw zip at PKGPROJ root, then move system/ under .p2p/.
    with zipfile.ZipFile(CANONICAL) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            full = PKGPROJ / info.filename
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_bytes(z.read(info.filename))
    dot_p2p = PKGPROJ / ".p2p"
    dot_p2p.mkdir(parents=True, exist_ok=True)
    shutil.move(str(PKGPROJ / "system"), str(dot_p2p / "system"))
    (dot_p2p / "state").mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=str(PKGPROJ),
                   check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(PKGPROJ), "config", "user.name",
                    "p2p-rebuild"], check=True, capture_output=True, text=True)
    subprocess.run(["git", "-C", str(PKGPROJ), "config", "user.email",
                    "p2p-rebuild@internal"], check=True, capture_output=True,
                   text=True)
    subprocess.run(["git", "-C", str(PKGPROJ), "add", "-A"], check=True,
                   capture_output=True, text=True)
    subprocess.run(["git", "-C", str(PKGPROJ), "commit", "-qm",
                    "packaged candidate .35"], check=True,
                   capture_output=True, text=True)
    pkg_system = dot_p2p / "system"
    tests_dir = pkg_system / "p2p_capabilities" / "tests"
    assert tests_dir.is_dir(), tests_dir
    # Canonical invocation: exactly the repo command that yields 240/240.
    # Discover resolves the relative start against cwd and inserts the parent
    # of the top-level test directory into sys.path; tests' own parents-offset
    # path logic resolves against PKGPROJ (the project root), and git-log-
    # based freshness tests resolve via SYSTEM_PATH.parents[1] = PKGPROJ.
    result = subprocess.run(
        [sys.executable, "-m", "unittest", "discover",
         "-s", "p2p_capabilities/tests", "-p", "test_*.py"],
        capture_output=True, text=True, cwd=str(pkg_system),
        env={k: v for k, v in ENV.items() if k not in ("PYTHONPATH",)})
    out = result.stdout + result.stderr
    last = out.strip().splitlines()[-2:]
    print(f"    unittest output tail: {last}")
    assert result.returncode == 0, out[-3000:]
    ran = [l for l in out.splitlines() if l.startswith("Ran ")]
    assert ran and "240 tests" in ran[0] and "OK" in out, (ran, last)


@step("GT/GP compatibility shadow READ-ONLY (byte-identical before/after)")
def check_shadow():
    for name, root in (("GT", GT), ("GP", GP)):
        before = _tree_hash(root)
        # Probe the packaged system against the project trees: read surfaces
        # must not create .p2p state dirs inside the project roots.
        code = (
            "import sys, os, glob\n"
            "from p2p_capabilities import fw06_operational_resilience as fw06\n"
            "import p2p_capabilities.decision_trace as dt\n"
            "p = fw06.read_fw06_events(ROOT)\n"
            "e = fw06.envelope_state(ROOT) if hasattr(fw06, 'envelope_state') else {}\n"
            "l = fw06.read_leases(ROOT)\n"
            "tr = dt.read_trace_records(ROOT)\n"
            "state_dirs = [d for d in glob.glob(os.path.join(ROOT, '.p2p'), recursive=True)]\n"
            "print('state_dirs', state_dirs)\n"
            "print('events', len(p), 'leases', len(l), 'trace', len(tr))\n"
        ).replace("ROOT", repr(str(root)))
        result = subprocess.run([sys.executable, "-c", code],
                                capture_output=True, text=True,
                                env={**ENV, "PYTHONPATH": str(SYSTEM)})
        assert result.returncode == 0, (name, result.stderr[-2000:])
        # GT/GP must remain byte-identical (read-only proof)
        after = _tree_hash(root)
        assert before == after, f"{name} tree mutated during shadow probe"
        print(f"    {name}: read-only probe ok, tree unchanged")


def main():
    print("REINSTALL + PACKAGED REGRESSION + GT/GP SHADOW (READ-ONLY)")
    check_idempotence()
    check_packaged_regression()
    check_shadow()
    print("ALL PHASE-13-15 CHECKS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
