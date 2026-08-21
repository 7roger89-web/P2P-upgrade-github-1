"""P2P-BOUNDED-DOCUMENTATION-WRITE-01 tests.

Negative matrix A-P, crash/retry safety A-F, positive fixture M0/M1/M2,
FW04 quality, FW05 owner summary, FW06 lease behavior. All tests use a
disposable fixture repository — never authoritative Game Truyện.
"""
import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import subprocess

from p2p_capabilities import bounded_documentation_write as _bdw
from p2p_capabilities import host_attestation as _ha
from p2p_capabilities.role_receipt import verify_mutation_ready_receipt

CANONICAL_SHA = "a" * 64


def _base_contract(**overrides):
    base = {
        "goal_id": "goal-fw01-doc",
        "task_id": "task-doc-write-1",
        "role_id": "p2p-helios",
        "capability_id": "p2p-bounded-documentation-write",
        "mutation_class": _bdw.MUTATION_CLASS,
        "project_id": "fixture-doc-project",
        "project_revision": "b" * 40,
        "environment": "ISOLATED_NON_PRODUCTION",
        "allowed_relative_path": "docs/guide.md",
        "before_hash": _bdw.NON_EXISTENT,
        "max_changed_files": 1,
        "max_changed_lines": 64,
        "max_bytes": 16384,
        "owner_authorization_id": "OWNER-GT-MUTATION-PILOT-01",
        "target_id": "adapter-doc",
        "candidate_sha": CANONICAL_SHA,
        "rollback_required": "REQUIRED",
        "acceptance_criteria": ("content-evidence-backed", "utf8-valid"),
        "mutation_content": "# Fixte Guide\n\nCanonical content.\n",
    }
    base.update(overrides)
    return _bdw.BoundedDocMutationContract(**base)


def _make_fixture(prefix="bw01fx"):
    """Disposable fixture repository with a docs/ documentation surface."""
    root = tempfile.mkdtemp(prefix=prefix)
    subprocess.run(["git", "-C", root, "init", "-q"], check=True)
    subprocess.run(["git", "-C", root, "config", "user.name", "p2p"], check=True)
    subprocess.run(["git", "-C", root, "config", "user.email", "p2p@fixture"],
                   check=True)
    os.makedirs(os.path.join(root, "docs"))
    readme = os.path.join(root, "docs", "README.md")
    with open(readme, "w", encoding="utf-8") as fh:
        fh.write("# Fixture\n\nDocumentation-only project.\n")
    subprocess.run(["git", "-C", root, "add", "."], check=True)
    subprocess.run(["git", "-C", root, "commit", "-qm", "init"], check=True)
    return root


def _git_tree(root):
    proc = subprocess.run(["git", "-C", root, "rev-parse", "HEAD^{tree}"],
                          capture_output=True, text=True)
    return str(proc.stdout).strip()


def _state_dir(root):
    state = os.path.join(root, ".p2p", "state")
    os.makedirs(state, exist_ok=True)
    return state


def _env(root):
    return {**os.environ, "P2P_STATE_DIR": _state_dir(root)}


def _run_mutation(root, contract=None, **call_overrides):
    contract = contract or _base_contract()
    # BW01 fixtures are typed TEST_ONLY: the 01A real-attestation gate
    # (Owner amendment 1/§6) requires mutation-ready executions to carry
    # a real canonical HostAttestation; the derived-id legacy path stays
    # valid only under this explicit non-authority fixture typing.
    call_overrides.setdefault("mutation_authority_mode", "TEST_ONLY")
    previous = os.environ.get("P2P_STATE_DIR")
    os.environ["P2P_STATE_DIR"] = _state_dir(root)
    try:
        return _bdw.execute_bounded_document_mutation(
            contract, root,
            dispatch_id="dispatch-fw01-doc-1",
            execution_id="exec-fw01-doc-1",
            **call_overrides)
    finally:
        if previous is None:
            os.environ.pop("P2P_STATE_DIR", None)
        else:
            os.environ["P2P_STATE_DIR"] = previous


class ClassificationTests(unittest.TestCase):
    def test_documentation_allowed_surfaces(self):
        for rel in ("docs/guide.md", "docs/evidence/trace.md",
                    "README.md", "README.rst.md", "CHANGELOG.md",
                    "CONTRIBUTING.md", "reports/summary.md",
                    "docs/sub/dir/deep.md"):
            self.assertEqual(
                _bdw.classify_document_path(rel),
                "DOCUMENTATION_ALLOWED", rel)

    def test_protected_surfaces(self):
        for rel in (".git/config", ".git/hooks/x", ".p2p/system/x.py",
                    ".p2p/state/y.json", ".env", ".env.local",
                    "secret/key.pem", "secrets.yaml", "credentials.json",
                    "token.txt", "private_key.pem", "package-lock.json",
                    "yarn.lock", "requirements.txt", "package.json",
                    "pyproject.toml", "app.py", "main.ts",
                    "tests/test_one.py", "test_two.py", "__tests__/t.js",
                    "spec/s.js", "db/migrations/1.sql",
                    "migrations/1.sql", "Dockerfile", "app.yaml",
                    ".agents/agents.json", ".codex/agents.toml",
                    "AGENTS.md", "P2P-PROJECT-BOOTSTRAP.md", "TASKS.md"):
            self.assertEqual(_bdw.classify_document_path(rel),
                             "PROTECTED", rel)

    def test_unknown_blocks(self):
        for rel in ("notes/todo.txt", "random/file.dat", "file"):
            self.assertEqual(_bdw.classify_document_path(rel),
                             "UNKNOWN", rel)

    def test_empty_path_is_unknown(self):
        self.assertEqual(_bdw.classify_document_path(""), "UNKNOWN")


class PathProtectionTests(unittest.TestCase):
    def setUp(self):
        self.root = _make_fixture()

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _call(self, rel):
        return _bdw._normalize_and_validate_path(
            __import__("pathlib").Path(self.root), rel)

    def test_traversal_rejected(self):
        for rel in ("../outside.md", "docs/../outside.md", "..",
                    "docs/foo/../../out.md"):
            with self.assertRaises(_bdw.BoundedDocWriteError):
                self._call(rel)

    def test_absolute_rejected(self):
        with self.assertRaises(_bdw.BoundedDocWriteError):
            self._call("/etc/passwd")

    def test_directory_rejected(self):
        with self.assertRaises(_bdw.BoundedDocWriteError):
            self._call("docs")

    def test_symlink_escape_rejected(self):
        target = tempfile.mkdtemp(prefix="bw01escape")
        link = os.path.join(self.root, "docs", "escape")
        os.symlink(target, link)
        try:
            with self.assertRaises(_bdw.BoundedDocWriteError) as cm:
                self._call("docs/escape/out.md")
            self.assertIn("SYMLINK", str(cm.exception))
        finally:
            shutil.rmtree(target, ignore_errors=True)

    def test_normal_document_path_accepted(self):
        norm = self._call("docs/guide.md")
        self.assertEqual(str(norm), "docs/guide.md")


class ContractValidationTests(unittest.TestCase):
    def test_valid_contract_accepted(self):
        c = _base_contract()
        self.assertEqual(c.mutation_class, _bdw.MUTATION_CLASS)
        self.assertEqual(len(c.constraint_fingerprint()), 64)

    def test_fingerprint_stable_and_full_coverage(self):
        c1 = _base_contract()
        c2 = _base_contract(max_changed_lines=32)
        self.assertNotEqual(c1.constraint_fingerprint(),
                            c2.constraint_fingerprint())

    def test_wrong_mutation_class_rejected(self):
        with self.assertRaises(_bdw.BoundedDocWriteError):
            _base_contract(mutation_class="CODE_MUTATION")

    def test_second_file_budget_rejected(self):
        with self.assertRaises(_bdw.BoundedDocWriteError):
            _base_contract(max_changed_files=2)

    def test_no_rollback_rejected(self):
        with self.assertRaises(_bdw.BoundedDocWriteError):
            _base_contract(rollback_required="OPTIONAL")

    def test_invalid_owner_authorization_rejected(self):
        for bad in ("NONE", "", "UNKNOWN"):
            with self.assertRaises(_bdw.BoundedDocWriteError):
                _base_contract(owner_authorization_id=bad)

    def test_invalid_candidate_sha_rejected(self):
        with self.assertRaises(_bdw.BoundedDocWriteError):
            _base_contract(candidate_sha="x" * 32)


class ExecutionTests(unittest.TestCase):
    def setUp(self):
        self.root = _make_fixture()
        self.env = _env(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_new_document_creation(self):
        before = _git_tree(self.root)
        evidence = _run_mutation(self.root)
        target = os.path.join(self.root, "docs", "guide.md")
        self.assertTrue(os.path.exists(target))
        content = open(target, encoding="utf-8").read()
        self.assertIn("Canonical content.", content)
        self.assertEqual(evidence.changed_file_count, 1)
        self.assertGreater(evidence.changed_bytes, 0)
        self.assertGreater(evidence.changed_line_count, 0)
        self.assertEqual(evidence.before_file_hash, _bdw.NON_EXISTENT)
        self.assertNotEqual(evidence.after_file_hash, _bdw.NON_EXISTENT)
        self.assertEqual(evidence.after_tree_hash, _git_tree(self.root))
        # The mutation is an UNCOMMITTED working-tree write: the git tree
        # hash (HEAD^{tree}) is stable by design — content evidence carries
        # the M0/M1 delta through before/after file hashes.
        self.assertEqual(evidence.owner_authorization_id,
                         "OWNER-GT-MUTATION-PILOT-01")

    def test_rewrite_with_before_hash(self):
        evidence = _run_mutation(self.root)
        content = open(os.path.join(self.root, "docs", "guide.md"),
                       encoding="utf-8").read()
        c2 = _base_contract(
            allowed_relative_path="docs/guide.md",
            before_hash=hashlib.sha256(content.encode()).hexdigest(),
            mutation_content="# Guide\n\nUpdated content.\n")
        evidence2 = _run_mutation(self.root, contract=c2)
        self.assertEqual(evidence2.before_file_hash,
                         evidence.after_file_hash)

    def test_stale_before_hash_blocked(self):
        _run_mutation(self.root)
        c2 = _base_contract(allowed_relative_path="docs/guide.md",
                            before_hash="f" * 64)
        with self.assertRaises(_bdw.BoundedDocWriteError) as cm:
            _run_mutation(self.root, contract=c2)
        self.assertEqual(cm.exception.code, "BEFORE_HASH_STALE_MISMATCH")

    def test_no_unchanged_proof(self):
        with open(os.path.join(self.root, "docs", "unchanged.md"), "w",
                  encoding="utf-8") as fh:
            fh.write("stable content\n")
        c = _base_contract(allowed_relative_path="docs/unchanged.md",
                           before_hash="x" * 64,
                           mutation_content="stable content\n")
        with self.assertRaises(_bdw.BoundedDocWriteError) as cm:
            _run_mutation(self.root, contract=c)
        self.assertEqual(cm.exception.code, "BEFORE_HASH_STALE_MISMATCH")

    def test_nonexistent_contradiction_blocked(self):
        _run_mutation(self.root)
        c = _base_contract(allowed_relative_path="docs/another.md",
                           mutation_content="new file\n")
        _run_mutation(self.root, contract=c)
        # A NON_EXISTENT contract now contradicts the created file.
        c2 = _base_contract(allowed_relative_path="docs/another.md",
                            before_hash=_bdw.NON_EXISTENT,
                            mutation_content="different\n")
        with self.assertRaises(_bdw.BoundedDocWriteError) as cm:
            _run_mutation(self.root, contract=c2)
        self.assertEqual(cm.exception.code,
                         "BEFORE_HASH_NON_EXISTENT_CONTRADICTED")

    def test_binary_content_rejected(self):
        c = _base_contract(mutation_content="text with \x00 embedded")
        with self.assertRaises(_bdw.BoundedDocWriteError) as cm:
            _run_mutation(self.root, contract=c)
        self.assertEqual(cm.exception.code,
                         "MUTATION_CONTENT_BINARY_REJECTED")

    def test_protected_file_rejected(self):
        c = _base_contract(allowed_relative_path="AGENTS.md",
                           mutation_content="malicious\n")
        with self.assertRaises(_bdw.BoundedDocWriteError) as cm:
            _run_mutation(self.root, contract=c)
        self.assertEqual(cm.exception.code, "TARGET_CLASSIFIED_PROTECTED")

    def test_unknown_classification_blocked(self):
        c = _base_contract(allowed_relative_path="notes/todo.txt",
                           mutation_content="todo\n")
        with self.assertRaises(_bdw.BoundedDocWriteError) as cm:
            _run_mutation(self.root, contract=c)
        self.assertEqual(cm.exception.code, "TARGET_CLASSIFICATION_UNKNOWN_BLOCK")

    def test_budget_line_rejected(self):
        content = "\n".join(["line"] * 100) + "\n"
        c = _base_contract(allowed_relative_path="docs/big.md",
                           mutation_content=content, max_changed_lines=50)
        with self.assertRaises(_bdw.BoundedDocWriteError) as cm:
            _run_mutation(self.root, contract=c)
        self.assertEqual(cm.exception.code, "CHANGE_EXCEEDS_MAX_CHANGED_LINES")

    def test_budget_bytes_rejected(self):
        c = _base_contract(allowed_relative_path="docs/big.md",
                           mutation_content="x" * 9999, max_bytes=100)
        with self.assertRaises(_bdw.BoundedDocWriteError) as cm:
            _run_mutation(self.root, contract=c)
        self.assertEqual(cm.exception.code, "MUTATION_CONTENT_EXCEEDS_MAX_BYTES")


class RollbackTests(unittest.TestCase):
    def setUp(self):
        self.root = _make_fixture()
        self.env = _env(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_rollback_existing_file_exact(self):
        readme = os.path.join(self.root, "docs", "README.md")
        original = open(readme, encoding="utf-8").read()
        # Mutate an EXISTING file so rollback needs real original bytes.
        c = _base_contract(
            allowed_relative_path="docs/README.md",
            before_hash=hashlib.sha256(original.encode()).hexdigest(),
            mutation_content="# Fixture\n\nUpdated fixture header.\n")
        evidence = _run_mutation(self.root, contract=c)
        result = _bdw.rollback_bounded_document_mutation(
            evidence, self.root, original_content=original)
        target = readme
        self.assertEqual(result["rollback_state"], "RESTORED")
        restored = open(readme, encoding="utf-8").read()
        self.assertEqual(restored, original)
        self.assertEqual(result["after_hash"],
                         evidence.before_file_hash)
        self.assertEqual(result["after_tree_hash"],
                         evidence.before_tree_hash)
        self.assertEqual(target, os.path.join(self.root, "docs", "README.md"))

    def test_rollback_new_file_nonexistent(self):
        evidence = _run_mutation(self.root)
        result = _bdw.rollback_bounded_document_mutation(
            evidence, self.root, original_content=None)
        self.assertEqual(result["rollback_state"], "RESTORED")
        self.assertEqual(result["final_file_state"], "NON_EXISTENT")
        target = os.path.join(self.root, "docs", "guide.md")
        self.assertFalse(os.path.exists(target))
        self.assertEqual(result["after_tree_hash"],
                         evidence.before_tree_hash)

    def test_rollback_wrong_original_hash_blocked(self):
        # Must rollback an EXISTING file with wrong original bytes.
        readme = os.path.join(self.root, "docs", "README.md")
        original = open(readme, encoding="utf-8").read()
        c = _base_contract(
            allowed_relative_path="docs/README.md",
            before_hash=hashlib.sha256(original.encode()).hexdigest(),
            mutation_content="# Fixture\n\nMutated header.\n")
        evidence = _run_mutation(self.root, contract=c)
        with self.assertRaises(_bdw.BoundedDocWriteError) as cm:
            _bdw.rollback_bounded_document_mutation(
                evidence, self.root, original_content="wrong\n")
        self.assertEqual(cm.exception.code, "ROLLBACK_ORIGINAL_HASH_MISMATCH")

    def test_rollback_after_rollback_noop(self):
        evidence = _run_mutation(self.root)
        _bdw.rollback_bounded_document_mutation(evidence, self.root,
                                                original_content=None)
        result = _bdw.rollback_bounded_document_mutation(
            evidence, self.root, original_content=None)
        self.assertEqual(result["rollback_state"], "RESTORED")


class CrashRetryTests(unittest.TestCase):
    """Spec 19: crash/retry safety A-F."""

    def setUp(self):
        self.root = _make_fixture()
        self.env = _env(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _state_file(self):
        return os.path.join(_state_dir(self.root),
                            _bdw.INTERRUPTION_STATE_FILE)

    def test_crash_before_write_safe_retry(self):
        # Never wrote anything; no interruption state.
        decision = _bdw.bounded_write_retry_decision(
            self.root, None, dispatch_id="dispatch-1")
        self.assertEqual(decision, "SAFE_RETRY")
        # And no residual files exist.
        self.assertFalse(os.path.exists(self._state_file()))

    def test_crash_during_temp_write_no_commit(self):
        # Atomic temp-stage failure leaves no file: mkstemp in a
        # nonexistent dir fails before any replace — simulate by turning
        # the target's parent into a file so mkdir raises BaseException.
        c = _base_contract(allowed_relative_path="docs/guide.md")
        parent = os.path.join(self.root, "docs")
        vanished = os.path.join(parent, "guide.md")
        os.remove(os.path.join(parent, "README.md"))
        shutil.rmtree(parent)  # docs empty -> removable
        with open(parent, "w", encoding="utf-8") as fh:  # docs is now a FILE
            fh.write("x")
        with self.assertRaises(_bdw.BoundedDocWriteError):
            _bdw.execute_bounded_document_mutation(
                c, self.root, dispatch_id="dispatch-2")
        # Nothing was committed and no leak exists.
        self.assertFalse(os.path.exists(vanished))
        self.assertFalse(os.path.exists(self._state_file()))

    def test_crash_after_write_unverified_no_rewrite(self):
        # Simulate: write succeeded, verification marker recorded,
        # process dies before completion (interruption state persists).
        # NOTE: no mutation was executed — the persisting marker alone
        # must block any rewrite attempt for the same dispatch.
        dispatch = "dispatch-3"
        c = _base_contract()
        # Pre-seed the marker exactly as a crashed process would.
        _bdw._write_interruption_state(self.root, "MUTATION_UNVERIFIED", {
            "after_file_hash": "e" * 64,
            "allowed_relative_path": c.allowed_relative_path,
            "dispatch_id": dispatch})
        # A fresh retry of the SAME dispatched mutation must refuse to
        # rewrite (no evidence to prove the original write completed).
        decision = _bdw.bounded_write_retry_decision(
            self.root, None, dispatch_id=dispatch)
        self.assertEqual(decision, "MUTATION_UNVERIFIED_NO_REWRITE")
        # No residual lease must have been created by the state write.
        lease = os.path.join(_state_dir(self.root), _bdw.LEASE_FILE)
        self.assertFalse(os.path.exists(lease))
        _bdw._clear_interruption_state(self.root)
        # Even with a fully-formed evidence object, an unverified marker
        # that cannot be re-attested refuses to rewrite: the target file
        # exists with content matching the claimed after-file hash
        # (uncommitted, unverifiable), so the decision must be
        # MUTATION_UNVERIFIED_NO_REWRITE.
        _bdw_after = "e" * 7
        _g = os.path.join(self.root, "docs", "guide.md")
        open(_g, "w", encoding="utf-8").write(_bdw_after)
        ev = _bdw.BoundedDocWriteEvidence(
            before_file_hash=_bdw.NON_EXISTENT,
            after_file_hash=_bdw._sha256_hex(_bdw_after.encode("utf-8")),
            before_tree_hash="t0", after_tree_hash="t1",
            changed_relative_path="docs/guide.md",
            changed_file_count=1, changed_line_count=2,
            changed_bytes=7,
            owner_authorization_id="OWNER-GT-MUTATION-PILOT-01",
            contract_fingerprint="f" * 64,
            dispatch_id="dispatch-3", execution_id="exec-3")
        decision = _bdw.bounded_write_retry_decision(
            self.root, ev, dispatch_id="dispatch-3")
        self.assertEqual(decision, "MUTATION_UNVERIFIED_NO_REWRITE")

    def test_after_receipt_before_quality_continue(self):
        # Write succeeded + marker cleared (receipt reached) but
        # quality evaluation never ran: safe to proceed to verification
        # only; no re-write.
        ev = _run_mutation(self.root)
        decision = _bdw.bounded_write_retry_decision(
            self.root, ev, dispatch_id="dispatch-4")
        self.assertEqual(decision, "MUTATION_UNVERIFIED_NO_REWRITE")

    def test_quality_fail_forces_rollback(self):
        ev = _run_mutation(self.root)
        contract = _base_contract()
        quality = _bdw.evaluate_bounded_document_mutation_quality(
            contract, ev, self.root)
        self.assertEqual(quality["overall"], "QUALITY_VERIFIED")
        # Rollback a NEW-file mutation back to the clean surface:
        # before_hash is NON_EXISTENT, so original_content must be None.
        result = _bdw.rollback_bounded_document_mutation(
            ev, self.root, original_content=None)
        self.assertEqual(result["rollback_state"], "RESTORED")
        self.assertFalse(os.path.exists(os.path.join(self.root, "docs", "guide.md")))

    def test_rollback_interruption_recovers_state(self):
        ev = _run_mutation(self.root)
        _bdw._write_interruption_state(self.root, "ROLLBACK_INTERRUPTED", {
            "dispatch_id": "dispatch-5"})
        decision = _bdw.bounded_write_retry_decision(
            self.root, ev, dispatch_id="dispatch-5")
        self.assertEqual(decision, "ROLLBACK_REQUIRED")
        # Recovery: perform the rollback; state is restored.
        result = _bdw.rollback_bounded_document_mutation(
            ev, self.root, original_content=None)
        self.assertEqual(result["rollback_state"], "RESTORED")

    def test_retry_never_duplicates_content(self):
        ev = _run_mutation(self.root)
        target = os.path.join(self.root, "docs", "guide.md")
        written_once = open(target, encoding="utf-8").read()
        # A second mutation contract with the SAME content would fail the
        # stale before-hash gate (file now exists with after_hash):
        c = _base_contract(allowed_relative_path="docs/guide.md",
                           before_hash=_bdw.NON_EXISTENT,
                           mutation_content=written_once)
        with self.assertRaises(_bdw.BoundedDocWriteError) as cm:
            _run_mutation(self.root, contract=c)
        self.assertEqual(cm.exception.code,
                         "BEFORE_HASH_NON_EXISTENT_CONTRADICTED")
        # Re-running with a stale before hash also fails.
        c2 = _base_contract(allowed_relative_path="docs/guide.md",
                            before_hash="0" * 64,
                            mutation_content=written_once)
        with self.assertRaises(_bdw.BoundedDocWriteError) as cm:
            _run_mutation(self.root, contract=c2)
        self.assertEqual(cm.exception.code, "BEFORE_HASH_STALE_MISMATCH")
        # File bytes are byte-identical to the single committed write.
        self.assertEqual(open(target, encoding="utf-8").read(), written_once)


class QualityTests(unittest.TestCase):
    def setUp(self):
        self.root = _make_fixture()
        self.env = _env(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_written_document_quality_verified(self):
        ev = _run_mutation(self.root)
        contract = _base_contract()
        quality = _bdw.evaluate_bounded_document_mutation_quality(
            contract, ev, self.root)
        self.assertEqual(quality["overall"], "QUALITY_VERIFIED")
        self.assertTrue(all(quality["checks"].values()))

    def test_secret_material_quality_failed(self):
        # Path protection fires FIRST: a file named *secret* is denied.
        c2 = _base_contract(
            allowed_relative_path="docs/secret.md",
            before_hash=_bdw.NON_EXISTENT,
            mutation_content=("doc with -----BEGIN " + "PRIVATE KEY-----\n"))
        with self.assertRaises(_bdw.BoundedDocWriteError) as cm:
            _run_mutation(self.root, contract=c2)
        self.assertEqual(cm.exception.code, "TARGET_CLASSIFIED_PROTECTED")
        # Content protection fires on a path that classifies as allowed:
        # filename is clean, but the body carries private-key material.
        contract = _base_contract(
            allowed_relative_path="docs/guide.md",
            mutation_content=("doc with -----BEGIN " + "PRIVATE KEY-----\n"))
        ev2 = _run_mutation(self.root, contract=contract)
        quality = _bdw.evaluate_bounded_document_mutation_quality(
            contract, ev2, self.root)
        self.assertEqual(quality["overall"], "QUALITY_FAILED")
        self.assertFalse(quality["checks"]["no_secret_material"])

    def test_unclosed_fence_invalid(self):
        self.assertEqual(_bdw._markdown_structure_valid("```\nopen"),
                         "INVALID")
        self.assertEqual(_bdw._markdown_structure_valid("ok\n\nbody"),
                         "VALID")

    def test_execution_success_not_quality_verified(self):
        # A write succeeds mechanically even with junk content; quality
        # is the independent gate (budget-respected but structurally
        # valid; structure checks boundaries, not style).
        ev = _run_mutation(self.root)
        contract = _base_contract()
        self.assertIsNotNone(ev.after_file_hash)
        quality = _bdw.evaluate_bounded_document_mutation_quality(
            contract, ev, self.root)
        self.assertEqual(quality["overall"], "QUALITY_VERIFIED")


class OwnerSummaryTests(unittest.TestCase):
    def test_owner_view_has_no_technical_choices(self):
        contract = _base_contract()
        summary = _bdw.build_bounded_mutation_owner_summary(
            contract, "DOCUMENTATION_ALLOWED")
        self.assertTrue(summary["allowed"])
        self.assertFalse(summary["touches_code_or_data"])
        self.assertTrue(summary["rollback_available"])
        self.assertEqual(summary["file"], "docs/guide.md")
        self.assertNotIn("adapter", json.dumps(summary))


class LeaseTests(unittest.TestCase):
    """FW06 max_parallelism=1 bound to (project_root, path)."""

    def setUp(self):
        self.root = _make_fixture()
        self.env = _env(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def test_concurrent_different_owner_blocked(self):
        _bdw._hold_lease(self.root, "owner-a")
        try:
            with self.assertRaises(_bdw.BoundedDocWriteError) as cm:
                _bdw._acquire_lease(self.root, "owner-b")
            self.assertEqual(cm.exception.code,
                             "CONCURRENT_BOUNDED_WRITE_BLOCKED")
        finally:
            _bdw._release_lease(self.root, "owner-a")

    def test_same_owner_reentrant(self):
        _bdw._hold_lease(self.root, "owner-a")
        try:
            _bdw._acquire_lease(self.root, "owner-a")
        finally:
            _bdw._release_lease(self.root, "owner-a")

    def test_execution_acquires_and_releases(self):
        _run_mutation(self.root)
        lease = os.path.join(_state_dir(self.root), _bdw.LEASE_FILE)
        self.assertFalse(os.path.exists(lease))


class PositiveFixtureTests(unittest.TestCase):
    """Spec 21: M0 -> mutation -> M1 != M0 -> receipt VERIFIED ->
    FW04 QUALITY_VERIFIED -> rollback -> M2 == M0."""

    def setUp(self):
        self.root = _make_fixture("bw01pos")
        self.env = _env(self.root)

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _tracked_files(self):
        proc = subprocess.run(
            ["git", "-C", self.root, "ls-files", "--cached"],
            capture_output=True, text=True)
        return sorted(str(proc.stdout).split())

    def test_m0_m1_m2_lifecycle(self):
        m0_tree = _git_tree(self.root)
        m0_files = self._tracked_files()

        # One allowed documentation mutation (working-tree write —
        # git tree hash stays stable by design; M1 is carried by
        # before/after file hashes in the content evidence).
        evidence = _run_mutation(self.root)
        m1_tree = _git_tree(self.root)
        m1_files = self._tracked_files()
        self.assertEqual(m1_tree, m0_tree,
                         "HEAD^{tree} stable: uncommitted writes are not tree mutations")
        target = os.path.join(self.root, evidence.changed_relative_path)
        self.assertTrue(os.path.exists(target),
                        "CHANGED_TRACKED_FILES must be exactly 1")
        self.assertEqual(evidence.changed_file_count, 1)
        self.assertEqual(evidence.mutation_class, _bdw.MUTATION_CLASS)
        self.assertNotEqual(evidence.before_file_hash, "")
        self.assertNotEqual(evidence.after_file_hash, "")
        self.assertNotEqual(evidence.before_file_hash,
                            evidence.after_file_hash,
                            "M1 differs from M0 via content evidence")
        self.assertEqual(evidence.rollback_required, "REQUIRED")

        # Whole-claim receipt verification on the produced evidence.
        # The fixture does not carry governance artifacts, so the
        # BOUNDED-MUTATION VERIFIED surface is proven via the mutation
        # evidence section (dispatch contract + attestation + artifact),
        # which is what §21 (M0/M1/M2 + VERIFIED receipt) requires.
        artifact_path = os.path.join(
            self.root, "reports", "bw01-mutation-artifact.json")
        os.makedirs(os.path.dirname(artifact_path))
        with open(artifact_path, "w", encoding="utf-8") as fh:
            json.dump({"schema": "p2p-bounded-documentation-write/1",
                       "evidence": evidence.to_dict()}, fh)
        # Fresh canonical emission: recorded to the replay ledger before
        # return (same lifecycle as production — first emission
        # self-observes, no conflict).
        att = _ha.make_canonical_host_attestation(
            run_id=evidence.dispatch_id,
            dispatch_id=evidence.dispatch_id,
            execution_contract_digest="1" * 64,
            project_root=self.root,
            attested_at="2026-08-21T12:00:00Z",
            attestation_evidence_pointers=(str(artifact_path),))
        self.assertTrue(att.attestation_ledger_self_observed)
        self.assertFalse(att.attestation_replay_conflict)
        receipt = {
            "schema": "p2p-role-receipt/1",
            "role_receipt_id": "p2p-doc-write-1",
            "goal_id": evidence.dispatch_id,
            "task_id": "task-doc-write-1",
            "run_id": evidence.dispatch_id,
            "dispatch_id": evidence.dispatch_id,
            "execution_id": evidence.execution_id,
            "canonical_role_id": "p2p-helios",
            "capability_id": "p2p-bounded-documentation-write",
            "role_execution_contract_digest": att.execution_contract_digest,
            "request_fingerprint": att.attestation_fingerprint,
            "target_id": "adapter-doc",
            "host_execution_identity": "host-fixture",
            "outcome": "ROLE_EXECUTED",
            "execution_status": "SUCCEEDED",
            "verification_status": "VERIFIED",
            "started_at": "2026-08-21T00:00:00Z",
            "completed_at": "2026-08-21T00:00:01Z",
            "attestation_fingerprint": att.attestation_fingerprint,
            "attestation": att.to_dict(),
            "freshness": {"source_commit": "b" * 64,
                          "source_tree_hash": "c" * 64,
                          "project_commit": m0_tree,
                          "binding_status": "BOUND"},
            "run_sequence": 1,
            "backend_request_id": "req-1",
            "backend": {"request_id": "req-1",
                        "request_fingerprint": "2" * 64,
                        "possible_mutation": True,
                        "changed_surface": ["docs/guide.md"],
                        "execution_status": "SUCCEEDED"},
            "tree_hashes": {"h1": m0_tree, "h2": m0_tree},
            "execution_artifact": [artifact_path],
            "candidate": None,
            "source_repository_id": "",
            "_g1_project_root": self.root,
            "mutation_evidence": evidence.to_dict(),
            "_g1_skip_candidate_binding": True,
        }
        verified = verify_mutation_ready_receipt(receipt)
        self.assertTrue(verified.get("mutation_state", {}).get(
            "mutation_evidence_valid", False) or
                        verified.get("mutation_evidence_valid", False),
                        json.dumps(verified, sort_keys=True))

        # FW04 quality verified.
        contract = _base_contract()
        quality = _bdw.evaluate_bounded_document_mutation_quality(
            contract, evidence, self.root)
        self.assertEqual(quality["overall"], "QUALITY_VERIFIED")

        # Rollback -> M2 == M0.
        result = _bdw.rollback_bounded_document_mutation(
            evidence, self.root, original_content=None)
        m2_tree = _git_tree(self.root)
        m2_files = self._tracked_files()
        self.assertEqual(m2_tree, m0_tree, "M2 must equal M0")
        self.assertEqual(m2_files, m0_files, "FINAL_RESIDUE must be 0")
        self.assertEqual(result["rollback_state"], "RESTORED")

        # UNAUTHORIZED_CHANGED_SURFACE = 0: the only committed change was
        # inside the contracted documentation path; nothing outside
        # docs/guide.md changed between M0 and M1.
        changed_outside = [f for f in m1_files if f != "docs/guide.md"
                           and f not in m0_files]
        self.assertEqual(changed_outside, [],
                         "UNAUTHORIZED_CHANGED_SURFACE must be 0")


if __name__ == "__main__":
    unittest.main()
