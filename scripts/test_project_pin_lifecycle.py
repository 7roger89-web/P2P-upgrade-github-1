"""Focused lifecycle tests for the packaged project-pin contract."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SYSTEM_SOURCE = ROOT / ".p2p" / "system"
sys.path.insert(0, str(SYSTEM_SOURCE))

from p2p_capabilities import project_pin
from p2p_capabilities.project_context import ProjectContextError, ProjectContextBootstrap, enforce_map_before_work


VERSION = "8.4.7-C-codex.73"
ARTIFACT_SHA = "a" * 64
OFFICIAL_SHA = "3a9ee51321e1f5e40e35ce73eb90727cddb571a672aa095d16d76af2feb03dd8"
SOURCE_COMMIT = "1" * 40
SOURCE_TREE = "2" * 40


def _json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def _metadata(system: Path) -> None:
    (system / "VERSION").write_text(VERSION + "\n", encoding="utf-8")
    _json(system / "CANDIDATE-DISTRIBUTION-MANIFEST.json", {
        "schema_version": "p2p-codex-candidate-distribution/1",
        "candidate_version": VERSION,
        "official_baseline_version": "8.4.7-C-codex.19",
        "official_baseline_sha256": OFFICIAL_SHA,
        "candidate_vs_official": "UNPROMOTED_SUCCESSOR_CANDIDATE",
    })
    _json(system / "SOURCE-BINDING.json", {
        "schema_version": "p2p-codex-source-binding/1",
        "candidate_version": VERSION,
        "source_commit": SOURCE_COMMIT,
        "source_tree": SOURCE_TREE,
        "source_commit_object": "VERIFIED",
        "source_tree_object": "VERIFIED",
        "source_tree_bound_to_commit": "VERIFIED",
    })
    _json(system / "ARTIFACT-IDENTITY.json", {"candidate_version": VERSION})


def _fixture() -> Path:
    base = ROOT / ".tmp"
    base.mkdir(exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix="project-pin-lifecycle-", dir=str(base)))
    (root / "README.md").write_text("project-owned\n", encoding="utf-8")
    system = root / ".p2p" / "system"
    system.mkdir(parents=True)
    _metadata(system)
    _json(system / "release.json", {"schema_version": "p2p-install-release/1", "package_version": VERSION, "candidate_version": VERSION, "artifact_sha256": ARTIFACT_SHA})
    pin = project_pin.build_pin(
        project_root=root,
        metadata_root=system,
        artifact_sha256=ARTIFACT_SHA,
        installation_mode="PACKAGED_PROJECT",
        rollback_source=".p2p/install-backups/test",
        managed_files=["VERSION", "p2p_capabilities/project_pin.py"],
    )
    project_pin.write_pin(root, pin)
    return root


def run() -> None:
    root = _fixture()
    try:
        result = project_pin.validate_pin(root, metadata_root=root / ".p2p" / "system", expected_artifact_sha256=ARTIFACT_SHA, expected_version=VERSION)
        assert result["status"] == "PASS"

        pin_path = root / ".p2p" / "project-pin.json"
        original = json.loads(pin_path.read_text(encoding="utf-8"))
        for field, value in (("p2p_candidate_artifact_sha256", "b" * 64), ("p2p_candidate_version", "8.4.7-C-codex.72"), ("project_fingerprint", "c" * 64)):
            changed = dict(original)
            changed[field] = value
            pin_path.write_text(json.dumps(changed), encoding="utf-8")
            try:
                project_pin.validate_pin(root, metadata_root=root / ".p2p" / "system")
            except project_pin.ProjectPinError:
                pass
            else:
                raise AssertionError(f"invalid pin accepted: {field}")
        pin_path.write_text(json.dumps(original), encoding="utf-8")

        bootstrap = ProjectContextBootstrap(root)
        bootstrap.save_project_map(bootstrap.get_project_map())
        assert enforce_map_before_work(root, mutation_intent=True) is True
        try:
            enforce_map_before_work(root, mutation_intent=True, permission_granted=False)
        except ProjectContextError:
            pass
        else:
            raise AssertionError("permission denial was accepted")
        map_path = root / ".p2p" / "context" / "project_map.json"
        map_path.unlink()
        try:
            enforce_map_before_work(root, mutation_intent=True)
        except ProjectContextError:
            pass
        else:
            raise AssertionError("missing map was accepted")
        print(json.dumps({"status": "PASS", "project_pin": "VERIFIED", "negative_cases": 5, "map_gate": "FAIL_CLOSED"}))
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    run()
