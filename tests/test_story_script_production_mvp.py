from __future__ import annotations

import json
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
if str(SYSTEM_ROOT) not in sys.path:
    sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities.story_script_core import (  # noqa: E402
    CAPABILITY_ID,
    StoryValidationError,
    load_story_case,
    validate_story_core,
)
from p2p_capabilities.story_video_adapter import (  # noqa: E402
    build_production_pack,
    export_production_pack,
    load_video_adapter,
)

CASE_DIR = REPO_ROOT / "kich-ban-truyen" / "production-mvp" / "BA_ANH_EM_IDENT_001"


class StoryScriptProductionMvpTests(unittest.TestCase):
    def setUp(self) -> None:
        self.bundle = load_story_case(CASE_DIR)
        self.report = validate_story_core(self.bundle)

    def test_acceptance_case_passes_and_preserves_owner_causal_signature(self) -> None:
        self.assertEqual(CAPABILITY_ID, "story.script.production_mvp")
        self.assertEqual(self.report["status"], "PASS", self.report["errors"])
        self.assertEqual(
            self.report["validated_spine_nodes"],
            [
                "N1_RUA_BITES",
                "N2_SUA_CHARGES",
                "N3_SUA_RELEASES",
                "N4_SAM_PROTECTS",
                "N5_BROTHERS_RESPOND",
                "N6_RESOLUTION",
                "N7_EARNED_LOGO",
            ],
        )
        self.assertEqual(self.bundle["state"]["initial"]["location"], "shallow_beach_water")
        self.assertEqual(self.bundle["locks"]["canon"]["rua.inciting_action"], "quick_mischievous_bite")
        self.assertEqual(self.bundle["locks"]["canon"]["sua.energy"], "blue-violet fantasy energy")
        self.assertEqual(
            self.bundle["locks"]["canon"]["sam.protection_mode"],
            "intentional_voluntary_shell_shield",
        )
        self.assertEqual(self.report["final_state"]["location"], "shallow_beach_water")
        self.assertTrue(self.report["final_state"]["conflict_resolved"])
        self.assertTrue(self.report["final_state"]["logo_earned"])
        self.assertEqual(self.report["final_state"]["time_s"], 15.0)

    def test_identity_lock_rejects_sua_gender_drift(self) -> None:
        bad = deepcopy(self.bundle)
        bad["beats"]["beats"][1]["identity_assertions"]["sua"]["gender"] = "female"
        report = validate_story_core(bad)
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any("IDENTITY_LOCK_CONTRADICTION:B2_SUA_CHARGES:sua:gender" in e for e in report["errors"]))

    def test_precondition_and_time_transition_drift_fail_closed(self) -> None:
        bad = deepcopy(self.bundle)
        bad["beats"]["beats"][3]["preconditions"]["sua_energy_released"] = False
        del bad["beats"]["beats"][4]["transition"]["time_s"]
        report = validate_story_core(bad)
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any(e.startswith("PRECONDITION_MISMATCH:B4_SAM_BLOCKS:sua_energy_released") for e in report["errors"]))
        self.assertTrue(any(e.startswith("DECLARED_TRANSITION_REQUIRED:B5_BROTHERS_RESPOND:time_s") for e in report["errors"]))

    def test_location_and_on_screen_transition_drift_fail_closed(self) -> None:
        bad = deepcopy(self.bundle)
        beat = bad["beats"]["beats"][4]
        beat["consequences"]["location"] = "dry_sand"
        beat["consequences"]["on_screen"] = ["dong_vu", "bao_dang", "minh_phuc"]
        report = validate_story_core(bad)
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any(e.startswith("DECLARED_TRANSITION_REQUIRED:B5_BROTHERS_RESPOND:location") for e in report["errors"]))
        self.assertTrue(any(e.startswith("DECLARED_TRANSITION_REQUIRED:B5_BROTHERS_RESPOND:on_screen") for e in report["errors"]))

    def test_canon_and_spine_reference_drift_fail_closed(self) -> None:
        bad = deepcopy(self.bundle)
        bad["beats"]["beats"][0]["canon_assertions"]["sua.gender"] = "female"
        bad["beats"]["beats"][6]["spine_ref"] = "N404"
        report = validate_story_core(bad)
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any(e.startswith("CANON_CONTRADICTION:B1_RUA_BITES:sua.gender") for e in report["errors"]))
        self.assertTrue(any(e.startswith("BEAT_SPINE_REF_INVALID:B7_EARNED_LOGO:N404") for e in report["errors"]))

    def test_video_adapter_warns_high_risk_without_rewriting_story(self) -> None:
        adapter = load_video_adapter(CASE_DIR / "video_adapter.yaml")
        original_beats = json.dumps(self.bundle["beats"], ensure_ascii=False, sort_keys=True)
        pack = build_production_pack(self.bundle, self.report, adapter)
        self.assertEqual(pack["owner_gate"], "PENDING")
        self.assertFalse(pack["generation_authorized"])
        self.assertEqual(pack["adapter_boundary"]["narrative_rewrite"], "FORBIDDEN")
        self.assertEqual(pack["adapter_boundary"]["feasibility_high"], "WARN_ONLY")
        self.assertEqual(len(pack["warnings"]), 2)
        self.assertEqual(json.dumps(self.bundle["beats"], ensure_ascii=False, sort_keys=True), original_beats)

    def test_video_adapter_rejects_narrative_mutation_field(self) -> None:
        adapter = load_video_adapter(CASE_DIR / "video_adapter.yaml")
        adapter["shots"][0]["consequences"] = {"logo_earned": True}
        with self.assertRaises(StoryValidationError):
            build_production_pack(self.bundle, self.report, adapter)

    def test_production_pack_exports_yaml_without_authorizing_generation(self) -> None:
        adapter = load_video_adapter(CASE_DIR / "video_adapter.yaml")
        pack = build_production_pack(self.bundle, self.report, adapter)
        with tempfile.TemporaryDirectory() as tmp:
            path = export_production_pack(pack, Path(tmp) / "production_pack.yaml")
            loaded = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(loaded["schema"], "story-production-pack/1")
            self.assertEqual(loaded["story_id"], "BA_ANH_EM_IDENT_001")
            self.assertEqual(loaded["owner_gate"], "PENDING")
            self.assertFalse(loaded["generation_authorized"])
            self.assertEqual(loaded["adapter_boundary"]["final_video_generation"], "OUT_OF_SCOPE")


if __name__ == "__main__":
    unittest.main()
