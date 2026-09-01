"""P2P-IMPECCABLE-01 (issue #44) focused proof.

Scope is deliberately narrow:
  - capability projection / registry record
  - routing eligibility through the EXISTING router
  - no default context loading, no global activation
  - deterministic detector proof on one bounded fixture pair
  - provenance / license boundary of the pinned vendor snapshot
  - non-regression of the existing UI capability catalog + profile routing
"""

from __future__ import annotations

import atexit
import copy
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
REGISTRY_PATH = SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json"
VENDOR_ROOT = REPO_ROOT / ".p2p" / "vendor" / "skill" / "pbakaus-impeccable-94b7f34"
PROVENANCE_PATH = REPO_ROOT / ".p2p" / "vendor" / "provenance" / "p2p-impeccable-01.json"
CATALOG_PATH = REPO_ROOT / "docs" / "p2p-development" / "capability-catalog" / "ui-game-threejs" / "capability-catalog.json"
ROUTING_PATH = REPO_ROOT / "docs" / "p2p-development" / "capability-catalog" / "ui-game-threejs" / "project-profile-routing.json"
FIXTURE_DIR = REPO_ROOT / "tests" / "fixtures" / "p2p-impeccable-design-quality"
BEFORE = FIXTURE_DIR / "before.html"
AFTER = FIXTURE_DIR / "after.html"

CAPABILITY_ID = "ui.design_quality"
UPSTREAM_COMMIT = "94b7f34f6e27b95bc32d8284a671601ed6ac1b2a"
UPSTREAM_TREE = "604c0d2d5f0c1c6bd1f3bd1cbc06bef637e24139"

# Deterministic categories that must be found on the BEFORE fixture in EVERY
# engine mode, including the zero-dependency regex mode.
REQUIRED_ANTIPATTERNS = {
    "gradient-text",        # generic/undesired gradient pattern
    "side-tab",             # generic AI accent-stripe card pattern
    "dark-glow",            # decorative chromatic glow
    "monotonous-spacing",   # spacing rhythm problem
    "flat-type-hierarchy",  # typography hierarchy problem
    "overused-font",        # typography/readability problem
}

sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities import impeccable_design_quality as idq  # noqa: E402
from p2p_capabilities.host_executor import PortableExecutionRequest  # noqa: E402
from p2p_capabilities.task_state import (  # noqa: E402
    LogicalOwner,
    TaskPlan,
    TaskRecord,
    TaskStateStore,
)
from p2p_capabilities.model import load_registry  # noqa: E402
from p2p_capabilities.vendor_skill import (  # noqa: E402
    discover_vendor_skills,
    is_vendor_skill,
    load_vendor_skill,
    snapshot_tree_sha256,
)


def _registry_entry() -> dict:
    raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    return next(item for item in raw["capabilities"] if item["CAPABILITY_ID"] == CAPABILITY_ID)


GOAL_ID = "IMPECCABLE_01"
TASK_ID = "p2p-impeccable-01"

# The one permission this capability ever needs, as approved by the Owner and
# recorded durably by the EXISTING task control plane.
OWNER_APPROVED_PERMISSION = {
    "status": "APPROVED",
    "source_ref": "governance/evidence/p2p-impeccable-01-deterministic-check.json",
    "scope": "READ",
}


def _task_record(**overrides) -> TaskRecord:
    payload = dict(
        task_id=TASK_ID,
        goal_id=GOAL_ID,
        title="Deterministic design-quality check",
        purpose="Run the pinned offline detector on explicitly supplied files.",
        scope=("tests/fixtures/p2p-impeccable-design-quality",),
        acceptance_requirements=("deterministic findings on the bounded fixture pair",),
        required_evidence=("governance/evidence/p2p-impeccable-01-deterministic-check.json",),
        required_capabilities=(CAPABILITY_ID,),
        permission_needs=("READ",),
    )
    payload.update(overrides)
    return TaskRecord(**payload)


def _install_task_authority(
    root: Path,
    registry: Path,
    *,
    permission_state: dict | None = None,
    task: TaskRecord | None = None,
) -> dict:
    """Write a real durable P2P task plan and run the EXISTING C11 preflight.

    This is the permission authority the adapter reuses. Nothing here is a new
    permission system: it is the ordinary task store plus
    ``evaluate_task_preflight``, exactly as the task control plane writes it.
    """

    record = task or _task_record()
    plan = TaskPlan(
        goal_id=GOAL_ID,
        logical_owner=LogicalOwner.for_goal(GOAL_ID),
        tasks={record.task_id: record},
        plan_scope=("p2p-impeccable-01",),
    )
    from p2p_capabilities.model import load_registry as _load_registry
    from p2p_capabilities.vendor_skill import vendor_readiness_snapshot as _readiness

    manifest = next(
        item for item in _load_registry(registry)["parsed"] if item.capability_id == CAPABILITY_ID
    )
    plan, result = plan.preflight(
        record.task_id,
        capability_readiness={
            CAPABILITY_ID: _readiness(manifest, repository_root=root, registry_path=registry)
        },
        permission_state=(
            {"READ": dict(OWNER_APPROVED_PERMISSION)} if permission_state is None else permission_state
        ),
    )
    TaskStateStore(root).save(plan)
    return result


def _grant(action: str = "ui.design_quality.deterministic_check", **kwargs) -> dict:
    return idq.authorize(
        action,
        granted_by=kwargs.pop("granted_by", "P2P-IMPECCABLE-01-test"),
        registry_path=kwargs.pop("registry_path", EXEC_REGISTRY),
        repository_root=kwargs.pop("repository_root", EXEC_ROOT),
        **kwargs,
    )


def _mirror_repository(destination: Path) -> Path:
    """Copy only what the adapter needs into a throwaway root.

    Tamper proofs run against this mirror; canonical vendored source is never
    mutated by the test suite.
    """

    for relative in (
        ".p2p/system/p2p_capabilities/capabilities.json",
        ".p2p/system/p2p_capabilities/impeccable_detector_runner.mjs",
        "tests/fixtures/p2p-impeccable-design-quality/before.html",
        "tests/fixtures/p2p-impeccable-design-quality/after.html",
    ):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, target)
    shutil.copytree(VENDOR_ROOT, destination / VENDOR_ROOT.relative_to(REPO_ROOT))
    return destination


def _authorized_mirror(destination: Path) -> Path:
    """A mirror that also carries a durable, Owner-approved, PASS task."""

    mirror = _mirror_repository(destination)
    _install_task_authority(mirror, mirror / ".p2p/system/p2p_capabilities/capabilities.json")
    return mirror


# Session-scoped execution root. Execution proofs never mutate the real
# repository: neither its vendored snapshot nor its .p2p/state task store.
_SESSION_DIR = tempfile.TemporaryDirectory(prefix="p2p-impeccable-exec-")
atexit.register(_SESSION_DIR.cleanup)
EXEC_ROOT = _authorized_mirror(Path(_SESSION_DIR.name).resolve())
EXEC_REGISTRY = EXEC_ROOT / ".p2p" / "system" / "p2p_capabilities" / "capabilities.json"
EXEC_FIXTURES = EXEC_ROOT / "tests" / "fixtures" / "p2p-impeccable-design-quality"
EXEC_BEFORE = EXEC_FIXTURES / "before.html"
EXEC_AFTER = EXEC_FIXTURES / "after.html"


def _route(request: str) -> dict:
    return discover_vendor_skills(request, registry_path=REGISTRY_PATH, repository_root=REPO_ROOT)


def _classification(request: str) -> str:
    route = _route(request)
    result = next(
        item for item in route["route"]["results"] if item["capability_id"] == CAPABILITY_ID
    )
    return result["classification"]


class RegistryProjectionTests(unittest.TestCase):
    def test_record_is_noncanonical_discovered_vendor_skill(self) -> None:
        entry = _registry_entry()
        self.assertEqual(entry["TYPE"], "SKILL")
        self.assertEqual(entry["STATUS"], "DISCOVERED")
        self.assertEqual(entry["INVOCATION_CLASS"], "MODEL_ROUTABLE")
        self.assertFalse(entry["CANONICAL_QUORUM_MEMBER"])
        self.assertFalse(entry["OPTIONAL_SPECIALIST"])
        manifest = next(
            item for item in load_registry(REGISTRY_PATH)["parsed"] if item.capability_id == CAPABILITY_ID
        )
        self.assertTrue(is_vendor_skill(manifest))

    def test_projection_is_bounded_and_advisory(self) -> None:
        projection = _registry_entry()["UPSTREAM_PROVENANCE"]["capability_projection"]
        self.assertEqual(len(projection["projected_actions"]), 7)
        self.assertEqual(projection["executable_actions"], ["ui.design_quality.deterministic_check"])
        self.assertEqual(tuple(projection["projected_actions"]), idq.PROJECTED_ACTIONS)
        self.assertTrue(projection["law"].startswith("AVAILABLE != LOADED != AUTHORIZED != EXECUTED"))
        self.assertIn("existing P2P permission", projection["law"])
        # Projection must be a strict subset of the discovered upstream surface.
        self.assertLess(len(projection["projected_actions"]), projection["upstream_commands_discovered"])
        self.assertNotIn("init", projection["projected_actions"])
        self.assertIn("live", projection["not_projected"])

    def test_no_global_activation_or_default_loading(self) -> None:
        entry = _registry_entry()
        integration = entry["UPSTREAM_PROVENANCE"]["integration"]
        self.assertEqual(integration["load_mode"], "ON_DEMAND")
        self.assertEqual(integration["install_mode"], "DISABLED")
        self.assertFalse(integration["network_runtime"])
        self.assertFalse(integration["credentials"])
        self.assertFalse(integration["browser_runtime"])
        self.assertFalse(integration["model_required"])
        for prohibition in ("default-context-loading", "global-activation", "own-implementation-decisions"):
            self.assertIn(prohibition, entry["PROHIBITED_ACTIONS"])

    def test_availability_is_metadata_only(self) -> None:
        report = idq.availability(registry_path=REGISTRY_PATH, repository_root=REPO_ROOT)
        self.assertTrue(report["available"])
        self.assertFalse(report["content_loaded"])
        self.assertFalse(report["authorized"])
        self.assertFalse(report["executed"])
        self.assertFalse(report["default_context_loading"])
        self.assertFalse(report["global_activation"])


class RoutingEligibilityTests(unittest.TestCase):
    def test_design_quality_request_is_eligible(self) -> None:
        route = _route("Run a design critique on the settings screen and flag any anti-patterns.")
        self.assertIn(CAPABILITY_ID, route["route"]["selected"])
        self.assertNotEqual(
            _classification("Run a design critique on the settings screen and flag any anti-patterns."),
            "NOT_APPLICABLE",
        )

    def test_unrelated_requests_do_not_route(self) -> None:
        for request in (
            "Explain how to choose a PostgreSQL index.",
            "Implement the cultivation game UI in code.",
            "Design a cultivation game UI image prompt.",
            "Create a whiteboard animation from an SRT and render an MP4",
            "Write an advertising slogan and campaign headline for a new brand.",
        ):
            with self.subTest(request=request):
                self.assertEqual(_classification(request), "NOT_APPLICABLE")
                self.assertNotIn(CAPABILITY_ID, _route(request)["selected"])

    def test_discovery_never_loads_vendor_content(self) -> None:
        route = _route("design critique for the dashboard")
        self.assertFalse(route["content_loaded"])
        self.assertFalse(route["permission_grant"])
        for skill in route["skills"]:
            self.assertFalse(skill["content_loaded"])

    def test_explicit_load_is_separate_from_routing(self) -> None:
        loaded = load_vendor_skill(
            CAPABILITY_ID,
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
            references=["skills/impeccable/reference/critique.md"],
        )
        self.assertTrue(loaded["content_loaded"])
        self.assertFalse(loaded["permission_grant"])
        self.assertFalse(loaded["network_used"])
        self.assertEqual(
            sorted(loaded["loaded_paths"]),
            ["skills/impeccable/SKILL.md", "skills/impeccable/reference/critique.md"],
        )


class AuthorizationLawTests(unittest.TestCase):
    def test_execution_requires_authorization(self) -> None:
        with self.assertRaises(idq.DesignQualityError):
            idq.deterministic_check(
                [EXEC_BEFORE], authorization={}, repository_root=EXEC_ROOT, registry_path=EXEC_REGISTRY
            )

    def test_authorization_uses_the_existing_portable_execution_contract(self) -> None:
        grant = _grant()
        self.assertEqual(
            grant["authority_surface"], "p2p_capabilities.host_executor.PortableExecutionRequest"
        )
        request = PortableExecutionRequest.from_mapping(grant["request"])
        self.assertEqual(request.required_capabilities, (CAPABILITY_ID,))
        self.assertEqual(request.purpose, "ui.design_quality.deterministic_check")
        self.assertEqual(request.task_fingerprint, grant["manifest_identity"])
        self.assertFalse(request.mutation_requested)
        self.assertEqual(request.fingerprint, grant["request_fingerprint"])

    def test_advisory_action_cannot_execute(self) -> None:
        grant = _grant("ui.design_quality.critique")
        self.assertTrue(grant["advisory_only"])
        with self.assertRaises(idq.DesignQualityError):
            idq.deterministic_check(
                [EXEC_BEFORE], authorization=grant, repository_root=EXEC_ROOT, registry_path=EXEC_REGISTRY
            )

    def test_unknown_action_is_rejected(self) -> None:
        with self.assertRaises(idq.DesignQualityError):
            idq.authorize(
                "ui.design_quality.redesign_everything",
                granted_by="P2P-IMPECCABLE-01-test",
                registry_path=REGISTRY_PATH,
                repository_root=REPO_ROOT,
            )

    def test_authorization_binds_verified_snapshot(self) -> None:
        grant = _grant()
        self.assertTrue(grant["authorized"])
        self.assertFalse(grant["executed"])
        self.assertEqual(grant["upstream_commit"], UPSTREAM_COMMIT)
        self.assertEqual(grant["snapshot_sha256"], snapshot_tree_sha256(VENDOR_ROOT))
        self.assertEqual(grant["implementation_authority"], "P2P")


class AuthorizationFailClosedTests(unittest.TestCase):
    """Control-Tower finding: authorization must not be forgeable caller data."""

    def _expect_fail_closed(self, authorization, *, root=EXEC_ROOT, registry=EXEC_REGISTRY, target=EXEC_BEFORE):
        with mock.patch.object(idq.subprocess, "run") as spawned:
            with self.assertRaises(idq.DesignQualityAuthorizationError) as caught:
                idq.deterministic_check(
                    [target], authorization=authorization, repository_root=root, registry_path=registry
                )
            spawned.assert_not_called()
        return str(caught.exception)

    # --- A. forged authorization -------------------------------------------
    def test_a1_naive_forged_mapping_fails_closed(self) -> None:
        reason = self._expect_fail_closed(
            {"authorized": True, "capability_id": CAPABILITY_ID, "action": "ui.design_quality.deterministic_check"}
        )
        self.assertEqual(reason, "AUTHORIZATION_SCHEMA_INVALID")

    def test_a2_self_consistent_forgery_is_not_an_issued_grant(self) -> None:
        """An attacker can rebuild the request and its fingerprint; it still fails."""

        real = _grant()
        forged = copy.deepcopy(real)
        rebuilt = PortableExecutionRequest.from_mapping(forged["request"])
        forged["request_fingerprint"] = rebuilt.fingerprint
        forged["granted_by"] = "attacker"
        self.assertEqual(forged["request_fingerprint"], real["request_fingerprint"])
        idq._ISSUED_GRANTS.discard(forged["request_fingerprint"])  # never minted here
        try:
            reason = self._expect_fail_closed(forged)
        finally:
            idq._ISSUED_GRANTS.add(real["request_fingerprint"])
        self.assertEqual(reason, "AUTHORIZATION_NOT_ISSUED_BY_P2P_AUTHORITY")

    def test_a3_tampered_fingerprint_fails_closed(self) -> None:
        forged = copy.deepcopy(_grant())
        forged["request_fingerprint"] = "0" * 64
        self.assertEqual(self._expect_fail_closed(forged), "AUTHORIZATION_FINGERPRINT_MISMATCH")

    def test_a4_missing_request_binding_fails_closed(self) -> None:
        forged = copy.deepcopy(_grant())
        forged.pop("request")
        self.assertEqual(self._expect_fail_closed(forged), "AUTHORIZATION_REQUEST_MISSING")

    # --- C. wrong capability / action / binding ----------------------------
    def test_c1_wrong_capability_fails_closed(self) -> None:
        forged = copy.deepcopy(_grant())
        forged["capability_id"] = "ui.design"
        self.assertEqual(self._expect_fail_closed(forged), "AUTHORIZATION_CAPABILITY_MISMATCH")

    def test_c2_advisory_action_cannot_be_promoted_to_execution(self) -> None:
        forged = copy.deepcopy(_grant("ui.design_quality.critique"))
        forged["action"] = "ui.design_quality.deterministic_check"
        self.assertEqual(self._expect_fail_closed(forged), "AUTHORIZATION_ACTION_BINDING_MISMATCH")

    def test_c3_action_swap_inside_the_bound_request_fails_closed(self) -> None:
        forged = copy.deepcopy(_grant())
        forged["request"]["purpose"] = "ui.design_quality.polish"
        self.assertEqual(self._expect_fail_closed(forged), "AUTHORIZATION_FINGERPRINT_MISMATCH")

    def test_c4_rebinding_to_another_snapshot_fails_closed(self) -> None:
        forged = copy.deepcopy(_grant())
        forged["request"]["candidate_binding"] = "vendor-snapshot:ui.design_quality:" + "f" * 64
        self.assertEqual(self._expect_fail_closed(forged), "AUTHORIZATION_FINGERPRINT_MISMATCH")

    def test_c5_escalated_permissions_fail_closed(self) -> None:
        forged = copy.deepcopy(_grant())
        forged["request"]["permission_needs"] = ["READ", "MUTATE"]
        forged["request"]["granted_permissions"] = ["READ", "MUTATE"]
        self.assertEqual(self._expect_fail_closed(forged), "AUTHORIZATION_FINGERPRINT_MISMATCH")

    # --- B. post-authorization snapshot drift ------------------------------
    def test_b1_vendor_drift_after_authorization_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            mirror = _authorized_mirror(Path(raw).resolve())
            registry = mirror / ".p2p" / "system" / "p2p_capabilities" / "capabilities.json"
            target = mirror / "tests" / "fixtures" / "p2p-impeccable-design-quality" / "before.html"
            grant = _grant(registry_path=registry, repository_root=mirror)

            # Authorization is valid at mint time against the mirror.
            self.assertTrue(grant["authorized"])

            # Vendor content changes AFTER authorization, BEFORE execution.
            drifted = mirror / VENDOR_ROOT.relative_to(REPO_ROOT) / "skills" / "impeccable" / "scripts" / "detector" / "registry" / "antipatterns.mjs"
            drifted.write_text(drifted.read_text(encoding="utf-8") + "\n// injected after authorization\n", encoding="utf-8")

            reason = self._expect_fail_closed(grant, root=mirror, registry=registry, target=target)
            self.assertIn(reason, {"VENDOR_SNAPSHOT_HASH_MISMATCH", "VENDOR_SNAPSHOT_DRIFT"})

        # Canonical vendored source is untouched by this proof.
        entry = _registry_entry()["UPSTREAM_PROVENANCE"]
        self.assertEqual(entry["snapshot_sha256"], snapshot_tree_sha256(VENDOR_ROOT))

    def test_b2_vendor_removal_after_authorization_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            mirror = _authorized_mirror(Path(raw).resolve())
            registry = mirror / ".p2p" / "system" / "p2p_capabilities" / "capabilities.json"
            target = mirror / "tests" / "fixtures" / "p2p-impeccable-design-quality" / "before.html"
            grant = _grant(registry_path=registry, repository_root=mirror)
            shutil.rmtree(mirror / VENDOR_ROOT.relative_to(REPO_ROOT))
            self.assertEqual(
                self._expect_fail_closed(grant, root=mirror, registry=registry, target=target),
                "VENDOR_SNAPSHOT_MISSING",
            )

    # --- D. valid unchanged authorized execution ---------------------------
    def test_d1_valid_grant_executes_after_revalidation(self) -> None:
        report = idq.deterministic_check(
            [EXEC_BEFORE], authorization=_grant(), repository_root=EXEC_ROOT, registry_path=EXEC_REGISTRY
        )
        if report.get("status") == "BLOCKED_OPTIONAL_RUNTIME":
            self.skipTest("node runtime unavailable")
        self.assertEqual(report["status"], "COMPLETED")
        self.assertTrue(report["binding_revalidated_before_execution"])
        self.assertEqual(report["snapshot_sha256"], snapshot_tree_sha256(VENDOR_ROOT))
        self.assertFalse(report["source_mutation"])
        self.assertFalse(report["network_used"])
        self.assertFalse(report["model_used"])

    def test_d2_mirror_execution_still_works_without_drift(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            mirror = _authorized_mirror(Path(raw).resolve())
            registry = mirror / ".p2p" / "system" / "p2p_capabilities" / "capabilities.json"
            target = mirror / "tests" / "fixtures" / "p2p-impeccable-design-quality" / "before.html"
            grant = _grant(registry_path=registry, repository_root=mirror)
            report = idq.deterministic_check(
                [target], authorization=grant, repository_root=mirror, registry_path=registry
            )
            if report.get("status") == "BLOCKED_OPTIONAL_RUNTIME":
                self.skipTest("node runtime unavailable")
            self.assertEqual(report["status"], "COMPLETED")
            self.assertTrue(REQUIRED_ANTIPATTERNS.issubset(set(report["antipattern_counts"])))


class PermissionAuthorityTests(unittest.TestCase):
    """Control-Tower finding 1: a binding contract is not permission authority.

    AUTHORIZATION = existing verified P2P permission (durable task state +
    C11 preflight) + PortableExecutionRequest identity/binding.
    """

    def _unauthorized_mirror(self, raw: str) -> tuple[Path, Path, Path]:
        mirror = _mirror_repository(Path(raw).resolve())
        registry = mirror / ".p2p" / "system" / "p2p_capabilities" / "capabilities.json"
        target = mirror / "tests" / "fixtures" / "p2p-impeccable-design-quality" / "before.html"
        return mirror, registry, target

    # --- E1: granted_by is a label, never an authority ---------------------
    def test_e1_arbitrary_granted_by_cannot_authorize(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            mirror, registry, _ = self._unauthorized_mirror(raw)
            for caller in ("attacker", "root", "P2P", "", "  "):
                with self.subTest(caller=caller):
                    with self.assertRaises(idq.DesignQualityAuthorizationError) as caught:
                        idq.authorize(
                            "ui.design_quality.deterministic_check",
                            granted_by=caller,
                            registry_path=registry,
                            repository_root=mirror,
                        )
                    self.assertNotIn("authorized", str(caught.exception).lower())

    def test_e1b_missing_permission_authority_is_named_precisely(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            mirror, registry, _ = self._unauthorized_mirror(raw)
            with self.assertRaises(idq.DesignQualityPermissionError) as caught:
                idq.authorize(
                    "ui.design_quality.deterministic_check",
                    granted_by="anyone",
                    registry_path=registry,
                    repository_root=mirror,
                )
            self.assertEqual(str(caught.exception), "PERMISSION_AUTHORITY_STATE_MISSING")

    # --- E2: a caller-minted binding without permission fails closed -------
    def test_e2_caller_minted_binding_without_permission_fails_closed(self) -> None:
        """The strongest forgery: a real, self-consistent, *issued* binding.

        The caller builds the exact portable request the adapter would build
        and even inserts its fingerprint into the issuance set. Without an
        existing P2P permission decision it still cannot execute.
        """

        with tempfile.TemporaryDirectory() as raw:
            mirror, registry, target = self._unauthorized_mirror(raw)
            identity = idq._resolve_identity(registry, mirror)
            request = PortableExecutionRequest(
                request_id="impeccable-caller-minted",
                task_id="p2p-impeccable-01",
                goal_id="IMPECCABLE_01",
                task_fingerprint=identity["manifest_identity"],
                project_binding=identity["project_binding"],
                candidate_binding=identity["candidate_binding"],
                purpose="ui.design_quality.deterministic_check",
                scope=(identity["vendor_relative"],),
                required_capabilities=(CAPABILITY_ID,),
                permission_needs=("READ",),
                granted_permissions=("READ",),
                expected_environment="LOCAL_PROJECT",
                created_at="P2P-IMPECCABLE-01",
            )
            forged = {
                "schema": idq.AUTHORIZATION_SCHEMA,
                "capability_id": CAPABILITY_ID,
                "action": "ui.design_quality.deterministic_check",
                "granted_by": "caller",
                "authorized": True,
                "request": request.to_dict(),
                "request_fingerprint": request.fingerprint,
            }
            idq._ISSUED_GRANTS.add(request.fingerprint)
            try:
                with mock.patch.object(idq.subprocess, "run") as spawned:
                    with self.assertRaises(idq.DesignQualityPermissionError) as caught:
                        idq.deterministic_check(
                            [target],
                            authorization=forged,
                            repository_root=mirror,
                            registry_path=registry,
                        )
                    spawned.assert_not_called()
            finally:
                idq._ISSUED_GRANTS.discard(request.fingerprint)
            self.assertEqual(str(caught.exception), "PERMISSION_AUTHORITY_STATE_MISSING")

    # --- E3: the durable owner decision is the authority -------------------
    def test_e3_denied_permission_blocks_authorization(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            mirror, registry, _ = self._unauthorized_mirror(raw)
            result = _install_task_authority(
                mirror,
                registry,
                permission_state={"READ": {"status": "DENIED", "source_ref": "owner-decision"}},
            )
            self.assertNotEqual(result["status"], "PASS")
            with self.assertRaises(idq.DesignQualityPermissionError) as caught:
                _grant(registry_path=registry, repository_root=mirror)
            self.assertTrue(str(caught.exception).startswith("PERMISSION_"))

    def test_e3b_unapproved_permission_waits_for_owner(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            mirror, registry, _ = self._unauthorized_mirror(raw)
            # An asserted permission with no owner source_ref is not approval.
            _install_task_authority(
                mirror, registry, permission_state={"READ": {"status": "APPROVED", "source_ref": ""}}
            )
            with self.assertRaises(idq.DesignQualityPermissionError):
                _grant(registry_path=registry, repository_root=mirror)

    def test_e4_permission_revoked_after_authorization_fails_closed(self) -> None:
        """Grant is valid at mint time; the Owner then revokes. Execution stops."""

        with tempfile.TemporaryDirectory() as raw:
            mirror, registry, target = self._unauthorized_mirror(raw)
            _install_task_authority(mirror, registry)
            grant = _grant(registry_path=registry, repository_root=mirror)
            self.assertTrue(grant["authorized"])

            (mirror / ".p2p" / "state" / "task-state.json").unlink()
            _install_task_authority(
                mirror,
                registry,
                permission_state={"READ": {"status": "REJECTED", "source_ref": "owner-decision"}},
            )
            with mock.patch.object(idq.subprocess, "run") as spawned:
                with self.assertRaises(idq.DesignQualityPermissionError):
                    idq.deterministic_check(
                        [target], authorization=grant, repository_root=mirror, registry_path=registry
                    )
                spawned.assert_not_called()

    # --- E5: what the minted grant actually claims -------------------------
    def test_e5_grant_records_the_reused_permission_authority(self) -> None:
        grant = _grant()
        self.assertEqual(
            grant["permission_authority_surface"],
            "p2p_capabilities.task_state.evaluate_task_preflight@.p2p/state/task-state.json",
        )
        self.assertEqual(grant["permission_task_id"], TASK_ID)
        self.assertEqual(grant["permission_preflight_status"], "PASS")
        self.assertTrue(grant["binding_is_not_permission"])
        self.assertTrue(str(grant["permission_binding"]).startswith(f"task-preflight:{TASK_ID}:"))
        request = PortableExecutionRequest.from_mapping(grant["request"])
        self.assertEqual(request.context_refs, (grant["permission_binding"],))
        self.assertEqual(request.task_id, TASK_ID)

    def test_e6_advisory_grant_carries_no_permission_and_no_execution(self) -> None:
        grant = _grant("ui.design_quality.critique")
        self.assertTrue(grant["advisory_only"])
        self.assertIsNone(grant["permission_authority_surface"])
        request = PortableExecutionRequest.from_mapping(grant["request"])
        self.assertEqual(request.granted_permissions, ())

    def test_e7_permission_binding_swap_fails_closed(self) -> None:
        forged = copy.deepcopy(_grant())
        forged["request"]["context_refs"] = ["task-preflight:p2p-impeccable-01:" + "0" * 64]
        rebuilt = PortableExecutionRequest.from_mapping(forged["request"])
        forged["request_fingerprint"] = rebuilt.fingerprint
        idq._ISSUED_GRANTS.add(rebuilt.fingerprint)
        try:
            with mock.patch.object(idq.subprocess, "run") as spawned:
                with self.assertRaises(idq.DesignQualityPermissionError) as caught:
                    idq.deterministic_check(
                        [EXEC_BEFORE],
                        authorization=forged,
                        repository_root=EXEC_ROOT,
                        registry_path=EXEC_REGISTRY,
                    )
                spawned.assert_not_called()
        finally:
            idq._ISSUED_GRANTS.discard(rebuilt.fingerprint)
        self.assertEqual(str(caught.exception), "PERMISSION_AUTHORITY_DRIFT")


class FinalMomentRevalidationTests(unittest.TestCase):
    """Control-Tower finding 2: the last check must be the last statement."""

    def _mutate_vendor(self, root: Path) -> None:
        drifted = (
            root
            / VENDOR_ROOT.relative_to(REPO_ROOT)
            / "skills"
            / "impeccable"
            / "scripts"
            / "detector"
            / "registry"
            / "antipatterns.mjs"
        )
        drifted.write_text(
            drifted.read_text(encoding="utf-8") + "\n// injected between preflight and launch\n",
            encoding="utf-8",
        )

    def test_f1_last_moment_vendor_drift_fails_closed_and_never_launches(self) -> None:
        """Drift lands AFTER authorization and AFTER every preflight check.

        ``shutil.which`` is the final piece of unrelated work before the launch
        sequence, so mutating the vendor mirror there proves the drift happened
        after the early gate passed and is still caught by the final gate.
        """

        with tempfile.TemporaryDirectory() as raw:
            mirror = _authorized_mirror(Path(raw).resolve())
            registry = mirror / ".p2p" / "system" / "p2p_capabilities" / "capabilities.json"
            target = mirror / "tests" / "fixtures" / "p2p-impeccable-design-quality" / "before.html"
            grant = _grant(registry_path=registry, repository_root=mirror)

            stages: list[str] = []
            real_verify = idq._verify_grant_for_execution

            def recording_verify(*args, **kwargs):
                stage = kwargs.get("stage", "PRE_EXECUTION")
                result = real_verify(*args, **kwargs)
                stages.append(stage)
                return result

            real_which = idq.shutil.which

            def drifting_which(name):
                self._mutate_vendor(mirror)
                return real_which(name)

            with mock.patch.object(idq, "_verify_grant_for_execution", recording_verify):
                with mock.patch.object(idq.shutil, "which", drifting_which):
                    with mock.patch.object(idq.subprocess, "run") as spawned:
                        with self.assertRaises(idq.DesignQualityAuthorizationError) as caught:
                            idq.deterministic_check(
                                [target],
                                authorization=grant,
                                repository_root=mirror,
                                registry_path=registry,
                            )
                        # SUBPROCESS_NOT_LAUNCHED
                        spawned.assert_not_called()

            # The early gate passed; only the final gate caught the drift.
            self.assertEqual(stages, ["PRE_EXECUTION"])
            self.assertIn(
                str(caught.exception), {"VENDOR_SNAPSHOT_HASH_MISMATCH", "VENDOR_SNAPSHOT_DRIFT"}
            )

    def test_f2_last_moment_permission_revocation_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            mirror = _authorized_mirror(Path(raw).resolve())
            registry = mirror / ".p2p" / "system" / "p2p_capabilities" / "capabilities.json"
            target = mirror / "tests" / "fixtures" / "p2p-impeccable-design-quality" / "before.html"
            grant = _grant(registry_path=registry, repository_root=mirror)

            real_which = idq.shutil.which

            def revoking_which(name):
                (mirror / ".p2p" / "state" / "task-state.json").unlink()
                return real_which(name)

            with mock.patch.object(idq.shutil, "which", revoking_which):
                with mock.patch.object(idq.subprocess, "run") as spawned:
                    with self.assertRaises(idq.DesignQualityPermissionError) as caught:
                        idq.deterministic_check(
                            [target],
                            authorization=grant,
                            repository_root=mirror,
                            registry_path=registry,
                        )
                    spawned.assert_not_called()
            self.assertEqual(str(caught.exception), "PERMISSION_AUTHORITY_STATE_MISSING")

    def test_f3_final_gate_is_the_statement_before_subprocess(self) -> None:
        """Source-level proof: nothing sits between the final gate and launch."""

        source = Path(idq.__file__).read_text(encoding="utf-8")
        marker = 'stage="FINAL_PRE_LAUNCH")'
        self.assertIn(marker, source)
        tail = source.split(marker, 1)[1]
        head = tail.split("subprocess.run(", 1)[0]
        statements = [
            line.strip()
            for line in head.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        self.assertEqual(
            statements,
            [
                'identity = verified["identity"]',
                'command = [node, str(runner), "--root", str(root), *absolute]',
                "completed =",
            ],
        )

    def test_f4_successful_run_records_the_final_revalidation(self) -> None:
        report = idq.deterministic_check(
            [EXEC_BEFORE], authorization=_grant(), repository_root=EXEC_ROOT, registry_path=EXEC_REGISTRY
        )
        if report.get("status") == "BLOCKED_OPTIONAL_RUNTIME":
            self.skipTest("node runtime unavailable")
        self.assertEqual(report["final_revalidation_stage"], "FINAL_PRE_LAUNCH")
        self.assertEqual(report["final_revalidation_position"], "IMMEDIATELY_BEFORE_SUBPROCESS")
        self.assertEqual(report["permission_task_id"], TASK_ID)


class DeterministicDetectorProofTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.grant = _grant()

    def check(self, target: Path) -> dict:
        return idq.deterministic_check(
            [target],
            authorization=self.grant,
            repository_root=EXEC_ROOT,
            registry_path=EXEC_REGISTRY,
        )

    def test_before_fixture_reports_required_categories(self) -> None:
        report = self.check(EXEC_BEFORE)
        if report.get("status") == "BLOCKED_OPTIONAL_RUNTIME":
            self.skipTest("node runtime unavailable")
        self.assertEqual(report["status"], "COMPLETED")
        found = set(report["antipattern_counts"])
        self.assertTrue(
            REQUIRED_ANTIPATTERNS.issubset(found),
            f"missing deterministic categories: {sorted(REQUIRED_ANTIPATTERNS - found)}",
        )
        self.assertGreaterEqual(report["finding_count"], len(REQUIRED_ANTIPATTERNS))

    def test_no_model_network_or_browser_is_used(self) -> None:
        report = self.check(EXEC_BEFORE)
        if report.get("status") == "BLOCKED_OPTIONAL_RUNTIME":
            self.skipTest("node runtime unavailable")
        self.assertFalse(report["model_used"])
        self.assertFalse(report["network_used"])
        self.assertFalse(report["browser_used"])
        self.assertFalse(report["source_mutation"])
        self.assertIn(report["engine_mode"], {"REGEX_DEGRADED", "STATIC_HTML_FULL"})

    def test_findings_are_stable_across_repeat_runs(self) -> None:
        first = self.check(EXEC_BEFORE)
        second = self.check(EXEC_BEFORE)
        if first.get("status") == "BLOCKED_OPTIONAL_RUNTIME":
            self.skipTest("node runtime unavailable")
        self.assertEqual(first["engine_mode"], second["engine_mode"])
        self.assertEqual(first["findings"], second["findings"])
        self.assertEqual(
            hashlib.sha256(json.dumps(first["findings"], sort_keys=True).encode()).hexdigest(),
            hashlib.sha256(json.dumps(second["findings"], sort_keys=True).encode()).hexdigest(),
        )

    def test_minimum_correction_clears_the_findings(self) -> None:
        before = self.check(EXEC_BEFORE)
        after = self.check(EXEC_AFTER)
        if before.get("status") == "BLOCKED_OPTIONAL_RUNTIME":
            self.skipTest("node runtime unavailable")
        self.assertEqual(after["finding_count"], 0)
        delta = idq.diff_reports(before, after)
        self.assertEqual(delta["after_finding_count"], 0)
        self.assertEqual(delta["introduced_antipatterns"], [])
        self.assertTrue(REQUIRED_ANTIPATTERNS.issubset(set(delta["resolved_antipatterns"])))

    def test_targets_outside_the_repository_are_refused(self) -> None:
        with self.assertRaises(idq.DesignQualityError):
            idq.deterministic_check(
                [Path("/etc/hosts")],
                authorization=self.grant,
                repository_root=EXEC_ROOT,
                registry_path=EXEC_REGISTRY,
            )


class ProvenanceBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.record = json.loads(PROVENANCE_PATH.read_text(encoding="utf-8"))
        cls.vendor = cls.record["vendors"][0]

    def test_upstream_pin_and_license_are_recorded(self) -> None:
        self.assertEqual(self.vendor["upstream_commit"], UPSTREAM_COMMIT)
        self.assertEqual(self.vendor["upstream_tree"], UPSTREAM_TREE)
        self.assertEqual(self.vendor["root_license"], "Apache-2.0")
        self.assertTrue((VENDOR_ROOT / "LICENSE").is_file())
        self.assertTrue((VENDOR_ROOT / "NOTICE.md").is_file())
        self.assertIn("Apache License", (VENDOR_ROOT / "LICENSE").read_text(encoding="utf-8")[:200])

    def test_every_vendored_file_is_hashed_and_unmodified(self) -> None:
        declared = {item["snapshot_path"]: item for item in self.vendor["files"]}
        present = {
            path.relative_to(REPO_ROOT).as_posix()
            for path in VENDOR_ROOT.rglob("*")
            if path.is_file()
        }
        self.assertEqual(set(declared), present)
        self.assertEqual(len(present), self.vendor["snapshot_file_count"])
        for relative, item in declared.items():
            with self.subTest(file=relative):
                digest = hashlib.sha256((REPO_ROOT / relative).read_bytes()).hexdigest()
                self.assertEqual(digest, item["sha256"])
                self.assertEqual(item["modification_status"], "UNMODIFIED")
                self.assertEqual(item["license"], "Apache-2.0")

    def test_snapshot_hash_matches_registry(self) -> None:
        entry = _registry_entry()["UPSTREAM_PROVENANCE"]
        self.assertEqual(entry["snapshot_sha256"], snapshot_tree_sha256(VENDOR_ROOT))
        self.assertEqual(entry["snapshot_sha256"], self.vendor["snapshot_sha256"])

    def test_no_runtime_cache_or_live_session_surface_was_imported(self) -> None:
        forbidden_names = {"package.json", "bun.lock", "skills-lock.json", "detect-antipatterns-browser.js"}
        forbidden_parts = {"node_modules", ".impeccable", "extension", "demos", "cli", "hooks", "live"}
        for path in VENDOR_ROOT.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(VENDOR_ROOT)
            self.assertNotIn(path.name, forbidden_names)
            self.assertFalse(forbidden_parts & set(relative.parts), f"forbidden surface: {relative}")
            self.assertNotIn("live-", path.name)


class CatalogNonRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        cls.routing = json.loads(ROUTING_PATH.read_text(encoding="utf-8"))

    def test_candidate_is_registered_without_global_install(self) -> None:
        candidate = next(c for c in self.catalog["candidates"] if c["candidate_id"] == "CAND-GAME-UI-019")
        self.assertFalse(candidate["global_install"])
        self.assertEqual(candidate["license"], "Apache-2.0")
        self.assertEqual(candidate["classification"], "CONDITIONAL")
        self.assertIn("ui.design_quality", candidate["capability_domains"])
        self.assertIn("ui.design_quality", self.catalog["domains"])
        self.assertIn(UPSTREAM_COMMIT, candidate["source_version_or_commit"])

    def test_design_quality_is_optional_in_every_profile(self) -> None:
        for name, profile in self.routing["profiles"].items():
            with self.subTest(profile=name):
                self.assertIn("ui.design_quality", profile["optional_capabilities"])
                self.assertNotIn("ui.design_quality", profile["required_capabilities"])
                self.assertNotIn("ui.design_quality", profile["excluded_capabilities"])

    def test_existing_profile_requirements_are_unchanged(self) -> None:
        expected = {
            "WEB_APP": ["ui.design", "ui.frontend"],
            "MOBILE_APP": ["ui.design", "ui.frontend"],
            "2D_GAME": ["ui.game_hud", "ui.design"],
            "THREEJS_GAME": ["game.three.visual", "game.three.asset", "ui.game_hud"],
            "R3F_GAME": ["game.three.visual", "game.three.asset", "ui.game_hud"],
        }
        for name, required in expected.items():
            with self.subTest(profile=name):
                self.assertEqual(self.routing["profiles"][name]["required_capabilities"], required)

    def test_review_authority_invariant_is_declared(self) -> None:
        invariants = " ".join(self.routing["projection_invariants"])
        self.assertIn("DESIGN_REVIEW_AUTHORITY != IMPLEMENTATION_AUTHORITY", invariants)
        self.assertIn("AVAILABLE != LOADED != AUTHORIZED != EXECUTED", invariants)


if __name__ == "__main__":
    unittest.main()
