"""Test for Map-Before-Work Gate Runtime Enforcement (§9)."""
import os
import sys
from pathlib import Path
import json
import shutil

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
    (p2p_dir / "context").mkdir()
    
    # Healthy Pin
    pin = {
        "project_name": "Test Project",
        "verification_status": "VERIFIED",
        "doctor_result": "HEALTHY",
        "p2p_artifact_sha256": "dummy"
    }
    with open(p2p_dir / "project-pin.json", "w") as f:
        json.dump(pin, f)
    
    # Create a dummy file for mapping
    with open(path / "file1.txt", "w") as f:
        f.write("hello")
    
    # Bootstrap context which creates and saves the map
    bootstrap = ProjectContextBootstrap(path)
    pmap = bootstrap.get_project_map()
    bootstrap.save_project_map()
    return pmap

def run_test():
    fixture_path = Path("/tmp/p2p_gate_fixture")
    setup_fixture(fixture_path)
    
    print("Scenario 1: Fresh Map + Mutation Intent")
    try:
        enforce_map_before_work(fixture_path, mutation_intent=True)
        print("Result: PASS (Allowed)")
    except ProjectContextError as e:
        print(f"Result: FAIL ({e})")

    print("\nScenario 2: Stale Map + Mutation Intent")
    # Induce drift by adding a file not in the saved map
    with open(fixture_path / "file2.txt", "w") as f:
        f.write("drift")
    
    try:
        enforce_map_before_work(fixture_path, mutation_intent=True)
        print("Result: FAIL (Allowed unexpectedly)")
    except ProjectContextError as e:
        print(f"Result: PASS (Blocked: {e})")

    print("\nScenario 3: No Project Context")
    bad_fixture = Path("/tmp/p2p_no_context")
    if bad_fixture.exists(): shutil.rmtree(bad_fixture)
    bad_fixture.mkdir()
    try:
        enforce_map_before_work(bad_fixture, mutation_intent=True)
        print("Result: FAIL (Allowed unexpectedly)")
    except ProjectContextError as e:
        print(f"Result: PASS (Blocked: {e})")

if __name__ == "__main__":
    run_test()
