"""P2P Adaptive Context Budget — Dynamic context allocation based on task complexity.

Design rules (per RM-CONTEXT-01B):
- Complexity Signals: Use task type, impact, and file counts to set budgets (Scenario L).
- Budget Enforcement: Strict soft/hard limits (Scenario K).
- Priority: Protect mandatory context while offloading optional assets.
- Redaction: Secret boundary protection (offload secrets).
"""

from __future__ import annotations
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

class ContextBudgetInsufficient(Exception):
    """Raised when context exceeds hard limits (Scenario L)."""
    pass

@dataclass(frozen=True)
class TaskComplexity:
    risk_class: str  # LOW, MODERATE, CROSS_SUBSYSTEM, SECURITY, ARCHITECTURE
    file_count: int
    max_depth: int
    is_mutation: bool = False
    task_type: str = "read" # read, write, refactor, audit

class AdaptiveBudgetManager:
    def __init__(self, base_budget: int = 10000):
        self.base_budget = base_budget

    def calculate_budget(self, task: TaskComplexity) -> Dict[str, int]:
        """Determine soft and hard limits based on complexity signals (Scenario L)."""
        multipliers = {
            "LOW": 1.0,
            "MODERATE": 1.5,
            "CROSS_SUBSYSTEM": 2.0,
            "SECURITY": 2.5,
            "ARCHITECTURE": 3.0
        }
        
        type_multipliers = {
            "read": 1.0,
            "write": 1.5,
            "refactor": 2.0,
            "audit": 1.2
        }
        
        # Risk and Type multipliers
        risk_mult = multipliers.get(task.risk_class, 1.0)
        type_mult = type_multipliers.get(task.task_type, 1.0)
        
        # Signal-based scaling
        file_mult = 1.0 + (min(task.file_count, 50) / 50.0)  # Up to 2x for large file sets
        depth_mult = 1.0 + (min(task.max_depth, 10) / 10.0)  # Up to 2x for deep nesting
        mutation_mult = 1.2 if task.is_mutation else 1.0
        
        soft = int(self.base_budget * risk_mult * type_mult * file_mult * depth_mult * mutation_mult)
        hard = int(soft * 1.5)
        
        return {
            "soft_limit": soft,
            "hard_limit": hard,
            "base": self.base_budget
        }

    def allocate_context(self, budget: Dict[str, int], required_items: List[Dict[str, Any]], optional_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Allocate items within budget (Scenario K)."""
        soft_limit = budget["soft_limit"]
        hard_limit = budget["hard_limit"]
        
        allocated_required = []
        allocated_optional = []
        current_size = 0
        
        # 1. Satisfy Required Context First (Mandatory)
        for item in required_items:
            size = item.get("size", 0)
            if current_size + size > hard_limit:
                # Scenario L: FAIL_CLOSED on hard limit breach
                raise ContextBudgetInsufficient(f"REQUIRED_CONTEXT_EXCEEDS_HARD_LIMIT: {current_size + size} > {hard_limit}")
            allocated_required.append(item)
            current_size += size
            
        # 2. Allocate Optional Items (Priority-driven)
        sorted_optional = sorted(optional_items, key=lambda x: x.get("priority", 99))
        
        for item in sorted_optional:
            size = item.get("size", 0)
            # Scenario K: Soft limit governs optional additions.
            if current_size + size <= soft_limit:
                allocated_optional.append(item)
                current_size += size
            else:
                # Stop once soft limit is reached for optional items
                break
                
        return {
            "required": allocated_required,
            "optional": allocated_optional,
            "total_size": current_size,
            "budget_status": "OK" if current_size <= soft_limit else "SOFT_LIMIT_REACHED",
            "limits": {"soft": soft_limit, "hard": hard_limit}
        }

    def redact_secrets(self, content: str) -> str:
        """Scenario: Secret Boundary Protection (offload secrets)."""
        # Simplified secret redaction patterns
        patterns = [
            r'AKIA[0-9A-Z]{16}',  # AWS
            r'sk-[a-zA-Z0-9]{32,}', # OpenAI
            r'password\s*=\s*[\'"][^\'"]+[\'"]'
        ]
        redacted = content
        for p in patterns:
            redacted = re.sub(p, "[REDACTED_SECRET]", redacted)
        return redacted
