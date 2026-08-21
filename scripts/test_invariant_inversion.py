#!/usr/bin/env python3
import sys
from pathlib import Path

# Add runtime to path
sys.path.append("/tmp/p2p-promo01/runtime/p2p_capabilities")
from project_context import ProjectContextBootstrap, ProjectContextError

def test_invariant_inversion():
    print("--- Test 1: Ready Check (Uninitialized) ---")
    root = Path("/tmp/p2p_fixture_inversion")
    if root.exists():
        import shutil
        shutil.rmtree(root)
    root.mkdir(parents=True)
    
    bootstrap = ProjectContextBootstrap(root)
    print(f"Is Ready (Expected False): {bootstrap.is_ready()}")
    
    print("\n--- Test 2: Invariant Inversion (Bootstrap Block) ---")
    try:
        bootstrap.bootstrap_task_context({"purpose": "Test"})
        print("FAIL: Allowed bootstrap without project pin")
    except ProjectContextError as e:
        print(f"PASS: Caught expected error: {e}")

    print("\n--- Test 3: Ready Check (Initialized) ---")
    # Simulate a verified installation
    p2p_dir = root / ".p2p"
    p2p_dir.mkdir()
    import json
    pin = {
        "verification_status": "VERIFIED",
        "doctor_result": "HEALTHY",
        "p2p_artifact_sha256": "dummy_sha"
    }
    with open(p2p_dir / "project-pin.json", "w") as f:
        json.dump(pin, f)
        
    print(f"Is Ready (Expected True): {bootstrap.is_ready()}")
    
    print("\n--- Test 4: Successful Bootstrap ---")
    try:
        res = bootstrap.bootstrap_task_context({"purpose": "Test Task"})
        print(f"PASS: Context plan schema: {res['context_plan']['schema']}")
        print(f"PASS: Ready event schema: {res['ready_event']['schema']}")
    except Exception as e:
        print(f"FAIL: Bootstrap failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_invariant_inversion()
