import os
import sys
from pathlib import Path
import json
import shutil
import hashlib

# Setup paths
capabilities_path = "/tmp/p2p-promo01/runtime/p2p_capabilities"
sys.path.insert(0, capabilities_path)

from project_context import enforce_map_before_work, ProjectContextError, ProjectContextBootstrap

def setup_fixture(path: Path):
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    p2p_dir = path / ".p2p"
    p2p_dir.mkdir()
    
    pin = {
        "project_name": "Test Project",
        "verification_status": "VERIFIED",
        "doctor_result": "HEALTHY",
        "p2p_artifact_sha256": "dummy"
    }
    with open(p2p_dir / "project-pin.json", "w") as f:
        json.dump(pin, f)
    
    with open(path / "file1.txt", "w") as f:
        f.write("hello")
    
    from project_map import ProjectMapBuilder
    builder = ProjectMapBuilder(str(path))
    pmap = builder.build_full_map()
    return pmap

def run_test():
    fixture_path = Path("/tmp/p2p_gate_fixture_debug")
    setup_fixture(fixture_path)
    
    print("Scenario 2: Stale Map (Modified File) + Mutation Intent")
    # MODIFICATION should be detected
    with open(fixture_path / "file1.txt", "w") as f:
        f.write("modified")
    
    try:
        enforce_map_before_work(fixture_path, mutation_intent=True)
        print("Result: FAIL (Allowed unexpectedly)")
    except ProjectContextError as e:
        print(f"Result: PASS (Blocked: {e})")

    print("\nScenario 4: Stale Map (New File) + Mutation Intent")
    # NEW FILE detection depends on check_freshness implementation
    # Current check_freshness ONLY checks existing files in the map
    with open(fixture_path / "file2.txt", "w") as f:
        f.write("new file")
        
    bootstrap = ProjectContextBootstrap(fixture_path)
    pmap = bootstrap.get_project_map()
    freshness = pmap.check_freshness(str(fixture_path))
    print(f"Freshness Status for New File: {freshness['status']}")

if __name__ == '__main__':
    run_test()
