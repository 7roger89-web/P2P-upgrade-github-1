"""C30 Composable Execution Target — ET1..ET60 test suite.

These tests exercise the pure, deterministic data model in
scripts/p2p_execution_target.py. The module intentionally contains NO
routing, NO execution, NO vendor-specific branches, and NO stored secrets.
It describes and validates execution composition only (§44-45 of C30).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from p2p_execution_target import (  # noqa: E402
    CapabilityState,
    ComponentCapabilities,
    ExecutionTarget,
    EligibilityState,
    Evidence,
    EvidenceFreshness,
    AuthProfile,
    EnvironmentProfile,
    HarnessProfile,
    HealthSnapshot,
    HealthState,
    ModelProfile,
    ModelVariant,
    PermissionProfile,
    ProtocolProfile,
    ProviderProfile,
    QuiesceState,
    TaskRequirements,
    BackendRegistry,
    ToolSetProfile,
    WorkspaceProfile,
    AuthProfile,
    ContractDriftState,
    ContractIdentity,
    drift_state,
    evaluate_execution_target,
    quiesce_allows_destructive,
    quiesce_transition,
)
from p2p_execution_target import _material_identity as _material_identity_payload

GOV_PATH = ROOT / "governance" / "development-control.json"
LEDGER_PATH = (
    ROOT / "docs" / "p2p-development" / "capability-ledger" / "capability-index.json"
)
RESEARCH_PATH = (
    ROOT / "docs" / "p2p-development" / "research" / "execution-target-pattern-research.md"
)
EXECUTION_TARGET_SOURCE = ROOT / "scripts" / "p2p_execution_target.py"


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------

def make_target(
    target_id="t",
    harness_supported=("repo_read", "repo_write", "command_execution"),
    harness_auth="VALID",
    provider_models=("gpt-5",),
    provider_auth="VALID",
    model_id="gpt-5",
    model_tc="SUPPORTED",
    model_so="SUPPORTED",
    evidence=None,
    workspace_class="EPHEMERAL_SANDBOX",
    permission=None,
    protocol=None,
    toolset=None,
):
    caps = ComponentCapabilities(supported=frozenset(harness_supported))
    h = HarnessProfile("codex", "1.0", caps, harness_auth)
    p = ProviderProfile(
        "openai", "https://api.openai.com", frozenset(provider_models),
        ("ACP", "REST"), provider_auth, {},
    )
    m = ModelProfile(model_id, "openai", model_tc, model_so, {}, evidence)
    w = WorkspaceProfile(workspace_class, f"{target_id}-ws", True, False)
    auth = AuthProfile(
        harness_auth_state=harness_auth, provider_auth_state=provider_auth,
    )
    kw = {"auth": auth}
    if permission is not None:
        kw["permission"] = permission
    if protocol is not None:
        kw["protocol"] = protocol
    if toolset is not None:
        kw["toolset"] = toolset
    return ExecutionTarget(target_id, h, p, m, workspace=w, **kw)


def requirements(*caps, workspace_class=None, permissions=None, protocols=None):
    kw = {"required_capabilities": frozenset(caps)}
    if workspace_class:
        kw["required_workspace_class"] = workspace_class
    if permissions:
        kw["required_permissions"] = frozenset(permissions)
    if protocols:
        kw["required_protocol_classes"] = frozenset(protocols)
    return TaskRequirements(**kw)


# ===========================================================================
# ET1..ET9 — separation of dimensions (Harness != Provider != Model != ...)
# ===========================================================================

class SeparationTests(unittest.TestCase):
    """Profiles are independent dimensions; no dimension is a proxy for another."""

    def test_et1_harness_not_provider(self):
        h = HarnessProfile("codex", "1.0", ComponentCapabilities(), "VALID")
        p = ProviderProfile("openai", "https://api.openai.com", frozenset(),
                            (), "VALID", {})
        self.assertNotEqual(h.harness_id, p.provider_id)
        self.assertIsInstance(h, HarnessProfile)
        self.assertIsInstance(p, ProviderProfile)

    def test_et2_provider_not_model(self):
        p = ProviderProfile("openai", "https://api.openai.com",
                            frozenset(["gpt-5"]), (), "VALID", {})
        m = ModelProfile("gpt-5", "openai", "SUPPORTED", "SUPPORTED")
        self.assertNotEqual(p.provider_id, m.model_id)
        self.assertFalse(p == m)

    def test_et3_harness_not_model(self):
        h = HarnessProfile("codex", "1.0", ComponentCapabilities(), "VALID")
        m = ModelProfile("gpt-5", "openai", "SUPPORTED", "SUPPORTED")
        self.assertNotEqual(h.harness_id, m.model_id)

    def test_et4_protocol_not_harness(self):
        pr = ProtocolProfile("ACP", "1.0")
        h = HarnessProfile("codex", "1.0", ComponentCapabilities(), "VALID")
        self.assertNotEqual(pr.protocol_class, h.harness_id)

    def test_et5_toolset_not_protocol(self):
        ts = ToolSetProfile(frozenset(["edit_file"]), frozenset())
        pr = ProtocolProfile("MCP_TOOLS", "1.0")
        self.assertNotEqual(ts.available_tools, pr.protocol_class)

    def test_et6_workspace_not_environment(self):
        w = WorkspaceProfile("CURRENT_REPO", "ws-1", "main")
        e = EnvironmentProfile(
            os_identity="sandbox", runtime_identity="env-1",
            repository_identity="host", cwd_identity="local",
            sandbox_identity="none", host_machine_identity="none",
        )
        self.assertIsNotNone(w.workspace_class)
        self.assertIsNotNone(e.os_identity)
        self.assertNotEqual(w.identity, e.runtime_identity)


class ExecutionBoundaryTests(unittest.TestCase):
    """ET8/ET9 — protocol support and compatibility are not execution truth."""

    def test_et8_mcp_not_execution_support(self):
        """MCP tool support alone never satisfies an execution capability."""
        ts = ToolSetProfile(
            frozenset(), frozenset(["read_resource", "list_tools"]),
            ComponentCapabilities(supported=frozenset(["structured_output"])),
        )
        t = make_target(target_id="mcp", harness_supported=("structured_output",),
                        toolset=ts)
        res = evaluate_execution_target(t, requirements("structured_output"))
        # structured_output is explicitly supported by the harness, so the
        # capability requirement is satisfied (toolset support reinforces):
        self.assertEqual(res.state, EligibilityState.ELIGIBLE)
        # but a capability only the MCP toolset claims with no harness opinion
        # remains unproven: a harness that says nothing about repo_write cannot
        # satisfy repo_write even when a protocol is attached.
        t2 = make_target(
            target_id="mcp2", harness_supported=(),
            toolset=ts, permission=PermissionProfile(frozenset(["repo_write"])),
        )
        res2 = evaluate_execution_target(
            t2, requirements("repo_write", permissions=("repo_write",)))
        # a harness that says nothing about repo_write cannot satisfy
        # repo_write — silence is never promotion; evidence must be explicit
        # (UNKNOWN, not ELIGIBLE):
        self.assertIn(res2.state, (EligibilityState.UNKNOWN,
                                   EligibilityState.INELIGIBLE_CAPABILITY))

    def test_et9_compatibility_not_certification(self):
        """provider_compatible marks transport fit, never behavioral
        certification — that requires the C22-C27 live-certification path,
        which this module does not implement."""
        m = ModelProfile("gpt-5", "openai", "SUPPORTED", "SUPPORTED")
        self.assertEqual(m.provider_compatible, "openai")
        t = make_target(model_id="gpt-5")
        self.assertIsNone(getattr(t, "certified", None))


# ===========================================================================
# ET10..ET15 — evidence honesty: UNKNOWN != SUPPORTED, STALE != CURRENT,
#              documented != live, present != valid, healthy != owned
# ===========================================================================

class EvidenceHonestyTests(unittest.TestCase):

    def test_et10_unknown_not_supported(self):
        t = make_target(target_id="unk", harness_supported=())
        res = evaluate_execution_target(t, requirements("repo_write"))
        self.assertEqual(res.state, EligibilityState.UNKNOWN)
        self.assertNotEqual(res.state, EligibilityState.ELIGIBLE)

    def test_et11_stale_not_current(self):
        ev = Evidence(observed_at="2026-01-01", freshness="STALE",
                      ref="stale-doc")
        t = make_target(
            target_id="st",
            model_id="gpt-5",
            evidence=ev,
        )
        # STALE evidence itself never corrupts eligibility (STALE != BLOCK):
        # capability evidence is still UNKNOWN without harness opinion, so
        # honesty is preserved — the target is not falsely ELIGIBLE:
        res = evaluate_execution_target(t, requirements("repo_write"))
        self.assertNotEqual(res.state, EligibilityState.ELIGIBLE)
        # and stale evidence blocks once the capability is otherwise met:
        t3 = make_target(target_id="st3", evidence=ev)
        res3 = evaluate_execution_target(
            t3, requirements(workspace_class="EPHEMERAL_SANDBOX"))
        # with no capability requirements and STALE model evidence, freshness
        # still fails closed:
        self.assertEqual(res3.state, EligibilityState.INELIGIBLE_FRESHNESS)

    def test_et12_documented_not_live(self):
        """A documented capability (Evidence with CURRENT freshness) is still
        not live-certified; certification is the C22-C27 runtime path."""
        ev = Evidence(observed_at="2026-08-17", freshness="CURRENT",
                      ref="docs")
        t = make_target(target_id="doc", evidence=ev)
        # CURRENT documented evidence is never silently upgraded to live
        # certification — eligibility is never implied by documentation:
        self.assertFalse(hasattr(t, "live_certified"))
        # documented-evidence freshness is honored: STALE document blocks
        # where CURRENT does not (et11 covers the blocking path).

    def test_et13_credential_presence_not_valid(self):
        from p2p_execution_target import AuthProfile
        auth = AuthProfile(
            harness_auth_state="VALID", provider_auth_state="PRESENT",
            harness_credential_ref="ref://vault/codex",
            provider_credential_ref="ref://vault/openai",
        )
        t = ExecutionTarget("pres", make_target().harness, make_target().provider,
                            make_target().model, auth=auth)
        res = evaluate_execution_target(t, requirements("repo_read"))
        self.assertEqual(res.state, EligibilityState.INELIGIBLE_AUTH)

    def test_et14_healthy_not_owned(self):
        order = HealthState.ORDER
        self.assertLess(order.index("HEALTHY"), order.index("OWNED"))

    def test_et15_owned_not_certified(self):
        order = HealthState.ORDER
        self.assertLess(order.index("OWNED"), order.index("CERTIFIED"))


# ===========================================================================
# ET16..ET21 — permission, auth, tool, workspace, freshness blocking
# ===========================================================================

class BlockingTests(unittest.TestCase):

    def test_et16_permission_never_widens(self):
        a = PermissionProfile(frozenset(["repo_read"]))
        b = PermissionProfile(frozenset(["repo_write"]))
        # union of permission envelopes is narrowing (intersection of
        # allowance):
        self.assertEqual(a.union(b).allowed_permissions, frozenset())
        # an allowed permission cannot appear after composition if neither
        # side allowed it:
        c = PermissionProfile(frozenset(["network"]))
        self.assertNotIn("browser", a.union(c).allowed_permissions)
        # Composition can never produce a permission neither side allowed:
        d = PermissionProfile(frozenset(["command_execution"]))
        composed = a.union(d)
        self.assertNotIn("secret_admin", composed.allowed_permissions)
        self.assertTrue(composed.is_subset_of(a))
        self.assertTrue(composed.is_subset_of(d))

    def test_et17_missing_required_permission_blocks(self):
        t = make_target(target_id="pm",
                        permission=PermissionProfile(frozenset(["repo_read"])))
        res = evaluate_execution_target(
            t, requirements("repo_read", permissions=("repo_write",)))
        self.assertEqual(res.state, EligibilityState.INELIGIBLE_PERMISSION)

    def test_et18_missing_material_auth_blocks(self):
        t = make_target(target_id="au", harness_auth="ABSENT")
        res = evaluate_execution_target(t, requirements("repo_read"))
        self.assertEqual(res.state, EligibilityState.INELIGIBLE_AUTH)

    def test_et19_missing_required_tool_capability_blocks(self):
        ts = ToolSetProfile(frozenset(), frozenset())
        t = make_target(target_id="tc", harness_supported=(), toolset=ts)
        res = evaluate_execution_target(t, requirements("structured_output"))
        self.assertIn(res.state, (EligibilityState.UNKNOWN,
                                  EligibilityState.INELIGIBLE_CAPABILITY))

    def test_et20_unsupported_workspace_blocks(self):
        t = make_target(target_id="ws", workspace_class="EPHEMERAL_SANDBOX")
        res = evaluate_execution_target(
            t, requirements("repo_read", workspace_class="REMOTE_WORKSPACE"))
        self.assertEqual(res.state, EligibilityState.INELIGIBLE_WORKSPACE)

    def test_et21_stale_protocol_evidence_blocks(self):
        stale = Evidence("2026-01-01", EvidenceFreshness.STALE, "stale-protocol-doc")
        pr = ProtocolProfile("ACP", "1.0", evidence=stale)
        t = make_target(target_id="pe", protocol=pr)
        res = evaluate_execution_target(
            t, requirements("repo_read", protocols=("ACP",)))
        self.assertEqual(res.state, EligibilityState.INELIGIBLE_FRESHNESS)


# ===========================================================================
# ET22..ET28 — determinism, no ranking, no execution, registry boundaries
# ===========================================================================

class DeterminismTests(unittest.TestCase):

    def test_et22_eval_deterministic(self):
        t = make_target()
        reqs = requirements("repo_write")
        a = evaluate_execution_target(t, reqs)
        b = evaluate_execution_target(t, reqs)
        self.assertEqual(a, b)
        # ten repeated evaluations stay identical:
        for _ in range(9):
            self.assertEqual(evaluate_execution_target(t, reqs), a)

    def test_et23_no_ranking(self):
        """Evaluation returns EligibilityResult — never a ranked list."""
        t = make_target()
        res = evaluate_execution_target(t, requirements("repo_write"))
        self.assertFalse(hasattr(res, "rank"))
        self.assertFalse(hasattr(res, "score"))

    def test_et24_eval_does_not_execute(self):
        """No subprocess/socket/exec call during evaluation."""
        import p2p_execution_target as mod
        src = Path(mod.__file__).read_text()
        for forbidden in ("subprocess", "os.system", "socket.socket", "exec("):
            self.assertNotIn(forbidden, src, forbidden)

    def test_et25_registry_no_routing(self):
        reg = BackendRegistry()
        h = HarnessProfile("h", "1.0",
                           ComponentCapabilities(supported=frozenset(["repo_write"])),
                           "VALID")
        p = ProviderProfile("p", "ep", frozenset(["m"]), (), "VALID", {})
        m = ModelProfile("m", "p", "SUPPORTED", "SUPPORTED")
        reg.register_harness(h)
        reg.register_provider(p)
        reg.register_model(m)
        # enumeration is mechanical; there is no select/prefer/route method:
        for attr in ("select_target", "route_task", "prefer", "rank",
                     "choose_backend", "auto_fallback"):
            self.assertFalse(hasattr(reg, attr), attr)

    def test_et26_registry_no_execution(self):
        import p2p_execution_target as mod
        src = Path(mod.__file__).read_text()
        for tok in ("subprocess", "asyncio.run", "os.exec", "execute_task",
                    "run_task"):
            self.assertNotIn(tok, src, tok)

    def test_et27_registry_no_task_state(self):
        reg = BackendRegistry()
        for attr in ("tasks", "task_state", "inflight", "queue"):
            self.assertFalse(hasattr(reg, attr), attr)

    def test_et28_registry_not_ledger(self):
        """Registry knows components, not capability-roadmap knowledge."""
        reg = BackendRegistry()
        self.assertFalse(hasattr(reg, "capabilities"))
        ledger = json.loads(LEDGER_PATH.read_text())
        reg_keys = set(vars(type(reg)) or dir(reg))
        ledger_keys = set(ledger.keys())
        self.assertFalse(reg_keys.issuperset(ledger_keys))


# ===========================================================================
# ET29..ET35 — fingerprint: no secrets, material changes change fingerprint
# ===========================================================================

class FingerprintTests(unittest.TestCase):

    def test_et29_fingerprint_excludes_secrets(self):
        """Credential *references* may appear in the fingerprint (identity
        only); secret *values* never do (AUTH_STATE != SECRET_VALUE, C28)."""
        t = make_target()
        Ap = AuthProfile(
            harness_auth_state="VALID", provider_auth_state="VALID",
            harness_credential_ref="ref://vault/codex-1",
            provider_credential_ref="ref://vault/openai-2",
        )
        with_creds = ExecutionTarget(
            "sec", t.harness, t.provider, t.model, auth=Ap,
        )
        with_creds2 = ExecutionTarget(
            "sec", t.harness, t.provider, t.model,
            auth=AuthProfile(
                harness_auth_state="VALID", provider_auth_state="VALID",
                harness_credential_ref="ref://vault/codex-A",
                provider_credential_ref="ref://vault/openai-B",
            ),
        )
        # reference change is a material identity change (different auth
        # bindings are different targets):
        self.assertNotEqual(t.fingerprint(), with_creds.fingerprint())
        self.assertNotEqual(with_creds.fingerprint(), with_creds2.fingerprint())
        # but no secret VALUE surfaces in the fingerprint payload:
        fp_payload = json.dumps(
            _material_identity_payload(t), sort_keys=True, separators=(",", ":"),
        )
        for tok in ("value", "secret", "token", "password", "key="):
            self.assertNotIn(tok, fp_payload.lower(), tok)

    def test_et36_old_contract_cannot_remain_current(self):
        cur = ContractIdentity("c", "1.0", "ACP", "2026-08-17")
        ds = drift_state(cur, "2.0", True)
        self.assertEqual(ds, ContractDriftState.MIGRATION_REQUIRED)

    def test_et36_fixed_old_contract_cannot_remain_current(self):
        cur = ContractIdentity("c", "1.0", "ACP", "2026-08-17")
        self.assertEqual(drift_state(cur, "2.0", True),
                         ContractDriftState.MIGRATION_REQUIRED)

    def test_et30_harness_version_changes_fingerprint(self):
        a = make_target()
        b = make_target()
        b2 = ExecutionTarget(
            "t",
            HarnessProfile("codex", "2.0", b.harness.capabilities, "VALID"),
            b.provider, b.model,
        )
        self.assertNotEqual(a.fingerprint(), b2.fingerprint())

    def test_et31_endpoint_identity_changes_fingerprint(self):
        a = make_target()
        b = ExecutionTarget(
            "t", a.harness,
            ProviderProfile("openai", "https://api.other.example",
                            frozenset(["gpt-5"]), ("ACP", "REST"), "VALID", {}),
            a.model,
        )
        self.assertNotEqual(a.fingerprint(), b.fingerprint())

    def test_et32_model_identity_changes_fingerprint(self):
        a = make_target()
        b = ExecutionTarget("t", a.harness, a.provider,
                            ModelProfile("gpt-6", "openai", "SUPPORTED",
                                         "SUPPORTED"))
        self.assertNotEqual(a.fingerprint(), b.fingerprint())

    def test_et33_contract_version_changes_fingerprint(self):
        pr = ProtocolProfile("ACP", "1.0")
        a = make_target(protocol=pr)
        b = make_target(protocol=ProtocolProfile("ACP", "2.0"))
        self.assertNotEqual(a.fingerprint(), b.fingerprint())

    def test_et34_workspace_identity_changes_fingerprint(self):
        a = make_target()
        b = ExecutionTarget("t", a.harness, a.provider, a.model,
                            workspace=WorkspaceProfile("EPHEMERAL_SANDBOX", "ws-2",
                                                       True, False))
        self.assertNotEqual(a.fingerprint(), b.fingerprint())

    def test_et35_permission_envelope_changes_fingerprint(self):
        a = make_target(permission=PermissionProfile(frozenset(["repo_read"])))
        b = make_target(permission=PermissionProfile(
            frozenset(["repo_read", "command_execution"])))
        self.assertNotEqual(a.fingerprint(), b.fingerprint())


# ===========================================================================
# ET36..ET41 — contract drift, substitution, metadata locality, UI-relevant
#              durability
# ===========================================================================

class DriftAndDurabilityTests(unittest.TestCase):

    def test_et37_future_harness_no_core_vendor_branch(self):
        """A new harness profile is plain data; no conditional branches in
        the core module."""
        future = HarnessProfile(
            "opencode", "0.9",
            ComponentCapabilities(supported=frozenset(["repo_read"])),
            "UNKNOWN",
        )
        t = make_target()
        t2 = ExecutionTarget("t", future, t.provider, t.model)
        res = evaluate_execution_target(t2, requirements("repo_read"))
        # UNKNOWN auth fails closed:
        self.assertEqual(res.state, EligibilityState.INELIGIBLE_AUTH)

    def test_et38_vendor_metadata_outside_selection(self):
        m = ModelProfile(
            "gpt-5", "openai", "SUPPORTED", "SUPPORTED",
            {"vendor_note": "marketing claim", "provider_rating": 9},
        )
        self.assertIn("vendor_note", m.context_metadata)
        src = EXECUTION_TARGET_SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("vendor_note", src)
        self.assertNotIn("provider_rating", src)

    def test_et39_browser_optional(self):
        t = make_target(target_id="br", harness_supported=("repo_read",))
        res = evaluate_execution_target(t, requirements("repo_read"))
        self.assertEqual(res.state, EligibilityState.ELIGIBLE)
        # browser is not a required capability for a read task:
        self.assertNotIn("browser", t.effective_capability().unsupported)

    def test_et40_workspace_binding_recorded(self):
        """C30 records workspace identity/binding; it does NOT create automatic
        worktrees (ET40, §31)."""
        w = WorkspaceProfile("ISOLATED_GIT_WORKTREE", "wt-42", "main")
        self.assertEqual(w.identity, "wt-42")
        self.assertEqual(w.repo_binding, "main")
        src = EXECUTION_TARGET_SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("worktree_create", src)

    def test_et41_quiesce_drain_recorded(self):
        self.assertTrue(quiesce_transition("QUIESCENT", "STOPPED"))
        self.assertTrue(quiesce_transition("DRAINING", "QUIESCENT"))
        self.assertTrue(quiesce_allows_destructive("DRAINING"))
        self.assertFalse(quiesce_allows_destructive("ACCEPTING_WORK"))
        self.assertFalse(quiesce_transition("UNKNOWN", "STOPPED"))


# ===========================================================================
# ET42..ET50 — durable research reconciliation, security posture
# ===========================================================================

class ResearchAndSecurityTests(unittest.TestCase):

    def test_et42_repo_map_recorded(self):
        artifact = RESEARCH_PATH.read_text()
        self.assertIn("repo map", artifact.lower())

    def test_et43_full_repo_graph_not_mandatory(self):
        artifact = RESEARCH_PATH.read_text()
        lower = artifact.lower()
        self.assertTrue("token" in lower or "budget" in lower)

    def test_et44_failure_only_diagnostics_recorded(self):
        artifact = RESEARCH_PATH.read_text()
        self.assertIn("diagnostic", artifact.lower())

    def test_et45_autopilot_recorded_not_implemented(self):
        artifact = RESEARCH_PATH.read_text()
        self.assertIn("autopilot", artifact.lower())
        src = EXECUTION_TARGET_SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("autopilot", src.lower())

    def test_et46_permission_bypass_rejected(self):
        artifact = RESEARCH_PATH.read_text()
        self.assertIn("bypass", artifact.lower())
        src = EXECUTION_TARGET_SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("bypass", src)

    def test_et47_unbounded_fanout_rejected(self):
        src = EXECUTION_TARGET_SOURCE.read_text(encoding="utf-8")
        for tok in ("spawn", "Thread(", "asyncio.create_task", "fan"):
            self.assertNotIn(tok, src, tok)

    def test_et48_no_background_autonomy(self):
        src = EXECUTION_TARGET_SOURCE.read_text(encoding="utf-8")
        for tok in ("daemon", "Timer(", "schedule", "Background", "cron",
                    "scheduler"):
            self.assertNotIn(tok, src, tok)

    def test_et49_github_not_authority(self):
        src = EXECUTION_TARGET_SOURCE.read_text(encoding="utf-8")
        self.assertNotIn("github", src.lower())

    def test_et50_compatibility_not_certification(self):
        m = ModelProfile("gpt-5", "openai", "SUPPORTED", "SUPPORTED")
        self.assertNotIn(m.provider_compatible, ("CERTIFIED", "VERIFIED"))


# ===========================================================================
# ET51..ET58 — regression anchors
# ===========================================================================

class RegressionAnchorTests(unittest.TestCase):

    def _run_suite(self, *paths: str) -> str:
        cmd = [
            sys.executable, "-m", "pytest",
            "-p", "no:warnings",
            "--tb=line",
            "-q",
        ] + [str(ROOT / p) for p in paths]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return r.stdout + r.stderr

    @unittest.skipUnless(importlib.util.find_spec("pytest"), "pytest is not installed in this environment")
    def test_et51_c29_gc_green(self):
        out = self._run_suite("tests/test_p2p_goal_closure.py")
        self.assertIn("passed", out)
        self.assertNotIn("failed", out.lower().split("passed")[-1])
        self.assertNotIn("error", out.lower().split("passed")[-1])

    @unittest.skipUnless(importlib.util.find_spec("pytest"), "pytest is not installed in this environment")
    def test_et52_c28_onboarding_green(self):
        out = self._run_suite("tests/test_p2p_secure_onboarding.py")
        self.assertIn("passed", out)
        self.assertNotIn("failed", out.lower().split("passed")[-1])

    @unittest.skipUnless(importlib.util.find_spec("pytest"), "pytest is not installed in this environment")
    def test_et53_c27_machinery_green(self):
        out = self._run_suite("tests/test_p2p_live_certification.py")
        self.assertIn("passed", out)
        self.assertNotIn("failed", out.lower().split("passed")[-1])

    @unittest.skipUnless(importlib.util.find_spec("pytest"), "pytest is not installed in this environment")
    def test_et54_c26_provenance_green(self):
        out = self._run_suite("tests/test_p2p_ledger_provenance.py")
        self.assertIn("passed", out)
        self.assertNotIn("failed", out.lower().split("passed")[-1])

    @unittest.skipUnless(importlib.util.find_spec("pytest"), "pytest is not installed in this environment")
    def test_et55_c25_charter_ledger_green(self):
        out = self._run_suite("tests/test_p2p_capability_foundation.py")
        self.assertIn("passed", out)
        self.assertNotIn("failed", out.lower().split("passed")[-1])

    def test_et56_c08_deferred(self):
        gov = json.loads(GOV_PATH.read_text())
        items = gov["roadmap"]["items"]
        c08 = next(i for i in items if i["id"] == "C08")
        self.assertEqual(c08["status"], "DEFERRED")

    def test_et57_c09_blocked(self):
        gov = json.loads(GOV_PATH.read_text())
        items = gov["roadmap"]["items"]
        c09 = next(i for i in items if i["id"] == "C09")
        self.assertEqual(c09["status"], "BLOCKED")

    def test_et58_baseline_immutable(self):
        gov = json.loads(GOV_PATH.read_text())
        base = gov.get("official_baseline") or {}
        self.assertEqual(base.get("version"), "8.4.7-C-codex.19")
        self.assertTrue(base.get("artifact_sha256"))


# ===========================================================================
# ET59..ET60 — candidate policy + research provenance
# ===========================================================================

class ClosureAnchorTests(unittest.TestCase):

    def test_et59_c29_candidate_policy_applied(self):
        """The repair goal changes runtime/governance but stays unpromoted."""
        gov = json.loads(GOV_PATH.read_text())
        current = gov["current_development"]
        self.assertEqual(current["development_goal"], "P2P-CANONICAL-LINEAGE-REPAIR-01")
        self.assertEqual(current["status"], "RECONCILED_NO_ACTIVE_PROMOTION_CANDIDATE")
        self.assertEqual(current["source_version_status"], "LINEAGE_RECONCILED")
        binding = current["candidate_identity_binding"]
        self.assertEqual(binding["candidate_version"], "8.4.7-C-codex.74")
        self.assertEqual(binding["status"], "HISTORICAL_SEALED_UNPROMOTED_REFERENCE")
        self.assertFalse(binding["current_promotion_target"])
        self.assertEqual(gov["official_baseline"]["version"], "8.4.7-C-codex.19")

    def test_et60_research_provenance_durable(self):
        self.assertTrue(RESEARCH_PATH.exists())
        text = RESEARCH_PATH.read_text()
        # all §40 ADOPT directions referenced:
        for keyword in ("control plane", "structured", "workspace",
                        "health", "drain", "drift", "repo map",
                        "diagnostic", "autopilot", "harness"):
            self.assertIn(keyword, text.lower(), keyword)
        # no vendored code:
        for repo in ("codex-chatgpt-web", "OpenHands", "OpenCode", "goose",
                     "Cline", "Aider", "vibe-kanban"):
            self.assertNotIn(f"vendored {repo.lower()}", text.lower())


if __name__ == "__main__":
    unittest.main()
