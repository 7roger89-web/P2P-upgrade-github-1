from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "docs" / "p2p-development" / "P2P-EVIDENCE-FIRST-VERIFICATION.md"
ENTRYPOINT = ROOT / "docs" / "p2p-development" / "P2P-AGENTS-INSTALL.md"
CHARTER = ROOT / "docs" / "p2p-development" / "P2P-DEVELOPMENT-CHARTER.md"


def test_evidence_first_profile_declares_core_contract() -> None:
    text = PROFILE.read_text(encoding="utf-8")
    for token in (
        "P2P_EVIDENCE_FIRST_VERIFICATION_V1=ACTIVE",
        "AGENT_CLAIM_IS_NOT_EVIDENCE=YES",
        "TEST_PASS_PROVES_ONLY_CHALLENGED_BEHAVIOR=YES",
        "OUTPUT_PASS != ACCEPTANCE_PROVEN",
        "GOAL_PASS != PROMOTION",
        "PROVEN | INCOMPLETE | FAILED",
    ):
        assert token in text


def test_profile_reuses_existing_execution_lanes_without_second_classifier() -> None:
    text = PROFILE.read_text(encoding="utf-8")
    for lane in ("`FAST`", "`STANDARD`", "`STRICT`", "`CRITICAL`"):
        assert lane in text
    assert "does not create a second risk classifier" in text
    assert "creates no second truth store, router, executor, permission system" in text


def test_strict_and_critical_require_independent_challenge() -> None:
    text = PROFILE.read_text(encoding="utf-8")
    assert "independent challenge of changed behavioral surface" in text
    assert "independent reviewer/verifier" in text
    assert "Mutation testing is not a universal ritual" in text
    assert "real path cannot be exercised" in text


def test_installed_entrypoint_discovers_profile_and_scopes_pass_claims() -> None:
    text = ENTRYPOINT.read_text(encoding="utf-8")
    for token in (
        "P2P-EVIDENCE-FIRST-VERIFICATION.md",
        "AGENT_CLAIM_IS_NOT_EVIDENCE",
        "TEST_PASS_PROVES_ONLY_CHALLENGED_BEHAVIOR",
        "P2P_EVIDENCE_FIRST_VERIFICATION_V1",
        "`FAST`",
        "`STANDARD`",
        "`STRICT`",
        "`CRITICAL`",
    ):
        assert token in text


def test_charter_records_profile_without_claiming_new_machine_invariant() -> None:
    text = CHARTER.read_text(encoding="utf-8")
    assert "P2P-EVIDENCE-FIRST-VERIFICATION.md" in text
    assert "Coverage and worker\nself-report are supportive inputs, never semantic acceptance authority." in text
    invariant_table = text.split("## 3A.", 1)[0]
    assert "`AGENT_CLAIM_NOT_EVIDENCE`" not in invariant_table
    assert "`TEST_PASS_SCOPE_BOUND`" not in invariant_table
    assert "`PROOF_CARRYING_CHANGE`" not in invariant_table
