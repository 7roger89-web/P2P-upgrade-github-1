"""P2P Contextual Rule Intelligence (CRI) — Domain-specific policy enforcement.

Rules (per RM-CONTEXT-01B):
- Scoped: Rules apply to specific paths, modules, or families with evidence binding.
- Authoritative: Hierarchical authority (Owner > Project > Upstream > Domain > External).
- Conflict-resolution: Authority precedence + explicit priority (Scenario M).
- Evidence-backed: Policies cite specific P2P-APR or SHA-256 evidence.
- Fail-closed: Malformed policies or unknown applicability block the operation.
"""

from __future__ import annotations
import json
import pathlib
import re
import enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

class AuthorityLevel(enum.IntEnum):
    OWNER_PROJECT = 100  # Explicit Owner / Project Policy
    PROJECT_TRUTH = 80   # Verified Project Truth
    OFFICIAL_UPSTREAM = 60 # Version-bound Official Upstream
    DOMAIN_POLICY = 40   # Verified P2P Domain Policy
    EXTERNAL_CORPUS = 20 # Generic External Rule Corpus (e.g. awesome-cursor-rules)

@dataclass(frozen=True)
class PolicyEvidence:
    source: str  # P2P-APR-XXX or file path
    hash: str    # SHA-256 of the decision document
    timestamp: str
    verification_status: str = "UNVERIFIED"

@dataclass(frozen=True)
class RuleApplicability:
    """Advanced applicability semantics (Scenario CRI-A)."""
    glob: str
    dependencies: List[str] = field(default_factory=list)
    version_range: Optional[str] = None
    language: Optional[str] = None
    task_type: Optional[str] = None
    surface: Optional[str] = None

@dataclass(frozen=True)
class DomainPolicy:
    policy_id: str
    authority: AuthorityLevel
    applicability: RuleApplicability
    rules: Dict[str, Any]
    priority: int
    evidence: PolicyEvidence
    tags: List[str] = field(default_factory=list)

class CRIError(Exception):
    """Base class for CRI errors."""
    pass

class PolicyMalformedError(CRIError):
    """Raised when a policy file is malformed (Fail-closed)."""
    pass

class CRIEngine:
    def __init__(self, policy_dir: str):
        self.policy_dir = pathlib.Path(policy_dir)
        self.policies: Dict[str, DomainPolicy] = {}
        self._load_policies()

    def _load_policies(self):
        if not self.policy_dir.exists():
            return
        
        # Scenario: awesome-cursor-rules-mdc direct import must be BLOCKED
        forbidden_patterns = ["awesome-cursor-rules", ".mdc"]
        
        for p in self.policy_dir.glob("*.json"):
            if any(pat in p.name for pat in forbidden_patterns):
                # Log or handle blocked corpus
                continue
                
            try:
                content = p.read_text()
                data = json.loads(content)
                
                # Mandatory fields check (Fail-closed)
                required = ["policy_id", "authority", "applicability", "rules", "evidence"]
                for req in required:
                    if req not in data:
                        raise PolicyMalformedError(f"Missing required field: {req} in {p.name}")
                
                ev_data = data["evidence"]
                evidence = PolicyEvidence(
                    source=ev_data.get("source", "UNKNOWN"),
                    hash=ev_data.get("hash", ""),
                    timestamp=ev_data.get("timestamp", ""),
                    verification_status=ev_data.get("verification_status", "UNVERIFIED")
                )
                
                app_data = data["applicability"]
                applicability = RuleApplicability(
                    glob=app_data.get("glob", "*"),
                    dependencies=app_data.get("dependencies", []),
                    version_range=app_data.get("version_range"),
                    language=app_data.get("language"),
                    task_type=app_data.get("task_type"),
                    surface=app_data.get("surface")
                )
                
                auth_val = data["authority"]
                if isinstance(auth_val, str):
                    authority = AuthorityLevel[auth_val]
                else:
                    authority = AuthorityLevel(auth_val)
                
                policy = DomainPolicy(
                    policy_id=data["policy_id"],
                    authority=authority,
                    applicability=applicability,
                    rules=data["rules"],
                    priority=data.get("priority", 10),
                    evidence=evidence,
                    tags=data.get("tags", [])
                )
                self.policies[policy.policy_id] = policy
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                # Fail-closed: do not silently skip if it's a material policy
                raise PolicyMalformedError(f"Failed to load policy {p.name}: {str(e)}")

    def get_applicable_policies(self, 
                                target_path: str, 
                                context: Dict[str, Any] = None) -> List[DomainPolicy]:
        """Find all policies matching the target and context, sorted by authority then priority."""
        context = context or {}
        applicable = []
        
        for policy in self.policies.values():
            app = policy.applicability
            
            # 1. Glob match
            if not re.search(app.glob.replace("*", ".*"), target_path):
                continue
                
            # 2. Dependency check (Scenario CRI-A)
            if app.dependencies:
                provided_deps = set(context.get("dependencies", []))
                if not all(dep in provided_deps for dep in app.dependencies):
                    continue
            
            # 3. Language check
            if app.language and context.get("language") != app.language:
                continue
                
            # 4. Task type check
            if app.task_type and context.get("task_type") != app.task_type:
                continue
            
            applicable.append(policy)
            
        # Authority Precedence: Higher authority first, then higher priority
        return sorted(applicable, key=lambda x: (x.authority, x.priority), reverse=True)

    def resolve_rules(self, target_path: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Merge rules with hierarchical authority precedence (Scenario CRI-M)."""
        policies = self.get_applicable_policies(target_path, context)
        merged_rules = {}
        provenance = {}
        
        for policy in policies:
            for key, value in policy.rules.items():
                if key not in merged_rules:
                    # Higher authority/priority wins
                    merged_rules[key] = value
                    provenance[key] = {
                        "policy_id": policy.policy_id,
                        "authority": policy.authority.name,
                        "evidence_hash": policy.evidence.hash
                    }
        
        return {
            "rules": merged_rules,
            "provenance": provenance,
            "match_count": len(policies)
        }

    def check_compliance(self, 
                         target_path: str, 
                         action: str, 
                         params: Dict[str, Any], 
                         context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Verify action compliance with strict authority binding."""
        resolution = self.resolve_rules(target_path, context)
        rules = resolution["rules"]
        
        # Action restriction check
        restricted = rules.get("restricted_actions", [])
        if action in restricted:
            return {
                "allowed": False,
                "reason": f"ACTION_RESTRICTED: {action} is forbidden by {resolution['provenance']['restricted_actions']['policy_id']}",
                "authority": resolution['provenance']['restricted_actions']['authority']
            }
            
        # Mandatory parameters check
        mandatory = rules.get("mandatory_params", {})
        for param, pattern in mandatory.items():
            val = str(params.get(param, ""))
            if not re.search(pattern, val):
                return {
                    "allowed": False,
                    "reason": f"MANDATORY_PARAM_MISMATCH: {param} must match {pattern}",
                    "policy_id": resolution["provenance"].get("mandatory_params", {}).get("policy_id")
                }

        return {"allowed": True, "reason": "OK", "resolution": resolution}
