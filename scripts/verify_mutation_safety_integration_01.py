#!/usr/bin/env python3
"""Fresh-tree verification for the P2P-MUTATION-SAFETY-INTEGRATION-01 candidate (.41).

Proves over the EXTRACTED package alone (no repo imports):
  1. Doctor pass (--package, full gate set)
  2. Capability presence: FW02-FW06 canonical modules, the three integrated
     mutation-safety modules, and their key contracts (fresh PYTHONPATH into
     system/ only)
  3. Fresh-process smoke: A-E path classification, platform/role separation
     invariant, team decision in an isolated subprocess (no home-repo
     contamination)
  4. Manifest/checksum integrity re-verify
"""
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

CANONICAL = Path("/home/ubuntu/fw01_work/auth-f01/reports/candidates/"
                 "P2P-8.4.7-C-Codex-Edition-v24-mutation-safety-integration-01-candidate.zip")
FRESH = Path("/tmp/p2p-fresh-41")
EXPECTED_SHA256 = "da835f8a48caf4536094ffdd82e3c65baa82da32aa9a7ae73714ee1f2e9c3d2d"


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
    # embedded version must be .41
    version = (FRESH / "VERSION").read_text().strip()
    assert version == "8.4.7-C-codex.41", version
    assert (FRESH / "runtime" / "VERSION").read_text().strip() == version


@step("doctor --package full gate set")
def check_doctor():
    result = subprocess.run(
        [sys.executable, str(FRESH / "scripts" / "doctor.py"),
         "--package", str(FRESH)],
        capture_output=True, text=True)
    last_line = result.stdout.strip().splitlines()[-1]
    assert "RESULT: PASS" in last_line, last_line


@step("integration-01 modules presence and contracts (fresh PYTHONPATH)")
def check_presence():
    env_path = str(FRESH / "runtime")
    code = (
        "import sys\n"
        "assert any(p == SYS for p in sys.path), sys.path\n"
        "# Canonical frameworks FW05/FW06 ship in the candidate (FW02-FW04 behavior\n"
        "# is provided by team_intelligence/bounded_documentation_write/role_receipt).\n"
        "from p2p_capabilities import fw05_owner_experience as fw05\n"
        "from p2p_capabilities import fw06_operational_resilience as fw06\n"
        "assert hasattr(fw05, 'make_decision_record') and hasattr(fw06, 'acquire_lease')\n"
        "# BW01: bounded-documentation-write primitive with A-E classification.\n"
        "from p2p_capabilities import bounded_documentation_write as bdw\n"
        "assert hasattr(bdw, 'execute_bounded_document_mutation') "
        "and hasattr(bdw, 'rollback_bounded_document_mutation')\n"
        "assert hasattr(bdw, 'classify_document_path') "
        "and hasattr(bdw, 'evaluate_bounded_document_mutation_quality')\n"
        "# integration-01: A-E classification with fail-closed canonical normalization.\n"
        "cases = [\n"
        " ('docs/TASKS.md', None),            # any-depth protected basename -> blocked\n"
        " ('docs/evidence/deep/TASKS.md', None),  # deep nesting also blocked\n"
        " ('TASKS.md', None),                 # root-only baseline\n"
        " ('AGENTS.md', None),\n"
        " ('docs/package.json', 'ALLOWED'),   # docs tree manifest at depth -> allowed\n"
        " ('docs/evidence/notes.md', 'ALLOWED'),  # evidence tree -> allowed\n"
        " ('etc/passwd', None),               # non-document -> blocked\n"
        "]\n"
        "for path, expect in cases:\n"
        "    r = bdw.classify_document_path(path)\n"
        "    if expect is None:\n"
        "        assert 'BLOCK' in r or 'PROTECTED' in r or 'UNKNOWN' in r, (path, r)\n"
        "    else:\n"
        "        assert expect in r, (path, r)\n"
        "print('A-E classification OK')\n"
        "# integration-01: platform/role separation constant ships.\n"
        "from p2p_capabilities import team_intelligence as ti\n"
        "assert hasattr(ti, 'FW02_BASE_PLATFORM_CAPABILITIES')\n"
        "base = set(ti.FW02_BASE_PLATFORM_CAPABILITIES)\n"
        "assert 'bounded_documentation_write' not in base, base\n"
        "print('PLATFORM_BASE_SET OK', sorted(base))\n"
        "# integration-01: role_receipt team checks ship.\n"
        "from p2p_capabilities import role_receipt as rr\n"
        "assert hasattr(rr, 'verify_bounded_mutation_receipt')\n"
        "print('team-receipt verifier OK')\n"
    ).replace("SYS", repr(env_path))
    result = subprocess.run([sys.executable, "-c", code], capture_output=True,
                            text=True, env={**ENV, "PYTHONPATH": env_path,
                                            "PYTHONDONTWRITEBYTECODE": "1"})
    assert result.returncode == 0, result.stderr[-2000:]
    assert "A-E classification OK" in result.stdout, result.stdout
    assert "PLATFORM_BASE_SET OK" in result.stdout, result.stdout
    assert "team-receipt verifier OK" in result.stdout, result.stdout


@step("fresh-process smoke: A-E classification + platform/role separation in "
      "isolated subprocess")
def check_smoke():
    env_path = str(FRESH / "runtime")
    state = "/tmp/p2p-fresh-41-state"
    subprocess.run(["rm", "-rf", state], check=False)
    code = (
        "import sys, os, tempfile\n"
        "tmp = os.path.join(ST, 's1')\n"
        "os.makedirs(tmp)\n"
        "from p2p_capabilities import bounded_documentation_write as bdw\n"
        "from p2p_capabilities import team_intelligence as ti\n"
        "# A-E baseline-lock: root-only basenames blocked at any depth.\n"
        "assert 'BLOCK' in bdw.classify_document_path('docs/TASKS.md') "
        "or 'PROTECTED' in bdw.classify_document_path('docs/TASKS.md')\n"
        "assert 'BLOCK' in bdw.classify_document_path('docs/evidence/deep/AGENTS.md') "
        "or 'PROTECTED' in bdw.classify_document_path('docs/evidence/deep/AGENTS.md')\n"
        "# lookalike traversal + normalization deny.\n"
        "assert 'PROTECTED' in bdw.classify_document_path('docs/evidence/../docs/TASKS.md')\n"
        "print('CLASSIFY_SMOKE_OK')\n"
        "# platform/role separation: base caps are infrastructure, never a\n"
        "# material failure for a role team decision.\n"
        "base = set(ti.FW02_BASE_PLATFORM_CAPABILITIES)\n"
        "assert 'bounded_documentation_write' not in base\n"
        "print('SEPARATION_SMOKE_OK base=', sorted(base))\n"
        "# team decision invariant: role caps cover mutation scope -> no material\n"
        "# failure even when base caps lack certifications (they are not role caps).\n"
        "task = {'task_id': 't1', 'goal_id': 'g1',\n"
        "        'required_capabilities': ('bounded_documentation_write',)}\n"
        "dec = ti.build_team_decision(\n"
        "    required_capabilities=('bounded_documentation_write',),\n"
        "    registry_records=[{'CAPABILITY_ID': 'p2p_architecton',\n"
        "        'ROLE_ID': 'p2p_architecton',\n"
        "        'PROVIDES': ('bounded_documentation_write',),\n"
        "        'CAPABILITY_EXECUTION_SCOPE_MAP': {'DOCUMENTATION_MUTATION_BOUNDED':\n"
        "            ('game-truyen-isolated',)},\n"
        "        'TARGET_CERTIFIED': 'live',\n"
        "        'ELIGIBILITY': 'ELIGIBLE'}],\n"
        "    live_required=False,\n"
        "    mutation_class='DOCUMENTATION_WRITE_ONLY',\n"
        "    eligibility_results={'p2p_architecton': {'eligible': True}},\n"
        "    capability_certifications={})\n"
        "mut = [c for c in dec.required_capabilities if c not in base]\n"
        "prov = set(dec.provided_capabilities) if dec.provided_capabilities else set()\n"
        "assert set(mut) <= prov, (mut, prov)\n"
        "assert dec.failure_class == '', dec.failure_class\n"
        "print('INVARIANT_SMOKE_OK')\n"
    ).replace("ST", repr(state))
    result = subprocess.run([sys.executable, "-c", code], capture_output=True,
                            text=True, env={**ENV, "PYTHONPATH": env_path,
                                            "PYTHONDONTWRITEBYTECODE": "1"})
    assert result.returncode == 0, result.stderr[-2000:]
    assert "CLASSIFY_SMOKE_OK" in result.stdout, result.stdout
    assert "SEPARATION_SMOKE_OK" in result.stdout, result.stdout
    assert "INVARIANT_SMOKE_OK" in result.stdout, result.stdout


ENV = {**{k: v for k, v in __import__("os").environ.items()
          if k != "PYTHONPATH"}, "PYTHONDONTWRITEBYTECODE": "1"}


def main():
    print("P2P-MUTATION-SAFETY-INTEGRATION-01 (.41) FRESH-TREE VERIFICATION")
    check_extract()
    check_doctor()
    check_presence()
    check_smoke()
    print("ALL FRESH-TREE CHECKS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
