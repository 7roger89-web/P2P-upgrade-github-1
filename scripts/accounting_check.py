#!/usr/bin/env python3
"""Mutually exclusive accounting of all candidate members.

Every member must land in EXACTLY one disjoint class:
  exact_tree_match        : member path == tree path (byte comparison vs HEAD tree)
  runtime_remap           : member under runtime/ whose file lives in the tree
                            under .p2p/system/<remapped> (documented remap)
  legacy_stable_absent    : runtime/ legacy UI/UX modules stable, absent from tree
  mint_generated          : the 7 regenerated integrity files
  self_ref_mint           : RELEASE-SHA256SUMS.txt, release-manifest.json
Any member not landing in one class = UNACCOUNTED.
"""
import hashlib
import json
import subprocess
import zipfile

ROOT = "/home/ubuntu/fw01_work/auth-f01"
CANDIDATE = ROOT + "/reports/candidates/P2P-8.4.7-C-codex.24-fw01-self-contained-patch-candidate-v2.zip"
REV = "HEAD"

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

def git_cat(rel):
    r = subprocess.run(["git", "show", f"{REV}:{rel}"], capture_output=True, cwd=ROOT)
    if r.returncode != 0:
        return None
    return r.stdout

Z = zipfile.ZipFile(CANDIDATE)
members = sorted(Z.namelist())
print("UNIQUE_CANDIDATE_MEMBERS =", len(members))

MINT_GENERATED = {
    "governance/drift-policy.json",
    "governance/live-specs.lock.json",
    "governance/runtime-manifest.lock.json",
    "manifest/external-sources.json",
    "manifest/source-inventory.json",
    "governance/release-evidence/technical-preview.json",
    "governance/supplemental-checksums.json",
}
SELF_REF = {"RELEASE-SHA256SUMS.txt", "release-manifest.json"}
LEGACY_ABSENT = {
    "runtime/scripts/p2p_uiux_doctor.py",
    "runtime/scripts/p2p_uiux_drift_check.py",
    "runtime/scripts/p2p_uiux_eval_impl.py",
    "runtime/scripts/p2p_uiux_governance.py",
    "runtime/scripts/p2p_uiux_secret_scan.py",
}
RUNTIME_REMAP_PREFIXES = {  # tree path prefix for runtime modules (.p2p/system/)
    ".p2p/system/": None,
}

def tree_path_for_runtime(member):
    # documented remap: runtime/<x> -> .p2p/system/<x>
    return ".p2p/system/" + member[len("runtime/"):]

counts = {k: 0 for k in ["exact_tree_match", "runtime_remap", "legacy_stable_absent",
                          "mint_generated", "self_ref_mint", "runtime_stable_remap",
                          "UNACCOUNTED"]}
detail = {k: [] for k in counts}

unaccounted = []
for m in members:
    if m in SELF_REF:
        counts["self_ref_mint"] += 1; detail["self_ref_mint"].append(m); continue
    if m in MINT_GENERATED:
        counts["mint_generated"] += 1; detail["mint_generated"].append(m); continue
    if m in LEGACY_ABSENT:
        counts["legacy_stable_absent"] += 1; detail["legacy_stable_absent"].append(m); continue
    zb = Z.read(m)
    if m.startswith("runtime/"):
        tp = tree_path_for_runtime(m)
        tb = git_cat(tp)
        if tb is not None and tb == zb:
            counts["runtime_remap"] += 1; detail["runtime_remap"].append(m); continue
        counts["UNACCOUNTED"] += 1; unaccounted.append((m, "runtime-remap-no-match")); continue
    # any other path: direct tree comparison
    tb = git_cat(m)
    if tb is not None and tb == zb:
        counts["exact_tree_match"] += 1; detail["exact_tree_match"].append(m); continue
    # maybe a runtime remap of a non-runtime member? (not by design)
    counts["UNACCOUNTED"] += 1; unaccounted.append((m, "no-match"))

print("=== ACCOUNTING ===")
for k, v in counts.items():
    print(f"{k}: {v}")
print("sum:", sum(counts.values()))
print("UNACCOUNTED_MEMBERS =", counts["UNACCOUNTED"])
print("true UNBOUND (self_ref) =", counts["self_ref_mint"])
print("=== unaccounted sample ===")
for m, why in unaccounted[:15]:
    print(" ", why, m)

# independent unique-union check
union = (set(detail["exact_tree_match"]) | set(detail["runtime_remap"]) |
         set(detail["legacy_stable_absent"]) | set(detail["mint_generated"]) |
         set(detail["self_ref_mint"]))
print("ACCOUNTED_UNIQUE_MEMBERS =", len(union))
print("ACCOUNTED_UNION_EQUALS_MEMBERS =", len(union) == len(members))
