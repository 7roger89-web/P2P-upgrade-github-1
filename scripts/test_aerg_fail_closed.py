import sys
import os
import pathlib
import datetime

# Thêm đường dẫn để import p2p_capabilities
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / ".p2p" / "system"))

from p2p_capabilities.aerg_model import Evidence, EvidenceType, AssuranceLevel
from p2p_capabilities.aerg_engine import AERGEngine
from p2p_capabilities.quality_intelligence import build_quality_verdict

def test_aerg_contradiction_fail_closed():
    print("Running AERG Contradiction Fail-Closed Test...")
    engine = AERGEngine(task_id="test-task-001")
    
    # 1. Create a claim
    claim = engine.create_claim(subject="file:governance/development-control.json", 
                               statement="SHA-256 matches baseline.")
    
    # 2. Add contradictory evidence (Shell output says mismatch)
    evidence = Evidence(
        type=EvidenceType.SHELL_OUTPUT,
        content="sha256sum: mismatch on line 1",
        source="sha256sum --check"
    )
    engine.add_evidence(claim.claim_id, evidence)
    
    # 3. Verify claim
    verdict = engine.verify_claim(claim.claim_id, expected_content="OK")
    print(f"Claim Verdict: {verdict}")
    assert verdict == "CONTRADICTED"
    
    # 4. Check quality verdict integration
    quality_verdict = build_quality_verdict(
        execution_status="SUCCESS",
        required_eval_results={"EVAL-001": "PASS"},
        reliability_claims=[claim]
    )
    
    print(f"Quality Status: {quality_verdict['quality_status']}")
    print(f"Quality Failures: {quality_verdict['quality_failures']}")
    
    assert "RELIABILITY_CONTRADICTION" in quality_verdict["quality_failures"]
    assert quality_verdict["quality_status"] == "QUALITY_REJECTED"
    assert quality_verdict["checkpoint_allowed"] is False
    
    print("Test AERG Contradiction Fail-Closed: PASS")

def test_aerg_freshness_enforcement():
    print("\nRunning AERG Freshness Enforcement Test...")
    engine = AERGEngine(task_id="test-task-002")
    claim = engine.create_claim(subject="process:1234", statement="Process is isolated.")
    
    # Add stale evidence (6 minutes old)
    stale_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=6)).isoformat()
    evidence = Evidence(
        type=EvidenceType.LOG_SNIPPET,
        content="Process 1234 started in sandbox.",
        source="sandbox-init.log",
        timestamp=stale_time
    )
    
    added = engine.add_evidence(claim.claim_id, evidence)
    print(f"Evidence Added (should be False): {added}")
    assert added is False
    assert claim.assurance_level == AssuranceLevel.L0_NONE
    
    print("Test AERG Freshness Enforcement: PASS")

if __name__ == "__main__":
    try:
        test_aerg_contradiction_fail_closed()
        test_aerg_freshness_enforcement()
        print("\nALL AERG TESTS PASSED.")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        sys.exit(1)
