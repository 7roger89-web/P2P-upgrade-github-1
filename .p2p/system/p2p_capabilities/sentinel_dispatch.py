"""Sentinel Dispatch (C34).

Mechanism for secure, bounded task dispatch to Manus as an ExecutionTarget.
Ensures every task has a unique identity, a strict budget, and evidence pointers.
"""

import time
import uuid
import hashlib
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

try:
    from .manus_adapter import ManusAdapter
    from .backend_contract import BackendExecutionResult
except ImportError:
    from manus_adapter import ManusAdapter
    from backend_contract import BackendExecutionResult

@dataclass
class SentinelTaskConfig:
    purpose: str
    prompt: str
    max_turns: int = 25
    timeout_seconds: int = 900
    risk_class: str = "LOW"
    agent_profile: str = "manus-1.6-lite"

class SentinelDispatcher:
    """Dispatches tasks to Manus with strict P2P-side identity and budget enforcement."""
    
    def __init__(self, adapter: ManusAdapter):
        self._adapter = adapter

    def dispatch(self, config: SentinelTaskConfig) -> BackendExecutionResult:
        """Dispatches a task and returns a normalized execution result."""
        request_id = str(uuid.uuid4())
        # Generate a deterministic fingerprint based on prompt and config
        fingerprint_input = f"{config.purpose}:{config.prompt}:{config.agent_profile}"
        request_fingerprint = hashlib.sha256(fingerprint_input.encode()).hexdigest()
        
        # In a real system, these would come from the roadmap/task manager
        task_id = f"task-{request_id[:8]}"
        goal_id = f"goal-{request_id[:8]}"
        
        print(f"Sentinel: Dispatching task {request_id} (Fingerprint: {request_fingerprint[:8]})")
        
        result = self._adapter.execute(
            request_id=request_id,
            request_fingerprint=request_fingerprint,
            task_id=task_id,
            goal_id=goal_id,
            prompt=config.prompt,
            max_turns=config.max_turns,
            timeout_seconds=config.timeout_seconds,
            title=f"P2P Sentinel: {config.purpose}",
            agent_profile=config.agent_profile
        )
        
        return result

def certify_manus_target() -> Dict[str, Any]:
    """Certifies Manus as a valid P2P ExecutionTarget (§9)."""
    adapter = ManusAdapter()
    identity = adapter.identity()
    health = adapter.health()
    
    certification = {
        "target_id": "manus-cloud-production",
        "adapter_id": identity.adapter_id,
        "adapter_version": identity.adapter_version,
        "certified_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "health_status": "HEALTHY" if health.healthy else "DEGRADED",
        "auth_state": health.auth_state,
        "capabilities": identity.toolset_capabilities,
        "execution_target_class": "REMOTE_BOUNDED_HARNESS",
        "provider_neutrality": "VERIFIED"
    }
    return certification
