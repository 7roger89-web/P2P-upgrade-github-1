"""Test for Map-Before-Work Gate Runtime Enforcement (§9)."""
import os
import sys
from pathlib import Path
import json
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
capabilities_path = ROOT / ".p2p" / "system" / "p2p_capabilities"
system_path = capabilities_path.parent
sys.path.insert(0, str(system_path))

from p2p_capabilities.project_context import enforce_map_before_work, ProjectContextError, ProjectContextBootstrap

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
    tmp_root = ROOT / ".tmp"
    tmp_root.mkdir(parents=True, exist_ok=True)
    fixture_path = Path(tempfile.mkdtemp(prefix="map-gate-", dir=str(tmp_root)))
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

    print("\nScenario 4: Ready Context + Missing Map")
    missing_fixture = Path(tempfile.mkdtemp(prefix="map-gate-missing-", dir=str(tmp_root)))
    (missing_fixture / ".p2p").mkdir(parents=True, exist_ok=True)
    with open(missing_fixture / ".p2p" / "project-pin.json", "w", encoding="utf-8") as handle:
        json.dump({"verification_status": "VERIFIED", "doctor_result": "HEALTHY"}, handle)
    try:
        enforce_map_before_work(missing_fixture, mutation_intent=True)
        print("Result: FAIL (Allowed unexpectedly)")
    except ProjectContextError as e:
        print(f"Result: PASS (Blocked: {e})")

    print("\nScenario 5: Context Ready + Permission Denied")
    try:
        enforce_map_before_work(fixture_path, mutation_intent=True, permission_granted=False)
        print("Result: FAIL (Allowed unexpectedly)")
    except ProjectContextError as e:
        print(f"Result: PASS (Blocked: {e})")

    print("\nScenario 3: No Project Context")
    bad_fixture = Path(tempfile.mkdtemp(prefix="map-gate-no-context-", dir=str(tmp_root)))
    if bad_fixture.exists(): shutil.rmtree(bad_fixture)
    bad_fixture.mkdir()
    try:
        enforce_map_before_work(bad_fixture, mutation_intent=True)
        print("Result: FAIL (Allowed unexpectedly)")
    except ProjectContextError as e:
        print(f"Result: PASS (Blocked: {e})")

if __name__ == "__main__":
    run_test()
