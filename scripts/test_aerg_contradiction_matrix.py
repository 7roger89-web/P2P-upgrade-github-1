import sys
import os
import datetime

# Setup path
sys.path.append(os.path.join(os.getcwd(), ".p2p/system"))

from p2p_capabilities.aerg_model import Evidence, EvidenceType, AssuranceLevel
from p2p_capabilities.aerg_engine import AERGEngine

def test_exit_failure_vs_pass():
    engine = AERGEngine("test-task")
    claim = engine.create_claim("process:1234", "Execution passed successfully")
    
    # Evidence shows exit code 1 (failure)
    ev = Evidence(
        type=EvidenceType.VALIDATOR_RESULT,
        content="ERROR: Process exited with code 1",
        source="shell_executor"
    )
    engine.add_evidence(claim.claim_id, ev)
    
    verdict = engine.verify_claim(claim.claim_id)
    print(f"Test Exit Failure vs Pass: {verdict}")
    assert verdict == "CONTRADICTED"

def test_sha_mismatch():
    engine = AERGEngine("test-task")
    claim = engine.create_claim("file:/app/bin", "SHA-256 is correct")
    
    # Evidence shows error in SHA check
    ev = Evidence(
        type=EvidenceType.VALIDATOR_RESULT,
        content="sha256sum: /app/bin: FAILED",
        source="integrity_checker"
    )
    engine.add_evidence(claim.claim_id, ev)
    
    verdict = engine.verify_claim(claim.claim_id)
    print(f"Test SHA Mismatch: {verdict}")
    assert verdict == "CONTRADICTED"

def test_stale_evidence():
    engine = AERGEngine("test-task")
    claim = engine.create_claim("file:/app/bin", "Fresh build")
    
    # Stale timestamp (1 hour ago)
    stale_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)).isoformat()
    ev = Evidence(
        type=EvidenceType.SHELL_OUTPUT,
        content="Build success",
        source="compiler",
        timestamp=stale_time
    )
    
    added = engine.add_evidence(claim.claim_id, ev)
    print(f"Test Stale Evidence (added): {added}")
    assert added is False

if __name__ == "__main__":
    test_exit_failure_vs_pass()
    test_sha_mismatch()
    test_stale_evidence()
    print("ALL CONTRADICTION MATRIX TESTS PASSED.")
