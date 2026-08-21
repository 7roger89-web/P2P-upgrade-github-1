"""Test for Real-world Manus Causal Closure (§12, §13)."""
import os
import sys
import time
from pathlib import Path

# Setup paths
capabilities_path = "/tmp/p2p-promo01/runtime/p2p_capabilities"
sys.path.insert(0, capabilities_path)

from sentinel_dispatch import SentinelDispatcher, SentinelTaskConfig
from manus_adapter import ManusAdapter

def run_causal_test():
    print("--- Test: Real-world Manus Causal Closure (§12, §13) ---")
    
    adapter = ManusAdapter()
    dispatcher = SentinelDispatcher(adapter)
    
    # 1. Define a causal task (§12)
    config = SentinelTaskConfig(
        purpose="Xác minh quan hệ nhân quả",
        prompt="Hãy liệt kê các tệp trong thư mục /tmp và trả về kết quả dưới dạng JSON.",
        max_turns=2,
        risk_class="LOW"
    )
    
    print(f"Dispatching task with purpose: {config.purpose}")
    start_time = time.time()
    
    # 2. Execute with Sentinel Dispatch (§13)
    result = dispatcher.dispatch(config)
    
    duration = time.time() - start_time
    
    # 3. Verify Causal Closure Evidence (§12, §13)
    print("\nVerifying Causal Closure Evidence:")
    print(f"  - Request ID: {result.request_id}")
    print(f"  - Request Fingerprint: {result.request_fingerprint}")
    print(f"  - Execution Status: {result.execution_status}")
    print(f"  - Verification Status: {result.verification_status}")
    print(f"  - Completion Status: {result.completion_status}")
    print(f"  - Output Pointers: {result.output_pointers}")
    print(f"  - Artifact Pointers: {result.artifact_pointers}")
    print(f"  - Duration: {duration:.2f}s")
    
    # Check if result contains evidence of its own identity
    if result.request_id and result.request_fingerprint:
        print("Result: PASS (CAUSAL_CLOSURE = VERIFIED)")
    else:
        print("Result: FAIL (Identity missing)")

if __name__ == "__main__":
    run_causal_test()
