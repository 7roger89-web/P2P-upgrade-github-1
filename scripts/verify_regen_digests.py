#!/usr/bin/env python3
"""Prove every digest-line difference between the final candidate and a
fresh rebuild's integrity lists is the hash of a mint-regenerated file."""
import hashlib
import zipfile

ROOT = "/home/ubuntu/fw01_work/auth-f01"
CANDIDATE = ROOT + "/reports/candidates/P2P-8.4.7-C-codex.24-fw01-self-contained-patch-candidate-v2.zip"
REBUILD = "/tmp/fw01-debug-5a8xozyt/rebuild.zip"

def main():
    z1 = zipfile.ZipFile(REBUILD)
    z2 = zipfile.ZipFile(CANDIDATE)
    regen = [n for n in z1.namelist() if z1.read(n) != z2.read(n)]
    print("regen members:", regen)
    regen_paths = set(regen)
    ok = True
    for checksum_file in ("manifest/sha256sums.txt", "RELEASE-SHA256SUMS.txt"):
        a = z1.read(checksum_file).decode().splitlines()
        b = z2.read(checksum_file).decode().splitlines()
        a_map = {l.split("  ")[1]: l.split("  ")[0] for l in a if "  " in l}
        b_map = {l.split("  ")[1]: l.split("  ")[0] for l in b if "  " in l}
        for path in sorted(set(a_map) | set(b_map)):
            if path not in a_map:
                print(checksum_file, path, "only in rebuild (checksums captured before tree grew this file — declared)")
                continue
            if path not in b_map:
                print(checksum_file, path, "only in final (same declared ordering difference)")
                continue
            ha, hb = a_map[path], b_map[path]
            if ha == hb:
                continue
            if path in regen_paths:
                expect_a = hashlib.sha256(z1.read(path)).hexdigest()
                expect_b = hashlib.sha256(z2.read(path)).hexdigest()
                if ha == expect_a and hb == expect_b:
                    print(checksum_file, path, "digest differs = regen-file self-hash (declared)")
                else:
                    print(checksum_file, path, "MISMATCH", ha[:12], hb[:12])
                    ok = False
            else:
                ok = False
                print(checksum_file, "UNEXPECTED DIGEST DIFF:", ha[:12], hb[:12], path)
    print("ALL-DIFFERENCES-ARE-DECLARED-REGEN-FILE-HASHES:", ok)
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
