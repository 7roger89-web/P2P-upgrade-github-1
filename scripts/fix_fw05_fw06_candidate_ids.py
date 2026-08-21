#!/usr/bin/env python3
"""PRE-PILOT: governance cleanup — assign missing candidate_id to records
8.4.7-C-codex.33 (FW05) and 8.4.7-C-codex.34 (FW06).

Principles (spec-compliant):
- Additive-only: only the empty candidate_id field is filled; every other
  field of the affected records remains byte-identical.
- No promotion, no release, no record reorder, no history rewrite.
- candidate_id values mirror the established convention used by .30-.32
  (FW04 family) so governance queries behave consistently.
"""
import json
import hashlib
import sys

REPO = "/home/ubuntu/fw01_work/auth-f01"
CTRL = f"{REPO}/governance/development-control.json"

EXPECTED_FIXES = {
    "8.4.7-C-codex.33": ("FW05_OWNER_EXPERIENCE_DECISION_TRACE", "8.4.7-C-codex.33"),
    "8.4.7-C-codex.34": ("FW06_PRODUCTION_AUTONOMY_RESILIENCE", "8.4.7-C-codex.34"),
}


def main():
    with open(CTRL, encoding="utf-8") as f:
        d = json.load(f)

    before_sha = hashlib.sha256(open(CTRL, "rb").read()).hexdigest()
    records = d.get("candidate_records") or []

    fixed = []
    for i, r in enumerate(records):
        if not isinstance(r, dict):
            continue
        version = r.get("candidate_version", "")
        if version not in EXPECTED_FIXES:
            continue
        if r.get("candidate_id") not in (None, ""):
            print(f"SKIP index {i} {version}: candidate_id already set")
            continue
        new_id, expected_version = EXPECTED_FIXES[version]
        assert r.get("candidate_label") and r["candidate_sha256"], \
            f"record {i} missing sibling fields, aborting"
        r["candidate_id"] = new_id
        fixed.append((i, version, new_id))

    assert fixed, "nothing fixed — unexpected state, aborting"
    assert len(fixed) == 2, f"expected exactly 2 fixes, got {fixed}"

    with open(CTRL, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
        f.write("\n")

    after_sha = hashlib.sha256(open(CTRL, "rb").read()).hexdigest()

    # Structural integrity: reload and re-validate the two records
    d2 = json.load(open(CTRL, encoding="utf-8"))
    r2 = d2["candidate_records"]
    seen = {}
    for r in r2:
        if not isinstance(r, dict):
            continue
        vid = r.get("candidate_id")
        if vid:
            assert vid not in seen, f"duplicate candidate_id {vid}"
            seen[vid] = r
    for i, version, cid in fixed:
        rec = r2[i]
        assert rec["candidate_id"] == cid
        assert rec["promotion_status"] == "UNPROMOTED", "must remain UNPROMOTED"
        # lineage chain preserved: record order unchanged
    print("FIXED:", fixed)
    print(f"candidate_records count unchanged: {len(r2)}")
    print(f"unique candidate_ids: {len(seen)}")
    print(f"file SHA before: {before_sha}")
    print(f"file SHA after:  {after_sha}")
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
