"""Focused regression tests for vendor snapshot provenance integrity.

Guards the skill-consumption seam (Issue #340 P1 / Issue #62): a vendored
skill snapshot that declares per-file provenance must keep its registry
metadata in sync with the committed snapshot bytes, otherwise
``load_vendor_skill`` fails closed with ``VENDOR_SNAPSHOT_HASH_MISMATCH`` and a
stockroom skill can never be consumed.

Regression anchor: ``visual.gpt_image_2_style_library`` shipped a snapshot that
is byte-identical to upstream ``freestylefly/awesome-gpt-image-2`` at pinned
commit ``9a7b2e9c39f816d6c699c2a133e11b6d8bfdc464`` (verified per-file against
``canonical_sha256``), while its registry ``snapshot_sha256`` and
``source_files[].sha256`` were stale, so loading was impossible.
"""

from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
REGISTRY_PATH = SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities import load_registry  # noqa: E402
from p2p_capabilities.vendor_skill import (  # noqa: E402
    VendorSkillError,
    is_vendor_skill,
    load_vendor_skill,
    snapshot_tree_sha256,
)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _vendored_provenance_skills() -> list:
    """Vendor skills that declare a complete per-file sparse snapshot."""
    registry = load_registry(REGISTRY_PATH)
    selected = []
    for manifest in registry["parsed"]:
        if not is_vendor_skill(manifest):
            continue
        provenance = manifest.upstream_provenance
        vendored = [
            item
            for item in provenance.get("source_files", [])
            if item.get("status") == "VENDORED" and item.get("snapshot_path")
        ]
        if vendored:
            selected.append((manifest, provenance, vendored))
    return selected


class VendorSnapshotIntegrityTests(unittest.TestCase):
    def test_every_vendored_snapshot_matches_its_registry_hashes(self) -> None:
        skills = _vendored_provenance_skills()
        self.assertTrue(
            skills,
            "expected at least one vendor skill with per-file provenance",
        )
        for manifest, provenance, vendored in skills:
            with self.subTest(capability_id=manifest.capability_id):
                root = REPO_ROOT / str(provenance.get("vendor_path", ""))
                self.assertTrue(root.is_dir())
                self.assertEqual(
                    snapshot_tree_sha256(root),
                    provenance.get("snapshot_sha256"),
                    "registry snapshot_sha256 is stale",
                )
                for item in vendored:
                    relative = str(item["snapshot_path"])
                    actual = _sha256_file(root / relative)
                    self.assertEqual(
                        item.get("sha256"),
                        actual,
                        f"registry source_files sha256 is stale: {relative}",
                    )
                    self.assertEqual(
                        item.get("canonical_sha256"),
                        actual,
                        f"registry canonical_sha256 drifted: {relative}",
                    )

    def test_vendored_skills_load_through_the_existing_loader(self) -> None:
        for manifest, _provenance, _vendored in _vendored_provenance_skills():
            with self.subTest(capability_id=manifest.capability_id):
                loaded = load_vendor_skill(
                    manifest.capability_id,
                    registry_path=REGISTRY_PATH,
                    repository_root=REPO_ROOT,
                )
                self.assertTrue(loaded["skill"]["content"])

    def test_visual_style_library_entrypoint_matches_declared_hash(self) -> None:
        registry = load_registry(REGISTRY_PATH)
        manifest = next(
            item
            for item in registry["parsed"]
            if item.capability_id == "visual.gpt_image_2_style_library"
        )
        provenance = manifest.upstream_provenance
        entrypoint = (
            REPO_ROOT
            / str(provenance.get("vendor_path", ""))
            / str(provenance.get("integration", {}).get("entrypoint", "SKILL.md"))
        )
        self.assertTrue(entrypoint.is_file())
        self.assertEqual(
            _sha256_file(entrypoint),
            provenance.get("integration", {}).get("entrypoint_sha256"),
        )

    def test_tampered_snapshot_fails_closed(self) -> None:
        import tempfile

        registry = load_registry(REGISTRY_PATH)
        manifest = next(
            item
            for item in registry["parsed"]
            if item.capability_id == "visual.gpt_image_2_style_library"
        )
        provenance = manifest.upstream_provenance
        relative_vendor = str(provenance.get("vendor_path", ""))
        source_root = REPO_ROOT / relative_vendor
        with tempfile.TemporaryDirectory(prefix="p2p-vendor-tamper-") as raw:
            fake_repo = Path(raw)
            tampered_root = fake_repo / relative_vendor
            tampered_root.mkdir(parents=True)
            for path in sorted(source_root.rglob("*")):
                if path.is_file():
                    target = tampered_root / path.relative_to(source_root)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(path.read_bytes())
            entrypoint = tampered_root / "SKILL.md"
            entrypoint.write_bytes(entrypoint.read_bytes() + b"\n# tampered\n")
            with self.assertRaises(VendorSkillError) as raised:
                load_vendor_skill(
                    manifest.capability_id,
                    registry_path=REGISTRY_PATH,
                    repository_root=fake_repo,
                )
            self.assertEqual(
                str(raised.exception), "VENDOR_SNAPSHOT_HASH_MISMATCH"
            )


if __name__ == "__main__":
    unittest.main()
