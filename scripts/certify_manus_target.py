import sys
import os
import json
from pathlib import Path

# Add capabilities to path
sys.path.append("/tmp/p2p-promo01/runtime/p2p_capabilities")

from sentinel_dispatch import certify_manus_target

def run_certification():
    print("Executing Manus ExecutionTarget Certification (§9)...")
    cert = certify_manus_target()
    
    print(json.dumps(cert, indent=2))
    
    # Validation logic
    assert cert["adapter_id"] == "manus-api"
    assert cert["execution_target_class"] == "REMOTE_BOUNDED_HARNESS"
    assert cert["provider_neutrality"] == "VERIFIED"
    
    # Write to evidence
    evidence_path = Path("/home/ubuntu/fw01_work/MANUS_CERTIFICATION_EVIDENCE.json")
    with open(evidence_path, "w") as f:
        json.dump(cert, f, indent=2)
    
    print(f"\nSUCCESS: Certification recorded at {evidence_path}")

if __name__ == "__main__":
    run_certification()
