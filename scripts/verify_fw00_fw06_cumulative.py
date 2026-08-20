#!/usr/bin/env python3
"""Fresh-tree verification for the FW00-FW06 cumulative candidate (.35).

Proves over the EXTRACTED package alone (no repo imports):
  1. Doctor pass (--package, full gate set)
  2. Capability presence: FW05 owner-experience + FW06 resilience surfaces import and
     expose their key contracts (fresh PYTHONPATH into system/ only)
  3. Fresh-process smoke: run classification/decision-id/lease logic in a subprocess
     whose PYTHONPATH is ONLY the extracted tree (no home-repo contamination)
  4. Manifest/checksum integrity re-verify
"""
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

CANONICAL = Path("/home/ubuntu/fw01_work/auth-f01/reports/candidates/"
                 "P2P-8.4.7-C-Codex-Edition-v24-fw00-fw06-cumulative-candidate.zip")
FRESH = Path("/tmp/p2p-fw00-fw06-fresh")
EXPECTED_SHA256 = "8cd26c23cb57d6821d318312493bcecc0278100cd7b527df1ede63b3dbf14a47"


def sha256(path: Path) -> str:
    d = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            d.update(block)
    return d.hexdigest()


def step(name):
    def deco(fn):
        def wrap():
            try:
                fn()
                print(f"  [PASS] {name}")
            except Exception as e:  # noqa: BLE001
                print(f"  [FAIL] {name}: {e}")
                sys.exit(3)
        return wrap
    return deco


@step("extract-byte-identical + manifest-checksum integrity")
def check_extract():
    if FRESH.exists():
        import shutil
        shutil.rmtree(FRESH)
    assert sha256(CANONICAL) == EXPECTED_SHA256, "candidate bytes changed"
    with zipfile.ZipFile(CANONICAL) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            data = z.read(info.filename)
            digest = hashlib.sha256(data).hexdigest()
            full = FRESH / info.filename
            full.parent.mkdir(parents=True, exist_ok=True)
            full.write_bytes(data)
    # manifest-driven re-verify
    manifest = json.loads((FRESH / "release-manifest.json").read_text())
    listed = {item["path"] for item in manifest["files"]}
    actual = {str(p.relative_to(FRESH)) for p in FRESH.rglob("*") if p.is_file()
              and not p.is_symlink()}
    extra = actual - listed - {"release-manifest.json", "RELEASE-SHA256SUMS.txt"}
    assert not extra, f"extra files beyond manifest: {list(extra)[:5]}"
    for item in manifest["files"]:
        full = FRESH / item["path"]
        assert sha256(full) == item["sha256"], item["path"]
        assert full.stat().st_size == item["size"], item["path"]
    sums = (FRESH / "RELEASE-SHA256SUMS.txt").read_text().splitlines()
    for line in sums:
        digest, _, rel = line.partition("  ")
        assert sha256(FRESH / rel) == digest, rel


@step("doctor --package full gate set")
def check_doctor():
    result = subprocess.run(
        [sys.executable, str(FRESH / "scripts" / "doctor.py"),
         "--package", str(FRESH)],
        capture_output=True, text=True)
    last_line = result.stdout.strip().splitlines()[-1]
    assert "RESULT: PASS" in last_line, last_line


@step("FW05/FW06 capability presence (fresh PYTHONPATH)")
def check_presence():
    env_path = str(FRESH / "system")
    code = (
        "import sys\n"
        "assert any(p == SYS for p in sys.path), sys.path\n"
        "from p2p_capabilities import fw05_owner_experience as fw05\n"
        "from p2p_capabilities import fw06_operational_resilience as fw06\n"
        "assert hasattr(fw05, 'make_decision_record') and hasattr(fw05, 'build_owner_inbox_item') "
        "and hasattr(fw05, 'resolve_owner_answer') and hasattr(fw05, 'read_inbox_records')\n"
        "assert hasattr(fw06, 'classify_failure') and hasattr(fw06, 'safe_continuation_decision') "
        "and hasattr(fw06, 'acquire_lease') and hasattr(fw06, 'recover_after_crash') "
        "and hasattr(fw06, 'quiesce_enter') and hasattr(fw06, 'is_paused')\n"
        "rec = fw05.make_decision_record(goal_id='g', task_id='t', decision_type='OWNER_GATE', "
        "input_facts=['f'], applied_policy_or_rule='p', selected_action='a', "
        "evidence_pointers=[], owner_decision_required=True)\n"
        "print('FW05 fields:', len(rec))\n"
        "print('FW06 classify UNKNOWN_MUTATION_STATE:', fw06.classify_failure('unknown_state'))\n"
    ).replace("SYS", repr(env_path))
    result = subprocess.run([sys.executable, "-c", code], capture_output=True,
                            text=True, env={**ENV, "PYTHONPATH": env_path,
                                            "PYTHONDONTWRITEBYTECODE": "1"})
    assert result.returncode == 0, result.stderr[-2000:]
    assert "FW05 fields:" in result.stdout, result.stdout
    assert "FW06 classify" in result.stdout, result.stdout


@step("fresh-process smoke: lease + decision-ID determinism in isolated subprocess")
def check_smoke():
    env_path = str(FRESH / "system")
    state = "/tmp/p2p-fw00-fw06-smoke-state"
    subprocess.run(["rm", "-rf", state], check=False)
    code = (
        "import sys, tempfile, os\n"
        "tmp = os.path.join(TMP, 's1')\n"
        "from p2p_capabilities import fw06_operational_resilience as fw06\n"
        "l1 = fw06.acquire_lease(tmp, owner_process='P1', project_id='proj1')\n"
        "l2 = fw06.acquire_lease(tmp, owner_process='P2', project_id='proj1')\n"
        "assert l2['acquired'] is False and l2.get('failure_class') == 'LEASE_CONFLICT', l2\n"
        "fw06.release_lease(tmp, l1['lease']['lease_id'])\n"
        "l3 = fw06.acquire_lease(tmp, owner_process='P1', project_id='proj1')\n"
        "assert l3['acquired'] is True, l3\n"
        "from p2p_capabilities import fw05_owner_experience as fw05\n"
        "r = fw05.make_decision_record(goal_id='g1', task_id='t1', decision_type='PROMOTION_GATE',\n"
        "    input_facts=['artifact exists'], applied_policy_or_rule='promotion policy',\n"
        "    selected_action='WAIT_OWNER', evidence_pointers=[],\n"
        "    owner_decision_required=True)\n"
        "r2 = fw05.make_decision_record(goal_id='g1', task_id='t1', decision_type='PROMOTION_GATE',\n"
        "    input_facts=['artifact exists'], applied_policy_or_rule='promotion policy',\n"
        "    selected_action='WAIT_OWNER', evidence_pointers=[],\n"
        "    owner_decision_required=True)\n"
        "assert r['DECISION_ID'] == r2['DECISION_ID'], (r['DECISION_ID'], r2['DECISION_ID'])\n"
        "print('LEASE_SMOKE_OK DECISION_ID', r['DECISION_ID'][:12])\n"
    ).replace("TMP", repr(state))
    result = subprocess.run([sys.executable, "-c", code], capture_output=True,
                            text=True, env={**ENV, "PYTHONPATH": env_path,
                                            "PYTHONDONTWRITEBYTECODE": "1"})
    assert result.returncode == 0, result.stderr[-2000:]
    assert "LEASE_SMOKE_OK" in result.stdout, result.stdout


ENV = {**{k: v for k, v in __import__("os").environ.items()
          if k != "PYTHONPATH"}, "PYTHONDONTWRITEBYTECODE": "1"}


def main():
    print("FW00-FW06 CUMULATIVE (.35) FRESH-TREE VERIFICATION")
    check_extract()
    check_doctor()
    check_presence()
    check_smoke()
    print("ALL FRESH-TREE CHECKS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
