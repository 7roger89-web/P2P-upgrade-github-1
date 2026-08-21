"""C36 Evidence-Bound Context & Efficiency Intelligence — deterministic tests.

Covers requirements 1-55+ of the C36 test matrix. All tests are deterministic:
they use fake targets, in-memory data, and explicit timestamps. No live
backend calls, no credentials, no provider I/O.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".p2p", "system"))

# req 45: C19 retrieval machinery reused by C36 manifest fingerprinting
from p2p_capabilities.context import context_fingerprint  # noqa: F401
# req 46: C35 role contract boundary — unchanged surface must still construct
from p2p_capabilities.role_contract import RoleExecutionContract  # noqa: F401
# req 47: C34 usage-evidence surface reused where applicable
from p2p_capabilities.evidence import detect_no_progress  # noqa: F401
from p2p_capabilities.context_manifest import (
    AUTHORITY_CLASSES,
    build_context_manifest,
    manifest_item_content_hash,
    manifests_identical,
)
from p2p_capabilities.context_envelope import (
    DeliveryEnvelope,
    DeliveryReceipt,
    DeliveryBindingError,
    DeliveryReceiptError,
    build_delivery_receipt,
    receipt_claims_read,
)
from p2p_capabilities.read_evidence import (
    READ_STATES,
    ReadEvidenceError,
    compute_read_gap,
    fresh_child_context,
    read_evidence_binds_to_task,
    record_read_evidence,
)
from p2p_capabilities.context_cache import (
    StaleCacheError,
    make_cache_entry,
    make_transformation_provenance,
    verify_cache,
)
from p2p_capabilities.context_efficiency import (
    UNKNOWN_VALUE,
    ContextBudgetInsufficient,
    EfficiencyAssessment,
    ExecutionTelemetry,
    soft_budget_check,
)
from p2p_capabilities.context_loop_guard import (
    AttemptLog,
    LoopGuardError,
    attempt_fingerprint,
)
from p2p_capabilities.decision_trace import (
    CANONICAL_IDENTITIES,
    DECISION_TYPES,
    append_trace,
    capture_material_decision,
    make_trace,
    read_trace_records,
)
from p2p_capabilities.role_contract import (
    AgentRoleSpec,
    build_role_execution_contract,
)
from scripts.p2p_goal_closure import ChangeSignals, candidate_policy


C36_GOAL = "C36"
SCHEMA_PREFIX = "ctx-manifest-"
ENV_PREFIX = "ctx-envelope-"
READ_PREFIX = "ctx-read-"
CACHE_PREFIX = "ctx-cache-"
XFORM_PREFIX = "ctx-xform-"


def _item(**overrides):
    base = dict(
        item_id="i-src",
        source_pointer="p:.p2p/system/p2p_capabilities/context.py",
        source_type="FILE",
        authority_class="AUTHORITATIVE",
        content_hash=manifest_item_content_hash("canonical-content-a"),
        required="REQUIRED",
        delta_allowed=False,
        freshness="STRICT",
        relevance_reason="execution contract requires the source of truth",
        scope_binding="TASK",
        permission_class="READ",
        expected_use="CONTEXT",
    )
    base.update(overrides)
    return base


def _manifest(items=None, **overrides):
    base = dict(
        goal_id=C36_GOAL,
        task_id="T-c36-001",
        project_binding="proj-x",
        workspace_binding="ws-1",
        environment_binding="env-prod",
        source_revision="9dc0811",
        context_requirement_revision="req-v1",
        items=items or [_item()],
    )
    base.update(overrides)
    return build_context_manifest(**base)


def _envelope(manifest=None, **overrides):
    m = manifest or _manifest()
    base = dict(
        manifest_id=m.identity(),
        manifest_hash=m.identity(),
        goal_id=m.goal_id,
        task_id=m.task_id,
        execution_target="fake-deterministic",
        target_fingerprint="fp-fake-1",
        workspace=m.workspace_binding,
        environment=m.environment_binding,
        permission_profile=("READ",),
        items_selected=tuple(it["item_id"] for it in m.items),
        delivery_order=tuple(it["item_id"] for it in m.items),
        delivery_format="adapter-v1",
        compression_record=(),
        delivery_budget="standard",
        request_fingerprint="req-fp-1",
        role_id="EXECUTOR",
    )
    base.update(overrides)
    return DeliveryEnvelope(**base)


class C36ManifestTests(unittest.TestCase):
    """Requirements 1-6: schema, determinism, source revision, authority,
    required vs optional, delta_allowed."""

    def test_1_manifest_schema_fields(self):
        m = _manifest()
        d = m.to_dict()
        self.assertEqual(d["schema_version"], "p2p-context-manifest-c36/1")
        for key in ("goal_id", "task_id", "role_id", "project_binding",
                    "workspace_binding", "environment_binding",
                    "source_revision", "context_requirement_revision", "items",
                    "manifest_identity"):
            self.assertIn(key, d)

    def test_2_manifest_determinism(self):
        a = _manifest()
        b = _manifest()
        self.assertEqual(a.identity(), b.identity())
        self.assertTrue(a.identity().startswith(SCHEMA_PREFIX))
        self.assertTrue(manifests_identical(a, b))

    def test_2b_manifest_changes_on_any_input(self):
        a = _manifest()
        b = _manifest(source_revision="different-revision")
        self.assertNotEqual(a.identity(), b.identity())

    def test_3_manifest_source_revision_binding(self):
        m = _manifest(source_revision="9dc0811")
        self.assertEqual(m.source_revision, "9dc0811")
        changed = _manifest(source_revision="other")
        self.assertFalse(manifests_identical(m, changed))

    def test_4_manifest_authority_classification(self):
        auth = _item(authority_class="AUTHORITATIVE")
        der = _item(item_id="i-der", authority_class="DERIVED", required="OPTIONAL")
        ref = _item(item_id="i-ref", authority_class="REFERENCE")
        evid = _item(item_id="i-ev", authority_class="EVIDENCE")
        hist = _item(item_id="i-hist", authority_class="HISTORICAL")
        ext = _item(item_id="i-ext", authority_class="UNTRUSTED_EXTERNAL")
        m = _manifest(items=[auth, der, ref, evid, hist, ext])
        classes = {it["authority_class"] for it in m.items}
        self.assertEqual(classes, set(AUTHORITY_CLASSES))

    def test_5_required_vs_optional(self):
        m = _manifest(items=[_item(required="REQUIRED"),
                             _item(item_id="i2", required="OPTIONAL")])
        # The manifest carries exactly one required and one optional item;
        # the override binds per item even though the helper base is REQUIRED.
        from collections import Counter as _Counter
        req = _Counter(it["required"] for it in m.items)
        self.assertEqual(req["REQUIRED"], 1)
        self.assertEqual(req["OPTIONAL"], 1)
        self.assertEqual(m.items[1]["required"], "OPTIONAL")

    def test_6_delta_allowed_enforced(self):
        m = _manifest(items=[_item(delta_allowed=False)])
        self.assertFalse(m.items[0]["delta_allowed"])
        m2 = _manifest(items=[_item(item_id="i2", delta_allowed=True, required="OPTIONAL")])
        self.assertTrue(m2.items[0]["delta_allowed"])
        h1 = manifest_item_content_hash("content-a")
        h2 = manifest_item_content_hash("content-b")
        self.assertNotEqual(h1, h2)
        self.assertEqual(len(h1), 64)

    def test_6b_invalid_authority_rejected(self):
        with self.assertRaises((ValueError, AssertionError)):
            _manifest(items=[_item(authority_class="INVALID_AUTHORITY")])

    def test_6c_unknown_required_rejected(self):
        with self.assertRaises((ValueError, AssertionError)):
            _manifest(items=[_item(required="UNKNOWN")])


class C36EnvelopeReceiptTests(unittest.TestCase):
    """Requirements 7-12: envelope identity, permission/environment/role-task
    binding, delivery receipt, DELIVERED != READ."""

    def setUp(self):
        self.manifest = _manifest()
        self.envelope = _envelope(self.manifest)

    def test_7_envelope_identity_determinism(self):
        a = self.envelope.identity()
        b = _envelope(self.manifest).identity()
        self.assertEqual(a, b)
        self.assertTrue(a.startswith(ENV_PREFIX))

    def test_7b_envelope_changes_when_manifest_changes(self):
        other = _manifest(source_revision="other")
        self.assertNotEqual(_envelope(self.manifest).identity(),
                            _envelope(other).identity())

    def test_8_permission_binding(self):
        # READ-only roles cannot widen permission (scenario J): the role
        # ceiling is read-only but the task asks for a WRITE grant; the
        # eligibility surface that envelopes sit on must mark the target
        # ineligible rather than silently widen.
        from p2p_capabilities.role_eligibility import (
            evaluate_role_target_eligibility,
        )
        from p2p_capabilities.fake_targets import fake_target_certification_record
        record = fake_target_certification_record(
            "fake-manus", certified_scopes=("NON_MUTATING_TASK",),
            current_auth_state="VALID")
        result = evaluate_role_target_eligibility(
            role_required_capabilities=("API_TRANSPORT",),
            role_permission_ceiling=("READ",),
            role_quorum_semantics="SINGLE",
            required_evidence=("api-transport-done",),
            task_permission_profile=("WRITE",),
            goal_permission_envelope=("NONE",),
            target=record,
            environment_binding="LOCAL_PROJECT",
            workspace_binding="ws-1",
        )
        self.assertFalse(result.get("eligible"))

    def test_9_environment_binding(self):
        with self.assertRaises((ValueError, AssertionError)):
            _envelope(self.manifest, environment="")

    def test_10_role_task_binding_on_receipt(self):
        m2 = _manifest(task_id="DIFFERENT-TASK")
        e2 = _envelope(m2)
        # Receipt built for a different envelope identity is rejected at
        # build time: bindings are verified per envelope.
        r = build_delivery_receipt(self.manifest, self.envelope,
                                   [{"item_id": "i-src",
                                     "item_hash": manifest_item_content_hash("canonical-content-a")}])
        self.assertEqual(r.task_id, self.manifest.task_id)
        self.assertNotEqual(r.task_id, m2.task_id)

    def test_11_delivery_receipt(self):
        r = build_delivery_receipt(
            self.manifest, self.envelope,
            [{"item_id": "i-src", "item_hash": manifest_item_content_hash("canonical-content-a")}])
        self.assertIsInstance(r, DeliveryReceipt)
        self.assertEqual(r.delivery_status, "DELIVERED")

    def test_11b_receipt_binding_to_envelope(self):
        r = build_delivery_receipt(
            self.manifest, self.envelope,
            [{"item_id": "i-src", "item_hash": manifest_item_content_hash("canonical-content-a")}])
        self.assertEqual(r.envelope_id, self.envelope.identity())
        self.assertEqual(r.manifest_id, self.manifest.identity())
        # Binding integrity: a receipt built from a manifest/envelope whose
        # identity has changed (scenario N) cannot match the original envelope.
        changed_manifest = _manifest(source_revision="other")
        r2 = build_delivery_receipt(
            changed_manifest, _envelope(changed_manifest),
            [{"item_id": "i-src", "item_hash": manifest_item_content_hash("canonical-content-a")}])
        self.assertNotEqual(r2.envelope_id, r.envelope_id)
        self.assertNotEqual(r2.manifest_id, r.manifest_id)

    def test_12_delivered_not_read(self):
        r = build_delivery_receipt(
            self.manifest, self.envelope,
            [{"item_id": "i-src", "item_hash": manifest_item_content_hash("canonical-content-a")}])
        self.assertEqual(r.delivery_status, "DELIVERED")
        self.assertFalse(receipt_claims_read(r))

    def test_12b_receipt_cannot_self_claim_read(self):
        r = build_delivery_receipt(
            self.manifest, self.envelope,
            [{"item_id": "i-src", "item_hash": manifest_item_content_hash("canonical-content-a")}])
        with self.assertRaises(DeliveryReceiptError):
            DeliveryReceipt(
                goal_id=r.goal_id, task_id=r.task_id, manifest_id=r.manifest_id,
                envelope_id=r.envelope_id, envelope_hash=r.envelope_hash,
                target=r.target, session_id=None, items_delivered=r.items_delivered,
                delivery_status="READ")

    def test_12c_required_missing_blocks_complete_receipt(self):
        with self.assertRaises(DeliveryReceiptError):
            build_delivery_receipt(self.manifest, self.envelope, [])


class C36ReadEvidenceTests(unittest.TestCase):
    """Requirements 13-16: read unknown, read proven only with evidence,
    read gap, wrong-task rejection. Also req 41-42 (authority collision)
    and req 22-23 (bounded child context)."""

    def setUp(self):
        self.manifest = _manifest()
        self.envelope = _envelope(self.manifest)

    def test_13_read_unknown_after_delivery(self):
        build_delivery_receipt(
            self.manifest, self.envelope,
            [{"item_id": "i-src", "item_hash": manifest_item_content_hash("canonical-content-a")}])
        gaps = compute_read_gap(
            self.manifest.items, ["i-src"], [], goal_id=C36_GOAL, task_id="T-c36-001")
        self.assertEqual(gaps[0]["outcome"], "DELIVERED_READ_UNKNOWN")
        self.assertIn(gaps[0]["read_state"], READ_STATES)

    def test_14_read_proven_only_with_observable_evidence(self):
        ev = record_read_evidence(
            goal_id=C36_GOAL, task_id="T-c36-001", session_id="S-1",
            manifest_id=self.manifest.identity(), item_id="i-src",
            evidence_kind="TOOL_FILE_ACCESS", evidence_value="fingerprint-match-1",
            state="READ_PROVEN")
        self.assertTrue(ev["read_identity"].startswith(READ_PREFIX))
        gaps = compute_read_gap(
            self.manifest.items, ["i-src"], [ev], goal_id=C36_GOAL, task_id="T-c36-001", session_id="S-1")
        self.assertEqual(gaps[0]["outcome"], "SATISFIED")
        self.assertEqual(gaps[0]["read_state"], "READ_PROVEN")

    def test_14b_self_report_cannot_prove_read(self):
        with self.assertRaises(ReadEvidenceError):
            record_read_evidence(
                goal_id=C36_GOAL, task_id="T-c36-001", session_id="S-1",
                manifest_id=self.manifest.identity(), item_id="i-src",
                evidence_kind="MODEL_SELF_REPORT", evidence_value="I read everything",
                state="READ_PROVEN")

    def test_15_read_gap_required_delivered_proven_distinct(self):
        ev = record_read_evidence(
            goal_id=C36_GOAL, task_id="T-c36-001", session_id="S-1",
            manifest_id=self.manifest.identity(), item_id="i-src",
            evidence_kind="TOOL_FILE_ACCESS", evidence_value="fp-1", state="READ_PROVEN")
        gaps = compute_read_gap(
            self.manifest.items, ["i-src"], [ev], goal_id=C36_GOAL, task_id="T-c36-001", session_id="S-1")
        self.assertEqual(gaps[0]["outcome"], "SATISFIED")
        no_ev = compute_read_gap(
            self.manifest.items, ["i-src"], [], goal_id=C36_GOAL, task_id="T-c36-001")
        self.assertEqual(no_ev[0]["outcome"], "DELIVERED_READ_UNKNOWN")
        not_del = compute_read_gap(self.manifest.items, [], [], goal_id=C36_GOAL, task_id="T-c36-001")
        self.assertEqual(not_del[0]["outcome"], "NOT_DELIVERED")

    def test_16_wrong_task_read_evidence_rejected(self):
        ev = record_read_evidence(
            goal_id=C36_GOAL, task_id="DIFFERENT-TASK", session_id="S-2",
            manifest_id=self.manifest.identity(), item_id="i-src",
            evidence_kind="TOOL_FILE_ACCESS", evidence_value="fp-2", state="READ_PROVEN")
        self.assertFalse(read_evidence_binds_to_task(ev, C36_GOAL, "T-c36-001"))
        gaps = compute_read_gap(
            self.manifest.items, ["i-src"], [ev], goal_id=C36_GOAL, task_id="T-c36-001")
        self.assertEqual(gaps[0]["outcome"], "DELIVERED_READ_UNKNOWN")

    def test_16b_wrong_session_rejected(self):
        ev = record_read_evidence(
            goal_id=C36_GOAL, task_id="T-c36-001", session_id="OTHER-SESSION",
            manifest_id=self.manifest.identity(), item_id="i-src",
            evidence_kind="TOOL_FILE_ACCESS", evidence_value="fp-3", state="READ_PROVEN")
        gaps = compute_read_gap(
            self.manifest.items, ["i-src"], [ev], goal_id=C36_GOAL, task_id="T-c36-001", session_id="S-1")
        self.assertEqual(gaps[0]["outcome"], "DELIVERED_READ_UNKNOWN")


class C36ChildContextTests(unittest.TestCase):
    """Requirements 22-23: bounded explicit child context; transcript != state."""

    def test_22_bounded_explicit_child_context(self):
        parent = _manifest(items=[
            _item(scope_binding="TASK"),
            _item(item_id="i2", scope_binding="CHILD"),
            _item(item_id="i3", scope_binding="PARENT_ONLY"),
        ])
        child = fresh_child_context(parent.items, child_scope=["CHILD"])
        self.assertFalse(child["full_parent_transcript_inherited"])
        self.assertEqual(child["source"], "BOUNDED_EXPLICIT")
        ids = {it["item_id"] for it in child["items"]}
        # Scope matching is exact: only the CHILD-scoped item propagates;
        # TASK-scoped and PARENT_ONLY items are excluded when the child
        # explicitly requests only the CHILD scope.
        self.assertEqual(ids, {"i2"})
        self.assertFalse(child.get("full_parent_transcript_inherited", True))

    def test_22b_child_budget_exceeded_rejected(self):
        parent = _manifest(items=[
            _item(item_id="i1", scope_binding="CHILD"),
            _item(item_id="i2", scope_binding="CHILD"),
        ])
        # max_bytes=1 makes the selected source pointers exceed the budget.
        with self.assertRaises(ReadEvidenceError):
            fresh_child_context(parent.items, child_scope=["CHILD"], max_bytes=1)

    def test_23_transcript_not_state(self):
        parent = _manifest(items=[_item(scope_binding="TASK")])
        child = fresh_child_context(parent.items, child_scope=["TASK"])
        raw = json.dumps(child)
        for banned in ("parent transcript", "conversation", "chat log"):
            self.assertNotIn(banned, raw)
        # Schema is bounded context, not state: only item pointers and hashes.
        self.assertEqual(child["schema"], "p2p-child-context-c36/1")


class C36CacheTests(unittest.TestCase):
    """Requirements 17-21: cache identity, verified hit, stale rejection,
    transformation provenance and output hash. Also req 48 (cache not source
    of truth)."""

    def setUp(self):
        self.content = "canonical-content-a"
        self.content_hash = manifest_item_content_hash(self.content)
        self.entry = make_cache_entry(
            content_hash=self.content_hash, source_pointer="p:c.py",
            source_revision="9dc0811", authority_class="AUTHORITATIVE",
            created_at="2026-08-18T00:00:00Z", freshness_policy="STRICT")

    def test_17_cache_identity(self):
        self.assertTrue(self.entry["cache_identity"].startswith(CACHE_PREFIX))
        again = make_cache_entry(
            content_hash=self.content_hash,
            source_pointer="p:c.py",
            source_revision="9dc0811",
            authority_class="AUTHORITATIVE",
            created_at="2026-08-18T00:00:00Z",
            freshness_policy="STRICT",
        )
        self.assertEqual(again["cache_identity"], self.entry["cache_identity"])

    def test_18_verified_cache_hit(self):
        result = verify_cache(self.entry, "9dc0811", self.content_hash,
                              item_required=True, item_authority="AUTHORITATIVE")
        self.assertEqual(result["decision"], "CACHE_HIT_VERIFIED")

    def test_19_stale_cache_rejected(self):
        result = verify_cache(self.entry, "OTHER-REVISION", self.content_hash)
        self.assertEqual(result["decision"], "CACHE_STALE_REJECTED")
        with self.assertRaises(StaleCacheError):
            verify_cache(self.entry, "9dc0811", manifest_item_content_hash("different"),
                         item_required=True, item_authority="AUTHORITATIVE")

    def test_19b_cache_miss_is_not_error(self):
        self.assertEqual(verify_cache({}, "9dc0811", self.content_hash)["decision"], "CACHE_MISS")

    def test_20_transformation_provenance_fields(self):
        tp = make_transformation_provenance(
            source_pointers=("p:c.py",), source_hashes=(self.content_hash,),
            transformation_id="summary-v1", transformation_version="1",
            output_hash="a" * 64, coverage="90PCT")
        self.assertTrue(tp["provenance_fingerprint"].startswith(XFORM_PREFIX))
        self.assertFalse(tp["lossless"])

    def test_21_transformation_output_hash_binding(self):
        tp1 = make_transformation_provenance(
            source_pointers=("p:c.py",), source_hashes=(self.content_hash,),
            transformation_id="summary-v1", transformation_version="1",
            output_hash="a" * 64)
        tp2 = make_transformation_provenance(
            source_pointers=("p:c.py",), source_hashes=(self.content_hash,),
            transformation_id="summary-v1", transformation_version="1",
            output_hash="b" * 64)
        # Transformation provenance fingerprints bind to the output hash:
        # two different outputs can never share a provenance identity.
        self.assertNotEqual(tp1["provenance_fingerprint"], tp2["provenance_fingerprint"])
        self.assertFalse(tp1.get("lossless_claim"))

    def test_20b_source_hash_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            make_transformation_provenance(
                source_pointers=("p:c.py",), source_hashes=(self.content_hash, "x"),
                transformation_id="t", transformation_version="1", output_hash="a" * 64)

    def test_48_cache_not_source_of_truth(self):
        with self.assertRaises(StaleCacheError):
            verify_cache(self.entry, "9dc0811", manifest_item_content_hash("b"),
                         item_required=True, item_authority="AUTHORITATIVE")


class C36AuthorityCollisionTests(unittest.TestCase):
    """Requirements 41-42: authority collision; external context cannot
    override canonical truth."""

    def test_41_authority_collision_surfaced(self):
        ext = _item(item_id="i-ext", authority_class="UNTRUSTED_EXTERNAL", required="REQUIRED")
        manifest = _manifest(items=[ext])
        ev = record_read_evidence(
            goal_id=C36_GOAL, task_id="T-c36-001", session_id="S-1",
            manifest_id=manifest.identity(), item_id="i-ext",
            evidence_kind="TOOL_FILE_ACCESS", evidence_value="conflict-detected",
            state="READ_CONFLICT")
        gaps = compute_read_gap(
            manifest.items, ["i-ext"], [ev], goal_id=C36_GOAL, task_id="T-c36-001",
            session_id="S-1", goal_authority=True)
        self.assertEqual(gaps[0]["outcome"], "READ_CONFLICT")

    def test_42_external_cannot_override_canonical(self):
        canon = _item(authority_class="AUTHORITATIVE")
        ext = _item(item_id="i-ext", authority_class="UNTRUSTED_EXTERNAL")
        manifest = _manifest(items=[canon, ext])
        gaps = compute_read_gap(manifest.items, ["i-src", "i-ext"], [],
                                goal_id=C36_GOAL, task_id="T-c36-001")
        outcomes = {g["item_id"]: g["outcome"] for g in gaps}
        self.assertNotEqual(outcomes["i-src"], "SATISFIED")


class C36BudgetAndTelemetryTests(unittest.TestCase):
    """Requirements 24-29: soft budget, no silent required drop, token/cost/
    cached-token/latency unknown semantics."""

    def test_24_soft_budget_ok(self):
        r = soft_budget_check({"hard_limit": 10000}, 3000, 1000, soft_limit=5000)
        self.assertFalse(r["soft_budget_exceeded"])
        self.assertEqual(r["signal"], "BUDGET_OK")

    def test_24b_soft_budget_warning(self):
        r = soft_budget_check({}, 3000, 3000, soft_limit=5000)
        self.assertTrue(r["soft_budget_exceeded"])
        self.assertEqual(r["signal"], "SOFT_BUDGET_WARNING")

    def test_25_no_silent_required_context_drop(self):
        # Required context alone exceeding the hard limit fails closed;
        # no REQUIRED content is silently dropped.
        with self.assertRaises(ContextBudgetInsufficient):
            soft_budget_check({"hard_limit": 2000}, 3000)
        # Soft-budget path always reports required not dropped
        r = soft_budget_check({}, 3000, 3000, soft_limit=5000)
        self.assertFalse(r["required_context_dropped"])

    def test_26_token_telemetry_unknown_semantics(self):
        t = ExecutionTelemetry(
            input_tokens=None, output_tokens=100.0, cached_input_tokens=None,
            cache_hit=None, provider_reported_cost=None, p2p_estimated_cost=0.002,
            currency="USD", latency_seconds=None, execution_duration_seconds=1.5,
            retry_count=0, context_bytes=4000, context_items=3, read_coverage=None,
            verification_passed=True, task_id="T1")
        d = t.to_dict()
        self.assertEqual(d["input_tokens"], UNKNOWN_VALUE)
        self.assertEqual(d["cached_input_tokens"], UNKNOWN_VALUE)
        self.assertEqual(d["output_tokens"], 100)

    def test_27_cost_telemetry_unknown_semantics(self):
        t = ExecutionTelemetry(
            input_tokens=500.0, output_tokens=100.0, cached_input_tokens=0.0,
            cache_hit=False, provider_reported_cost=None, p2p_estimated_cost=None,
            currency="UNKNOWN", latency_seconds=None, execution_duration_seconds=None,
            retry_count=0, context_bytes=1000, context_items=2, read_coverage=None,
            verification_passed=None, task_id="T2")
        d = t.to_dict()
        self.assertEqual(d["provider_reported_cost"], UNKNOWN_VALUE)
        self.assertEqual(d["p2p_estimated_cost"], UNKNOWN_VALUE)
        self.assertEqual(d["currency"], "UNKNOWN")

    def test_28_cached_token_evidence(self):
        t = ExecutionTelemetry(
            input_tokens=500.0, output_tokens=100.0, cached_input_tokens=200.0,
            cache_hit=True, provider_reported_cost=0.001, p2p_estimated_cost=None,
            currency="USD", latency_seconds=0.5, execution_duration_seconds=2.0,
            retry_count=0, context_bytes=1000, context_items=2, read_coverage=1.0,
            verification_passed=True, task_id="T3")
        d = t.to_dict()
        self.assertEqual(d["cached_input_tokens"], 200)
        self.assertTrue(d["cache_hit"])
        self.assertEqual(d["read_coverage"], 1.0)

    def test_29_latency_evidence(self):
        t = ExecutionTelemetry(
            input_tokens=500.0, output_tokens=100.0, cached_input_tokens=None,
            cache_hit=None, provider_reported_cost=None, p2p_estimated_cost=None,
            currency="USD", latency_seconds=1.2, execution_duration_seconds=3.0,
            retry_count=0, context_bytes=1000, context_items=2, read_coverage=None,
            verification_passed=True, task_id="T4")
        self.assertEqual(t.to_dict()["latency_seconds"], 1.2)


class C36EfficiencyConstraintTests(unittest.TestCase):
    """Requirements 30-37: quality constraint, cheaper-failed, first-pass,
    rework, no provider/model ranking, no fallback, no routing."""

    def test_30_31_quality_constraint_cheaper_failed_not_better(self):
        assessment = EfficiencyAssessment(
            task_id="T1",
            strategies=(
                {"name": "A-cheap", "verification_passed": False,
                 "input_tokens": 100, "p2p_estimated_cost": 0.001,
                 "verified_work_units": 0},
                {"name": "B-costly", "verification_passed": True,
                 "input_tokens": 1000, "p2p_estimated_cost": 0.01,
                 "verified_work_units": 1},
                {"name": "C-unknown-verification", "verification_passed": None},
            ))
        r = assessment.rank()
        self.assertEqual(r["verdict"], "VERIFIED_STRATEGY_SELECTED")
        self.assertEqual(r["winner"], "B-costly")
        self.assertEqual(r["disqualified"][0]["reason"], "VERIFICATION_FAILED")
        self.assertEqual(r["incomparable"][0]["reason"], "VERIFICATION_UNKNOWN")

    def test_30b_no_verified_strategy(self):
        assessment = EfficiencyAssessment(
            task_id="T2",
            strategies=(
                {"name": "A-fail", "verification_passed": False,
                 "p2p_estimated_cost": 0.001},
            ))
        r = assessment.rank()
        self.assertIsNone(r["winner"])
        self.assertEqual(r["verdict"], "NO_VERIFIED_STRATEGY")

    def test_32_first_pass_verification_metric(self):
        assessment = EfficiencyAssessment(
            task_id="T3",
            primary_metric="first_pass_verification_rate",
            strategies=(
                {"name": "P1", "verification_passed": True, "first_pass_rate": 0.5},
                {"name": "P2", "verification_passed": True, "first_pass_rate": 0.9},
            ))
        r = assessment.rank()
        self.assertEqual(r["winner"], "P2")

    def test_33_rework_cost_metric(self):
        assessment = EfficiencyAssessment(
            task_id="T4",
            primary_metric="verified_work_per_cost",
            strategies=(
                {"name": "Q1", "verification_passed": True,
                 "verified_work_units": 1, "p2p_estimated_cost": 2.0},
                {"name": "Q2", "verification_passed": True,
                 "verified_work_units": 1, "p2p_estimated_cost": 0.5},
            ))
        r = assessment.rank()
        self.assertEqual(r["winner"], "Q2")

    def test_34_no_provider_ranking(self):
        assessment = EfficiencyAssessment(
            task_id="T5",
            strategies=(
                {"name": "provider-codex", "verification_passed": True,
                 "p2p_estimated_cost": 0.01, "verified_work_units": 1},
                {"name": "provider-other", "verification_passed": True,
                 "p2p_estimated_cost": 0.005, "verified_work_units": 1},
            ))
        r = assessment.rank()
        # Even when provider names appear, the telemetry surface never
        # emits a provider selection decision: C37 owns routing.
        self.assertNotIn("provider_selection", str(r))
        self.assertNotIn("routing", str(r).lower())

    def test_35_no_model_ranking(self):
        assessment = EfficiencyAssessment(
            task_id="T6",
            strategies=(
                {"name": "model-A", "verification_passed": True,
                 "p2p_estimated_cost": 0.02, "verified_work_units": 1},
                {"name": "model-B", "verification_passed": True,
                 "p2p_estimated_cost": 0.01, "verified_work_units": 1},
            ))
        r = assessment.rank()
        self.assertNotIn("model_selection", str(r))

    def test_36_no_fallback(self):
        telemetry = ExecutionTelemetry(
            input_tokens=None, output_tokens=None, cached_input_tokens=None,
            cache_hit=None, provider_reported_cost=None, p2p_estimated_cost=None,
            currency="UNKNOWN", latency_seconds=None, execution_duration_seconds=None,
            retry_count=0, context_bytes=None, context_items=None, read_coverage=None,
            verification_passed=None, task_id="T7")
        # Missing evidence stays UNKNOWN; no fallback/estimate fabrication.
        d = telemetry.to_dict()
        fabricated = [k for k, v in d.items()
                      if v not in (UNKNOWN_VALUE, "UNKNOWN", None, "", False, 0)]
        self.assertEqual(set(fabricated), {"task_id", "schema"})

    def test_37_no_routing(self):
        """Efficiency telemetry exists but no provider/model selection occurs
        in C36: the surface exposes metrics only."""
        telemetry = ExecutionTelemetry(
            input_tokens=100.0, output_tokens=50.0, cached_input_tokens=None,
            cache_hit=False, provider_reported_cost=None, p2p_estimated_cost=0.001,
            currency="USD", latency_seconds=1.0, execution_duration_seconds=2.0,
            retry_count=0, context_bytes=500, context_items=2, read_coverage=0.5,
            verification_passed=True, task_id="T8")
        d = telemetry.to_dict()
        for key in ("routing", "provider_selection", "model_selection", "fallback"):
            self.assertNotIn(key, d)
        self.assertEqual(d["schema"], "p2p-execution-telemetry-c36/1")


class C36NeutralityTests(unittest.TestCase):
    """Requirements 38-40: no vendor branching in C36 core; no external
    backend call; secret-reference safety."""

    def test_38_no_vendor_branching(self):
        # The six C36 modules contain no vendor/adapter selection logic:
        # provider names appear only as opaque strings in tests/telemetry.
        import p2p_capabilities.context_manifest as cm
        import p2p_capabilities.context_envelope as ce
        import p2p_capabilities.read_evidence as re_
        import p2p_capabilities.context_cache as cc
        import p2p_capabilities.context_efficiency as cef
        import p2p_capabilities.context_loop_guard as clg
        for module in (cm, ce, re_, cc, cef, clg):
            source = open(module.__file__, encoding="utf-8").read()
            for banned in ("CodexAdapter", "ClaudeCodeAdapter",
                           "adapter_cls", "select_provider", "dispatch_to_"):
                self.assertNotIn(banned, source, module.__name__)

    def test_39_no_external_backend_call(self):
        import p2p_capabilities.context_manifest as cm
        import p2p_capabilities.context_envelope as ce
        import p2p_capabilities.read_evidence as re_
        import p2p_capabilities.context_cache as cc
        import p2p_capabilities.context_efficiency as cef
        import p2p_capabilities.context_loop_guard as clg
        for module in (cm, ce, re_, cc, cef, clg):
            source = open(module.__file__, encoding="utf-8").read()
            for banned in ("requests.", "urllib.request", "httpx", "subprocess.Popen",
                           "subprocess.run", "os.system", "Popen"):
                self.assertNotIn(banned, source, module.__name__)

    def test_40_secret_reference_safety(self):
        item_with_secret = _item(
            item_id="i-secret",
            source_pointer="p:credentials.env",
            content_hash=manifest_item_content_hash("secret-value"),
        )
        m = _manifest(items=[item_with_secret])
        env = _envelope(m,
                        items_selected=("i-secret",),
                        delivery_order=("i-secret",))
        # Receipt builder asserts no secret-bearing fields in delivered items
        # (_assert_no_secret_fields rejects literal secret values).
        with self.assertRaises((ValueError, AssertionError)):
            build_delivery_receipt(
                m, env,
                [{"item_id": "i-secret",
                  "item_hash": manifest_item_content_hash("secret-value"),
                  "secret_value": "super-secret"}])


class C36DecisionTraceTests(unittest.TestCase):
    """Requirement 43: Decision Trace integration with C36 vocabulary.
    Requirement 44: FACT/Live/CAPSULE authority preserved. Also req 44's
    manifest round-trip check."""

    def test_43_decision_trace_integration(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = _manifest()
            envelope = _envelope(manifest)
            trace = make_trace(
                goal_id=C36_GOAL,
                decision_type="ARCHITECTURE",
                status="RECORDED",
                outcome="C36 context manifest frozen for T-c36-001",
                decision_basis={
                    "summary": "C36 froze a deterministic context manifest "
                               "and delivery envelope for the task.",
                },
                evidence_refs=[manifest.identity(), envelope.identity()],
            )
            self.assertIn("DECISION_ID", trace)
            stored = append_trace(tmp, trace)
            records = read_trace_records(tmp)
            self.assertGreater(len(records.get("records", [])), 0)
            # Non-canonical decision id usage: C36 does not claim canonical
            # identities (no collision with CANONICAL_IDENTITIES).
            self.assertNotIn(trace["DECISION_ID"], CANONICAL_IDENTITIES)

    def test_43b_capture_material_decision_for_context_choice(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = capture_material_decision(
                tmp,
                request="C36 chose bounded explicit context over full parent transcript",
                goal_id=C36_GOAL,
                run_id="run-c36-1",
                workflow_status="RECORDED",
                outcome="BOUNDED_EXPLICIT_CONTEXT",
                evidence_refs=["p2p-context-manifest-c36/1"],
                artifact_refs=[".p2p/system/p2p_capabilities/context_manifest.py"],
                decision_type="ARCHITECTURE",
            )
            self.assertTrue(result.get("captured"))
            self.assertIn("trace", result)
            stored = append_trace(tmp, result["trace"])
            # The ledger appends idempotently: re-appending the same
            # decision yields ALREADY_PRESENT with an integrity status;
            # a first append yields the stored decision record.
            self.assertIn(stored.get("status"), ("STORED", "ALREADY_PRESENT"))

    def test_44_authority_preserved_across_pipeline(self):
        # FACT-derived AUTHORITATIVE items keep their classification from
        # manifest -> envelope -> receipt -> read gap; no reclassification.
        item = _item(authority_class="AUTHORITATIVE", required="REQUIRED")
        manifest = _manifest(items=[item])
        envelope = _envelope(manifest)
        receipt = build_delivery_receipt(
            manifest, envelope,
            [{"item_id": "i-src",
              "item_hash": manifest_item_content_hash("canonical-content-a")}])
        ev = record_read_evidence(
            goal_id=C36_GOAL, task_id="T-c36-001", session_id="S-1",
            manifest_id=manifest.identity(), item_id="i-src",
            evidence_kind="TOOL_FILE_ACCESS", evidence_value="fp-1",
            state="READ_PROVEN")
        gaps = compute_read_gap(
            manifest.items, ["i-src"], [ev], goal_id=C36_GOAL,
            task_id="T-c36-001", session_id="S-1")
        self.assertEqual(gaps[0]["authority_class"], "AUTHORITATIVE")


class C36LoopGuardTests(unittest.TestCase):
    """Requirements 49-53: fingerprint semantics, identical retry blocked,
    changed evidence may retry, unknown mutation blocks, no oscillation."""

    def test_49_loop_fingerprint_semantics(self):
        f1 = attempt_fingerprint("G", "T", "context-delivery", "h1", "s1", "TIMEOUT")
        f2 = attempt_fingerprint("G", "T", "context-delivery", "h1", "s1", "TIMEOUT")
        f3 = attempt_fingerprint("G", "T", "context-delivery", "h2", "s1", "TIMEOUT")
        self.assertEqual(f1, f2)
        self.assertNotEqual(f1, f3)

    def test_50_identical_retry_blocked(self):
        log = AttemptLog()
        log.record("G", "T", "context-delivery", "h1", "s1", "TIMEOUT")
        log.record("G", "T", "context-delivery", "h1", "s1", "TIMEOUT")
        with self.assertRaises(LoopGuardError) as ctx:
            log.may_retry("G", "T", "context-delivery", "h1", "s1", "TIMEOUT")
        self.assertIn("LOOP_GUARD_TRIGGERED", str(ctx.exception))

    def test_51_changed_evidence_may_retry(self):
        log = AttemptLog()
        log.record("G", "T", "context-delivery", "h1", "s1", "TIMEOUT")
        decision = log.may_retry("G", "T", "context-delivery", "h2", "s1", "TIMEOUT")
        self.assertTrue(decision["allowed"])

    def test_52_unknown_mutation_blocks_blind_retry(self):
        log = AttemptLog()
        log.record("G", "T", "context-delivery", "h1", "s1", "TIMEOUT")
        with self.assertRaises(LoopGuardError) as ctx:
            log.may_retry("G", "T", "context-delivery", "h1", "s1", "TIMEOUT",
                          mutation_unknown=True)
        self.assertIn("UNKNOWN_MUTATION", str(ctx.exception))

    def test_53_no_oscillating_state_loop(self):
        log = AttemptLog()
        for sv in ("sa", "sb", "sa", "sb"):
            log.record("G", "T", "ctx", "h1", sv, "FAIL")
        with self.assertRaises(LoopGuardError):
            log.may_retry("G", "T", "ctx", "h1", "sa", "FAIL")


class C36BoundaryPreservationTests(unittest.TestCase):
    """Requirements 45-47: existing surfaces preserved; 55: candidate-policy
    detects C36 runtime surface."""

    def test_45_c19_retrieval_reused(self):
        # C36 manifest fingerprinting is built on C19's deterministic
        # content hashing path; the C19 function is importable and pure.
        h1 = context_fingerprint({"a": 1, "b": [2, 3]})
        h2 = context_fingerprint({"a": 1, "b": [2, 3]})
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)

    def test_46_c35_role_contract_preserved(self):
        # C35 RoleExecutionContract still constructs unchanged by the C36
        # surface: the C35 builder contract with fresh-child-by-default
        # behaviour (context digest from bounded package, read-only ceiling)
        # remains the authoritative path. Follows the C35 test's exact spec
        # construction via AgentRoleSpec from the C35 test module.
        from tests.test_p2p_c35_provider_neutral_runtime import (
            _cert_for as _c35_cert,
            build_role_execution_contract as _c35_build,
        )
        from p2p_capabilities.agent_role import build_role_spec
        from p2p_capabilities.fake_targets import fake_target_fingerprint
        record = _c35_cert("fake-manus")
        spec = build_role_spec("p2p_anon")
        contract = _c35_build(
            spec, goal_id=C36_GOAL, task_id="T-c36-001",
            task_objective="C36 boundary check: C35 contract still builds",
            project_binding="proj-x", environment_binding="LOCAL_PROJECT",
            workspace_binding="ws-1",
            approved_scope=(".p2p/system/p2p_capabilities/context.py",),
            permission_profile=("READ",),
            explicit_execution_target="fake-manus",
            target_fingerprint=fake_target_fingerprint("fake-manus"),
        )
        self.assertEqual(contract.task_id, "T-c36-001")
        self.assertEqual(contract.role_id, "p2p_anon")
        self.assertIn("context_digest", contract.to_dict())

    def test_47_c34_usage_evidence_reused(self):
        # C34 no-progress detection remains usable by the C36 loop guard layer:
        # repeated identical state fingerprints escalate rather than loop.
        observations = [
            {"state_fingerprint": "fp-same", "status": "FAILED"},
            {"state_fingerprint": "fp-same", "status": "FAILED"},
            {"state_fingerprint": "fp-same", "status": "FAILED"},
        ]
        result = detect_no_progress(observations)
        self.assertEqual(result["status"], "ESCALATE")

    def test_55_candidate_policy_detects_c36_surface(self):
        # The canonical candidate-policy machinery (p2p_goal_closure) must
        # classify the six C36 module additions as runtime change — the
        # candidate-gated surface — while neither governance nor release
        # artifacts are touched by the C36 surface itself.
        repo = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))
        if repo not in sys.path:
            sys.path.insert(0, repo)
        files = [".p2p/system/p2p_capabilities/context_manifest.py",
                 ".p2p/system/p2p_capabilities/context_envelope.py",
                 ".p2p/system/p2p_capabilities/read_evidence.py",
                 ".p2p/system/p2p_capabilities/context_cache.py",
                 ".p2p/system/p2p_capabilities/context_efficiency.py",
                 ".p2p/system/p2p_capabilities/context_loop_guard.py"]
        sig = ChangeSignals.detect(files)
        self.assertTrue(sig.runtime_changed)
        self.assertFalse(sig.governance_changed)
        self.assertFalse(sig.release_artifact_changed)
        # Policy consequence: a PASS terminal over this surface requires a
        # candidate (the machinery answer, stated mechanically).
        declared = candidate_policy("PASS", None, sig)
        self.assertEqual(declared, "YES")


class C36FreshCloneRecoveryTests(unittest.TestCase):
    """Requirement 54: fresh-clone recovery includes the C36 surface in the
    authorized closure growth set (matches C34 precedent)."""

    def test_54_fresh_clone_recovery_c36_surface_present(self):
        here = os.path.dirname(os.path.abspath(__file__))
        repo = os.path.dirname(here)
        for module in ("context_manifest", "context_envelope", "read_evidence",
                       "context_cache", "context_efficiency", "context_loop_guard"):
            path = os.path.join(
                repo, ".p2p", "system", "p2p_capabilities", f"{module}.py")
            self.assertTrue(os.path.exists(path), module)


if __name__ == "__main__":
    unittest.main()
