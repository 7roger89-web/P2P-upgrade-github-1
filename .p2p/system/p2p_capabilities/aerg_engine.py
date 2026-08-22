import datetime
import hashlib
from typing import List, Optional
from .aerg_model import ReliabilityClaim, Evidence, AssuranceLevel, EvidenceType

class AERGEngine:
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.claims: List[ReliabilityClaim] = []

    def create_claim(self, subject: str, statement: str) -> ReliabilityClaim:
        claim_id = f"CLAIM-{hashlib.sha256(f'{self.task_id}-{subject}-{datetime.datetime.now().timestamp()}'.encode()).hexdigest()[:8]}"
        claim = ReliabilityClaim(
            claim_id=claim_id,
            subject=subject,
            statement=statement
        )
        self.claims.append(claim)
        return claim

    def add_evidence(self, claim_id: str, evidence: Evidence) -> bool:
        claim = next((c for c in self.claims if c.claim_id == claim_id), None)
        if not claim:
            return False
        
        # Freshness Check: Evidence must be recent (e.g., within last 5 minutes for active tasks)
        evidence_time = datetime.datetime.fromisoformat(evidence.timestamp.replace('Z', '+00:00'))
        now = datetime.datetime.now(datetime.timezone.utc)
        if (now - evidence_time).total_seconds() > 300:
            # Stale evidence
            return False

        claim.evidence.append(evidence)
        self._update_assurance_level(claim)
        return True

    def verify_claim(self, claim_id: str, expected_content: Optional[str] = None) -> str:
        claim = next((c for c in self.claims if c.claim_id == claim_id), None)
        if not claim:
            return "UNKNOWN"

        if not claim.evidence:
            claim.verdict = "UNKNOWN"
            return claim.verdict

        # Deterministic Contradiction Detection
        for ev in claim.evidence:
            # Case 1: Shell output doesn't match expected outcome
            if ev.type == EvidenceType.SHELL_OUTPUT and expected_content:
                if expected_content not in ev.content:
                    claim.verdict = "CONTRADICTED"
                    claim.contradiction_details = f"Expected '{expected_content}' not found in shell output."
                    return claim.verdict
            
            # Case 2: Validator result is explicitly negative
            if ev.type == EvidenceType.VALIDATOR_RESULT:
                if "FAIL" in ev.content.upper() or "ERROR" in ev.content.upper():
                    claim.verdict = "CONTRADICTED"
                    claim.contradiction_details = f"Validator reported failure: {ev.content[:100]}"
                    return claim.verdict

        claim.verdict = "VALID"
        claim.verified_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
        return claim.verdict

    def _update_assurance_level(self, claim: ReliabilityClaim):
        if not claim.evidence:
            claim.assurance_level = AssuranceLevel.L0_NONE
            return

        has_tool_verification = any(e.type == EvidenceType.VALIDATOR_RESULT or e.type == EvidenceType.GIT_DIFF for e in claim.evidence)
        has_shell = any(e.type == EvidenceType.SHELL_OUTPUT for e in claim.evidence)
        has_log = any(e.type == EvidenceType.LOG_SNIPPET for e in claim.evidence)

        if has_tool_verification:
            claim.assurance_level = AssuranceLevel.L3_DETERMINISTIC_PROOF
        elif has_shell:
            claim.assurance_level = AssuranceLevel.L2_VERIFIED_BY_TOOL
        elif has_log:
            claim.assurance_level = AssuranceLevel.L1_CLAIM_WITH_LOG
        else:
            claim.assurance_level = AssuranceLevel.L0_NONE
