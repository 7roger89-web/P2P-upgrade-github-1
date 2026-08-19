#!/usr/bin/env python3
"""Build fresh candidate from temp copy, keep the zip, and print the raw
diffs of the three remaining varying files."""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = "/home/ubuntu/fw01_work/auth-f01"
CANDIDATE = ROOT + "/reports/candidates/P2P-8.4.7-C-codex.24-fw01-self-contained-patch-candidate-v2.zip"

def main():
    tmpdir = tempfile.mkdtemp(prefix="fw01-debug-")
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
    print("=== manifest/sha256sums.txt ===")
    a = z1.read("manifest/sha256sums.txt").decode().splitlines()
    b = z2.read("manifest/sha256sums.txt").decode().splitlines()
    import difflib
    shown = 0
    for d in difflib.unified_diff(b, a, lineterm="", n=0):
        if d.startswith(("+", "-")):
            print(d[:150])
            shown += 1
        if shown > 20:
            print("...(truncated)")
            break
    print("=== runtime lock protected_files diff count ===")
    la = json.load(z1.open("governance/runtime-manifest.lock.json"))
    lb = json.load(z2.open("governance/runtime-manifest.lock.json"))
    pa, pb = la["protected_files"], lb["protected_files"]
    diffs = 0
    for k in set(pa) | set(pb):
        if pa.get(k) != pb.get(k):
            diffs += 1
            if diffs <= 3:
                print(k, "| orig:", str(pb.get(k))[:50], "| rebuild:", str(pa.get(k))[:50])
    print("entry diffs:", diffs, "of", len(set(pa) | set(pb)))
    # virtual_hashes
    print("virtual_hashes diff:", la.get("virtual_hashes") != lb.get("virtual_hashes"))
    print("reason:", lb.get("reason"), "->", la.get("reason"))
    print("tmpdir kept:", tmpdir)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
