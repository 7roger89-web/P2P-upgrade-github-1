from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from p2p_workflow import append_event  # noqa: E402
from p2p_capabilities.control_tower_handoff import (  # noqa: E402
    NO_UPLOAD_INSTRUCTION,
    USER_ACTION_BLOCK,
    ControlTowerAttachment,
    ControlTowerAttachmentManifest,
    ControlTowerHandoffError,
    ControlTowerReturnPacket,
    ControlTowerRotationHandoff,
    ControlTowerState,
    ControlTowerSuccessorPacket,
    bind_session,
    build_execution_prompt,
    create_return_packet,
    normalize_host,
    prepare_control_tower_rotation,
    reconcile_control_tower_successor,
    to_execution_ledger_event,
)


BASE_SHA = "a" * 64
BASE_TREE = "b" * 64
STALE_SHA = "c" * 64
STALE_TREE = "d" * 64


class ControlTowerSessionHandoffTests(unittest.TestCase):
    def binding(self, host: str = "CODEX"):
        return bind_session(
            session_id=f"ct01-{host.lower()}-session",
            host=host,
            goal_id="P2P-CT01",
            goal="Durable Control Tower Session Handoff Integration",
        )

    def packet(self, host: str = "CODEX", state: str = "READY", **overrides):
        values = {
            "session_state": state,
            "canonical_base_sha": BASE_SHA,
            "canonical_base_tree": BASE_TREE,
            "canonical_relation": "CURRENT",
            "worktree": str(REPO_ROOT / ".tmp" / "p2p-ct01-test-worktree"),
            "branch": "codex/p2p-ct01-control-tower",
            "changes": ["protocol-boundary"],
            "test_results": {"focused": "PENDING"},
            "evidence": ["E1-P1B-TEST"],
            "candidate_or_checkpoint_sha": "UNKNOWN",
            "next_recommended_action": "Return packet to Control Tower.",
        }
        values.update(overrides)
        return create_return_packet(self.binding(host), **values)

    def ingest(self, state: ControlTowerState, packet: ControlTowerReturnPacket, **kwargs):
        return state.ingest(
            packet,
            current_canonical_base_sha=BASE_SHA,
            current_canonical_base_tree=BASE_TREE,
            **kwargs,
        )

    def successor_handoff(self, **overrides):
        values = {
            "current_control_tower_instance_id": "CT001",
            "proposed_successor_control_tower_instance_id": "CT002",
            "latest_control_tower_snapshot_sequence": 7,
            "current_canonical_claim": {
                "status": "INTEGRATED",
                "candidate": "UNPROMOTED",
            },
            "current_canonical_confidence": "CONFIRMED",
            "host_lanes": {
                "MANUS": {
                    "SESSION_ID": "manus-active-session",
                    "CONTROL_TOWER_STATUS": "RUNNING",
                },
                "CODEX": {
                    "CONTROL_TOWER_STATUS": "IDLE",
                },
            },
            "confirmed_active_execution": {
                "SESSION_ID": "manus-active-session",
                "HOST": "MANUS",
                "GOAL_ID": "P2P-CT01",
                "STATE": "RUNNING",
            },
            "owner_gates": (
                {"GATE_ID": "OWNER_REVIEW_CT01", "STATUS": "PENDING"},
            ),
            "pending_work": ("Reconcile durable evidence",),
            "recently_closed_material_work": ("Attachment-aware handoff",),
            "blockers_and_risks": (
                {"RISK_ID": "CHAT_CONTEXT_NOT_CANONICAL", "STATUS": "OPEN"},
            ),
            "critical_invariants": (
                "Successor packet is bootstrap data, not canonical truth",
                "Do not transfer host lanes",
            ),
            "next_safe_action": "Reconcile the packet with durable P2P evidence.",
            "durable_evidence_checkpoint_refs": ("checkpoint:ct01/7",),
            "unresolved_chat_only_not_canonical": ("CT001 narrative remains chat-only",),
        }
        values.update(overrides)
        return prepare_control_tower_rotation(**values)

    def test_a_ready_return_is_not_promotion(self):
        state = ControlTowerState.empty(["MANUS"])

        result = self.ingest(state, self.packet(state="READY"))

        self.assertEqual(result.control_tower_status, "READY")
        self.assertEqual(result.mapped_lifecycle_state, "READY")
        self.assertFalse(result.promoted)
        self.assertFalse(result.protected_action_executed)
        self.assertFalse(result.packet_is_canonical_truth)
        self.assertEqual(state.lanes["CODEX"]["PROMOTED"], False)

    def test_b_blocked_lane_isolated_and_not_success(self):
        state = ControlTowerState.empty(["CODEX"])

        result = self.ingest(
            state,
            self.packet(host="MANUS", state="BLOCKED", blockers=("HOST_UNAVAILABLE",)),
        )

        self.assertEqual(result.host, "MANUS")
        self.assertEqual(result.control_tower_status, "BLOCKED")
        self.assertEqual(result.mapped_lifecycle_state, "BLOCKED")
        self.assertEqual(result.blockers, ("HOST_UNAVAILABLE",))
        self.assertFalse(result.promoted)
        self.assertEqual(state.lanes["CODEX"]["CONTROL_TOWER_STATUS"], "IDLE")

    def test_c_explicit_authoritative_host_beats_codex_manus_prose(self):
        state = ControlTowerState.empty(["MANUS"])

        result = self.ingest(
            state,
            self.packet(host="CODEX"),
            narrative_host="MANUS says that the prose should select MANUS",
        )

        self.assertEqual(result.host, "CODEX")
        self.assertTrue(result.narrative_host_ignored)
        self.assertIn("CODEX", state.lanes)
        self.assertEqual(state.lanes["MANUS"]["CONTROL_TOWER_STATUS"], "IDLE")

    def test_d_stale_base_requires_reconciliation_without_overwrite(self):
        state = ControlTowerState.empty(["MANUS"])
        packet = self.packet(
            state="READY",
            canonical_base_sha=STALE_SHA,
            canonical_base_tree=STALE_TREE,
            canonical_relation="CURRENT",
        )

        result = self.ingest(state, packet)

        self.assertEqual(result.canonical_relation, "STALE")
        self.assertEqual(result.control_tower_status, "RECONCILIATION_REQUIRED")
        self.assertFalse(result.promoted)
        self.assertFalse(result.canonical_state_overwritten)
        self.assertEqual(
            state.lanes["CODEX"]["CURRENT_CANONICAL_BASE_SHA"],
            BASE_SHA,
        )
        self.assertIn("CANONICAL_BASE_STALE", result.blockers)
        self.assertEqual(state.lanes["MANUS"]["CONTROL_TOWER_STATUS"], "IDLE")

    def test_e_waiting_owner_gate_records_gate_without_protected_action(self):
        state = ControlTowerState.empty()
        gate = {"gate_id": "CT01_OWNER_REVIEW", "required_action": "review packet"}

        result = self.ingest(
            state,
            self.packet(state="WAITING_OWNER_GATE", owner_gate=gate),
        )

        self.assertEqual(result.control_tower_status, "WAITING_OWNER_GATE")
        self.assertEqual(result.owner_gate, gate)
        self.assertFalse(result.protected_action_executed)
        self.assertFalse(result.promoted)
        self.assertEqual(state.return_events[-1]["PROTECTED_ACTION_EXECUTED"], "NO")

    def test_f_failed_return_is_recorded_without_false_success(self):
        state = ControlTowerState.empty()

        result = self.ingest(
            state,
            self.packet(
                state="FAILED",
                blockers=("TEST_FAILURE",),
                next_recommended_action="Return failure and await a new bounded attempt.",
            ),
        )

        self.assertEqual(result.control_tower_status, "FAILED")
        self.assertEqual(result.mapped_lifecycle_state, "BLOCKED")
        self.assertTrue(result.failure_recorded)
        self.assertFalse(result.promoted)
        self.assertFalse(result.protected_action_executed)
        self.assertEqual(state.return_events[-1]["CONTROL_TOWER_RECONCILIATION"]["FAILURE_RECORDED"], True)

    def test_g_recursive_prompt_contains_return_contract_and_exact_user_action(self):
        binding = self.binding("CLAUDE")
        prompt = build_execution_prompt(
            binding,
            "Continue the bounded CT01 implementation.",
            worktree=str(REPO_ROOT / ".tmp" / "ct01-prompt"),
            branch="claude/ct01",
            canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE,
            acceptance_criteria=("preserve canonical truth", "return terminal state"),
        )

        self.assertIn("CONTROL_TOWER_RETURN_PACKET", prompt)
        for field_name in (
            "SESSION_ID",
            "HOST",
            "GOAL_ID",
            "GOAL",
            "SESSION_STATE",
            "CANONICAL_BASE_SHA",
            "CANONICAL_BASE_TREE",
            "CANONICAL_RELATION",
            "WORKTREE",
            "BRANCH",
            "CHANGES",
            "TEST_RESULTS",
            "EVIDENCE",
            "CANDIDATE_OR_CHECKPOINT_SHA",
            "TERMINAL_VERDICT",
            "OWNER_GATE",
            "BLOCKERS",
            "NEXT_RECOMMENDED_ACTION",
        ):
            self.assertIn(field_name, prompt)
        self.assertIn("P2P_SUPREME_LAW_PREFLIGHT", prompt)
        self.assertIn("P2P_SUPREME_OPERATING_LAW_V1", prompt)
        self.assertIn("TASK_BRANCH != LAW_AUTHORITY", prompt)
        self.assertIn("TARGET_PROJECT != LAW_SOURCE", prompt)
        self.assertIn("even when the task executes in a different repository or branch", prompt)
        self.assertIn("7roger89-web/P2P-upgrade-github-1@main", prompt)
        self.assertIn("docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md", prompt)
        self.assertIn(".p2p/system/docs/P2P-OPERATIONS-NOTEBOOK.md", prompt)
        self.assertIn("SUPREME_LAW_CAPSULE", prompt)
        self.assertIn("defer premature supporting infrastructure or ceremony", prompt)
        self.assertIn("Keep one active Supreme Law", prompt)
        self.assertIn("Do not claim that a repository file was read unless it actually was.", prompt)
        self.assertIn("PACKET_IS_CANONICAL_TRUTH: NO", prompt)
        self.assertIn(USER_ACTION_BLOCK, prompt)
        self.assertNotIn("previous session transcript", prompt.lower())

    def test_h_authoritative_host_wins_and_only_its_lane_changes(self):
        state = ControlTowerState.empty(["CODEX", "MANUS"])
        before_codex = dict(state.lanes["CODEX"])
        before_manus = dict(state.lanes["MANUS"])

        result = self.ingest(
            state,
            self.packet(host="GEMINI"),
            narrative_host="CLAUDE",
        )

        self.assertEqual(result.host, "GEMINI")
        self.assertEqual(state.lanes["CODEX"], before_codex)
        self.assertEqual(state.lanes["MANUS"], before_manus)
        self.assertEqual(state.lanes["GEMINI"]["SESSION_STATE"], "READY")

    def test_invalid_binding_and_implicit_inheritance_fail_closed(self):
        with self.assertRaises(ControlTowerHandoffError):
            bind_session(
                session_id="ct01",
                host="CODEX",
                goal_id="P2P-CT01",
                goal="goal",
                inherited_state={},
            )

        with self.assertRaises(ControlTowerHandoffError):
            bind_session(
                session_id="ct01",
                host="Codex is authoritative because the prose says so",
                goal_id="P2P-CT01",
                goal="goal",
            )

        with self.assertRaises(ControlTowerHandoffError):
            ControlTowerReturnPacket.from_mapping({"schema": "wrong"})

    def test_owner_gate_is_required_for_waiting_state(self):
        with self.assertRaises(ControlTowerHandoffError):
            self.packet(state="WAITING_OWNER_GATE")

    def test_unknown_base_is_not_current(self):
        state = ControlTowerState.empty()
        packet = self.packet(
            canonical_base_sha="UNKNOWN",
            canonical_base_tree="UNKNOWN",
            canonical_relation="CURRENT",
        )

        result = state.ingest(
            packet,
            current_canonical_base_sha="UNKNOWN",
            current_canonical_base_tree="UNKNOWN",
        )

        self.assertEqual(result.canonical_relation, "UNKNOWN")
        self.assertEqual(result.control_tower_status, "RECONCILIATION_REQUIRED")
        self.assertFalse(result.promoted)

    def test_packet_round_trip_event_and_projection_are_json_safe(self):
        packet = self.packet(
            changes={"files": ["control_tower_handoff.py"]},
            test_results={"focused": "PASS"},
        )
        restored = ControlTowerReturnPacket.from_mapping(packet.to_dict())
        state = ControlTowerState.empty()
        result = self.ingest(state, restored)
        event = to_execution_ledger_event(restored, result)

        json.dumps(packet.to_dict(), ensure_ascii=False)
        json.dumps(event, ensure_ascii=False)
        projection = state.to_dict()
        json.dumps(projection, ensure_ascii=False)
        self.assertEqual(restored.binding.to_dict(), packet.binding.to_dict())
        self.assertEqual(restored.session_state, "READY")
        self.assertEqual(event["CANONICAL_TRUTH_UPDATED"], "NO")
        self.assertEqual(projection["PROMOTION_EXECUTED"], "NO")

    def test_future_provider_label_is_normalized_without_provider_logic(self):
        self.assertEqual(normalize_host("future-host"), "FUTURE_HOST")
        self.assertEqual(self.binding("generic-real").host, "GENERIC_REAL")

    def test_isolated_worktree_path_stays_under_repo_tmp(self):
        test_tmp_root = REPO_ROOT / ".tmp"
        test_tmp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=test_tmp_root, prefix="ct01-isolated-") as temp_path:
            temp_root = Path(temp_path).resolve()
            self.assertTrue(temp_root.is_relative_to(test_tmp_root.resolve()))
            packet = self.packet(worktree=str(temp_root))
            self.assertTrue(Path(packet.worktree).is_relative_to(test_tmp_root.resolve()))

    def test_return_event_uses_existing_execution_ledger_writer(self):
        test_tmp_root = REPO_ROOT / ".tmp"
        test_tmp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=test_tmp_root, prefix="ct01-ledger-") as temp_path:
            ledger = Path(temp_path) / ".p2p" / "state" / "execution-ledger.jsonl"
            packet = self.packet()
            state = ControlTowerState.empty()
            result = self.ingest(state, packet)
            append_event(ledger, to_execution_ledger_event(packet, result))
            stored = json.loads(ledger.read_text(encoding="utf-8").splitlines()[0])

        self.assertEqual(stored["schema_version"], "p2p-execution-event/1")
        self.assertEqual(stored["event_type"], "CONTROL_TOWER_RETURN_PACKET")
        self.assertEqual(
            stored["CONTROL_TOWER_RETURN_PACKET"]["PACKET_IS_CANONICAL_TRUTH"],
            "NO",
        )

    def test_attachment_manifest_no_upload_requires_only_copy_back(self):
        packet = self.packet(attachment_manifest=ControlTowerAttachmentManifest())

        serialized = packet.to_dict()
        manifest = serialized["CONTROL_TOWER_ATTACHMENT_MANIFEST"]

        self.assertEqual(serialized["UPLOAD_REQUIRED"], "NO")
        self.assertEqual(manifest["UPLOAD_REQUIRED"], "NO")
        self.assertEqual(manifest["ATTACHMENTS"], [])
        self.assertEqual(manifest["USER_INSTRUCTION"], NO_UPLOAD_INSTRUCTION)
        self.assertEqual(manifest["LOCAL_PATH_ALONE_PROVES_CONTENTS_AVAILABLE"], "NO")
        self.assertEqual(manifest["ATTACHMENTS_ARE_CANONICAL_TRUTH"], "NO")

    def test_attachment_manifest_yes_lists_one_minimal_required_file(self):
        entry = ControlTowerAttachment(
            filename="ct01-handoff.md",
            local_path=str(REPO_ROOT / ".tmp" / "ct01-handoff.md"),
            purpose="Consolidated terminal handoff",
            why_control_tower_needs_contents="The Control Tower cannot read executor-local reports by path alone.",
        )
        packet = self.packet(
            attachment_manifest=ControlTowerAttachmentManifest(
                upload_required="YES",
                attachments=(entry,),
            )
        )

        manifest = packet.to_dict()["CONTROL_TOWER_ATTACHMENT_MANIFEST"]
        self.assertEqual(packet.to_dict()["UPLOAD_REQUIRED"], "YES")
        self.assertEqual(len(manifest["ATTACHMENTS"]), 1)
        self.assertEqual(manifest["ATTACHMENTS"][0]["FILENAME"], "ct01-handoff.md")
        self.assertEqual(manifest["ATTACHMENTS"][0]["CLASSIFICATION"], "REQUIRED")
        self.assertEqual(manifest["ATTACHMENTS"][0]["CONTENTS_AVAILABLE_TO_CONTROL_TOWER"], "UNKNOWN")

    def test_attachment_manifest_preserves_required_optional_and_do_not_upload(self):
        entries = (
            ControlTowerAttachment(
                filename="required.md",
                local_path=".tmp/required.md",
                purpose="Required evidence",
                why_control_tower_needs_contents="It contains the exact terminal result.",
                classification="REQUIRED",
            ),
            ControlTowerAttachment(
                filename="optional.md",
                local_path=".tmp/optional.md",
                purpose="Optional context",
                why_control_tower_needs_contents="It provides extra context only.",
                classification="OPTIONAL",
            ),
            ControlTowerAttachment(
                filename="secrets.txt",
                local_path=".tmp/secrets.txt",
                purpose="Protected local material",
                why_control_tower_needs_contents="It is not needed and must remain local.",
                classification="DO_NOT_UPLOAD",
            ),
        )

        manifest = ControlTowerAttachmentManifest("YES", entries)

        self.assertEqual(
            [item["CLASSIFICATION"] for item in manifest.to_dict()["ATTACHMENTS"]],
            ["REQUIRED", "OPTIONAL", "DO_NOT_UPLOAD"],
        )

    def test_attachment_local_path_alone_is_not_contents_access(self):
        entry = ControlTowerAttachment(
            filename="evidence.md",
            local_path=".tmp/evidence.md",
            purpose="Evidence input",
            why_control_tower_needs_contents="The Control Tower must inspect the uploaded content.",
        )

        serialized = entry.to_dict()

        self.assertEqual(serialized["LOCAL_PATH"], ".tmp/evidence.md")
        self.assertEqual(serialized["LOCAL_PATH_ALONE_PROVES_CONTENTS_AVAILABLE"], "NO")
        self.assertEqual(serialized["CONTENTS_AVAILABLE_TO_CONTROL_TOWER"], "UNKNOWN")

    def test_attachment_is_evidence_input_not_canonical_truth(self):
        entry = ControlTowerAttachment(
            filename="handoff.md",
            local_path=".tmp/handoff.md",
            purpose="Return evidence",
            why_control_tower_needs_contents="The Control Tower cannot infer the report contents from a path.",
        )
        packet = self.packet(
            attachment_manifest=ControlTowerAttachmentManifest("YES", (entry,))
        )
        state = ControlTowerState.empty()

        result = self.ingest(state, packet)
        lane = state.lanes["CODEX"]
        event_packet = state.return_events[-1]["CONTROL_TOWER_RETURN_PACKET"]

        self.assertEqual(result.control_tower_status, "READY")
        self.assertEqual(lane["UPLOAD_REQUIRED"], "YES")
        self.assertEqual(lane["CONTROL_TOWER_ATTACHMENT_MANIFEST"]["ATTACHMENTS_ARE_CANONICAL_TRUTH"], "NO")
        self.assertEqual(event_packet["PACKET_IS_CANONICAL_TRUTH"], "NO")
        self.assertEqual(event_packet["CONTROL_TOWER_ATTACHMENT_MANIFEST"]["ATTACHMENTS_ARE_EVIDENCE_INPUT_ONLY"], "YES")

    def test_recursive_prompt_preserves_attachment_aware_contract(self):
        prompt = build_execution_prompt(
            self.binding("MANUS"),
            "Continue the bounded CT01 handoff.",
            worktree=str(REPO_ROOT / ".tmp" / "ct01-prompt"),
            branch="manus/ct01",
            canonical_base_sha=BASE_SHA,
            canonical_base_tree=BASE_TREE,
        )

        for field_name in (
            "UPLOAD_REQUIRED",
            "CONTROL_TOWER_ATTACHMENT_MANIFEST",
            "FILENAME",
            "LOCAL_PATH",
            "PURPOSE",
            "WHY_CONTROL_TOWER_NEEDS_CONTENTS",
            "REQUIRED",
            "OPTIONAL",
            "DO_NOT_UPLOAD",
        ):
            self.assertIn(field_name, prompt)
        self.assertIn("local path alone does not make file contents available", prompt.lower())
        self.assertIn("attachments are evidence input only", prompt.lower())
        self.assertIn("SESSION_ID-CONTROL-TOWER-HANDOFF.md", prompt)
        self.assertIn("P2P_CONTROL_TOWER_SUCCESSOR_PACKET", prompt)
        self.assertIn("CHAT_ONLY_NOT_CANONICAL", prompt)
        self.assertIn("Control Tower chats are rotatable", prompt)

    def test_attachment_manifest_rejects_ambiguous_upload_requirements(self):
        entry = ControlTowerAttachment(
            filename="optional.md",
            local_path=".tmp/optional.md",
            purpose="Optional context",
            why_control_tower_needs_contents="It is not required for reconciliation.",
            classification="OPTIONAL",
        )

        with self.assertRaises(ControlTowerHandoffError):
            ControlTowerAttachmentManifest("NO", (entry,))

        with self.assertRaises(ControlTowerHandoffError):
            ControlTowerAttachmentManifest("YES", ())

        with self.assertRaises(ControlTowerHandoffError):
            ControlTowerAttachmentManifest("YES", (entry,))

    def test_rotation_a_ct001_to_ct002_preserves_material_state(self):
        handoff = self.successor_handoff()
        serialized = handoff.to_dict()
        restored = ControlTowerSuccessorPacket.from_mapping(
            serialized["P2P_CONTROL_TOWER_SUCCESSOR_PACKET"]
        )

        result = reconcile_control_tower_successor(
            restored,
            current_canonical_claim={"status": "INTEGRATED", "candidate": "UNPROMOTED"},
            current_canonical_confidence="CONFIRMED",
            current_snapshot_sequence=7,
            expected_successor_control_tower_instance_id="CT002",
        )

        self.assertEqual(handoff.old_chat_archive_name, "90 — P2P CONTROL TOWER — CT001 — ARCHIVE")
        self.assertEqual(handoff.new_chat_name, "00 — P2P CONTROL TOWER — CT002")
        self.assertEqual(result.control_tower_status, "READY")
        self.assertEqual(result.canonical_claim_relation, "CURRENT")
        self.assertEqual(result.snapshot_sequence_relation, "CURRENT")
        self.assertEqual(result.pending_work, ("Reconcile durable evidence",))
        self.assertEqual(result.host_lanes["MANUS"]["SESSION_ID"], "manus-active-session")
        self.assertEqual(result.unresolved_chat_only_not_canonical, ("CT001 narrative remains chat-only",))
        self.assertFalse(result.packet_is_canonical_truth)

    def test_rotation_b_owner_gates_persist_without_execution(self):
        packet = self.successor_handoff().successor_packet

        result = reconcile_control_tower_successor(
            packet,
            current_canonical_claim=packet.current_canonical_claim,
            current_canonical_confidence=packet.current_canonical_confidence,
            current_snapshot_sequence=packet.latest_control_tower_snapshot_sequence,
        )

        self.assertEqual(result.owner_gates, packet.owner_gates)
        self.assertFalse(result.owner_gate_executed)
        self.assertFalse(result.owner_approval_inherited)
        self.assertFalse(result.promoted)
        self.assertEqual(result.to_dict()["OWNER_GATE_EXECUTED"], "NO")

    def test_rotation_c_confirmed_manus_execution_remains_manus(self):
        packet = self.successor_handoff().successor_packet

        result = reconcile_control_tower_successor(
            packet,
            current_canonical_claim=packet.current_canonical_claim,
            current_canonical_confidence=packet.current_canonical_confidence,
            current_snapshot_sequence=packet.latest_control_tower_snapshot_sequence,
        )

        self.assertIsNotNone(result.confirmed_active_execution)
        self.assertEqual(result.confirmed_active_execution["HOST"], "MANUS")
        self.assertEqual(result.confirmed_active_execution["SESSION_ID"], "manus-active-session")
        self.assertFalse(result.active_execution_closed)
        self.assertFalse(result.host_lane_reassigned)

    def test_rotation_d_stale_canonical_claim_requires_reconciliation(self):
        packet = self.successor_handoff().successor_packet

        result = reconcile_control_tower_successor(
            packet,
            current_canonical_claim={"status": "PROMOTED", "candidate": "DIFFERENT"},
            current_canonical_confidence="CONFIRMED",
            current_snapshot_sequence=packet.latest_control_tower_snapshot_sequence,
        )

        self.assertEqual(result.canonical_claim_relation, "STALE")
        self.assertEqual(result.control_tower_status, "RECONCILIATION_REQUIRED")
        self.assertIn("CANONICAL_CLAIM_STALE", result.blockers)
        self.assertFalse(result.packet_is_canonical_truth)
        self.assertIn("durable P2P evidence", result.next_safe_action)

    def test_rotation_e_missing_active_execution_is_not_invented(self):
        handoff = self.successor_handoff(
            confirmed_active_execution=None,
            host_lanes={"MANUS": {"CONTROL_TOWER_STATUS": "IDLE"}},
        )

        result = reconcile_control_tower_successor(
            handoff.successor_packet,
            current_canonical_claim=handoff.successor_packet.current_canonical_claim,
            current_canonical_confidence=handoff.successor_packet.current_canonical_confidence,
            current_snapshot_sequence=handoff.successor_packet.latest_control_tower_snapshot_sequence,
        )

        self.assertIsNone(result.confirmed_active_execution)
        self.assertFalse(result.active_execution_invented)
        self.assertFalse(result.active_execution_closed)
        self.assertEqual(result.host_lanes["MANUS"]["CONTROL_TOWER_STATUS"], "IDLE")

    def test_rotation_f_beginner_bootstraps_without_full_history(self):
        handoff = self.successor_handoff()
        serialized = handoff.to_dict()
        json.dumps(serialized, ensure_ascii=False)
        restored = ControlTowerRotationHandoff.from_mapping(serialized)

        self.assertTrue(serialized["CONTROL_TOWER_ROTATION_HANDOFF"])
        self.assertTrue(serialized["P2P_CONTROL_TOWER_SUCCESSOR_PACKET"]["P2P_CONTROL_TOWER_SUCCESSOR_PACKET"])
        self.assertEqual(serialized["FULL_CHAT_HISTORY_INCLUDED"], "NO")
        self.assertIn("Rename the current Control Tower chat to", serialized["ROTATION_USER_ACTION"])
        self.assertIn("Create a new chat named", serialized["ROTATION_USER_ACTION"])
        self.assertIn("Do not manually summarize", serialized["ROTATION_USER_ACTION"])
        self.assertEqual(restored.successor_packet.current_control_tower_instance_id, "CT001")
        self.assertEqual(restored.successor_packet.proposed_successor_control_tower_instance_id, "CT002")
        self.assertEqual(restored.successor_packet.to_dict()["FULL_CHAT_HISTORY_INCLUDED"], "NO")


if __name__ == "__main__":
    unittest.main()
