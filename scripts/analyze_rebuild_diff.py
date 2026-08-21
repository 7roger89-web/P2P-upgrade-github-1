#!/usr/bin/env python3
"""Build a fresh candidate from a temp copy of the final tree and compare
structurally against the final candidate v2 to classify the variance."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = "/home/ubuntu/fw01_work/auth-f01"
CANDIDATE = ROOT + "/reports/candidates/P2P-8.4.7-C-codex.24-fw01-self-contained-patch-candidate-v2.zip"

def main():
    tmpdir = tempfile.mkdtemp(prefix="fw01-rebuild-analysis-")
    build_root = tmpdir + "/tree"
    shutil.copytree(ROOT, build_root)
    zip_out = tmpdir + "/rebuild.zip"
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    r = subprocess.run(
        [sys.executable, build_root + "/scripts/package_release.py",
         "--root", build_root, "--output", zip_out, "build"],
        capture_output=True, text=True, cwd=build_root, env=env)
    if r.returncode != 0:
        print("BUILD FAILED:", (r.stdout + r.stderr)[-300:])
        shutil.rmtree(tmpdir, ignore_errors=True)
        return 2
    z1 = zipfile.ZipFile(zip_out)
    z2 = zipfile.ZipFile(CANDIDATE)
    report = {}
    for name in ["release-manifest.json", "governance/runtime-manifest.lock.json",
                 "manifest/sha256sums.txt"]:
        a, b = z1.read(name).decode("utf-8"), z2.read(name).decode("utf-8")
        report[name] = {"byte_identical": a == b}
    d1 = json.loads(z1.read("release-manifest.json"))
    d2 = json.loads(z2.read("release-manifest.json"))
    d1n = {k: ([{"path": f["path"]} for f in v] if k == "files" else v)
           for k, v in d1.items() if k not in ("generated_at",)}
    d2n = {k: ([{"path": f["path"]} for f in v] if k == "files" else v)
           for k, v in d2.items() if k not in ("generated_at",)}
    report["release-manifest.json"]["structurally_identical_minus_digests"] = (
        json.dumps(d1n, sort_keys=True) == json.dumps(d2n, sort_keys=True))
    l1 = json.loads(z1.read("governance/runtime-manifest.lock.json"))
    l2 = json.loads(z2.read("governance/runtime-manifest.lock.json"))
    l1n = {k: v for k, v in l1.items()
           if k not in ("protected_files", "virtual_hashes", "generated_at", "reason")}
    l2n = {k: v for k, v in l2.items()
           if k not in ("protected_files", "virtual_hashes", "generated_at", "reason")}
    report["governance/runtime-manifest.lock.json"]["structurally_identical_minus_hashes"] = (
        json.dumps(l1n, sort_keys=True) == json.dumps(l2n, sort_keys=True))
    report["governance/runtime-manifest.lock.json"]["protected_files_count"] = {
        "original": len(l2["protected_files"]), "rebuild": len(l1["protected_files"])}
    k1, k2 = set(l1["protected_files"]), set(l2["protected_files"])
    report["governance/runtime-manifest.lock.json"]["protected_files_keys_diff"] = sorted(k1 ^ k2)[:10]
    # release-manifest: structural comparison without per-file digests
    d1 = json.loads(z1.read("release-manifest.json"))
    d2 = json.loads(z2.read("release-manifest.json"))
    d1n = {k: ([{"path": f["path"]} for f in v] if k == "files" else v)
           for k, v in d1.items() if k not in ("generated_at",)}
    d2n = {k: ([{"path": f["path"]} for f in v] if k == "files" else v)
           for k, v in d2.items() if k not in ("generated_at",)}

    # sha256sums: compare sets of (path) minus self-referencing digest lines
    import re
    skip = re.compile(r"^[0-9a-f]{64}\s+(RELEASE-SHA256SUMS|sha256sums|release-manifest)\.(txt|json)")
    a_lines = [re.sub(r"^[0-9a-f]{64}\s", "DIGEST ", l)
               for l in z1.read("manifest/sha256sums.txt").decode("utf-8").splitlines()
               if not skip.match(l)]
    b_lines = [re.sub(r"^[0-9a-f]{64}\s", "DIGEST ", l)
               for l in z2.read("manifest/sha256sums.txt").decode("utf-8").splitlines()
               if not skip.match(l)]
    report["manifest/sha256sums.txt"]["normalized_identical"] = a_lines == b_lines
    print(json.dumps(report, ensure_ascii=False, indent=2))
    shutil.rmtree(tmpdir, ignore_errors=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
