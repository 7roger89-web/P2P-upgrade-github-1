from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any
import datetime

class AssuranceLevel(Enum):
    L0_NONE = 0
    L1_CLAIM_WITH_LOG = 1
    L2_VERIFIED_BY_TOOL = 2
    L3_DETERMINISTIC_PROOF = 3

class EvidenceType(Enum):
    SHELL_OUTPUT = "shell_output"
    FILE_CONTENT = "file_content"
    GIT_DIFF = "git_diff"
    VALIDATOR_RESULT = "validator_result"
    LOG_SNIPPET = "log_snippet"
    METADATA = "metadata"

@dataclass
class Evidence:
    type: EvidenceType
    content: str
    source: str
    timestamp: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ReliabilityClaim:
    claim_id: str
    subject: str  # e.g., "file:/path/to/file", "process:1234"
    statement: str
    evidence: List[Evidence] = field(default_factory=list)
    assurance_level: AssuranceLevel = AssuranceLevel.L0_NONE
    verified_at: Optional[str] = None
    verdict: str = "UNKNOWN"  # UNKNOWN, VALID, CONTRADICTED
    contradiction_details: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "subject": self.subject,
            "statement": self.statement,
            "evidence": [
                {
                    "type": e.type.value,
                    "content": e.content,
                    "source": e.source,
                    "timestamp": e.timestamp,
                    "metadata": e.metadata
                } for e in self.evidence
            ],
            "assurance_level": self.assurance_level.name,
            "verified_at": self.verified_at,
            "verdict": self.verdict,
            "contradiction_details": self.contradiction_details
        }
