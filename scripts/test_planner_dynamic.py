import json
import os
import shutil
import subprocess

REPO = "/home/ubuntu/fw01_work/auth-f01"
TEST_ROOT = "/tmp/p2p_planner_test"

def setup_fixture(baseline_version, baseline_sha, promotion_status="PROMOTED_VERIFIED"):
    if os.path.exists(TEST_ROOT):
        shutil.rmtree(TEST_ROOT)
    os.makedirs(os.path.join(TEST_ROOT, "governance"), exist_ok=True)
    os.makedirs(os.path.join(TEST_ROOT, "docs/p2p-development/capability-ledger"), exist_ok=True)
    os.makedirs(os.path.join(TEST_ROOT, "scripts"), exist_ok=True)
    
    # Copy planner
    shutil.copy(os.path.join(REPO, "scripts/p2p_roadmap_planner.py"), os.path.join(TEST_ROOT, "scripts/"))
    
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
        
    with open(os.path.join(TEST_ROOT, "governance/development-control.json"), "w") as f:
        json.dump(dctl, f)
        
    # Create minimal roadmap
    roadmap = {"items": []}
    with open(os.path.join(TEST_ROOT, "governance/p2p-development-roadmap.json"), "w") as f:
        json.dump(roadmap, f)
        
    # Create minimal ledger
    ledger = {"records": []}
    with open(os.path.join(TEST_ROOT, "governance/research-adoption-ledger.json"), "w") as f:
        json.dump(ledger, f)
        
    # Create minimal capability index
    cap = {"capabilities": []}
    with open(os.path.join(TEST_ROOT, "docs/p2p-development/capability-ledger/capability-index.json"), "w") as f:
        json.dump(cap, f)

def run_planner():
    cmd = ["python3", os.path.join(TEST_ROOT, "scripts/p2p_roadmap_planner.py"), "--repo", TEST_ROOT]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def test_dynamic_acceptance():
    print("Test A: Official .46 acceptance...")
    setup_fixture("8.4.7-C-codex.46", "2901adca106d3533b3df37e1d10d8a375162b64b001c32bec28b4b178c2f3bb7")
    code, out, err = run_planner()
    assert code == 0, f"Expected success, got {code}. Err: {err}"
    print("  PASS")

    print("Test B: Future .47 fixture acceptance...")
    setup_fixture("8.4.7-C-codex.47", "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890")
    code, out, err = run_planner()
    assert code == 0, f"Expected success, got {code}. Err: {err}"
    print("  PASS")

    print("Test D: Missing official baseline fail-closed...")
    setup_fixture(None, None)
    code, out, err = run_planner()
    assert code != 0, "Expected failure for missing baseline"
    assert "BASELINE IDENTITY MISSING" in err
    print("  PASS")

    print("Test E: Unpromoted record fail-closed...")
    setup_fixture("8.4.7-C-codex.48", "hash", "UNPROMOTED")
    code, out, err = run_planner()
    assert code != 0, "Expected failure for unpromoted baseline"
    assert "BASELINE PROMOTION INVALID" in err
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
