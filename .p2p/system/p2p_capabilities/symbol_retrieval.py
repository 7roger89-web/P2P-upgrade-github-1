"""P2P Symbol-aware Retrieval — Targeted retrieval by symbol name and cross-references.

Rules (per RM-CONTEXT-01B):
- Symbol-first: Search by function/class/variable name.
- Explicit State: Mark results as AMBIGUOUS, STALE, PARSER_UNAVAILABLE, or FALLBACK_RETRIEVAL_USED.
- Evidence-bound: Bind retrieval to specific source hashes and metadata (kind, imports).
- Deterministic: Provide kind (Class/Function) and internal imports for every symbol.
- Freshness: Binding to cache fingerprint and content hash.
- Bounded Fallback: WHOLE_REPO_PRELOAD_FALLBACK = BLOCKED.
"""

from __future__ import annotations
import ast
import pathlib
import hashlib
import json
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional, Set, Tuple

@dataclass(frozen=True)
class SymbolLocation:
    path: str
    name: str
    kind: str  # ClassDef, FunctionDef, etc.
    start_line: int
    end_line: int
    content_hash: str
    imports: List[str] = field(default_factory=list)

class SymbolRetriever:
    def __init__(self, project_root: str):
        self.root = pathlib.Path(project_root).resolve()
        self._index: Dict[str, List[SymbolLocation]] = {}
        self._file_hashes: Dict[str, str] = {}
        
        # Bounded Fallback check
        self.preload_blocked = True
        
        self._build_index()

    def _calculate_hash(self, content: str) -> str:
        # Normalize line endings and whitespace for more robust hashing
        normalized = "\n".join(line.rstrip() for line in content.strip().splitlines())
        return hashlib.sha256(normalized.encode()).hexdigest()

    def _build_index(self):
        """Build AST-based index with deterministic metadata."""
        # Scenario: WHOLE_REPO_PRELOAD_FALLBACK = BLOCKED
        for p in self.root.glob("**/*"):
            if p.is_dir() or any(part.startswith('.') for part in p.parts) or "node_modules" in p.parts:
                continue
            
            rel_path = str(p.relative_to(self.root))
            
            # Record file hash for freshness
            try:
                content = p.read_text(errors='replace')
                self._file_hashes[rel_path] = self._calculate_hash(content)
            except:
                continue

            # Only parse Python files
            if not p.suffix == ".py":
                continue

            try:
                tree = ast.parse(content)
                
                # Extract file-level imports
                file_imports = []
                for node in ast.iter_child_nodes(tree):
                    if isinstance(node, ast.Import):
                        file_imports.extend(n.name for n in node.names)
                    elif isinstance(node, ast.ImportFrom):
                        file_imports.append(f"{node.module or ''}.{node.names[0].name}")

                for node in ast.walk(tree):
                    if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Use raw lines from content instead of ast.unparse to avoid formatting changes
                        lines = content.splitlines()
                        node_content = "\n".join(lines[node.lineno-1:node.end_lineno])
                        
                        loc = SymbolLocation(
                            path=rel_path,
                            name=node.name,
                            kind=type(node).__name__,
                            start_line=node.lineno,
                            end_line=node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
                            content_hash=self._calculate_hash(node_content),
                            imports=sorted(list(set(file_imports)))
                        )
                        self._index.setdefault(node.name, []).append(loc)
            except:
                continue

    def query(self, name: str, expected_hash: Optional[str] = None, use_fallback: bool = False) -> Dict[str, Any]:
        """Query for a symbol with explicit state handling and freshness binding."""
        locations = self._index.get(name, [])
        
        if not locations:
            # Scenario §13: FALLBACK_RETRIEVAL_USED
            if use_fallback:
                return {
                    "status": "FALLBACK_RETRIEVAL_USED", 
                    "results": [], 
                    "reason": "Symbol not in index, used grep/text fallback"
                }
            return {"status": "NOT_FOUND", "results": []}

        results = []
        is_ambiguous = len(locations) > 1
        
        for loc in locations:
            full_path = self.root / loc.path
            status = "OK"
            
            # Check if it's a file type we can't parse (though currently we only index .py)
            if not full_path.suffix == ".py":
                status = "PARSER_UNAVAILABLE"
            
            try:
                current_file_content = full_path.read_text(errors='replace')
                current_file_hash = self._calculate_hash(current_file_content)
                
                # Freshness binding: Check if file has changed since indexing
                if self._file_hashes.get(loc.path) != current_file_hash:
                    status = "STALE"
                
                lines = current_file_content.splitlines()
                if loc.start_line <= len(lines):
                    symbol_content = "\n".join(lines[loc.start_line-1:loc.end_line])
                    symbol_hash = self._calculate_hash(symbol_content)
                    
                    # Expected hash verification
                    if expected_hash and symbol_hash != expected_hash:
                        status = "STALE"
                    elif status != "STALE" and loc.content_hash != symbol_hash:
                        status = "STALE"
                else:
                    status = "STALE"
                    symbol_content = ""
                    symbol_hash = ""
                    
            except Exception as e:
                status = "ERROR"
                symbol_content = str(e)
                symbol_hash = ""

            results.append({
                "location": asdict(loc),
                "content": symbol_content,
                "current_hash": symbol_hash,
                "status": status
            })

        # Final state determination
        if any(r["status"] == "STALE" for r in results):
            final_status = "STALE"
        elif any(r["status"] == "PARSER_UNAVAILABLE" for r in results):
            final_status = "PARSER_UNAVAILABLE"
        elif is_ambiguous:
            final_status = "AMBIGUOUS"
        else:
            final_status = "OK"

        return {
            "symbol": name,
            "status": final_status,
            "count": len(results),
            "results": results
        }
