import os
import shutil
import sys
import time
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / ".p2p" / "system"))

from p2p_capabilities.project_context import ProjectContextBootstrap, enforce_map_before_work, ProjectContextError
from p2p_capabilities.project_map import ProjectMap
from p2p_capabilities import project_pin
from test_project_pin_lifecycle import ARTIFACT_SHA, VERSION, _metadata

_TEMP_ROOT = ROOT / ".tmp"
_TEMP_ROOT.mkdir(parents=True, exist_ok=True)
TEST_ROOT = Path(tempfile.mkdtemp(prefix="map-freshness-", dir=str(_TEMP_ROOT)))

def setup_project():
    if TEST_ROOT.exists():
        shutil.rmtree(TEST_ROOT)
    TEST_ROOT.mkdir(parents=True)
    (TEST_ROOT / "src").mkdir()
    with open(TEST_ROOT / "src/main.py", "w") as f:
        f.write("print('hello')")
    
    # Fake a healthy pin
    p2p_dir = TEST_ROOT / ".p2p"
    p2p_dir.mkdir()
    system = p2p_dir / "system"
    system.mkdir()
    _metadata(system)
    (system / "release.json").write_text('{"package_version": "' + VERSION + '", "artifact_sha256": "' + ARTIFACT_SHA + '"}', encoding="utf-8")
    project_pin.write_pin(TEST_ROOT, project_pin.build_pin(
        project_root=TEST_ROOT,
        metadata_root=system,
        artifact_sha256=ARTIFACT_SHA,
        installation_mode="PACKAGED_PROJECT",
        rollback_source=".p2p/install-backups/test",
        managed_files=["VERSION"],
    ))

def test_freshness_flow():
    setup_project()
    
    print("Step 1: Initial Map Generation...")
    # We use a bootstrap instance to generate the initial map
    bootstrap = ProjectContextBootstrap(TEST_ROOT)
    pmap = bootstrap.get_project_map()
    bootstrap.save_project_map(pmap)
    print(f"  Initial Identity: {pmap.identity()}")
    freshness_info = pmap.check_freshness(str(TEST_ROOT))
    print(f"  Initial Freshness: {freshness_info['status']}")
    
    print("\nStep 2: Verify Mutation Allowed when Fresh...")
    try:
        # enforce_map_before_work creates its own bootstrap instance
        enforce_map_before_work(TEST_ROOT, mutation_intent=True)
        print("  PASS: Mutation allowed")
    except ProjectContextError as e:
        print(f"  FAIL: Mutation blocked: {e}")
        assert False
        
    print("\nStep 3: Simulate Drift (Modify file)...")
    # Small delay to ensure mtime change if filesystem resolution is low
    time.sleep(0.1)
    with open(TEST_ROOT / "src/main.py", "w") as f:
        f.write("print('modified content')")
    system = TEST_ROOT / ".p2p" / "system"
    project_pin.write_pin(TEST_ROOT, project_pin.build_pin(
        project_root=TEST_ROOT,
        metadata_root=system,
        artifact_sha256=ARTIFACT_SHA,
        installation_mode="PACKAGED_PROJECT",
        rollback_source=".p2p/install-backups/test",
        managed_files=["VERSION"],
    ))
    
    # Check freshness using the original map object
    freshness_info = pmap.check_freshness(str(TEST_ROOT))
    print(f"  Freshness after drift: {freshness_info['status']}")
    print(f"  Drift details: {freshness_info.get('drift')}")
    assert freshness_info['status'] == "STALE"
    
    print("\nStep 4: Verify Mutation Blocked when Stale...")
    try:
        # enforce_map_before_work should detect the STALE map
        # Note: In our current implementation, get_project_map() without force_refresh 
        # will rebuild the map if self._map is None.
        # But enforce_map_before_work creates a NEW bootstrap, so it will build a NEW map.
        # To test the gate, we need to ensure the map it builds is compared against disk.
        # Wait, if it builds a NEW map from disk, it will be FRESH by definition.
        # The invariant NO_PROJECT_MAP_NO_PROJECT_MUTATION means we need a DURABLE map.
        
        # Let's simulate a scenario where the map is LOADED from a stale cache.
        # For this proof, we'll modify the bootstrap to return a stale map.
        
        class StaleBootstrap(ProjectContextBootstrap):
            def get_project_map(self, force_refresh=False):
                return pmap # Return the original (now stale) map
        
        import p2p_capabilities.project_context as project_context
        original_bootstrap = project_context.ProjectContextBootstrap
        project_context.ProjectContextBootstrap = StaleBootstrap
        
        try:
            enforce_map_before_work(TEST_ROOT, mutation_intent=True)
            print("  FAIL: Mutation allowed despite STALE map")
            assert False
        except ProjectContextError as e:
            print(f"  PASS: Mutation blocked: {e}")
            assert "Mutation blocked" in str(e) or "context not ready" in str(e)
        finally:
            project_context.ProjectContextBootstrap = original_bootstrap

    except Exception as e:
        print(f"  ERROR during Step 4: {e}")
        raise e

    print("\nStep 5: Refresh Map...")
    # A new bootstrap with force_refresh=True should get a fresh map
    bootstrap_new = ProjectContextBootstrap(TEST_ROOT)
    pmap_new = bootstrap_new.get_project_map(force_refresh=True)
    bootstrap_new.save_project_map(pmap_new)
    print(f"  New Identity: {pmap_new.identity()}")
    freshness_info = pmap_new.check_freshness(str(TEST_ROOT))
    print(f"  New Freshness: {freshness_info['status']}")
    assert freshness_info['status'] == "CURRENT"
    assert pmap_new.identity() != pmap.identity()

    print("\nStep 6: Verify Mutation Allowed after Refresh...")
    enforce_map_before_work(TEST_ROOT, mutation_intent=True)
    print("  PASS: Mutation allowed again")

if __name__ == "__main__":
    try:
        test_freshness_flow()
        print("\nALL MAP FRESHNESS TESTS PASSED")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
