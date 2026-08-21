import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TEMP_ROOT = REPO / ".tmp"
TEMP_ROOT.mkdir(parents=True, exist_ok=True)
TEST_ROOT = TEMP_ROOT / "planner-dynamic"

def setup_fixture(baseline_version, baseline_sha, promotion_status="PROMOTED_VERIFIED"):
    if os.path.exists(TEST_ROOT):
        shutil.rmtree(TEST_ROOT)
    os.makedirs(TEST_ROOT / "governance", exist_ok=True)
    os.makedirs(TEST_ROOT / "docs/p2p-development/capability-ledger", exist_ok=True)
    os.makedirs(TEST_ROOT / "scripts", exist_ok=True)
    
    # Copy planner
    shutil.copy(REPO / "scripts/p2p_roadmap_planner.py", TEST_ROOT / "scripts/")
    
    # Create development-control.json
    dctl = {
        "official_baseline": {
            "version": baseline_version,
            "artifact_sha256": baseline_sha,
            "promotion_status": promotion_status
        },
        "roadmap": {"items": []}
    }
    if baseline_version is None:
        del dctl["official_baseline"]
        
    with open(TEST_ROOT / "governance/development-control.json", "w", encoding="utf-8") as f:
        json.dump(dctl, f)
        
    # Create minimal roadmap
    roadmap = {"items": []}
    with open(TEST_ROOT / "governance/p2p-development-roadmap.json", "w", encoding="utf-8") as f:
        json.dump(roadmap, f)
        
    # Create minimal ledger
    ledger = {"records": []}
    with open(TEST_ROOT / "governance/research-adoption-ledger.json", "w", encoding="utf-8") as f:
        json.dump(ledger, f)
        
    # Create minimal capability index
    cap = {"capabilities": []}
    with open(TEST_ROOT / "docs/p2p-development/capability-ledger/capability-index.json", "w", encoding="utf-8") as f:
        json.dump(cap, f)

def run_planner():
    cmd = [sys.executable, "-X", "utf8", str(TEST_ROOT / "scripts/p2p_roadmap_planner.py"), "--repo", str(TEST_ROOT)]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return result.returncode, result.stdout, result.stderr

def test_dynamic_acceptance():
    print("Test A: Canonical .19 acceptance...")
    setup_fixture("8.4.7-C-codex.19", "3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8")
    code, out, err = run_planner()
    assert code == 0, f"Expected success, got {code}. Err: {err}"
    print("  PASS")

    print("Test B: Future .72 fixture acceptance...")
    setup_fixture("8.4.7-C-codex.72", "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890")
    code, out, err = run_planner()
    assert code == 0, f"Expected success, got {code}. Err: {err}"
    print("  PASS")

    print("Test D: Missing official baseline fail-closed...")
    setup_fixture(None, None)
    code, out, err = run_planner()
    assert code != 0, "Expected failure for missing baseline"
    assert "BASELINE IDENTITY MISSING" in (out + (err or ""))
    print("  PASS")

    print("Test E: Unpromoted record fail-closed...")
    setup_fixture("8.4.7-C-codex.72", "hash", "UNPROMOTED")
    code, out, err = run_planner()
    assert code != 0, "Expected failure for unpromoted baseline"
    assert "BASELINE PROMOTION INVALID" in (out + (err or ""))
    print("  PASS")

if __name__ == "__main__":
    try:
        test_dynamic_acceptance()
        print("\nALL DYNAMIC PLANNER TESTS PASSED")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        os._exit(1)
