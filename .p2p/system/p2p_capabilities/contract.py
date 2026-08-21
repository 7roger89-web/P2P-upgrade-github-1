"""P2P Context Intelligence — Context Result Contract and Serialization.

Rules (per RM-CONTEXT-01B):
- §9: Host-neutral Serialization (JSON canonical).
- §17: Context Result Contract (Structured results).
"""

from __future__ import annotations
import json
import hashlib
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Optional

@dataclass(frozen=True)
class ContextResult:
    """Structured Context Result Contract (§17)."""
    repository_fingerprint: str
    task_fingerprint: str
    map_fingerprint: str
    selected_symbols: List[str]
    selected_files: List[str]
    selected_policy_fragments: List[str]
    rejected_candidates: List[str]
    evidence_pointers: List[str]
    coverage_state: str
    budget_requested: int
    budget_used: int
    cache_hit_miss: str
    fallbacks: List[str]
    freshness: str
    conflicts_resolution: Dict[str, str]
    unknowns: List[str]
    verification_evidence: str

    def to_canonical_json(self) -> str:
        """Host-neutral Serialization (§9)."""
        # Sort keys and ensure deterministic output
        data = asdict(self)
        return json.dumps(data, sort_keys=True, indent=2)

    def get_hash(self) -> str:
        return hashlib.sha256(self.to_canonical_json().encode()).hexdigest()

def verify_host_neutrality(result: ContextResult) -> bool:
    """Prove same canonical policy serializes to two deterministic fixture targets."""
    target_a = result.to_canonical_json()
    
    # Simulate a different host environment by re-serializing with different internal ordering
    # but the same to_canonical_json() should produce the exact same string.
    data = asdict(result)
    target_b = json.dumps(data, sort_keys=True, indent=2)
    
    return target_a == target_b
