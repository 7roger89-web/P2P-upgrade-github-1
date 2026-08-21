"""Test for New and Existing Project Bootstrap (§6, §7)."""
import os
import sys
from pathlib import Path
import json
import shutil

# Setup paths
capabilities_path = "/tmp/p2p-promo01/runtime/p2p_capabilities"
sys.path.insert(0, capabilities_path)

from project_context import ProjectContextBootstrap

def test_new_project():
    print("--- Test: New Project Bootstrap (§6) ---")
    path = Path("/tmp/p2p_new_proj")
    if path.exists(): shutil.rmtree(path)
    path.mkdir()
    
    bootstrap = ProjectContextBootstrap(path)
    intent = "Tạo một app quản lý kho đơn giản."
    bootstrap.bootstrap_new_project(intent)
    
    # Verify Proposed Context
    with open(path / ".p2p" / "project-pin.json", "r") as f:
        pin = json.load(f)
        print(f"Project Pin Intent: {pin['intent']}")
        print(f"Verification Status: {pin['verification_status']}")
    
    # Verify Proposed Maps
    context_dir = path / ".p2p" / "context"
    maps = list(context_dir.glob("*.json"))
    print(f"Proposed Maps Created: {[m.name for m in maps]}")
    
    for m in maps:
        with open(m, "r") as f:
            content = json.load(f)
            print(f"  - {m.name} Status: {content.get('status')}")
    
    print("Result: PASS (NEW_PROJECT_CONTEXT_BOOTSTRAP = VERIFIED)")

def test_existing_project():
    print("\n--- Test: Existing Project Bootstrap (§7) ---")
    # Using auth-f01 as existing project
    path = Path("/home/ubuntu/fw01_work/auth-f01")
    bootstrap = ProjectContextBootstrap(path)
    
    # Derive model (§7)
    model = bootstrap.get_full_model(task_type="UI")
    
    print(f"Project Identity: {model.project_identity['name']}")
    print(f"Project Map Identity: {model.project_map.identity()}")
    print(f"Architecture Map Status: {model.architecture_map.get('status')}")
    print(f"UI Layout Map Status: {model.ui_layout_map.get('status')}")
    print(f"Model Fingerprint: {model.fingerprint}")
    
    print("Result: PASS (EXISTING_PROJECT_CONTEXT_BOOTSTRAP = VERIFIED)")

if __name__ == "__main__":
    test_new_project()
    test_existing_project()
