"""P2P Project Map (L0-L3) — Token-bounded hierarchical repository representation.

Design rules (per RM-CONTEXT-01B):
- L0: Structural (File tree, sizes, hashes).
- L1: Functional (Module/Class/Function signatures, docstrings).
- L2: Relational (Import graph, symbol call graph, cross-references).
- L3: Authoritative (Pointers to deep logic, implementation details).
- Token-bounded: Each level has a strict budget; higher levels compress lower levels.
- Freshness: Map identity binds to repository state (HEAD) and individual file hashes.
- Bounded Fallback: WHOLE_REPO_PRELOAD_FALLBACK = BLOCKED.
"""

from __future__ import annotations
import hashlib
import json
import os
import pathlib
import re
import ast
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from .context import context_fingerprint, _assert_no_secret_fields
except ImportError:
    def context_fingerprint(data: Any) -> str:
        s = json.dumps(data, sort_keys=True)
        return hashlib.sha256(s.encode()).hexdigest()
    def _assert_no_secret_fields(data: Any): pass

MAP_SCHEMA_VERSION = "p2p-project-map/3"

# Token Budgets (Approximate tokens, 1 token ~= 4 chars)
LEVEL_BUDGETS = {
    0: 5000,   # L0: Structural tree
    1: 15000,  # L1: Signatures
    2: 10000,  # L2: Relations
    3: 20000,  # L3: Deep logic (demand-only)
}

@dataclass(frozen=True)
class MapLevel:
    level: int
    content: Dict[str, Any]
    token_count: int
    fingerprint: str
    is_truncated: bool = False

class ProjectMap:
    def __init__(self, project_root: str, source_commit: str, levels: Dict[int, MapLevel]):
        self.project_root = project_root
        self.source_commit = source_commit
        self.levels = levels
        self.schema_version = MAP_SCHEMA_VERSION

    def identity(self) -> str:
        payload = {
            "project_root": self.project_root,
            "source_commit": self.source_commit,
            "level_fingerprints": {lvl: m.fingerprint for lvl, m in self.levels.items()}
        }
        return "proj-map-" + context_fingerprint(payload)

    def check_freshness(self, current_root: str) -> Dict[str, Any]:
        """Spec §12: Map/Cache Freshness. Detects drift between map and disk."""
        root = pathlib.Path(current_root)
        drift = []
        
        # Check L0 file tree hashes
        l0 = self.levels.get(0)
        if not l0:
            return {"status": "UNKNOWN", "drift": []}
            
        file_tree = l0.content.get("file_tree", {})
        for rel_path, info in file_tree.items():
            p = root / rel_path
            if not p.exists():
                drift.append({"path": rel_path, "type": "DELETED"})
                continue
            
            try:
                current_hash = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
                if current_hash != info.get("hash"):
                    drift.append({"path": rel_path, "type": "MODIFIED"})
            except:
                drift.append({"path": rel_path, "type": "READ_ERROR"})
        
        status = "STALE" if drift else "CURRENT"
        return {"status": status, "drift": drift}

class ProjectMapBuilder:
    def __init__(self, project_root: str):
        self.root = pathlib.Path(project_root).resolve()
        if not self.root.exists():
            raise ValueError(f"PROJECT_ROOT_NOT_FOUND: {project_root}")
        
        self.preload_blocked = True
        
        import subprocess
        try:
            self.source_commit = subprocess.run(
                ["git", "-C", str(self.root), "rev-parse", "HEAD"],
                capture_output=True, text=True, check=True).stdout.strip()
        except:
            self.source_commit = "UNKNOWN_REVISION"
            
        self.file_hashes = {}

    def _estimate_tokens(self, data: Any) -> int:
        return len(json.dumps(data)) // 4

    def build_l0(self) -> MapLevel:
        tree = {}
        total_tokens = 0
        is_truncated = False
        
        files = sorted([p for p in self.root.glob("**/*") if p.is_file()])
        
        for p in files:
            if any(part.startswith('.') for part in p.parts) or "node_modules" in p.parts:
                continue
                
            rel_path = str(p.relative_to(self.root))
            try:
                stats = p.stat()
                file_hash = hashlib.sha256(p.read_bytes()).hexdigest()[:16]
                self.file_hashes[rel_path] = file_hash
                
                entry = {"size": stats.st_size, "suffix": p.suffix, "hash": file_hash}
                entry_tokens = self._estimate_tokens({rel_path: entry})
                
                if total_tokens + entry_tokens > LEVEL_BUDGETS[0]:
                    is_truncated = True
                    break
                    
                tree[rel_path] = entry
                total_tokens += entry_tokens
            except:
                continue
        
        content = {"file_tree": tree}
        return MapLevel(0, content, total_tokens, context_fingerprint(content), is_truncated)

    def build_l1(self) -> MapLevel:
        signatures = {}
        total_tokens = 0
        is_truncated = False
        
        py_files = sorted([p for p in self.root.glob("**/*.py") if not any(part.startswith('.') for part in p.parts)])
        
        for p in py_files:
            rel_path = str(p.relative_to(self.root))
            try:
                tree = ast.parse(p.read_text(errors='replace'))
                file_sigs = []
                for node in ast.iter_child_nodes(tree):
                    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                        sig = self._get_node_sig(node)
                        file_sigs.append(sig)
                
                entry_tokens = self._estimate_tokens({rel_path: file_sigs})
                if total_tokens + entry_tokens > LEVEL_BUDGETS[1]:
                    is_truncated = True
                    break
                    
                signatures[rel_path] = file_sigs
                total_tokens += entry_tokens
            except:
                continue
                
        content = {"signatures": signatures}
        return MapLevel(1, content, total_tokens, context_fingerprint(content), is_truncated)

    def _get_node_sig(self, node: Any) -> Dict[str, Any]:
        res = {"name": node.name, "type": type(node).__name__}
        if isinstance(node, ast.ClassDef):
            res["bases"] = [ast.unparse(b) for b in node.bases]
            res["methods"] = [self._get_node_sig(n) for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            res["args"] = ast.unparse(node.args)
        
        doc = ast.get_docstring(node)
        if doc:
            res["doc"] = doc[:60].strip() + "..." if len(doc) > 60 else doc
        return res

    def build_l2(self) -> MapLevel:
        imports = {}
        total_tokens = 0
        is_truncated = False
        
        py_files = sorted([p for p in self.root.glob("**/*.py") if not any(part.startswith('.') for part in p.parts)])
        
        for p in py_files:
            rel_path = str(p.relative_to(self.root))
            try:
                tree = ast.parse(p.read_text(errors='replace'))
                file_imports = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for n in node.names: file_imports.append(n.name)
                    elif isinstance(node, ast.ImportFrom):
                        file_imports.append(f"{node.module or ''}.{node.names[0].name}")
                
                file_imports = sorted(list(set(file_imports)))
                entry_tokens = self._estimate_tokens({rel_path: file_imports})
                if total_tokens + entry_tokens > LEVEL_BUDGETS[2]:
                    is_truncated = True
                    break
                    
                imports[rel_path] = file_imports
                total_tokens += entry_tokens
            except:
                continue
                
        content = {"import_graph": imports}
        return MapLevel(2, content, total_tokens, context_fingerprint(content), is_truncated)

    def build_full_map(self) -> ProjectMap:
        return ProjectMap(
            project_root=str(self.root),
            source_commit=self.source_commit,
            levels={0: self.build_l0(), 1: self.build_l1(), 2: self.build_l2()}
        )
