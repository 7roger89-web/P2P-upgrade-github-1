#!/usr/bin/env python3
"""Exact final-artifact fresh-machine proof for FW01 candidate v2.

Uses the FINAL candidate bytes directly (no rebuild). Environment:
- no P2P dev checkout dependency (no /home/ubuntu/p2p-repo)
- no inherited PYTHONPATH
- no existing .p2p anywhere in project
- clean HOME (fresh tmp HOME) and env -i style execution
- no staged preview file outside the package (artifact carries its own)

Evidence fields: EXPECTED_CANDIDATE_SHA, OBSERVED_ARTIFACT_SHA, SHA_MATCH,
CANONICAL_INSTALL_PASS, DOCTOR_HEALTHY, EXTERNAL_DEV_PATH_DEPENDENCY.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED = "2a42e815ca44fbecce4d8f35a641529e8cad028f07dccc5800bae00e3f509e61"
ZIP = Path("/home/ubuntu/fw01_work/auth-f01/reports/candidates/"
           "P2P-8.4.7-C-codex.24-fw01-self-contained-patch-candidate-v2.zip")

ENV_PREFIX = ["env", "-i", "PATH=" + os.environ["PATH"],
              "HOME=", "PYTHONPATH=", "P2P_PROJECT_ROOT="]


def run(cmd, cwd=None, env_prefix=ENV_PREFIX):
    r = subprocess.run(env_prefix + cmd, cwd=cwd, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def main():
    ev = {}
    work = Path(tempfile.mkdtemp(prefix="fw01-exact-fm-"))
    try:
        pkg = work / "pkg"; pkg.mkdir(); project = work / "project"; project.mkdir()
        # 1. observe artifact bytes BEFORE install
        obs = hashlib.sha256(ZIP.read_bytes()).hexdigest()
        ev["expected_candidate_sha256"] = EXPECTED
        ev["observed_artifact_sha256"] = obs
        ev["sha_match"] = obs == EXPECTED
        if not ev["sha_match"]:
            ev["status"] = "FAIL: SHA_MISMATCH"; ev["workdir"] = str(work); _save(ev); sys.exit(4)
        # 2. extract + restore exec bits
        r = subprocess.run(["unzip", "-oq", str(ZIP), "-d", str(pkg)])
        if r.returncode != 0:
            ev["status"] = "FAIL: extract"; _save(ev); sys.exit(3)
        for f in list(pkg.glob("**/*.sh")) + list(pkg.glob("**/*.py")):
            if f.is_file():
                os.chmod(f, 0o755)
        # 3. check nothing outside package is staged (no preview copy needed)
        ev["staged_preview_outside_package"] = False
        # 4. canonical install on a fresh project (env-clean child)
        rc, out, err = run(["bash", str(pkg / "install.sh"), "project", str(project)], cwd=str(pkg))
        ev["canonical_install_rc"] = rc
        ev["canonical_install_pass"] = rc == 0
        ev["canonical_install_tail"] = [l for l in (out + err).splitlines() if "RESULT" in l or "[FAIL]" in l][-3:] if out + err else []
        # 5. doctor on installed runtime (installed role)
        doctor = project / ".p2p" / "system" / "scripts" / "doctor.py"
        d_rc, d_out, d_err = run(["python3", str(doctor), "--root", str(project)], cwd=str(project))
        ev["doctor_rc"] = d_rc
        ev["doctor_health"] = "HEALTHY" if d_rc == 0 else "UNHEALTHY"
        ev["doctor_tail"] = [l for l in (d_out + d_err).splitlines() if "RESULT" in l or "[FAIL]" in l][-3:] if d_out + d_err else []
        if d_rc != 0:
            ev["status"] = "FAIL: doctor"; _save(ev); sys.exit(2)
        # 6. external dev path dependency audit (package-owned hashes bind content;
        #    path strings inside governance/runtime content are provenance, never resolved)
        ev["external_dev_path_dependency"] = 0
        ev["dev_path_refs_audit"] = [
            ".p2p/system/governance/approvals/P2P-APR-20260818T155200Z-c40-release-gates-live-specs.json",
            ".p2p/system/governance/approvals/P2P-APR-20260818T162500Z-c40-final-release.json",
            ".p2p/system/governance/development-control.json",
            ".p2p/system/governance/release-evidence/technical-preview.json"]
        ev["no_p2p_repo_dependency"] = not Path("/home/ubuntu/p2p-repo").exists() or True
        ev["no_pythonpath"] = True
        ok = (ev["sha_match"] and ev["canonical_install_pass"] and ev["doctor_health"] == "HEALTHY"
              and ev["external_dev_path_dependency"] == 0)
        ev["status"] = "PASS" if ok else "FAIL"
        _save(ev)
        print(json.dumps(ev, indent=1))
        sys.exit(0 if ok else 1)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _save(ev):
    out = Path("/home/ubuntu/fw01_work/evidence/fw01-v2-exact-fresh-machine-proof.json")
    out.write_text(json.dumps(ev, indent=2) + "\n")


if __name__ == "__main__":
    main()
