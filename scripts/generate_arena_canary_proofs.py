#!/usr/bin/env python3
"""Generate durable Arena FAST_CANARY runtime proofs for Issue #254.

Emits, for the SAME repository state and from the real runtime surfaces:
  1. a generated medium/high-risk NEW Arena Control Tower prompt (FAST_CANARY
     injected, ONE first-turn return contract, no terminal packet contract);
  2. a generated Arena prompt for a task the Control Tower explicitly declared
     LOW_RISK_MECHANICAL (FAST_CANARY bypassed);
  3. a generated non-Arena prompt for the same medium/high-risk task;
  4. the Owner /goal beginner Arena packet for a triggered canary (one active
     first-turn mode; RULE 20 only inside the deferred resumed-task section);
  5. a pure evidence-only canary ingest: the canonical CANARY_EVIDENCE_PACKET_V1
     plus checkpoint metadata, ingested through the real CLI and graded
     externally, followed by Owner continuation.

The proofs are real CLI / builder output, not documentation strings.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
for candidate in (str(REPO_ROOT / ".p2p" / "system"), str(REPO_ROOT / "scripts"), str(REPO_ROOT)):
    if candidate not in sys.path:
        sys.path.insert(0, candidate)

import p2p_control_tower as control_tower  # noqa: E402
from p2p_capabilities import owner_goal  # noqa: E402

MEDIUM_HIGH_TASK = (
    "Repair the Control Tower runtime so a new medium/high-risk Arena session "
    "stops at the FAST_CANARY boundary, mutating runtime prompt generation, "
    "ledger events and gates"
)
LOW_RISK_TASK = "Fix a typo in the README changelog label"
GOAL_COMMAND = "/goal Hoàn thiện workflow hợp đồng logistics, dùng Arena"

REQUIRED_TOKENS = (
    "FAST_CANARY_REQUIRED=YES",
    "REAL_TASK_FIRST_SLICE=CANARY",
    "CANARY_DURABLE_MUTATION_ALLOWED=NO",
    "STOP_AFTER_CANARY=YES",
    "EXECUTOR_SELF_CLASSIFICATION=FORBIDDEN",
    "MODEL_IDENTITY=UNKNOWN",
    "CANARY_EVIDENCE_PACKET_V1",
    "FIRST_TURN_RETURN_CONTRACT=CANARY_EVIDENCE_PACKET_V1_THEN_STOP",
    "CONTINUATION_CHECKPOINT=READY",
    "OWNER_ACTION_REQUIRED=YES",
    "NATIVE_ACTION_HINT=KEEP_WORKING_IF_APPROVED",
    "FALLBACK_OWNER_REPLY=Tiếp tục công việc",
)
CONFLICTING_TERMINAL_CONTRACT = (
    "CONTROL_TOWER_RETURN_PACKET_BEGIN",
    "CONTROL_TOWER_RETURN_PACKET_END",
    "Finish with one structured CONTROL_TOWER_RETURN_PACKET",
    "Return a truthful terminal packet",
)
EVIDENCE_ONLY_RESPONSE = "\n".join(
    (
        "CANARY_EVIDENCE_PACKET_V1",
        "P2P_LAW_SOURCE=7roger89-web/P2P-upgrade-github-1@main:docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md",
        "CURRENT_STATE=arena/canary @ 3cb8049921805dbd963a091d9b37ae06a3a9fd61",
        "FACTS=canary prompt carries one first-turn return contract; ledger holds session start",
        "DECISIVE_CHECK=python3 scripts/p2p_control_tower.py snapshot --json",
        "CHECK_RESULT=exit=0; PASS",
        "ERRORS_ENCOUNTERED=NONE",
        "RECOVERY_ACTIONS=NONE",
        "DURABLE_MUTATION_CREATED=NO",
        "MODEL_IDENTITY=UNKNOWN",
        "",
        "CONTINUATION_CHECKPOINT=READY",
        "OWNER_ACTION_REQUIRED=YES",
        "NATIVE_ACTION_HINT=KEEP_WORKING_IF_APPROVED",
        "FALLBACK_OWNER_REPLY=Tiếp tục công việc",
        "",
    )
)


def run_cli(root: Path, *args: str) -> dict:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = control_tower.main(["--root", str(root), *args, "--json"])
    if code != 0:
        raise SystemExit(f"control tower {args[0]} failed: {buffer.getvalue()}")
    return json.loads(buffer.getvalue())


def generate(root: Path, host: str, goal: str, session_id: str, *extra: str) -> str:
    result = run_cli(
        root,
        "start",
        "--host",
        host,
        "--goal-id",
        "P2P-CT01-CANARY",
        "--task-id",
        "TASK-CANARY-1",
        "--session-id",
        session_id,
        "--goal",
        goal,
        *extra,
    )
    return result["recommendation"]["PROMPT"]


def split_resumed_section(text: str) -> tuple[str, str]:
    lines = text.splitlines()
    begin = next(i for i, line in enumerate(lines) if line.startswith("RESUMED_TASK_CONTRACT"))
    end = lines.index(owner_goal.RESUMED_TASK_CONTRACT_END)
    return "\n".join(lines[:begin] + lines[end + 1 :]), "\n".join(lines[begin : end + 1])


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="p2p-canary-proof-") as directory:
        root = Path(directory)
        medium_high = generate(root, "ARENA", MEDIUM_HIGH_TASK, "proof-arena-medium-high")
        low_risk = generate(root, "ARENA", LOW_RISK_TASK, "proof-arena-low-risk", "--low-risk-mechanical")
        non_arena = generate(root, "CODEX", MEDIUM_HIGH_TASK, "proof-codex-medium-high")
        goal_project = root / "goal-project"
        goal_project.mkdir()
        intake = owner_goal.build_owner_goal_intake(goal_project, GOAL_COMMAND)
        # Dedicated project root: exactly one triggered canary session.
        ingest_root = root / "ingest-proof"
        ingest_root.mkdir()
        generate(ingest_root, "ARENA", MEDIUM_HIGH_TASK, "proof-arena-canary-ingest")
        response_path = ingest_root / "canary-response.txt"
        response_path.write_text(EVIDENCE_ONLY_RESPONSE, encoding="utf-8")
        graded = run_cli(
            ingest_root, "ingest", "--response-file", str(response_path), "--session-id", "proof-arena-canary-ingest"
        )
        resumed = run_cli(
            ingest_root, "continue", "--session-id", "proof-arena-canary-ingest", "--owner-reply", "Tiếp tục công việc"
        )
        ledger_types = [
            json.loads(line)["event_type"]
            for line in (ingest_root / ".p2p" / "state" / "execution-ledger.jsonl").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    goal_packet = intake["beginner_arena_handoff"]["packet_text"].replace(directory, "<TMP>")
    goal_active, goal_deferred = split_resumed_section(goal_packet)

    report: list[str] = []
    report.append("P2P Arena FAST_CANARY runtime proof (Issue #254)")
    report.append("")
    report.append("Generated by scripts/generate_arena_canary_proofs.py from the real Control Tower")
    report.append("CLI (`scripts/p2p_control_tower.py start|ingest|continue`) and the real Owner /goal")
    report.append("intake. Sizes, token presence and grades are measured, not asserted from docs.")
    report.append("")

    report.append("=== GENERATED_MEDIUM_HIGH_ARENA_PROMPT_PROOF ===")
    report.append("HOST=ARENA; SESSION=NEW; SESSION_QUALITY=UNKNOWN; RISK=MEDIUM_OR_HIGH_RISK (fail closed)")
    report.append(f"TASK={MEDIUM_HIGH_TASK}")
    report.append(f"PROMPT_CHARS={len(medium_high)}")
    for token in REQUIRED_TOKENS:
        report.append(f"{token} -> {'PRESENT' if token in medium_high else 'MISSING'}")
    for marker in CONFLICTING_TERMINAL_CONTRACT:
        report.append(f"CONFLICT:{marker} -> {'PRESENT (defect)' if marker in medium_high else 'ABSENT (expected)'}")
    report.append(
        "FIRST_TURN_RETURN_CONTRACT occurrences -> "
        f"{medium_high.count('FIRST_TURN_RETURN_CONTRACT=CANARY_EVIDENCE_PACKET_V1_THEN_STOP')}"
    )
    report.append(f"CONTROL_TOWER_CONTEXT -> {'PRESENT' if control_tower.CONTEXT_MARKER in medium_high else 'MISSING'}")
    report.append(f"OE_GATE -> {'PRESENT' if 'OE_GATE=' in medium_high else 'MISSING'}")
    report.append(f"CONTROL_TOWER_SELF_LAW_RECEIPT -> {'PRESENT' if 'CONTROL_TOWER_SELF_LAW_RECEIPT=' in medium_high else 'MISSING'}")
    report.append(f"SUPREME_LAW_CAPSULE -> {'PRESENT' if 'SUPREME_LAW_CAPSULE:' in medium_high else 'MISSING'}")
    report.append(f"ORIGINAL_REAL_TASK_PRESERVED -> {'PRESENT' if MEDIUM_HIGH_TASK in medium_high else 'MISSING'}")
    report.append("")

    report.append("=== GENERATED_LOW_RISK_ARENA_PROMPT_PROOF (explicit --low-risk-mechanical) ===")
    report.append("HOST=ARENA; SESSION=NEW; RISK=LOW_RISK_MECHANICAL (explicit Control Tower declaration)")
    report.append(f"TASK={LOW_RISK_TASK}")
    report.append(f"PROMPT_CHARS={len(low_risk)}")
    for token in REQUIRED_TOKENS:
        report.append(f"{token} -> {'PRESENT (unexpected)' if token in low_risk else 'ABSENT (expected)'}")
    report.append(f"TERMINAL_RETURN_CONTRACT -> {'PRESENT (expected)' if 'CONTROL_TOWER_RETURN_PACKET_BEGIN' in low_risk else 'MISSING'}")
    report.append("")

    report.append("=== GENERATED_NON_ARENA_PROMPT_PROOF (same medium/high task) ===")
    report.append("HOST=CODEX; SESSION=NEW")
    report.append(f"PROMPT_CHARS={len(non_arena)}")
    for token in REQUIRED_TOKENS:
        report.append(f"{token} -> {'PRESENT (unexpected)' if token in non_arena else 'ABSENT (expected)'}")
    report.append("")

    report.append("=== OWNER_GOAL_ARENA_CANARY_PACKET_PROOF (beginner packet the Owner pastes) ===")
    report.append(f"COMMAND={GOAL_COMMAND}")
    report.append(f"FAST_CANARY_REQUIRED={intake['arena_handoff']['fast_canary_required']}")
    report.append(f"EXECUTION_MODE={intake['arena_handoff']['execution_mode']}")
    report.append(f"RESUMED_TASK_MODE={intake['arena_handoff']['resumed_task_mode']}")
    report.append(f"PACKET_CHARS={len(goal_packet)}")
    report.append(f"ACTIVE:AUTONOMOUS_UNTIL_TERMINAL -> {'PRESENT (defect)' if 'AUTONOMOUS_UNTIL_TERMINAL' in goal_active else 'ABSENT (expected)'}")
    report.append(f"ACTIVE:RULE20 -> {'PRESENT (defect)' if 'RULE20' in goal_active else 'ABSENT (expected)'}")
    report.append(f"ACTIVE:branch/PR creation -> {'PRESENT (defect)' if 'create exactly one bounded branch' in goal_active else 'ABSENT (expected)'}")
    report.append(f"ACTIVE:STOP_AFTER_CANARY=YES -> {'PRESENT' if 'STOP_AFTER_CANARY=YES' in goal_active else 'MISSING'}")
    report.append(f"DEFERRED:RESUMED_TASK_MODE=AUTONOMOUS_UNTIL_TERMINAL -> {'PRESENT' if 'RESUMED_TASK_MODE=AUTONOMOUS_UNTIL_TERMINAL' in goal_deferred else 'MISSING'}")
    report.append("")

    report.append("=== PURE_CANARY_EVIDENCE_ONLY_INGEST_PROOF ===")
    report.append(f"INPUT_CONTAINS_CONTROL_TOWER_RETURN_PACKET={'YES (defect)' if 'CONTROL_TOWER_RETURN_PACKET' in EVIDENCE_ONLY_RESPONSE else 'NO'}")
    report.append("COMMAND=p2p_control_tower.py ingest --response-file canary-response.txt --session-id proof-arena-canary-ingest")
    report.append(f"CANARY_CLASSIFICATION={graded['canary_grade']['CLASSIFICATION']}")
    report.append(f"SESSION_POLICY={graded['canary_grade']['SESSION_POLICY']}")
    report.append(f"NEXT_SAFE_ACTION={graded['snapshot']['NEXT_SAFE_ACTION']['ACTION']}")
    report.append(f"OWNER_GATE={graded['snapshot']['OWNER_GATES'][0]['GATE']}")
    report.append(f"RESUMED_PROMPT_HAS_TERMINAL_CONTRACT={'YES' if 'CONTROL_TOWER_RETURN_PACKET_BEGIN' in resumed['recommendation']['PROMPT'] else 'NO'}")
    report.append(f"CONTINUATION_MODE={resumed['recommendation']['CONTINUATION_MODE']}")
    report.append(f"CONTINUATION_SESSION_ID={resumed['recommendation']['SESSION_ID']}")
    report.append(f"CANARY_REPEAT={resumed['recommendation']['CANARY_REPEAT']}")
    report.append(f"LEDGER_EVENTS={','.join(ledger_types)}")
    report.append("")

    report.append("=== FULL GENERATED MEDIUM/HIGH ARENA PROMPT ===")
    report.append(medium_high)
    report.append("")
    report.append("=== FULL GENERATED LOW-RISK ARENA PROMPT ===")
    report.append(low_risk)
    report.append("")

    out_dir = REPO_ROOT / "evidence" / "p2p-arena-canary-runtime-254"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "generated-arena-prompts.txt").write_text("\n".join(report), encoding="utf-8")
    (out_dir / "generated-medium-high-arena-prompt.txt").write_text(medium_high, encoding="utf-8")
    (out_dir / "generated-low-risk-arena-prompt.txt").write_text(low_risk, encoding="utf-8")
    (out_dir / "generated-owner-goal-arena-canary-packet.txt").write_text(goal_packet, encoding="utf-8")
    (out_dir / "canary-evidence-only-ingest-input.txt").write_text(EVIDENCE_ONLY_RESPONSE, encoding="utf-8")
    print(f"WROTE {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
