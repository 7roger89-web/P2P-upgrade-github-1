from __future__ import annotations

import copy
import importlib
import json
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONTROL_PATH = REPO_ROOT / "governance" / "development-control.json"
ANCHOR_COMMIT = "2a71410afd1b29651016ef57a5d2da38938c3f68"
ANCHOR_TREE = "3e6ab12ff78a72c4a3ea2a418e11167a8649aaad"
ANCHOR_PARENT = "af02170ac7ba180900ca78beb26a2972d80c73b6"
GOVREC01_COMMIT = "6c860eea9332b3641d2b7806daf37043b4bf123d"
sys.path.insert(0, str(REPO_ROOT / "scripts"))
control = importlib.import_module("p2p_development_control")


def load_record() -> dict[str, object]:
    return json.loads(CONTROL_PATH.read_text(encoding="utf-8"))


class P2PGovrec02SourceAnchorTests(unittest.TestCase):
    def test_active_record_names_one_explicit_git_source_anchor(self) -> None:
        record = load_record()
        authority = record["authority"]  # type: ignore[index]
        self.assertIn("promoted_source_anchor", authority)
        self.assertNotIn("current_promoted_source", authority)
        anchor = authority["promoted_source_anchor"]
        self.assertEqual(anchor["semantic_type"], "PROMOTED_IMPLEMENTATION_SOURCE_ANCHOR")
        self.assertEqual(anchor["source_kind"], "GIT_COMMIT_TREE")
        self.assertEqual(anchor["observed_ref"], "origin/main")
        self.assertEqual(anchor["anchor_commit"], ANCHOR_COMMIT)
        self.assertEqual(anchor["anchor_tree"], ANCHOR_TREE)
        self.assertEqual(anchor["lineage_policy"], "CURRENT_OR_CANDIDATE_HEAD_MUST_EQUAL_OR_DESCEND_FROM_ANCHOR")

    def test_current_checkout_observes_head_descending_and_origin_main_equal(self) -> None:
        result = control.validate_control(load_record(), repo_root=REPO_ROOT)
        source_anchor = result["source_anchor"]
        self.assertEqual(source_anchor["anchor_commit"], ANCHOR_COMMIT)
        self.assertEqual(source_anchor["anchor_tree"], ANCHOR_TREE)
        self.assertEqual(source_anchor["head_relationship"], "HEAD_DESCENDS_FROM_ANCHOR")
        self.assertEqual(source_anchor["origin_main_relationship"], "ORIGIN_MAIN_EQUALS_ANCHOR")

    def test_before_state_equal_anchor_is_valid(self) -> None:
        result = control.validate_control(
            load_record(),
            repo_root=REPO_ROOT,
            observed_head=ANCHOR_COMMIT,
            observed_origin_main=ANCHOR_COMMIT,
        )
        source_anchor = result["source_anchor"]
        self.assertEqual(source_anchor["observed_head"], ANCHOR_COMMIT)
        self.assertEqual(source_anchor["observed_origin_main"], ANCHOR_COMMIT)
        self.assertEqual(source_anchor["head_relationship"], "HEAD_EQUALS_ANCHOR")
        self.assertEqual(source_anchor["origin_main_relationship"], "ORIGIN_MAIN_EQUALS_ANCHOR")

    def test_hypothetical_post_promotion_descendant_is_valid(self) -> None:
        result = control.validate_control(
            load_record(),
            repo_root=REPO_ROOT,
            observed_head=GOVREC01_COMMIT,
            observed_origin_main=GOVREC01_COMMIT,
        )
        source_anchor = result["source_anchor"]
        self.assertEqual(source_anchor["observed_head"], GOVREC01_COMMIT)
        self.assertEqual(source_anchor["observed_origin_main"], GOVREC01_COMMIT)
        self.assertEqual(source_anchor["head_relationship"], "HEAD_DESCENDS_FROM_ANCHOR")
        self.assertEqual(source_anchor["origin_main_relationship"], "ORIGIN_MAIN_DESCENDS_FROM_ANCHOR")

    def test_diverged_head_is_rejected_fail_closed(self) -> None:
        with self.assertRaises(control.ControlError) as raised:
            control.validate_control(
                load_record(),
                repo_root=REPO_ROOT,
                observed_head=ANCHOR_PARENT,
                observed_origin_main=ANCHOR_COMMIT,
            )
        self.assertEqual(raised.exception.code, "AUTHORITY_LINEAGE_DIVERGED")

    def test_missing_anchor_commit_is_rejected(self) -> None:
        record = load_record()
        record["authority"]["promoted_source_anchor"]["anchor_commit"] = "0" * 40  # type: ignore[index]
        with self.assertRaises(control.ControlError) as raised:
            control.validate_control(record, repo_root=REPO_ROOT)
        self.assertEqual(raised.exception.code, "AUTHORITY_ANCHOR_COMMIT_MISSING")

    def test_anchor_tree_mismatch_is_rejected(self) -> None:
        record = load_record()
        record["authority"]["promoted_source_anchor"]["anchor_tree"] = "0" * 40  # type: ignore[index]
        with self.assertRaises(control.ControlError) as raised:
            control.validate_control(record, repo_root=REPO_ROOT)
        self.assertEqual(raised.exception.code, "AUTHORITY_ANCHOR_TREE_MISMATCH")

    def test_legacy_and_duplicate_authority_shapes_are_rejected(self) -> None:
        legacy = load_record()
        authority = legacy["authority"]  # type: ignore[index]
        authority["current_promoted_source"] = authority.pop("promoted_source_anchor")
        with self.assertRaises(control.ControlError) as legacy_error:
            control.validate_control(legacy)
        self.assertEqual(legacy_error.exception.code, "AUTHORITY_LEGACY_FIELD")

        duplicate = load_record()
        duplicate["authority"]["current_promoted_source"] = copy.deepcopy(duplicate["authority"]["promoted_source_anchor"])  # type: ignore[index]
        with self.assertRaises(control.ControlError) as duplicate_error:
            control.validate_control(duplicate)
        self.assertEqual(duplicate_error.exception.code, "AUTHORITY_DUPLICATE")

    def test_historical_artifact_and_self_reference_are_rejected(self) -> None:
        artifact = load_record()
        artifact["authority"]["promoted_source_anchor"]["semantic_type"] = "OFFICIAL_ARTIFACT_AUTHORITY"  # type: ignore[index]
        with self.assertRaises(control.ControlError) as artifact_error:
            control.validate_control(artifact)
        self.assertEqual(artifact_error.exception.code, "AUTHORITY_HISTORICAL_ARTIFACT")

        self_reference = load_record()
        self_reference["authority"]["promoted_source_anchor"]["lineage_policy"] = "CURRENT_HEAD_MUST_EQUAL_OWN_COMMIT"  # type: ignore[index]
        with self.assertRaises(control.ControlError) as self_reference_error:
            control.validate_control(self_reference)
        self.assertEqual(self_reference_error.exception.code, "AUTHORITY_SELF_REFERENCE")

    def test_status_projection_exposes_dynamic_anchor_relationships(self) -> None:
        projection = control.status_projection(load_record(), repo_root=REPO_ROOT)
        source_anchor = projection["validation"]["source_anchor"]
        self.assertEqual(source_anchor["head_relationship"], "HEAD_DESCENDS_FROM_ANCHOR")
        self.assertEqual(source_anchor["origin_main_relationship"], "ORIGIN_MAIN_EQUALS_ANCHOR")

    def test_static_package_validation_does_not_require_a_git_remote(self) -> None:
        result = control.validate_control(load_record())
        source_anchor = result["source_anchor"]
        self.assertEqual(source_anchor["head_relationship"], "NOT_OBSERVED")
        self.assertEqual(source_anchor["origin_main_relationship"], "NOT_OBSERVED")


if __name__ == "__main__":
    unittest.main()
