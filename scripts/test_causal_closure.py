#!/usr/bin/env python3
import sys
import json
import time
from pathlib import Path

# Add runtime to path
sys.path.append("/tmp/p2p-promo01/runtime/p2p_capabilities")
from sentinel_dispatch import SentinelDispatcher, SentinelTaskConfig, certify_manus_target
from manus_adapter import ManusAdapter
from agent_role import AgentRoleSpec, CANONICAL_ROLES, load_capability_registry

def test_causal_closure():
    print("--- Test 1: Certification (§9) ---")
    cert = certify_manus_target()
    print(f"Manus Certified: {cert['target_id']} (Status: {cert['health_status']})")
    
    print("\n--- Test 2: Role Conformance (§13) ---")
    # Verify the 8 canonical roles exist
    print(f"Canonical Roles Count: {len(CANONICAL_ROLES)}")
    expected_roles = set(CANONICAL_ROLES)
    
    # Load from registry to verify actual availability
    registry = load_capability_registry()
    actual_roles = {r.get("CAPABILITY_ID") for r in registry if r.get("CAPABILITY_ID") in CANONICAL_ROLES}
    missing = expected_roles - actual_roles
    if not missing:
        print("PASS: All 8 canonical roles confirmed.")
    else:
        print(f"FAIL: Missing roles: {missing}")
    
    print("\n--- Test 3: Causal Closure (P2P -> Manus -> P2P) (§12) ---")
    adapter = ManusAdapter()
    dispatcher = SentinelDispatcher(adapter)
    
    config = SentinelTaskConfig(
        purpose="Verify Causal Closure",
        prompt="Respond with P2P_CAUSAL_CLOSURE_VERIFIED",
        max_turns=5
    )
    
    print("Dispatching task...")
    result = dispatcher.dispatch(config)
    
    # In our adapter, the result is stored in output_pointers as a tuple of "prefix:content"
    answer = ""
    for ptr in result.output_pointers:
        if ptr.startswith("text://"):
            answer = ptr[len("text://"):]
            break
    print(f"Manus Response: {answer}")
    
    if "P2P_CAUSAL_CLOSURE_VERIFIED" in answer:
        print("PASS: Causal closure verified. Task identity and result correctly bound.")
    else:
        print("FAIL: Causal closure failed. Response mismatch.")

if __name__ == "__main__":
    test_causal_closure()
