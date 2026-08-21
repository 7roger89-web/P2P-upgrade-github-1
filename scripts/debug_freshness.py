import os
import sys
from pathlib import Path
import hashlib

capabilities_path = "/tmp/p2p-promo01/runtime/p2p_capabilities"
sys.path.insert(0, capabilities_path)

from project_map import ProjectMapBuilder

root = Path("/tmp/debug_root")
if root.exists(): import shutil; shutil.rmtree(root)
root.mkdir()
(root / "file1.txt").write_text("hello")

builder = ProjectMapBuilder(str(root))
pmap = builder.build_full_map()

print(f"Map file tree: {pmap.levels[0].content['file_tree']}")

(root / "file1.txt").write_text("modified")
freshness = pmap.check_freshness(str(root))
print(f"Freshness after modification: {freshness['status']}")
if freshness['drift']:
    print(f"Drift: {freshness['drift']}")

(root / "file2.txt").write_text("new")
freshness = pmap.check_freshness(str(root))
print(f"Freshness after new file: {freshness['status']}")
