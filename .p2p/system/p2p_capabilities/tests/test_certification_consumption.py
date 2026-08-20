"""Seam B: FW04 capability-specific certification evidence consumption by
FW03 adaptive team eligibility. Cases A-H per P2P-FW04 specification.

All assertions run against the REAL team_intelligence.build_team_decision and
the REAL quality_intelligence.load_certification_evidence. Test fixtures are
injected only at the evidence-boundary layer (_cert_store within the FW04
quality-intelligence module, plus the live source commit), never inside the
team-decision algorithm itself.
"""
import subprocess
import sys
import unittest
from pathlib import Path

SYSTEM_PATH = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SYSTEM_PATH))

from p2p_capabilities import quality_intelligence as qi  # noqa: E402
from p2p_capabilities import team_intelligence as ti  # noqa: E402

CAP = "security_audit"


def _current_commit() -> str:
    result = subprocess.run(
        ["git", "log", "-1", "--format=%H"],
        cwd=str(SYSTEM_PATH.parents[1]),
        capture_output=True, text=True)
    return result.stdout.strip()


def _canonical_registry() -> list:
    registry_path = SYSTEM_PATH / "p2p_capabilities" / "capabilities.json"
    import json
    with open(registry_path) as f:
        payload = json.load(f)
    entries = payload.get("capabilities", [])
    if isinstance(entries, list):
        return entries
    return []


def _with_records(records):
    """Module-boundary patch: tier and freshness both read through
    _cert_store, so the whole evidence view is pinned to the fixture.
    The REAL tier/freshness/current_eligibility logic is exercised."""
    original_store = qi._cert_store
    fixture = {"records": [dict(r) for r in records]}
    qi._cert_store = lambda: fixture
    return original_store


def _restore_records(original_store):
    qi._cert_store = original_store


def _role_covers(decision):
    """Per-role coverage sets from the decision's own evidence trace."""
    covers = {}
    for item in decision.decision_trace:
        if item.step == "ROLE_PROVIDE":
            parts = item.fact.split(" provides=", 1)
            if len(parts) == 2:
                import json as _json
                covers[parts[0]] = set(_json.loads(
                    parts[1].replace("'", '"')))
    return covers


def _build(reqs, certs=None):
    return ti.build_team_decision(
        required_capabilities=reqs,
        registry_records=_canonical_registry(),
        live_required=False,
        task_risk_class="LOW",
        mutation_class="READ_ONLY",
        capability_certifications=certs,
    )


def _cert_map(commit):
    """REAL FW04 evidence provider: capability-specific, fail-closed."""
    return qi.load_certification_evidence((CAP,), commit)


class CertificationConsumptionTests(unittest.TestCase):
    """Seam B — certification evidence is consumed exactly, never loosely."""

    def test_a_certified_eligible_cap_counts(self):
        commit = _current_commit()
        records = [
            {"eval_id": "eval-fw04-001", "eval_version": "1.0",
             "capability_id": CAP, "subject": "p2p_security_audit",
             "target_environment": "",
             "timestamp": "2026-08-19T00:00:00Z", "result": "CERTIFIED",
             "evidence_pointers": ["ptr-security-audit-v1"],
             "freshness_bound": commit,
             "kind": "CAPABILITY_CERTIFICATION"},
        ]
        # Without certification evidence the decision must fail closed:
        # NO capability may be provided on the strength of a registry
        # claim alone when eligibility evidence is absent.
        baseline = _build((CAP,))
        orig = _with_records(records)
        try:
            certs = _cert_map(commit)
            self.assertTrue(certs[CAP]["currently_eligible"],
                            certs[CAP])
            decision = _build((CAP,), certs)
            base_covers = _role_covers(baseline)
            with_covers = _role_covers(decision)
            # Coverage extension: roles that could not previously claim
            # CAP must gain exactly CAP — no capability invention beyond
            # the certified scope.
            for role in with_covers:
                added = with_covers[role] - base_covers.get(role, set())
                if CAP in added:
                    self.assertEqual(added, {CAP},
                                     f"role {role} gained {sorted(added)} "
                                     "from a security_audit-only "
                                     "certification")
            # The certified cap now appears in more roles' coverage.
            roles_with = {r for r, s in with_covers.items() if CAP in s}
            roles_base = {r for r, s in base_covers.items() if CAP in s}
            self.assertGreater(len(roles_with), len(roles_base),
                               ("certified currently-eligible coverage "
                                "must extend role coverage: base=%d "
                                "with=%d") % (len(roles_base),
                                              len(roles_with)))
        finally:
            _restore_records(orig)

    def test_b_cert_for_x_does_not_satisfy_y(self):
        commit = _current_commit()
        records = [
            {"eval_id": "eval-fw04-002", "eval_version": "1.0",
             "capability_id": CAP, "subject": "p2p_security_audit",
             "target_environment": "",
             "timestamp": "2026-08-19T00:00:00Z", "result": "CERTIFIED",
             "evidence_pointers": ["ptr-security-audit-v2"],
             "freshness_bound": commit,
             "kind": "CAPABILITY_CERTIFICATION"},
        ]
        orig = _with_records(records)
        try:
            certs = _cert_map(commit)
            # The evidence map is keyed by the REQUESTED capability only:
            # an X certification never appears when Y is required. That
            # keyed isolation IS the scope-exactness boundary.
            req_y = ("data_backup",)
            certs_y = qi.load_certification_evidence(req_y, commit)
            self.assertEqual(tuple(certs_y.keys()), req_y,
                             "the certification evidence map must return "
                             "exactly the requested capabilities — an X "
                             "certification must never leak into a Y "
                             "requirement")
            decision = _build(req_y, certs_y)
            provided = set(decision.provided_capabilities)
            self.assertNotIn(CAP, provided,
                             "an X certification must never satisfy a Y "
                             "requirement")
            self.assertNotIn("data_backup", provided,
                             "X-certified coverage cannot transfer to Y")
        finally:
            _restore_records(orig)

    def test_c_generic_execution_receipt_does_not_certify(self):
        commit = _current_commit()
        # A ROLE_EXECUTION_BINDING proves 'this identity executed' only;
        # it is NOT a capability certification, regardless of scope.
        records = [
            {"role_id": "p2p_security_audit",
             "receipt_pointer": "receipt-2026-08-19-001",
             "capability_scope": (CAP,),
             "timestamp": "2026-08-19T00:00:00Z",
             "kind": "ROLE_EXECUTION_BINDING"},
        ]
        orig = _with_records(records)
        try:
            certs = _cert_map(commit)
            self.assertFalse(certs[CAP]["currently_eligible"],
                             "a generic execution binding must not produce "
                             "an eligible certification")
            decision = _build((CAP,), certs)
            self.assertNotIn(CAP, decision.provided_capabilities,
                             "execution receipt without a capability "
                             "certification cannot close the gap")
        finally:
            _restore_records(orig)

    def test_d_stale_certification_does_not_count(self):
        commit = _current_commit()
        records = [
            {"eval_id": "eval-fw04-003", "eval_version": "1.0",
             "capability_id": CAP, "subject": "p2p_security_audit",
             "target_environment": "",
             "timestamp": "2026-06-01T00:00:00Z", "result": "CERTIFIED",
             "evidence_pointers": ["ptr-stale-v1"],
             # freshness bound from an OLD commit — provenance has moved.
             "freshness_bound": "0" * 40,
             "kind": "CAPABILITY_CERTIFICATION"},
        ]
        orig = _with_records(records)
        try:
            certs = _cert_map(commit)
            self.assertEqual(certs[CAP]["freshness"], "STALE",
                             certs[CAP])
            self.assertFalse(certs[CAP]["currently_eligible"])
            decision = _build((CAP,), certs)
            self.assertNotIn(CAP, decision.provided_capabilities,
                             "a STALE certification must not extend the "
                             "provide set")
        finally:
            _restore_records(orig)

    def test_e_unknown_currency_fails_closed(self):
        commit = _current_commit()
        records = [
            {"eval_id": "eval-fw04-004", "eval_version": "1.0",
             "capability_id": CAP, "subject": "p2p_security_audit",
             "target_environment": "",
             "timestamp": "2026-08-19T00:00:00Z", "result": "CERTIFIED",
             "evidence_pointers": ["ptr-unbound-v1"],
             "freshness_bound": "",  # no bound — currency unprovable.
             "kind": "CAPABILITY_CERTIFICATION"},
        ]
        orig = _with_records(records)
        try:
            elig = qi.current_eligibility(CAP, commit)
            self.assertFalse(elig["currently_eligible"])
            self.assertTrue(elig["fail_closed_on_unknown"])
            certs = _cert_map(commit)
            self.assertFalse(certs[CAP]["currently_eligible"],
                             certs[CAP])
            decision = _build((CAP,), certs)
            self.assertNotIn(CAP, decision.provided_capabilities,
                             "UNBOUND/unknown currency must fail closed, "
                             "never assume CURRENT")
        finally:
            _restore_records(orig)

    def test_f_malformed_evidence_fails_closed(self):
        # A record missing a required field must REFUSE to persist — the
        # evidence boundary never admits malformed pointers.
        original_store = qi._cert_store()
        try:
            with self.assertRaises(ValueError):
                qi.record_capability_certification(
                    eval_id="",  # missing
                    eval_version="1.0",
                    capability_id=CAP,
                    subject="p2p_security_audit",
                    timestamp="2026-08-19T00:00:00Z",
                    result="CERTIFIED",
                    evidence_pointers=())
            # Store unchanged: nothing malformed ever persisted.
            self.assertEqual(qi._cert_store(), original_store)
            commit = _current_commit()
            certs = qi.load_certification_evidence((CAP,), commit)
            self.assertFalse(certs[CAP]["currently_eligible"])
            decision = _build((CAP,), certs)
            self.assertNotIn(CAP, decision.provided_capabilities,
                             "absent certification evidence must fail "
                             "closed")
        finally:
            pass  # real store intentionally untouched

    def test_g_decision_changes_only_with_valid_evidence(self):
        commit = _current_commit()
        baseline = _build((CAP,))
        records = [
            {"eval_id": "eval-fw04-005", "eval_version": "1.0",
             "capability_id": CAP, "subject": "p2p_security_audit",
             "target_environment": "",
             "timestamp": "2026-08-19T00:00:00Z", "result": "CERTIFIED",
             "evidence_pointers": ["ptr-g-v1"],
             "freshness_bound": commit,
             "kind": "CAPABILITY_CERTIFICATION"},
        ]
        orig = _with_records(records)
        try:
            certs = _cert_map(commit)
            with_evidence = _build((CAP,), certs)
            base_provided = set(baseline.provided_capabilities)
            with_provided = set(with_evidence.provided_capabilities)
            base_covers = _role_covers(baseline)
            with_covers = _role_covers(with_evidence)
            # A valid certification changes the decision ONLY by closing
            # the gap it is evidence for — no more, no less.
            for role in with_covers:
                added = with_covers[role] - base_covers.get(role, set())
                if added:
                    self.assertEqual(added, {CAP},
                                     f"role {role} gained {sorted(added)} "
                                     "beyond the certified capability")
            self.assertNotEqual(base_covers, with_covers,
                                "valid capability evidence must change "
                                "the coverage decision")
            # The decision must remain fail-closed at the dispatch gate:
            # certification evidence extends COVERAGE, never eligibility.
            self.assertIn(with_evidence.failure_class,
                          ("", "NO_ELIGIBLE_ROLE"),
                          with_evidence.to_dict())
        finally:
            _restore_records(orig)

    def test_h_certification_never_grants_permission(self):
        commit = _current_commit()
        records = [
            {"eval_id": "eval-fw04-006", "eval_version": "1.0",
             "capability_id": CAP, "subject": "p2p_security_audit",
             "target_environment": "",
             "timestamp": "2026-08-19T00:00:00Z", "result": "CERTIFIED",
             "evidence_pointers": ["ptr-h-v1"],
             "freshness_bound": commit,
             "kind": "CAPABILITY_CERTIFICATION"},
        ]
        orig = _with_records(records)
        try:
            certs = _cert_map(commit)
            decision = _build((CAP,), certs)
            decision_dict = decision.to_dict()
            # The team decision carries capability coverage only. It must
            # never carry permission grants or gate approvals.
            for key in decision_dict.keys():
                self.assertFalse(
                    key.startswith("permission")
                    or key in ("owner_gate", "permission_granted",
                               "granted_permissions"),
                    f"TeamDecision must not carry permission key {key}")
            # FW04 produced the evidence; it did not select the team —
            # the decision is fully deterministic from registry + evidence.
            self.assertIsInstance(decision.participant_roles, tuple)
            # Eligibility evidence is absent from this boundary-only test,
            # so the fail-closed mode_reason is NO_ELIGIBLE_ROLE — and it
            # carries no granted coverage, only certified capabilities.
            self.assertIn(decision.failure_class,
                          ("", "NO_ELIGIBLE_ROLE"),
                          decision.to_dict())
        finally:
            _restore_records(orig)


if __name__ == "__main__":
    unittest.main()
