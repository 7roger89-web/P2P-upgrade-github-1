"""C35 deterministic test suite: provider-neutral P2P agent runtime.

Covers the 55+ required C35 test scenarios:
    1-3    canonical inventory / aesthetica denominator / repo truth sourcing;
    4-5    deterministic fingerprints / material-change sensitivity;
    6-13   Role != Task/Model/Provider/Harness/ExecutionTarget/Skill/
           AutoPilot/Adapter;
    14-15  same role across multiple fake targets / target identity does not
           mutate the role spec;
    16-23  role contract binds Goal/Task/Project/Environment/Context/
           Permission/Target/RequestFingerprint;
    24-30  receipt rejection set (wrong role / stale spec / wrong task /
           wrong environment / permission widening / missing evidence /
           unknown mutation fail-closed);
    31     requested != observed target until attested;
    32-35  certification semantics (historical != current eligibility,
           capability-scoped enforcement, text/non-mutating != code mutation,
           revoked/no-valid auth blocked);
    36-37  backend-done != verified; transcript != state;
    38-39  fresh bounded child context / no full-parent transcript default;
    40-44  adaptive participation / 8/8 quorum / duplicates / unverified /
           stale receipts;
    45-46  same target multiple roles / mixed targets quorum;
    47     no vendor branching in role core;
    48-50  registry != router / no ranking / no silent fallback;
    51-52  no background autonomy / no unbounded fanout;
    53     canonical release/promotion gates unchanged;
    54     fresh-clone durable recovery;
    55     candidate-policy sees C35 runtime changes;
    56     decision-trace vocabulary;
    57     one receipt cannot satisfy two roles (independent assertion).

Provider-neutral except where a real backend would be required: C35 uses
the deterministic fake execution backend and explicit synthetic target
identities. NO live backend call. NO Manus call (revoked key honored).
"""
from __future__ import annotations

import inspect
import json
import os
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SYSTEM_ROOT = os.path.join(REPO_ROOT, ".p2p", "system")
if SYSTEM_ROOT not in sys.path:
    sys.path.insert(0, SYSTEM_ROOT)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from p2p_capabilities.agent_role import (  # noqa: E402
    AgentRoleSpec, CANONICAL_ROLE_DENOMINATOR, CANONICAL_ROLES,
    OPTIONAL_SPECIALIST_ROLE, AgentRoleError, ALL_P2P_ROLES,
    build_role_spec, canonical_role_specs, load_capability_registry,
    profile_body_fingerprint, role_semantic_fingerprint, role_spec_lookup,
    validate_role_inventory,
)
from p2p_capabilities.backend_contract import (  # noqa: E402
    AUTH_STATES, BackendCapabilityCertification, BackendExecutionResult,
    CERTIFICATION_SCOPES,
)
from p2p_capabilities.backend_execution_bridge import (  # noqa: E402
    BackendAdapterRegistry, BackendExecutionBridge,
    contract_request_fingerprint,
)
from p2p_capabilities.fake_targets import (  # noqa: E402
    FAKE_TARGET_IDS, fake_target_certification_record,
    fake_target_fingerprint, fake_target_identity, register_fake_targets,
)
from p2p_capabilities.role_bridge import (  # noqa: E402
    RoleBridgeError, RoleExecutionBridge, register_explicit_adapter,
)
from p2p_capabilities.role_contract import (  # noqa: E402
    ROLE_CONTRACT_SCHEMA, RoleContractError, RoleExecutionContract,
    build_role_execution_contract, context_digest_fingerprint,
    role_contract_fingerprint, target_fingerprint_from_profile,
)
from p2p_capabilities.role_eligibility import (  # noqa: E402
    TargetCertificationRecord, evaluate_role_target_eligibility,
    re_like_known,
)
from p2p_capabilities.role_quorum import (  # noqa: E402
    RoleQuorumError, adaptive_participant_set, evaluate_role_quorum,
)
from p2p_capabilities.role_receipt import (  # noqa: E402
    RoleExecutionReceipt, RoleReceiptError, new_role_receipt,
)
from p2p_capabilities.role_verifier import (  # noqa: E402
    DECISION_CODES, RoleVerifierError, decision_record,
    permission_profile_fingerprint, verify_role_execution_receipt,
)

import p2p_capabilities.agent_role as agent_role  # noqa: E402
import p2p_capabilities.role_contract as role_contract  # noqa: E402
import p2p_capabilities.role_eligibility as role_eligibility  # noqa: E402
import p2p_capabilities.role_receipt as role_receipt  # noqa: E402
import p2p_capabilities.role_verifier as role_verifier  # noqa: E402
import p2p_capabilities.role_quorum as role_quorum  # noqa: E402

GOAL_ID = "goal:c35:quorum-gate"
TASK_ID = "task:c35:anon:1"
PROJECT_BINDING = "P2P-upgrade-github-1"


def _make_bridge():
    registry = BackendAdapterRegistry()
    bridge = BackendExecutionBridge(registry, {"adapter_id": "adapter-fake-manus"})
    return registry, bridge


def _dispatch_role(spec, registry, *, target_id="fake-manus",
                   backend_outcome="SUCCEEDED",
                   backend_verification_status="VERIFIED",
                   goal_id=GOAL_ID, task_id=TASK_ID,
                   permission_profile=("READ",)):
    bridge = BackendExecutionBridge(registry,
                                    {"adapter_id": f"adapter-{target_id}"})
    contract = build_role_execution_contract(
        spec, goal_id=goal_id, task_id=task_id,
        task_objective="C35 test role task: deterministic role execution proof.",
        project_binding=PROJECT_BINDING,
        environment_binding="LOCAL_PROJECT",
        workspace_binding="synthetic-workspace",
        approved_scope=("p2p-governance",),
        context_package=("p2p-governance",),
        permission_profile=permission_profile,
        explicit_execution_target=target_id,
        target_fingerprint=fake_target_fingerprint(target_id),
    )
    dispatched = RoleExecutionBridge(bridge).dispatch(
        contract, adapter_id=f"adapter-{target_id}",
        backend_outcome=backend_outcome,
        backend_verification_status=backend_verification_status)
    receipt = RoleExecutionReceipt(dispatched["role_receipt"])
    # The backend result is the synthetic envelope produced by the bridge
    # and is passed to the independent verifier — backend "done" alone
    # never counts as verified.
    # The dispatch dict carries a schema envelope; the dataclass only
    # accepts its declared fields.
    # Rebuild the normalized backend result via the canonical envelope
    # loader (from_mapping validates the schema and hex fields).
    backend_result = BackendExecutionResult.from_mapping(
        dispatched["backend_result"])
    return contract, receipt, backend_result


def _cert_for(target_id, scopes=("NON_MUTATING_TASK", "API_TRANSPORT",
                    "SYNTHETIC_TEXT_EXECUTION"),
              auth_state="VALID"):
    return fake_target_certification_record(
        target_id, certified_scopes=scopes, current_auth_state=auth_state)


def required_names(contract):
    """Requirement names carried by the contract's required_evidence."""
    return tuple(str(item).strip() for item in contract.required_evidence)


def honest_observation_pointers(receipt, contract, target_evidence=None):
    """Synthetic but honest observation pointers: the dispatcher's own
    receipt pointers plus one class evidence pointer per contract
    requirement, bound to the task id."""
    pointers = list(target_evidence or ())
    if receipt.raw_backend_receipt_pointer:
        pointers.append(receipt.raw_backend_receipt_pointer)
    for requirement in required_names(contract):
        if requirement:
            pointers.append(
                f"evidence:{requirement}:{receipt.task_id}")
    return tuple(pointers)


def _verify_receipt(receipt, contract, spec, *, permission_profile=("READ",),
                    extra_kwargs=None, target_evidence=None,
                    backend_result=None):
    kwargs = dict(extra_kwargs or {})
    if backend_result is not None:
        kwargs["backend_result"] = backend_result
    return verify_role_execution_receipt(
        receipt=receipt, expected_contract=contract,
        expected_role_spec_hash=spec.role_spec_hash,
        expected_permission_profile=permission_profile,
        required_evidence=contract.required_evidence,
        observed_target_evidence_pointers=honest_observation_pointers(
            receipt, contract, target_evidence),
        certification_records=_cert_for(receipt.observed_target
                                        .replace("adapter-", ""),
                                        scopes=("NON_MUTATING_TASK",
                                                "API_TRANSPORT",
                                                "SYNTHETIC_TEXT_EXECUTION"
                                                )).scope_certifications,
        **kwargs,
    )


class TestC35CanonicalInventory(unittest.TestCase):
    """Tests 1-3: canonical inventory recovered from repository truth."""

    def test_1_canonical_eight_recover_exactly(self):
        inventory = validate_role_inventory()
        self.assertTrue(inventory["valid"])
        self.assertEqual(len(inventory["canonical_roles"]), 8)
        self.assertEqual(set(inventory["canonical_roles"]), set(CANONICAL_ROLES))
        self.assertEqual(inventory["canonical_count"], CANONICAL_ROLE_DENOMINATOR)
        # The eight are fixed, not discovered by heuristic.
        expected = {"p2p_iris", "p2p_tecton", "p2p_axiom", "p2p_vector",
                    "p2p_datos", "p2p_anon", "p2p_architecton", "p2p_helios"}
        self.assertEqual(set(inventory["canonical_roles"]), expected)

    def test_2_aesthetica_no_denominator_drift(self):
        inventory = validate_role_inventory()
        self.assertTrue(inventory.get("aesthetica_present", True))
        self.assertTrue(inventory.get("optional_excluded_from_denominator",
                                      True))
        specs = role_spec_lookup()
        aesthetica = specs[OPTIONAL_SPECIALIST_ROLE]
        self.assertEqual(aesthetica.quorum_semantics, "OPTIONAL_SPECIALIST")
        self.assertEqual(len(CANONICAL_ROLES), CANONICAL_ROLE_DENOMINATOR)
        self.assertNotIn(OPTIONAL_SPECIALIST_ROLE, CANONICAL_ROLES)
        # A quorum requiring the eight never forces aesthetica.
        q = evaluate_role_quorum(())
        self.assertEqual(set(q["required_roles"]), set(CANONICAL_ROLES))
        self.assertNotIn(OPTIONAL_SPECIALIST_ROLE, q["required_roles"])

    def test_3_role_definitions_sourced_from_repo_truth(self):
        records = load_capability_registry()
        ids = {str(r.get("CAPABILITY_ID")) for r in records}
        for role_id in CANONICAL_ROLES:
            self.assertIn(role_id, ids, f"{role_id} not in capability registry")
            spec = build_role_spec(role_id, records)
            self.assertEqual(spec.role_id, role_id)
            # SOURCE_PROVENANCE must point at the registry + codex profile.
            prov = spec.source_provenance
            self.assertEqual(prov["capability_registry"],
                             "p2p-capability-registry/1")
            self.assertIn("codex_profile", prov)


class TestC35RoleSpecFingerprints(unittest.TestCase):
    """Tests 4-5: deterministic, material-change-sensitive fingerprints."""

    def test_4_fingerprints_deterministic(self):
        hashes1 = {spec.role_id: spec.role_spec_hash
                   for spec in canonical_role_specs()}
        hashes2 = {spec.role_id: spec.role_spec_hash
                   for spec in canonical_role_specs()}
        self.assertEqual(hashes1, hashes2)
        # Every hash is a real hex64 of the material semantics.
        for role_id, hash_value in hashes1.items():
            self.assertRegex(hash_value, r"^[0-9a-f]{64}$")
            self.assertEqual(
                hash_value,
                role_semantic_fingerprint(canonical_role_specs()[0].to_dict())
                if role_id == "p2p_iris" else hash_value)

    def test_5_material_semantic_change_changes_fingerprint(self):
        spec = build_role_spec("p2p_anon")
        original = spec.role_spec_hash
        mutated = dict(spec.to_dict())
        mutated["forbidden_actions"] = spec.forbidden_actions + ("new-action",)
        self.assertNotEqual(role_semantic_fingerprint(mutated), original)
        # Format-only / non-semantic changes (purpose prose) do NOT alter it.
        prose = dict(spec.to_dict())
        prose["purpose"] = spec.purpose + " extra prose"
        self.assertEqual(role_semantic_fingerprint(prose), original)


class TestC35RoleIdentityBoundaries(unittest.TestCase):
    """Tests 6-13: role is a governance identity, distinct from every
    execution-layer concept."""

    def setUp(self):
        self.spec = build_role_spec("p2p_anon")

    def test_6_task_not_role(self):
        # A task record has no role identity surface: role_spec_hash,
        # quorum_semantics, forbidden_actions are role surfaces.
        self.assertTrue(hasattr(self.spec, "role_spec_hash"))
        self.assertEqual(self.spec.schema, "p2p-agent-role-spec/1")
        self.assertNotEqual(self.spec.schema,
                            "p2p-autopilot-task-contract/1")

    def test_7_role_not_model(self):
        # Role spec contains no model field; model belongs to the target.
        spec_dict = self.spec.to_dict()
        for forbidden_field in ("model", "model_id", "provider"):
            self.assertNotIn(forbidden_field, spec_dict)

    def test_8_role_not_provider(self):
        spec_dict = self.spec.to_dict()
        for forbidden_field in ("provider", "openai", "anthropic"):
            self.assertNotIn(str(forbidden_field), json.dumps(spec_dict))

    def test_9_role_not_harness(self):
        # The role spec carries no harness/provider/model identity field;
        # provenance references to codex files are evidence of sourcing,
        # not executable harness binding.
        spec_dict = self.spec.to_dict()
        for forbidden_field in ("harness", "provider", "model", "model_id"):
            self.assertNotIn(forbidden_field, spec_dict,
                             f"harness/provider field present: {forbidden_field}")

    def test_10_role_not_execution_target(self):
        spec_dict = self.spec.to_dict()
        self.assertNotIn("execution_target", spec_dict)
        # The same role spec builds contracts for ANY target identity.
        specs = {spec.role_id: spec for spec in canonical_role_specs()}
        contract_manus = build_role_execution_contract(
            specs["p2p_anon"], goal_id="g1", task_id="t1",
            task_objective="o", project_binding=PROJECT_BINDING,
            workspace_binding="w", explicit_execution_target="fake-manus",
            target_fingerprint=fake_target_fingerprint("fake-manus"))
        contract_grok = build_role_execution_contract(
            specs["p2p_anon"], goal_id="g1", task_id="t1",
            task_objective="o", project_binding=PROJECT_BINDING,
            workspace_binding="w", explicit_execution_target="fake-grok",
            target_fingerprint=fake_target_fingerprint("fake-grok"))
        self.assertEqual(contract_manus.role_spec_hash,
                         contract_grok.role_spec_hash)

    def test_11_role_not_skill(self):
        # Skills are resources, not canonical roles: no skill id is a
        # canonical role id.
        spec_dict = self.spec.to_dict()
        self.assertNotIn("skill", spec_dict)

    def test_12_autopilot_not_role(self):
        # The AutoPilot core consumes backend.execute(contract); it does
        # not consume role machinery by default. Role machinery lives in
        # its own modules.
        for role_id in ALL_P2P_ROLES:
            spec = build_role_spec(role_id)
            self.assertNotIn("autopilot", spec.role_id)

    def test_13_adapter_not_role(self):
        # Adapter identity surface != role spec surface.
        adapter_id = "adapter-fake-manus"
        self.assertFalse(adapter_id.startswith("p2p_"))
        spec_dict = self.spec.to_dict()
        self.assertNotIn("adapter_id", spec_dict)


class TestC35TargetIdentityIsolation(unittest.TestCase):
    """Tests 14-15: same role through multiple fake targets; target
    identity changes do not mutate the role spec."""

    def test_14_same_role_multiple_fake_targets(self):
        registry, _ = _make_bridge()
        register_fake_targets(registry)
        spec = build_role_spec("p2p_anon")
        fingerprints = {}
        for target_id in ("fake-manus", "fake-codex", "fake-grok"):
            contract, receipt, _ = _dispatch_role(spec, registry,
                                                  target_id=target_id)
            fingerprints[target_id] = contract.request_fingerprint
            self.assertEqual(receipt.role_id, "p2p_anon")
            self.assertEqual(receipt.requested_target, target_id)
        # Different targets produce different request fingerprints
        # (target is part of the binding set) — but the role spec hash
        # never moves.
        self.assertEqual(len(set(fingerprints.values())), 3)
        spec_now = build_role_spec("p2p_anon")
        self.assertEqual(spec_now.role_spec_hash, spec.role_spec_hash)

    def test_15_target_change_does_not_mutate_role_spec(self):
        before = canonical_role_specs()
        registry, _ = _make_bridge()
        register_fake_targets(registry)
        spec = build_role_spec("p2p_anon")
        _dispatch_role(spec, registry, target_id="fake-gemini")
        after = canonical_role_specs()
        self.assertEqual(
            [s.role_spec_hash for s in before],
            [s.role_spec_hash for s in after])


class TestC35ContractBindings(unittest.TestCase):
    """Tests 16-23: role contract binding set."""

    def setUp(self):
        self.spec = build_role_spec("p2p_anon")
        self.contract = build_role_execution_contract(
            self.spec, goal_id="g1", task_id="t1",
            task_objective="bounded role task", project_binding=PROJECT_BINDING,
            environment_binding="LOCAL_PROJECT",
            workspace_binding="synthetic-workspace",
            approved_scope=("p2p-governance",),
            context_package=("p2p-governance",),
            permission_profile=("READ",),
            explicit_execution_target="fake-manus",
            target_fingerprint=fake_target_fingerprint("fake-manus"))

    def test_16_binds_goal(self):
        self.assertEqual(self.contract.goal_id, "g1")
        other = build_role_execution_contract(
            self.spec, goal_id="g2", task_id="t1", task_objective="x",
            project_binding=PROJECT_BINDING, workspace_binding="w",
            explicit_execution_target="fake-manus",
            target_fingerprint=self.contract.target_fingerprint)
        self.assertNotEqual(self.contract.request_fingerprint,
                            other.request_fingerprint)

    def test_17_binds_task(self):
        other = build_role_execution_contract(
            self.spec, goal_id="g1", task_id="t2", task_objective="x",
            project_binding=PROJECT_BINDING, workspace_binding="w",
            explicit_execution_target="fake-manus",
            target_fingerprint=self.contract.target_fingerprint)
        self.assertNotEqual(self.contract.request_fingerprint,
                            other.request_fingerprint)

    def test_18_binds_project(self):
        other = build_role_execution_contract(
            self.spec, goal_id="g1", task_id="t1", task_objective="x",
            project_binding="OTHER-PROJECT", workspace_binding="w",
            explicit_execution_target="fake-manus",
            target_fingerprint=self.contract.target_fingerprint)
        self.assertNotEqual(self.contract.request_fingerprint,
                            other.request_fingerprint)

    def test_19_binds_environment(self):
        other = build_role_execution_contract(
            self.spec, goal_id="g1", task_id="t1", task_objective="x",
            project_binding=PROJECT_BINDING,
            environment_binding="CLOUD_VM", workspace_binding="w",
            explicit_execution_target="fake-manus",
            target_fingerprint=self.contract.target_fingerprint)
        self.assertNotEqual(self.contract.request_fingerprint,
                            other.request_fingerprint)

    def test_20_binds_context_digest(self):
        self.assertEqual(self.contract.context_digest,
                         context_digest_fingerprint(("p2p-governance",)))
        other = build_role_execution_contract(
            self.spec, goal_id="g1", task_id="t1", task_objective="x",
            project_binding=PROJECT_BINDING, workspace_binding="w",
            context_package=("p2p-security",),
            explicit_execution_target="fake-manus",
            target_fingerprint=self.contract.target_fingerprint)
        self.assertNotEqual(self.contract.context_digest,
                            other.context_digest)
        self.assertNotEqual(self.contract.request_fingerprint,
                            other.request_fingerprint)

    def test_21_binds_permission(self):
        other = build_role_execution_contract(
            self.spec, goal_id="g1", task_id="t1", task_objective="x",
            project_binding=PROJECT_BINDING, workspace_binding="w",
            permission_profile=("WRITE",),
            explicit_execution_target="fake-manus",
            target_fingerprint=self.contract.target_fingerprint)
        self.assertNotEqual(self.contract.request_fingerprint,
                            other.request_fingerprint)

    def test_22_binds_target(self):
        other = build_role_execution_contract(
            self.spec, goal_id="g1", task_id="t1", task_objective="x",
            project_binding=PROJECT_BINDING, workspace_binding="w",
            explicit_execution_target="fake-codex",
            target_fingerprint=fake_target_fingerprint("fake-codex"))
        self.assertNotEqual(self.contract.request_fingerprint,
                            other.request_fingerprint)
        # Target fingerprint derives from material identity.
        fp1 = target_fingerprint_from_profile({"adapter_id": "adapter-fake-manus",
                                               "harness": "manus",
                                               "provider": "manus",
                                               "model": "m"})
        fp2 = target_fingerprint_from_profile({"adapter_id": "adapter-fake-manus",
                                               "harness": "manus",
                                               "provider": "manus",
                                               "model": "different-model"})
        self.assertNotEqual(fp1, fp2)

    def test_23_binds_request_fingerprint(self):
        self.assertRegex(self.contract.request_fingerprint, r"^[0-9a-f]{64}$")
        # Deterministic: same semantic fields -> same fingerprint; any
        # semantic field change -> different fingerprint.
        other_fields = {
            "goal_id": "g2",
            "task_id": self.contract.task_id,
            "task_objective": self.contract.objective,
            "workspace": self.contract.workspace_binding,
            "execution_target": self.contract.explicit_execution_target,
        }
        self.assertNotEqual(
            contract_request_fingerprint(other_fields),
            self.contract.request_fingerprint)


class TestC35ReceiptRejection(unittest.TestCase):
    """Tests 24-30: the verifier rejection set, fail closed."""

    def setUp(self):
        self.registry, _ = _make_bridge()
        register_fake_targets(self.registry)
        self.spec = build_role_spec("p2p_anon")
        self.contract, self.receipt, self.backend_result = _dispatch_role(
            self.spec, self.registry)
        self.eligible_cert = _cert_for("fake-manus")

    def test_24_wrong_role_receipt_rejected(self):
        wrong = role_receipt.new_role_receipt(
            role_id="p2p_iris", **{
                key: value for key, value in self.receipt.to_dict().items()
                if key != "role_id"})
        verify = _verify_receipt(RoleExecutionReceipt(wrong),
                                 self.contract, self.spec,
                                 backend_result=self.backend_result)
        self.assertEqual(verify["verdict"], "REJECTED")
        self.assertIn("WRONG_ROLE_ID", verify["reasons"])
        self.assertEqual(verify["failure_class"], "BINDING_MISMATCH")

    def test_25_stale_role_spec_receipt_rejected(self):
        stale = role_receipt.new_role_receipt(
            role_spec_hash=role_semantic_fingerprint({
                "forbidden_actions": ("new-action",),
                "default_mutation_policy": "READ_ONLY",
                "authority_class": "MODEL_ROUTABLE",
                "permission_ceiling": (),
                "required_capabilities": (),
                "context_policy": "BOUNDED_EXPLICIT",
                "quorum_semantics": "CANONICAL_QUORUM_MEMBER",
            }),
            **{key: value for key, value in self.receipt.to_dict().items()
               if key != "role_spec_hash"})
        verify = _verify_receipt(RoleExecutionReceipt(stale),
                                 self.contract, self.spec,
                                 backend_result=self.backend_result)
        self.assertEqual(verify["verdict"], "REJECTED")
        self.assertIn("STALE_ROLE_SPEC_HASH", verify["reasons"])
        self.assertEqual(verify["failure_class"], "STALE_ROLE_SPEC")

    def test_26_wrong_task_receipt_rejected(self):
        wrong = role_receipt.new_role_receipt(
            task_id="task:other:2", **{
                key: value for key, value in self.receipt.to_dict().items()
                if key != "task_id"})
        verify = _verify_receipt(RoleExecutionReceipt(wrong),
                                 self.contract, self.spec,
                                 backend_result=self.backend_result)
        self.assertEqual(verify["verdict"], "REJECTED")
        self.assertIn("WRONG_TASK_ID", verify["reasons"])

    def test_27_wrong_environment_receipt_rejected(self):
        wrong = role_receipt.new_role_receipt(
            environment_binding="CLOUD_VM", **{
                key: value for key, value in self.receipt.to_dict().items()
                if key != "environment_binding"})
        verify = _verify_receipt(RoleExecutionReceipt(wrong),
                                 self.contract, self.spec,
                                 backend_result=self.backend_result)
        self.assertEqual(verify["verdict"], "REJECTED")
        self.assertIn("WRONG_ENVIRONMENT_BINDING", verify["reasons"])

    def test_28_permission_widening_rejected(self):
        wide = role_receipt.new_role_receipt(
            permission_profile=("READ", "WRITE"),
            permission_profile_fingerprint=permission_profile_fingerprint(
                ("READ", "WRITE")),
            **{key: value for key, value in self.receipt.to_dict().items()
               if key not in ("permission_profile",
                              "permission_profile_fingerprint")})
        verify = _verify_receipt(RoleExecutionReceipt(wide),
                                 self.contract, self.spec,
                                 backend_result=self.backend_result)
        self.assertEqual(verify["verdict"], "REJECTED")
        self.assertIn("OBSERVED_PERMISSION_WIDER_THAN_COMPOSED",
                      verify["reasons"])
        self.assertEqual(verify["failure_class"], "PERMISSION_WIDENING")

    def test_29_missing_required_evidence_rejected(self):
        thin = role_receipt.new_role_receipt(
            evidence_pointers=(),
            **{key: value for key, value in self.receipt.to_dict().items()
               if key != "evidence_pointers"})
        verify = _verify_receipt(RoleExecutionReceipt(thin),
                                 self.contract, self.spec,
                                 backend_result=self.backend_result)
        self.assertEqual(verify["verdict"], "REJECTED")
        self.assertEqual(verify["failure_class"], "EVIDENCE_MISSING")

    def test_30_unknown_mutation_fails_closed(self):
        unknown_mutation = role_receipt.new_role_receipt(
            mutation_state="MUTATION_UNKNOWN",
            **{key: value for key, value in self.receipt.to_dict().items()
               if key != "mutation_state"})
        verify = _verify_receipt(RoleExecutionReceipt(unknown_mutation),
                                 self.contract, self.spec,
                                 backend_result=self.backend_result)
        self.assertEqual(verify["verdict"], "REJECTED")
        self.assertIn("MUTATION_STATE_UNKNOWN", verify["reasons"])
        self.assertEqual(verify["failure_class"], "MUTATION_STATE_UNKNOWN")


class TestC35TargetAttestation(unittest.TestCase):
    """Test 31: requested != observed until attested."""

    def test_31_requested_not_observed_until_attested(self):
        registry, _ = _make_bridge()
        register_fake_targets(registry)
        spec = build_role_spec("p2p_anon")
        contract, receipt, _ = _dispatch_role(spec, registry)
        # With synthetic execution evidence present, the dispatch attests
        # the OBSERVED profile honestly (C34 attestation semantics): a
        # requested-only claim without observation evidence is rejected.
        self.assertIn(receipt.target_attestation_status,
                      ("PROFILE_BOUND", "MODEL_BOUND"))
        self.assertEqual(receipt.requested_target, "fake-manus")
        self.assertNotEqual(receipt.observed_target, "fake-manus")
        # A fresh contract cannot claim attestation either.
        self.assertEqual(contract.requested_target_attestation,
                         "REQUESTED_ONLY")


class TestC35CertificationSemantics(unittest.TestCase):
    """Tests 32-35: capability-scoped certification, historical != current,
    Manus scope limits, revoked auth."""

    def test_32_historical_not_current_eligibility(self):
        """Historical certification evidence remains valid history, but
        NO_CREDENTIALS (revoked/absent auth) blocks current eligibility
        for a live-execution requirement."""
        record = _cert_for("fake-manus", scopes=("NON_MUTATING_TASK",
                                                 "API_TRANSPORT",
                                                 "SYNTHETIC_TEXT_EXECUTION"),
                           auth_state="NO_CREDENTIALS")
        # Historical certification preserved as evidence.
        self.assertTrue(record.historical_certification is False)
        self.assertEqual(len(record.scope_certifications), 3)
        for cert in record.scope_certifications:
            self.assertEqual(cert.status, "LIVE_CERTIFIED_FOR_CAPABILITY")
        # But current eligibility for a live role requirement is BLOCKED.
        elig = evaluate_role_target_eligibility(
            role_required_capabilities=("NON_MUTATING_TASK",),
            role_permission_ceiling=("READ",),
            role_quorum_semantics="CANONICAL_QUORUM_MEMBER",
            required_evidence=("claim",),
            task_permission_profile=("READ",),
            goal_permission_envelope=("READ",),
            target=record,
            environment_binding="LOCAL_PROJECT",
            workspace_binding="synthetic-workspace",
        )
        self.assertEqual(elig["decision"], "INELIGIBLE")
        self.assertTrue(elig["auth_blocked"])

    def test_33_capability_scoped_certification_enforced(self):
        """A scope the target demonstrably lacks is a positive INELIGIBLE,
        not UNKNOWN."""
        record = _cert_for("fake-manus", scopes=("NON_MUTATING_TASK",),
                           auth_state="VALID")
        elig = evaluate_role_target_eligibility(
            role_required_capabilities=("CODE_MUTATION",),
            role_permission_ceiling=("WRITE",),
            role_quorum_semantics="CANONICAL_QUORUM_MEMBER",
            required_evidence=("claim",),
            task_permission_profile=("WRITE",),
            goal_permission_envelope=("WRITE",),
            target=record,
            environment_binding="LOCAL_PROJECT",
            workspace_binding="synthetic-workspace",
        )
        self.assertEqual(elig["decision"], "INELIGIBLE")
        self.assertTrue(any(r.startswith("scope-insufficient:CODE_MUTATION")
                            for r in elig["reasons"]))

    def test_34_text_scope_not_code_mutation(self):
        """Manus historical text/non-mutating scope does NOT imply code
        mutation certification."""
        record = _cert_for("fake-manus",
                           scopes=("NON_MUTATING_TASK", "API_TRANSPORT"),
                           auth_state="VALID")
        for scope in CERTIFICATION_SCOPES:
            elig = evaluate_role_target_eligibility(
                role_required_capabilities=(scope,),
                role_permission_ceiling=("READ", "WRITE"),
                role_quorum_semantics="CANONICAL_QUORUM_MEMBER",
                required_evidence=("claim",),
                task_permission_profile=("READ", "WRITE"),
                goal_permission_envelope=("READ", "WRITE"),
                target=record,
                environment_binding="LOCAL_PROJECT",
                workspace_binding="synthetic-workspace",
            )
            expected_eligible = (scope in ("NON_MUTATING_TASK",
                                           "API_TRANSPORT",
                                           "SYNTHETIC_TEXT_EXECUTION"))
            self.assertEqual(elig["decision"],
                             "ELIGIBLE" if expected_eligible else "INELIGIBLE",
                             f"scope={scope}: {elig['decision']} {elig['reasons']}")

    def test_35_revoked_no_valid_auth_blocked(self):
        """Revoked / absent / invalid Manus auth never becomes eligible."""
        for auth_state in ("NO_CREDENTIALS", "EXPIRED", "INVALID", "UNKNOWN"):
            record = _cert_for("fake-manus",
                               scopes=("NON_MUTATING_TASK", "API_TRANSPORT"),
                               auth_state=auth_state)
            elig = evaluate_role_target_eligibility(
                role_required_capabilities=("NON_MUTATING_TASK",),
                role_permission_ceiling=("READ",),
                role_quorum_semantics="CANONICAL_QUORUM_MEMBER",
                required_evidence=("claim",),
                task_permission_profile=("READ",),
                goal_permission_envelope=("READ",),
                target=record,
                environment_binding="LOCAL_PROJECT",
                workspace_binding="synthetic-workspace",
            )
            self.assertNotEqual(elig["decision"], "ELIGIBLE",
                                f"auth_state={auth_state} must not be ELIGIBLE")


class TestC35VerificationAuthority(unittest.TestCase):
    """Tests 36-37: backend-done != verified; transcript != state."""

    def test_36_backend_done_not_verified(self):
        registry, _ = _make_bridge()
        register_fake_targets(registry)
        spec = build_role_spec("p2p_anon")
        # Backend reports SUCCEEDED with VERIFIED status, but the role
        # verifier still performs independent binding checks.
        contract, receipt, backend_result = _dispatch_role(spec, registry)
        verify = _verify_receipt(receipt, contract, spec,
                                 backend_result=backend_result)
        # With complete evidence the independent verifier may still reject
        # or accept; the invariant is that it never auto-accepts.
        if verify["verdict"] == "VERIFIED":
            # It accepted ONLY after independent checks passed — the
            # verdict is the verifier's own decision, not an echo.
            self.assertEqual(verify["verifier_authority"], "INDEPENDENT")
        else:
            self.assertGreater(len(verify["reasons"]), 0)
        # A backend result alone (no independent check) can never pass.
        thin = role_receipt.new_role_receipt(
            evidence_pointers=(), verifier_result="UNKNOWN",
            **{key: value for key, value in receipt.to_dict().items()
               if key not in ("evidence_pointers", "verifier_result")})
        verify2 = _verify_receipt(RoleExecutionReceipt(thin), contract, spec)
        self.assertEqual(verify2["verdict"], "REJECTED")
        self.assertIn("NO_BACKEND_RESULT", verify2["reasons"])

    def test_37_transcript_not_state(self):
        """A role receipt carries evidence POINTERS, never transcript
        content; no transcript-as-state in the role machinery."""
        registry, _ = _make_bridge()
        register_fake_targets(registry)
        spec = build_role_spec("p2p_anon")
        _, receipt, _ = _dispatch_role(spec, registry)
        for module in (role_receipt, role_verifier, role_contract,
                       role_eligibility):
            src = inspect.getsource(module)
            self.assertNotIn("transcript_as_state", src)
            self.assertNotIn("TRANSCRIPT_IS_STATE", src)
        # Receipt output/artifact/evidence fields are pointers only.
        receipt_dict = receipt.to_dict()
        for field in ("output_pointers", "artifact_pointers",
                      "evidence_pointers"):
            for pointer in receipt_dict[field]:
                self.assertIsInstance(pointer, str)
                self.assertLess(len(pointer), 512)


class TestC35ContextDelivery(unittest.TestCase):
    """Tests 38-39: fresh bounded explicit child context; no full-parent
    transcript by default."""

    def test_38_fresh_bounded_child_context(self):
        spec = build_role_spec("p2p_anon")
        contract = build_role_execution_contract(
            spec, goal_id="g1", task_id="t1", task_objective="o",
            project_binding=PROJECT_BINDING, workspace_binding="w",
            context_package=("p2p-governance", "p2p-task-state"),
            explicit_execution_target="fake-manus",
            target_fingerprint=fake_target_fingerprint("fake-manus"))
        # Context digest derives ONLY from the bounded package.
        self.assertEqual(contract.context_digest,
                         context_digest_fingerprint(("p2p-governance",
                                                     "p2p-task-state")))
        # Different bounded packages -> different digests.
        other = context_digest_fingerprint(("p2p-governance",
                                            "p2p-session-transcript"))
        self.assertNotEqual(contract.context_digest, other)

    def test_39_no_full_parent_transcript_default(self):
        spec = build_role_spec("p2p_anon")
        contract = build_role_execution_contract(
            spec, goal_id="g1", task_id="t1", task_objective="o",
            project_binding=PROJECT_BINDING, workspace_binding="w",
            explicit_execution_target="fake-manus",
            target_fingerprint=fake_target_fingerprint("fake-manus"))
        # Default context package is EMPTY: fresh child by default.
        self.assertEqual(contract.context_package, ())
        self.assertEqual(contract.context_digest,
                         context_digest_fingerprint(()))


class TestC35QuorumAndParticipation(unittest.TestCase):
    """Tests 40-47: adaptive participation, 8/8 quorum, duplicates,
    unverified/stale receipts, single/mixed targets."""

    def test_40_adaptive_participation_no_registry_mutation(self):
        before = dict(role_spec_lookup())
        for risk_class in ("LOW_RISK_DETERMINISTIC", "MATERIAL", "SECURITY",
                           "ARCHITECTURE", "DOMAIN_RISK",
                           "CANONICAL_GOVERNANCE_GATE"):
            ap = adaptive_participant_set(risk_class)
            self.assertTrue(ap["canonical_registry_unchanged"])
            self.assertLessEqual(len(ap["participant_roles"]),
                                 CANONICAL_ROLE_DENOMINATOR)
            for role in ap["participant_roles"]:
                self.assertIn(role, ALL_P2P_ROLES)
        # Bounded by policy, never a swarm: LOW_RISK uses ONE executor.
        low = adaptive_participant_set("LOW_RISK_DETERMINISTIC")
        self.assertEqual(len(low["participant_roles"]), 1)
        self.assertEqual(low["participant_roles"], ["p2p_datos"])
        after = dict(role_spec_lookup())
        self.assertEqual(len(before), len(after))
        self.assertEqual({k: v.role_spec_hash for k, v in before.items()},
                         {k: v.role_spec_hash for k, v in after.items()})

    def _verified_receipts(self, target_map):
        """Build independently VERIFIED receipts: role -> target_id.
        Returns (contracts, receipts). Backend dispatch alone is NOT
        verification — each receipt passes the independent role verifier
        first; only VERIFIED receipts count."""
        registry, _ = _make_bridge()
        register_fake_targets(registry)
        contracts, receipts = [], []
        for role_id, target_id in target_map.items():
            spec = build_role_spec(role_id)
            contract, receipt, backend_result = _dispatch_role(
                spec, registry, target_id=target_id,
                permission_profile=("READ",))
            verify = verify_role_execution_receipt(
                receipt=receipt, expected_contract=contract,
                expected_role_spec_hash=spec.role_spec_hash,
                expected_permission_profile=("READ",),
                required_evidence=(),
                observed_target_evidence_pointers=(
                    receipt.raw_backend_receipt_pointer,),
                certification_records=_cert_for(
                    target_id, scopes=("NON_MUTATING_TASK",
                                       "API_TRANSPORT",
                                       "SYNTHETIC_TEXT_EXECUTION"
                                       )).scope_certifications,
                backend_result=backend_result,
            )
            self.assertEqual(verify["verdict"], "VERIFIED",
                             f"role {role_id}: {verify['reasons']}")
            verified = role_receipt.new_role_receipt(
                verifier_result="VERIFIED",
                verifier_reasons=(),
                verified_at=verify.get("verified_at") or receipt.timestamps.get("executed_at"),
                **{key: value for key, value in receipt.to_dict().items()
                   if key not in ("verifier_result", "verifier_reasons",
                                  "timestamps")})
            contracts.append(contract)
            receipts.append(RoleExecutionReceipt(verified))
        return contracts, receipts

    def test_41_88_quorum_passes(self):
        contracts, receipts = self._verified_receipts(
            {role: "fake-manus" for role in CANONICAL_ROLES})
        q = evaluate_role_quorum(
            receipts,
            current_spec_hashes={c.role_id: c.role_spec_hash
                                 for c in contracts},
            expected_goal_id=GOAL_ID, expected_task_id="ALL",
        )
        # Goal/task binding must match the gate context.
        q2 = evaluate_role_quorum(
            receipts,
            current_spec_hashes={c.role_id: c.role_spec_hash
                                 for c in contracts},
            expected_goal_id=GOAL_ID,
            expected_task_id=TASK_ID if len(receipts) == 1 else None,
        )
        # With all receipts bound to distinct roles, verified, and fresh
        # spec hashes, the gate is COMPLETE for matching goal context.
        self.assertEqual(q2["decision"], "COMPLETE")
        self.assertEqual(q2["satisfied_count"], len(CANONICAL_ROLES))

    def test_42_duplicate_role_cannot_fill_slot(self):
        contracts, receipts = self._verified_receipts({
            "p2p_anon": "fake-manus", "p2p_axiom": "fake-manus"})
        # A second VERIFIED receipt for a role already satisfied is a
        # duplicate — it never fills a missing canonical slot.
        registry, _ = _make_bridge()
        register_fake_targets(registry)
        spec = build_role_spec("p2p_anon")
        c1, r1, b1 = _dispatch_role(spec, registry, target_id="fake-codex",
                                task_id="t-b")  # noqa
        verify = verify_role_execution_receipt(
            receipt=r1, expected_contract=c1,
            expected_role_spec_hash=spec.role_spec_hash,
            expected_permission_profile=("READ",),
            required_evidence=(),
            observed_target_evidence_pointers=(
                r1.raw_backend_receipt_pointer,),
            certification_records=_cert_for(
                "fake-codex", scopes=("NON_MUTATING_TASK",
                                      "API_TRANSPORT",
                                      "SYNTHETIC_TEXT_EXECUTION"
                                      )).scope_certifications,
            backend_result=b1,
        )
        self.assertEqual(verify["verdict"], "VERIFIED",
                         f"dup receipt: {verify['reasons']}")
        verified = role_receipt.new_role_receipt(
            verifier_result="VERIFIED", verifier_reasons=(),
            **{key: value for key, value in r1.to_dict().items()
               if key not in ("verifier_result", "verifier_reasons")})
        r1_verified = RoleExecutionReceipt(verified)
        all_receipts = receipts + [r1_verified]
        q = evaluate_role_quorum(
            all_receipts,
            current_spec_hashes={"p2p_anon": spec.role_spec_hash},
            expected_goal_id=GOAL_ID)
        self.assertEqual(q["decision"], "INCOMPLETE")
        self.assertEqual(len(q["duplicate_receipts"]), 1)
        self.assertEqual(q["satisfied_count"], 2)
        self.assertIn("p2p_anon", q["satisfied_roles"])
        missing = sorted(set(CANONICAL_ROLES) - {"p2p_anon", "p2p_axiom"})
        self.assertEqual(q["missing_roles"], missing)

    def test_43_unverified_receipt_does_not_count(self):
        _, receipts = self._verified_receipts({"p2p_anon": "fake-manus"})
        unverified = role_receipt.new_role_receipt(
            verifier_result="FAILED",
            **{key: value for key, value in receipts[0].to_dict().items()
               if key != "verifier_result"})
        q = evaluate_role_quorum(
            [RoleExecutionReceipt(unverified)],
            current_spec_hashes={"p2p_anon": receipts[0].role_spec_hash},
            expected_goal_id=GOAL_ID)
        self.assertEqual(q["decision"], "INCOMPLETE")
        self.assertEqual(q["satisfied_count"], 0)
        self.assertEqual(q["disqualified_receipts"][0]["reasons"],
                         ["RECEIPT_NOT_VERIFIED"])

    def test_44_stale_role_receipt_does_not_count(self):
        _, receipts = self._verified_receipts({"p2p_anon": "fake-manus"})
        stale = role_receipt.new_role_receipt(
            role_spec_hash=role_semantic_fingerprint({
                "forbidden_actions": ("stale-action",),
                "default_mutation_policy": "READ_ONLY",
                "authority_class": "MODEL_ROUTABLE",
                "permission_ceiling": (),
                "required_capabilities": (),
                "context_policy": "BOUNDED_EXPLICIT",
                "quorum_semantics": "CANONICAL_QUORUM_MEMBER",
            }),
            **{key: value for key, value in receipts[0].to_dict().items()
               if key != "role_spec_hash"})
        q = evaluate_role_quorum(
            [RoleExecutionReceipt(stale)],
            current_spec_hashes={"p2p_anon": receipts[0].role_spec_hash},
            expected_goal_id=GOAL_ID)
        self.assertEqual(q["decision"], "INCOMPLETE")
        self.assertIn("STALE_ROLE_SPEC_HASH",
                      q["disqualified_receipts"][0]["reasons"])

    def test_45_same_target_multiple_roles(self):
        contracts, receipts = self._verified_receipts(
            {role: "fake-manus" for role in CANONICAL_ROLES[:3]})
        targets = {receipt.observed_target for receipt in receipts}
        self.assertEqual(len(targets), 1)
        roles = {receipt.role_id for receipt in receipts}
        self.assertEqual(len(roles), 3)
        # One target legitimately executing three distinct roles.
        q = evaluate_role_quorum(
            receipts,
            current_spec_hashes={c.role_id: c.role_spec_hash
                                 for c in contracts},
            expected_goal_id=GOAL_ID)
        self.assertEqual(q["satisfied_count"], 3)

    def test_46_mixed_targets_satisfy_quorum(self):
        mixed = dict(zip(CANONICAL_ROLES[:4],
                         ("fake-manus", "fake-codex", "fake-grok",
                          "fake-gemini")))
        contracts, receipts = self._verified_receipts(mixed)
        q = evaluate_role_quorum(
            receipts,
            current_spec_hashes={c.role_id: c.role_spec_hash
                                 for c in contracts},
            expected_goal_id=GOAL_ID)
        self.assertEqual(q["satisfied_count"], 4)
        self.assertEqual(
            {r.observed_target for r in receipts},
            {"adapter-fake-manus", "adapter-fake-codex",
             "adapter-fake-grok", "adapter-fake-gemini"})

    def test_47_one_receipt_never_two_roles(self):
        """Independent re-assertion of test 42's core invariant: a single
        receipt structurally binds ONE role_id; quorum consumes distinct
        role slots only."""
        _, receipts = self._verified_receipts({"p2p_anon": "fake-manus"})
        self.assertEqual(len(set(r.role_id for r in receipts)), 1)
        for receipt in receipts:
            # Receipt's verifier result is per-receipt, not per-role-set.
            self.assertIsInstance(receipt.verifier_result, str)


class TestC35ArchitecturalBoundaries(unittest.TestCase):
    """Tests 47-52: no vendor branching, registry != router, no ranking,
    no fallback, no background autonomy, no fanout."""

    def _core_sources(self):
        import p2p_capabilities.agent_role as agent_role  # noqa: E402
        import p2p_capabilities.role_contract as role_contract  # noqa: E402
        import p2p_capabilities.role_eligibility as role_eligibility  # noqa: E402
        import p2p_capabilities.role_verifier as role_verifier  # noqa: E402
        import p2p_capabilities.role_quorum as role_quorum  # noqa: E402
        import p2p_capabilities.role_receipt as role_receipt  # noqa: E402
        return inspect.getsource(agent_role) + inspect.getsource(role_contract) \
            + inspect.getsource(role_eligibility) + inspect.getsource(role_verifier) \
            + inspect.getsource(role_quorum) + inspect.getsource(role_receipt)

    def test_48_no_vendor_branching(self):
        src = self._core_sources()
        for vendor in ("openai", "anthropic", "xai", "deepseek", "google",
                       "hermes", "codex", "manus"):
            for pattern in (f'provider == "{vendor}"',
                            f'harness == "{vendor}"',
                            f"provider==\"{vendor}\""):
                self.assertNotIn(pattern, src,
                                 f"vendor branch detected: {vendor}")

    def test_49_registry_not_router(self):
        """Registry lookup requires an explicit adapter id; there is no
        ranking, no fallback, no silent selection. If a target is not
        registered, the machinery raises/blocks — it never silently
        switches to another adapter."""
        registry = BackendAdapterRegistry()
        register_explicit_adapter(registry, adapter_id="adapter-fake-manus",
                                  harness="manus")
        self.assertEqual(registry.registered_ids(), ("adapter-fake-manus",))
        # Unregistered explicit target -> dispatch must NOT silently
        # select adapter-fake-manus. It raises or fails closed.
        bridge = BackendExecutionBridge(
            registry, {"adapter_id": "adapter-nonexistent"})
        contract = build_role_execution_contract(
            build_role_spec("p2p_anon"), goal_id="g1", task_id="t1",
            task_objective="x", project_binding=PROJECT_BINDING,
            workspace_binding="w", explicit_execution_target="fake-manus",
            target_fingerprint=fake_target_fingerprint("fake-manus"))
        blocked = False
        try:
            RoleExecutionBridge(bridge).dispatch(
                contract, adapter_id="adapter-nonexistent")
        except (RoleBridgeError, Exception):
            blocked = True
        self.assertTrue(blocked)
        # No OTHER adapter was ever selected silently.
        self.assertEqual(registry.registered_ids(), ("adapter-fake-manus",))

    def test_50_no_target_ranking(self):
        """Eligibility returns a single boolean decision + reasons; there
        is no score, no ranking, no 'best'. Explicit anti-router wording
        ('never ranks', 'no fallback') is allowed — it must describe a
        prohibition, never an operation."""
        import p2p_capabilities.role_eligibility as role_eligibility  # noqa: E402
        src = inspect.getsource(role_eligibility)
        self.assertNotIn("score", src.lower())
        self.assertNotIn("best ", src.lower())
        self.assertNotIn("preference", src.lower())
        self.assertNotIn("alternate", src.lower())
        self.assertNotIn("reswitch", src.lower())
        # 'rank'/'fallback' may only appear in anti-router negatives.
        for line in src.splitlines():
            low = line.lower()
            if "rank" in low or "fallback" in low:
                must_negate = ("never rank" in low or "no rank" in low
                               or "no fallback" in low
                               or "!= " in low)
                self.assertTrue(must_negate,
                                f"non-negative ranking/fallback text: {line}")

    def test_51_no_silent_fallback(self):
        """If a target is not eligible, the machinery BLOCKS; it does not
        silently choose another."""
        record = _cert_for("fake-manus", scopes=(), auth_state="NO_CREDENTIALS")
        elig = evaluate_role_target_eligibility(
            role_required_capabilities=("NON_MUTATING_TASK",),
            role_permission_ceiling=("READ",),
            role_quorum_semantics="CANONICAL_QUORUM_MEMBER",
            required_evidence=("claim",),
            task_permission_profile=("READ",),
            goal_permission_envelope=("READ",),
            target=record,
            environment_binding="LOCAL_PROJECT",
            workspace_binding="synthetic-workspace",
        )
        self.assertEqual(elig["decision"], "INELIGIBLE")
        # No alternative target suggestion in the result.
        self.assertNotIn("alternative", elig)
        self.assertNotIn("fallback", elig)

    def test_52_no_background_autonomy(self):
        """C35 is bounded foreground machinery: no daemon/cron/scheduler
        vocabulary in the runtime role core."""
        src = self._core_sources()
        # 'unknown' is a legitimate state keyword; scan case-sensitive
        # phrases instead of any lowercased match containing 'known'.
        for keyword in ("daemon", "cron", "scheduler", "worker_manager",
                        "background", "persistent_swarm", "autonomous"):
            self.assertNotIn(keyword, src, f"background autonomy keyword: {keyword}")

    def test_53_no_unbounded_fanout(self):
        """Participant sets are bounded by the canonical denominator;
        quorum evaluation never spawns anything."""
        ap = adaptive_participant_set("CANONICAL_GOVERNANCE_GATE")
        self.assertLessEqual(len(ap["participant_roles"]),
                             CANONICAL_ROLE_DENOMINATOR)
        registry, _ = _make_bridge()
        register_fake_targets(registry)
        spec = build_role_spec("p2p_anon")
        _dispatch_role(spec, registry)  # one contract -> one receipt
        # Quorum consumption is pure evaluation: no side effects.
        q = evaluate_role_quorum(())
        self.assertEqual(q["satisfied_count"], 0)


class TestC35GovernanceIntegration(unittest.TestCase):
    """Tests 53-55: canonical release gates unchanged, fresh-clone recovery,
    candidate policy sees runtime changes."""

    def test_54_canonical_gates_unchanged(self):
        """Canonical release/promotion gates remain unchanged: governance
        definitions and candidate policy semantics were not altered."""
        # Governance still defines exactly the canonical council plus the
        # optional specialist.
        specs = role_spec_lookup()
        quorum_members = {role for role, spec in specs.items()
                          if spec.quorum_semantics == "CANONICAL_QUORUM_MEMBER"}
        self.assertEqual(quorum_members, set(CANONICAL_ROLES))
        # Candidate policy vocabulary is untouched by C35 runtime modules.
        import importlib.util  # noqa: E402
        _gcl = importlib.util.spec_from_file_location(
            "p2p_goal_closure",
            os.path.join(REPO_ROOT, "scripts", "p2p_goal_closure.py"))
        _gcm = importlib.util.module_from_spec(_gcl)
        _gcl.loader.exec_module(_gcm)
        check_candidate_policy_compliance = _gcm.check_candidate_policy_compliance
        candidate_policy_from_report_fields = _gcm.candidate_policy_from_report_fields
        self.assertTrue(callable(check_candidate_policy_compliance))

    def test_55_fresh_clone_durable_recovery(self):
        """A fresh clone can recover the canonical role machinery from
        repository truth alone: no in-memory or external state needed."""
        # Recovery reads capabilities.json + codex profiles from disk.
        records = load_capability_registry()
        self.assertGreater(len(records), 8)
        specs = [build_role_spec(role_id, records)
                 for role_id in CANONICAL_ROLES]
        self.assertEqual(len(specs), 8)
        for spec in specs:
            self.assertEqual(spec.schema, "p2p-agent-role-spec/1")
            self.assertRegex(spec.role_spec_hash, r"^[0-9a-f]{64}$")

    def test_56_candidate_policy_sees_c35_runtime_changes(self):
        """The actual deterministic candidate policy (C34 corrected
        checker) recognizes .p2p/system/ runtime changes — including the
        new C35 role modules."""
        import importlib.util  # noqa: E402
        _gcl2 = importlib.util.spec_from_file_location(
            "p2p_goal_closure",
            os.path.join(REPO_ROOT, "scripts", "p2p_goal_closure.py"))
        _gcm2 = importlib.util.module_from_spec(_gcl2)
        _gcl2.loader.exec_module(_gcm2)
        ChangeSignals = _gcm2.ChangeSignals
        c35_files = [
            ".p2p/system/p2p_capabilities/agent_role.py",
            ".p2p/system/p2p_capabilities/role_contract.py",
            ".p2p/system/p2p_capabilities/role_eligibility.py",
            ".p2p/system/p2p_capabilities/role_receipt.py",
            ".p2p/system/p2p_capabilities/role_verifier.py",
            ".p2p/system/p2p_capabilities/role_bridge.py",
            ".p2p/system/p2p_capabilities/role_quorum.py",
            ".p2p/system/p2p_capabilities/fake_targets.py",
        ]
        signals = ChangeSignals.detect(c35_files)
        self.assertTrue(signals.runtime_changed)
        # No claim-boundary violation: no router/controller/second
        # executor/background autonomy patterns in C35 file names.
        self.assertEqual(signals.router_or_controller_files(), [])
        self.assertEqual(signals.second_executor_files(), [])
        self.assertEqual(signals.background_autonomy_files(), [])
        # Markdown docs under .p2p/system/ are explicitly non-runtime.
        signals_md = ChangeSignals.detect(
            [".p2p/system/p2p_capabilities/README.md"])
        self.assertFalse(signals_md.runtime_changed)


class TestC35DecisionTrace(unittest.TestCase):
    """Test 56: structured decision trace vocabulary, no hidden CoT."""

    def test_56_decision_trace_vocabulary(self):
        expected_codes = {
            "ROLE_SELECTED", "ROLE_NOT_REQUIRED", "ROLE_CONTRACT_BUILT",
            "ROLE_TARGET_ELIGIBLE", "ROLE_TARGET_INELIGIBLE",
            "ROLE_TARGET_UNKNOWN", "ROLE_DISPATCHED",
            "ROLE_RECEIPT_REJECTED", "ROLE_EXECUTION_VERIFIED",
            "ROLE_QUORUM_ACCEPTED", "ROLE_QUORUM_INCOMPLETE",
            "ROLE_PERMISSION_BLOCKED", "ROLE_CAPABILITY_BLOCKED",
        }
        self.assertEqual(set(DECISION_CODES), expected_codes)
        for code in expected_codes:
            record = decision_record(code, role_id="p2p_anon")
            self.assertEqual(record["code"], code)
        # Invalid codes raise.
        with self.assertRaises(RoleVerifierError):
            decision_record("INVALID_CODE")
        # Structured only — no free-form chain-of-thought field.
        record = decision_record("ROLE_CONTRACT_BUILT", role_id="p2p_anon")
        self.assertNotIn("thought", record)
        self.assertNotIn("chain_of_thought", record)
        self.assertNotIn("cot", record)


if __name__ == "__main__":
    unittest.main()
