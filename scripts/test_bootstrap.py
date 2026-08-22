"""Test for New and Existing Project Bootstrap (§6, §7)."""
import sys
from pathlib import Path
import json
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / ".p2p" / "system"))

from p2p_capabilities.project_context import ProjectContextBootstrap

def test_new_project():
    print("--- Test: New Project Bootstrap (§6) ---")
    path = Path(tempfile.mkdtemp(prefix="bootstrap-proposal-", dir=str(ROOT / ".tmp")))
    if path.exists(): shutil.rmtree(path)
    path.mkdir()
    
    bootstrap = ProjectContextBootstrap(path)
    intent = "Tạo một app quản lý kho đơn giản."
    bootstrap.bootstrap_new_project(intent)
    
    # Proposal bootstrap is not an installation and must not mint readiness.
    assert not (path / ".p2p" / "project-pin.json").exists()
    proposal = json.loads((path / ".p2p" / "context" / "project-bootstrap-proposal.json").read_text(encoding="utf-8"))
    assert proposal["status"] == "PROPOSED"
    assert not ProjectContextBootstrap(path).is_ready()
    
    # Verify Proposed Maps
    context_dir = path / ".p2p" / "context"
    maps = list(context_dir.glob("*.json"))
    print(f"Proposed Maps Created: {[m.name for m in maps]}")
    
    for m in maps:
        with open(m, "r") as f:
            content = json.load(f)
            print(f"  - {m.name} Status: {content.get('status')}")
    
    shutil.rmtree(path, ignore_errors=True)
    print("Result: PASS (PROPOSAL_DOES_NOT_CREATE_PROJECT_PIN)")

if __name__ == "__main__":
    test_new_project()
