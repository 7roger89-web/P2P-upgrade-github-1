"""P2P-VIDEO-CAPABILITY-INTEGRATION-01 focused validation (GitHub issue #71).

ONE bounded capability (`video.prompt.director_spec`) and ONE representative
synthetic validation:

    USER IDEA -> MASTER DIRECTOR SPEC -> SHORT PROVIDER PROMPT

Scope discipline: this module is the single focused validation for this goal. It is
not a broad video test suite, not a consistency engine, not a schema validator
framework, and it renders no video, calls no API, and installs nothing.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = REPO_ROOT / ".p2p" / "system"
REGISTRY_PATH = SYSTEM_ROOT / "p2p_capabilities" / "capabilities.json"
LEDGER_PATH = REPO_ROOT / "governance" / "research-adoption-ledger.json"
CATALOG = REPO_ROOT / "docs" / "p2p-development" / "capability-catalog" / "video-director-spec"
PROTOCOL = CATALOG / "director-spec-protocol.md"
DERIVED = CATALOG / "research-derived-reference.md"
CATALOG_README = CATALOG / "README.md"
VRP_SCHEMA = (
    REPO_ROOT
    / "docs"
    / "p2p-development"
    / "capability-catalog"
    / "game-asset-forge"
    / "visual-reference-pack.schema.json"
)
VALIDATION_DIR = (
    REPO_ROOT
    / "docs"
    / "plans"
    / "2026-09-03-p2p-video-capability-integration-01"
    / "validation"
)
MASTER_SPEC_PATH = VALIDATION_DIR / "ly-truong-sinh-sword-descent.master-spec.json"
PROJECTION_PATH = VALIDATION_DIR / "ly-truong-sinh-sword-descent.provider-projection.json"

CAPABILITY_ID = "video.prompt.director_spec"
BASE_MAIN_SHA = "c1ddc4fdbc3bf6639a5f3e3f171a7fb5c1df6352"
BASELINE_CAPABILITY_COUNT = 72
BASELINE_LEDGER_RECORD_COUNT = 69
NEW_RECORD_IDS = [f"RA-EXT-{n:03d}" for n in range(70, 78)]
REPOS_REVIEWED = 7

TWELVE_FIELDS = (
    "identity_constraints",
    "scene",
    "actor_performance",
    "camera",
    "lighting",
    "physics",
    "timeline",
    "dialogue",
    "audio",
    "continuity",
    "negative_constraints",
    "model_specific_projection",
)
CONSISTENCY_TAXONOMY = (
    "IDENTITY_CONSISTENCY",
    "HAIR_CONSISTENCY",
    "BODY_PROPORTION_CONSISTENCY",
    "COSTUME_CONSISTENCY",
    "PROP_WEAPON_CONSISTENCY",
    "ENVIRONMENT_CONSISTENCY",
    "STYLE_CONSISTENCY",
    "IMAGE_CONSISTENCY",
    "VIDEO_TEMPORAL_CONSISTENCY",
    "SHOT_TO_SHOT_CONTINUITY",
)
VRP_VIEW_IDS = (
    "full_body_front",
    "full_body_three_quarter",
    "full_body_side",
    "full_body_back",
    "face_front",
    "face_three_quarter",
)
CONDITIONING_CONCEPTS = (
    "REFERENCE_IMAGE",
    "FIRST_FRAME",
    "LAST_FRAME",
    "FIRST_LAST_FRAME",
    "MULTI_IMAGE_REFERENCE",
    "REFERENCE_TO_VIDEO",
)
POST_PRODUCTION_PIPELINE = (
    "SCRIPT",
    "MATERIAL",
    "NARRATION",
    "SUBTITLE",
    "MUSIC",
    "RENDER",
    "FINAL_ARTIFACT",
)
PROFILE_FIELDS = (
    "input_prompt_budget",
    "reference_image_support",
    "reference_image_count",
    "first_frame_support",
    "last_frame_support",
    "first_last_frame_support",
    "multi_image_support",
    "reference_to_video_support",
    "duration_controls",
    "aspect_ratio_controls",
    "marker_syntax",
    "accepts_labelled_structured_prompt",
)

# Canonical hashes of the origin/main content this goal must not disturb.
PRESERVED_IDENTITY_HASHES = {
    "visual.gpt_image_2_style_library": "81f9394346af72f2b6ce7c910dca12966100ae3499e61d31757063e19962beb4",
    "media.whiteboard_animation": "d451e77538625a681b210e65199bdaf9b0b20ac5425336f0015e505ce5575104",
    "creative.copywriting": "2b1d77e311c36a4df9409597fda636265498e8d65f4b282ab67258d1fe875d5f",
}
PRESERVED_LEDGER_RECORDS_HASH = "9318599107e5786b8f134e305d4ddcbe550f98d690d60d872b61fe84855c62b9"
PRESERVED_LEDGER_TOPLEVEL_HASH = "23d85912b13543ba6ea01fc4c8a83213ab8a61e4cbad99e02738927f123ed3ec"
PRESERVED_VRP_SCHEMA_SHA256 = "71ea8fd728705eb57e545188cf272e042893a0d6ebfe72c815ecb3090d78ab83"

JACOBYE_COMMIT = "f74d2fcfa803cec4007fdfbeae9cde8831693ee7"
JACOBYE_TREE = "883377396a8c945d8d1f9ff4a37cde73a9bca6e6"
JACOBYE_REPO = "https://github.com/jacobye2017-afk/jacob-ye-seedance-prompt"
EXPECTED_PINS = {
    "https://github.com/jacobye2017-afk/jacob-ye-seedance-prompt": JACOBYE_COMMIT,
    "https://github.com/opensource-works/awesome-seedance-prompts": "5ba05bc9849b4502e282fce329ff7ba741bcca18",
    "https://github.com/Wan-Video/Wan2.2": "42bf4cfaa384bc21833865abc2f9e6c0e67233dc",
    "https://github.com/ali-vilab/VACE": "48eb44f1c4be87cc65a98bff985a26976841e9f3",
    "https://github.com/KlingAIResearch/ReCamMaster": "fcf98bc86e876bb534518cd99e8a65b282f0f16e",
    "https://github.com/divolleggett/awesome-character-consistency": "81ec30770ae70ad2602997f258292a4e6bb3e9d6",
    "https://github.com/harry0703/MoneyPrinterTurbo": "cbbb366393105d5cefc254dc9ed492d43da0711b",
}

# The synthetic validation request from issue #71.
USER_IDEA = (
    "T\u1ea1o c\u1ea3nh L\u00fd Tr\u01b0\u1eddng Sinh c\u01b0\u1ee1i ki\u1ebfm lao xu\u1ed1ng "
    "Thi\u00ean Ki\u1ebfm Th\u00e0nh, gi\u1eef nguy\u00ean khu\u00f4n m\u1eb7t, trang ph\u1ee5c "
    "v\u00e0 thanh ki\u1ebfm; camera \u0111u\u1ed5i t\u1eeb ph\u00eda sau r\u1ed3i v\u00f2ng "
    "sang ch\u00ednh di\u1ec7n."
)
NAMESPACED_REQUEST = f"Vi\u1ebft video prompt ({CAPABILITY_ID}): {USER_IDEA}"

# Existing routing requests already asserted elsewhere in the suite. The new
# capability's triggers must not change any of these selections.
PRESERVED_ROUTE_REQUESTS = (
    ("Write a precise Arena Agent prompt to improve the Three.js camera.", ["game.mengto.camera_controls"]),
    ("Implement a local combat cooldown bug fix.", ["game.mengto.action_combat"]),
    ("Create a Three.js xianxia sword from an approved reference.", ["game.mengto.hybrid_assets", "game.majid.threejs_qa_release"]),
    ("Improve browser performance in the current Three.js scene.", ["game.mengto.performance"]),
    ("Learn my writing voice from these samples.", ["creative.social.voice_profile"]),
    ("Write a LinkedIn post about AI agents in my voice.", ["creative.social.post"]),
    ("Give me 6 hooks about AI agents.", ["creative.social.hook"]),
    ("Give me 20 content ideas.", ["creative.social.content_matrix"]),
    ("Format this as AIDA.", ["creative.social.post_format"]),
    ("Write an advertising slogan and campaign headline for a new brand.", ["creative.copywriting"]),
    ("Create/render a whiteboard animation.", ["media.whiteboard_animation", "ui.motion"]),
    ("Write marketing copy for an image-generation product.", ["creative.copywriting"]),
    ("Thi\u1ebft k\u1ebf app qu\u1ea3n l\u00fd d\u1ec5 nh\u00ecn.", ["p2p-uiux"]),
)

sys.path.insert(0, str(SYSTEM_ROOT))

from p2p_capabilities import load_registry  # noqa: E402
from p2p_capabilities.routing import classify_capabilities  # noqa: E402
from p2p_capabilities.vendor_skill import discover_vendor_skills, is_vendor_skill  # noqa: E402


def _canon(value) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class P2PVideoDirectorSpecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.raw_registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        cls.registry = load_registry(REGISTRY_PATH)
        cls.entries = {item.capability_id: item for item in cls.registry["parsed"]}
        cls.raw_entries = {item["CAPABILITY_ID"]: item for item in cls.raw_registry["capabilities"]}
        cls.capability = cls.entries[CAPABILITY_ID]
        cls.provenance = cls.capability.upstream_provenance
        cls.master_spec = json.loads(MASTER_SPEC_PATH.read_text(encoding="utf-8"))
        cls.projection = json.loads(PROJECTION_PATH.read_text(encoding="utf-8"))
        cls.ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
        cls.records = {item["research_id"]: item for item in cls.ledger["records"]}
        cls.protocol_text = PROTOCOL.read_text(encoding="utf-8")
        cls.derived_text = DERIVED.read_text(encoding="utf-8")

    def route(self, request: str):
        return classify_capabilities(request, self.registry["parsed"])

    # ---------------------------------------------------------------- 01 registry

    def test_01_registry_gains_exactly_one_bounded_capability(self) -> None:
        self.assertTrue(self.registry["valid"], self.registry["errors"])
        self.assertEqual(self.raw_registry["schema"], "p2p-capability-registry/1")
        self.assertEqual(
            self.registry["capability_count"],
            BASELINE_CAPABILITY_COUNT + 1,
            "exactly one new capability may be added",
        )
        self.assertEqual(self.registry["canonical_denominator"], 8)
        self.assertEqual(self.registry["full_quorum"], "8/8")

        manifest = self.capability
        self.assertEqual(manifest.type, "KNOWLEDGE_SOURCE")
        self.assertEqual(manifest.semantic_kind, "SKILL")
        self.assertEqual(manifest.invocation_class, "MODEL_ROUTABLE")
        self.assertEqual(manifest.trust_level, "PURE_DATA")
        self.assertEqual(manifest.status, "ACTIVE")
        self.assertFalse(manifest.canonical_quorum_member)
        self.assertFalse(manifest.optional_specialist)
        self.assertIn("existing-p2p-router", manifest.requires)
        self.assertIn("p2p-visual-reference-pack/1", manifest.authority)
        self.assertIn(
            "docs/p2p-development/capability-catalog/game-asset-forge/visual-reference-pack.schema.json",
            manifest.context_pointers,
        )

        # PURE_DATA knowledge source: never a vendor skill, never host code.
        self.assertFalse(is_vendor_skill(manifest))
        for pointer in manifest.context_pointers:
            if pointer.startswith("docs/") or pointer.startswith("governance/"):
                self.assertTrue((REPO_ROOT / pointer).is_file(), pointer)

        proven = self.provenance
        self.assertEqual(proven["mode"], "P2P_NATIVE_KNOWLEDGE_DERIVATION")
        self.assertEqual(sorted(proven["dual_classification"]), ["KNOWLEDGE_SOURCE", "MODEL_ROUTABLE_SKILL"])
        self.assertEqual(proven["repos_reviewed"], REPOS_REVIEWED)
        self.assertEqual(proven["master_spec_fields"], list(TWELVE_FIELDS))
        self.assertFalse(proven["typed_schema_or_validator_framework_created"])
        self.assertEqual(proven["separate_capabilities_created_for"], [])
        self.assertFalse(proven["video_studio_created"])
        self.assertFalse(proven["execution_authorized"])
        self.assertFalse(proven["network_runtime"])
        self.assertFalse(proven["credentials"])
        self.assertEqual(proven["install_mode"], "DISABLED")
        self.assertEqual(proven["dependency_mode"], "NONE")

    def test_02_no_second_router_registry_orchestrator_or_runtime_surface(self) -> None:
        proven = self.provenance
        for key in (
            "new_router_created",
            "new_registry_created",
            "new_orchestrator_created",
            "new_database_created",
            "new_server_created",
            "new_queue_created",
            "new_daemon_created",
            "model_weights_downloaded",
            "video_runtime_installed",
            "paid_video_generation_used",
            "second_character_reference_schema_created",
            "consistency_engine_built",
        ):
            with self.subTest(key=key):
                self.assertFalse(proven[key])

        # No executable video surface was added to the capability package.
        capability_dir = SYSTEM_ROOT / "p2p_capabilities"
        video_modules = [
            path.name
            for path in capability_dir.glob("*.py")
            if "video" in path.name.lower() or "director" in path.name.lower()
        ]
        self.assertEqual(video_modules, [], "no video/director runtime module may be added")

        # No vendor snapshot, no third-party corpus, no weights.
        vendor_root = REPO_ROOT / ".p2p" / "vendor" / "skill"
        self.assertFalse(
            any("seedance" in p.name.lower() or "video" in p.name.lower() for p in vendor_root.iterdir()),
            "no video/seedance vendor snapshot may be created",
        )
        self.assertFalse(any(CATALOG.glob("*.schema.json")), "no typed schema framework for this capability")
        self.assertFalse(any(CATALOG.glob("*.py")), "no executable code in the knowledge catalog")

        # No separate executable capabilities for the deferred artifacts.
        forbidden_ids = {
            "video.character_bible",
            "video.world_bible",
            "video.style_bible",
            "video.shot_spec",
            "video.continuity",
            "video.studio",
            "video.generate",
            "video.render",
        }
        self.assertEqual(forbidden_ids & set(self.entries), set())
        new_ids = set(self.raw_entries) - set(PRESERVED_IDENTITY_HASHES)
        video_ids = {cid for cid in self.raw_entries if cid.startswith("video.")}
        self.assertEqual(video_ids, {CAPABILITY_ID}, "exactly one video.* capability")
        self.assertIn(CAPABILITY_ID, new_ids)

    def test_03_existing_responsibilities_are_preserved_byte_identically(self) -> None:
        for capability_id, expected in PRESERVED_IDENTITY_HASHES.items():
            with self.subTest(capability_id=capability_id):
                self.assertEqual(_canon(self.raw_entries[capability_id]), expected)

        self.assertEqual(
            hashlib.sha256(VRP_SCHEMA.read_bytes()).hexdigest(),
            PRESERVED_VRP_SCHEMA_SHA256,
            "p2p-visual-reference-pack/1 must not be edited or re-declared",
        )

        # Image prompting stays image-only; whiteboard stays whiteboard-only.
        style_lib = self.raw_entries["visual.gpt_image_2_style_library"]
        self.assertNotIn("video", json.dumps(style_lib, ensure_ascii=False).lower().replace("video.prompt.director_spec", ""))
        self.assertIn("camera", style_lib["NEGATIVE_TRIGGERS"])
        whiteboard = self.raw_entries["media.whiteboard_animation"]
        self.assertNotIn(CAPABILITY_ID, json.dumps(whiteboard, ensure_ascii=False))

        # The new capability must not absorb those responsibilities.
        self.assertIn(
            "expand-visual.gpt_image_2_style_library-into-video-direction",
            self.capability.prohibited_actions,
        )
        self.assertIn(
            "route-generic-video-direction-into-media.whiteboard_animation",
            self.capability.prohibited_actions,
        )
        self.assertIn("create-second-character-reference-schema", self.capability.prohibited_actions)
        self.assertIn(CATALOG_README.name, {p.name for p in CATALOG.iterdir()})

    # ---------------------------------------------------------------- 04 routing

    def test_04_existing_router_selects_the_capability_without_a_second_router(self) -> None:
        route = self.route(NAMESPACED_REQUEST)
        self.assertTrue(route["single_router"])
        self.assertEqual(route["schema"], "p2p-capability-route/1")
        self.assertIn(CAPABILITY_ID, route["selected"])
        selected = next(item for item in route["results"] if item["capability_id"] == CAPABILITY_ID)
        self.assertEqual(selected["classification"], "PRIMARY")
        self.assertIn(CAPABILITY_ID, selected["positive_triggers"])
        self.assertIn("video prompt", selected["positive_triggers"])
        self.assertEqual(selected["negative_triggers"], [])

        # The bare idea sentence carries no video-direction signal, so the new
        # capability must NOT capture it. Over-capture would be a routing defect.
        bare = self.route(USER_IDEA)
        self.assertNotIn(CAPABILITY_ID, bare["selected"])

        # Vendor projection stays vendor-only; a PURE_DATA knowledge source is
        # never projected as a vendor skill and never auto-loads content.
        vendor = discover_vendor_skills(
            NAMESPACED_REQUEST,
            registry_path=REGISTRY_PATH,
            repository_root=REPO_ROOT,
        )
        self.assertNotIn(CAPABILITY_ID, vendor["selected"])
        self.assertFalse(vendor["content_loaded"])
        self.assertFalse(vendor["permission_grant"])

    def test_05_new_triggers_do_not_disturb_existing_route_selections(self) -> None:
        for request, expected in PRESERVED_ROUTE_REQUESTS:
            with self.subTest(request=request):
                result = self.route(request)
                self.assertNotIn(CAPABILITY_ID, result["selected"])
                self.assertEqual(
                    set(result["selected"]) & {expected[0], CAPABILITY_ID},
                    {expected[0]},
                    "the new capability must never displace an existing selection",
                )

    # ---------------------------------------------------------------- 06 master spec

    def test_06_master_spec_demonstrates_all_twelve_minimum_fields(self) -> None:
        spec = self.master_spec
        self.assertEqual(spec["capability"], CAPABILITY_ID)
        self.assertEqual(spec["spec_id"], "VDS-VALIDATION-01-LY-TRUONG-SINH-SWORD-DESCENT")
        self.assertTrue(spec["provider_neutral"])
        self.assertEqual(spec["source_request"]["user_idea_verbatim"], USER_IDEA)

        for field in TWELVE_FIELDS:
            with self.subTest(field=field):
                self.assertIn(field, spec, f"master spec is missing {field}")
                value = spec[field]
                self.assertTrue(value, f"{field} must not be empty")
                if isinstance(value, dict):
                    self.assertTrue(any(str(k).strip() for k in value))

        # dialogue may be NOT_APPLICABLE but only with an explicit reason and a
        # forward contract; it may not be silently absent.
        dialogue = spec["dialogue"]
        self.assertEqual(dialogue["status"], "NOT_APPLICABLE")
        self.assertTrue(dialogue["reason"])
        self.assertTrue(dialogue["conditional_contract_if_dialogue_is_added_later"]["language_declaration_required"])

        # Every beat declares a visible end-state, and the input decomposition is complete.
        for beat in spec["timeline"]["beats"]:
            with self.subTest(beat=beat["beat"]):
                for key in (
                    "actor_action",
                    "camera_framing",
                    "principal_camera_move",
                    "environment",
                    "lighting",
                    "physics",
                    "dialogue",
                    "audio",
                    "visible_end_state",
                    "continuity",
                ):
                    self.assertTrue(str(beat[key]).strip(), key)
        decomposed = spec["source_request"]["decomposed_inputs"]
        self.assertEqual(
            sorted(decomposed),
            ["ACTION", "CAMERA_INTENT", "CANONICAL_REFERENCES", "STYLE_WORLD_INTENT", "USER_IDEA"],
        )

    def test_07_two_move_camera_request_yields_two_beats_not_one_overloaded_command(self) -> None:
        spec = self.master_spec
        camera = spec["camera"]
        self.assertEqual(camera["rule_applied"], "ONE_PRINCIPAL_CAMERA_MOVE_PER_BEAT")
        self.assertEqual(camera["rule_status"], "DIRECTOR_RULE_NOT_UNIVERSAL_VALIDATOR")
        self.assertIsNone(camera["recorded_deviation"])

        beats = camera["beats"]
        self.assertGreaterEqual(len(beats), 2, "rear chase + arc to frontal must not collapse into one beat")
        self.assertEqual(spec["source_request"]["camera_moves_requested"], 2)
        self.assertFalse(camera["moves_requested_vs_beats"]["collapsed_into_one_overloaded_command"])

        moves = []
        for beat in beats:
            with self.subTest(beat=beat["beat"]):
                self.assertEqual(
                    beat["principal_camera_move_count"],
                    1,
                    "exactly one principal camera move per beat",
                )
                self.assertTrue(beat["principal_camera_move"].strip())
                self.assertTrue(beat["end_state_of_move"].strip())
                self.assertTrue(beat["framing"].strip())
                self.assertTrue(beat["lens_intent_as_visible_effect"].strip())
                self.assertEqual(len(beat["window_fraction_of_shot"]), 2)
                moves.append(beat["principal_camera_move"])

        self.assertEqual(len(set(moves)), len(moves), "principal moves must be distinct")
        joined = " ".join(moves).upper()
        self.assertIn("REAR_CHASE_FOLLOW", joined, "beat 1 must be the rear chase")
        self.assertIn("ARC_TO_FRONTAL", joined, "beat 2 must be the arc to frontal")
        chase_index = next(i for i, m in enumerate(moves) if "REAR_CHASE" in m.upper())
        arc_index = next(i for i, m in enumerate(moves) if "ARC_TO_FRONTAL" in m.upper())
        self.assertLess(chase_index, arc_index, "the chase must precede the arc")

        # Beat windows are ordered, non-overlapping, and cover the shot.
        windows = [tuple(beat["window_fraction_of_shot"]) for beat in beats]
        self.assertEqual(windows[0][0], 0.0)
        self.assertEqual(windows[-1][1], 1.0)
        for (_, previous_end), (next_start, _) in zip(windows, windows[1:]):
            self.assertEqual(previous_end, next_start)

        # The rule is a director rule, never a universal hard validator.
        self.assertIn("not a validator", self.protocol_text.lower())
        self.assertFalse((SYSTEM_ROOT / "p2p_capabilities" / "video_camera_validator.py").exists())

    def test_08_reference_binding_reuses_the_existing_pack_and_excludes_per_slot(self) -> None:
        binding = self.master_spec["reference_binding"]
        self.assertEqual(binding["rule"], "REFERENCE SLOT -> ADOPT -> EXCLUDE")
        self.assertEqual(binding["schema_reused"], "p2p-visual-reference-pack/1")
        self.assertFalse(binding["second_character_reference_schema_created"])
        self.assertTrue(binding["every_slot_declares_ADOPT_and_EXCLUDE"])

        slots = {slot["slot"]: slot for slot in binding["slots"]}
        self.assertIn("CHARACTER_REFERENCE", slots)
        self.assertIn("SYMBOLIC_PROP_REFERENCE", slots, "a canonical symbolic prop gets its own slot")
        self.assertTrue(slots["SYMBOLIC_PROP_REFERENCE"]["own_slot_reason"])

        for name, slot in slots.items():
            with self.subTest(slot=name):
                self.assertTrue(slot["ADOPT"], "every slot must declare ADOPT")
                self.assertTrue(slot["EXCLUDE"], "every slot must declare EXCLUDE")

        character = slots["CHARACTER_REFERENCE"]
        for expected in ("face", "hair", "body proportions", "outfit"):
            self.assertIn(expected, character["ADOPT"])
        for excluded in ("source background", "unrelated characters", "unrelated props"):
            self.assertIn(excluded, character["EXCLUDE"])

        # Vocabulary is reused from p2p-visual-reference-pack/1, never re-declared.
        schema = json.loads(VRP_SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(schema["$id"], "p2p-visual-reference-pack/1")
        enum = schema["properties"]["views"]["items"]["properties"]["view_id"]["enum"]
        self.assertEqual(sorted(enum), sorted(VRP_VIEW_IDS))
        self.assertEqual(sorted(character["view_ids_used"]), sorted(VRP_VIEW_IDS))
        self.assertEqual(character["bound_to_schema"], "p2p-visual-reference-pack/1")

        protocol_text = self.protocol_text
        for view_id in VRP_VIEW_IDS:
            self.assertIn(view_id, protocol_text, "protocol must reuse the pack vocabulary by name")
        self.assertIn("Do not create a second character-reference schema", protocol_text)

    def test_09_consistency_taxonomy_records_ten_distinct_concepts_and_the_inequality(self) -> None:
        self.assertEqual(list(self.provenance["consistency_taxonomy"]), list(CONSISTENCY_TAXONOMY))
        self.assertFalse(self.provenance["consistency_engine_built"])
        for concept in CONSISTENCY_TAXONOMY:
            with self.subTest(concept=concept):
                self.assertIn(concept, self.protocol_text)

        inequality = self.provenance["consistency_inequality_asserted"]
        self.assertIn("IMAGE_CONSISTENCY != VIDEO_TEMPORAL_CONSISTENCY", inequality)
        self.assertIn("VIDEO_TEMPORAL_CONSISTENCY != SHOT_TO_SHOT_CONTINUITY", inequality)
        self.assertIn("IMAGE_CONSISTENCY != SHOT_TO_SHOT_CONTINUITY", inequality)
        self.assertIn(
            "IMAGE_CONSISTENCY  !=  VIDEO_TEMPORAL_CONSISTENCY  !=  SHOT_TO_SHOT_CONTINUITY",
            self.protocol_text,
        )

        continuity = self.master_spec["continuity"]
        locked = continuity["concepts_locked_for_this_shot"]
        self.assertEqual(sorted(locked), ["IMAGE_CONSISTENCY", "SHOT_TO_SHOT_CONTINUITY", "VIDEO_TEMPORAL_CONSISTENCY"])
        for name, entry in locked.items():
            with self.subTest(concept=name):
                self.assertTrue(entry["requirement"])
        self.assertFalse(locked["IMAGE_CONSISTENCY"]["sufficient_for_shot_acceptance"])
        self.assertFalse(locked["VIDEO_TEMPORAL_CONSISTENCY"]["sufficient_for_shot_acceptance"])
        self.assertFalse(locked["SHOT_TO_SHOT_CONTINUITY"]["satisfied_within_one_generation"])
        self.assertEqual(continuity["inequality_asserted"], list(inequality))
        self.assertTrue(continuity["global_lock_statements_repeated_per_shot"])
        self.assertIn("sword", continuity["prop_and_costume_state_ledger"])

    def test_10_shot_chaining_and_post_production_stay_knowledge_only(self) -> None:
        chaining = self.provenance["shot_chaining"]
        self.assertEqual(chaining["status"], "KNOWLEDGE_ONLY")
        self.assertEqual(
            chaining["pattern"],
            "CANONICAL_CHARACTER_REFERENCE + PREVIOUS_SHOT_FINAL_FRAME + NEXT_SHOT_SPEC -> NEXT_VIDEO_GENERATION",
        )
        self.assertEqual(list(chaining["conditioning_concepts"]), list(CONDITIONING_CONCEPTS))
        self.assertFalse(chaining["execution_built"])
        self.assertFalse(chaining["video_generated"])
        for concept in CONDITIONING_CONCEPTS:
            self.assertIn(concept, self.protocol_text)

        handoff = self.master_spec["chain_handoff"]
        self.assertEqual(handoff["execution_status"].split(" ")[0], "KNOWLEDGE_ONLY")
        self.assertEqual(handoff["consistency_problem_class"], "SHOT_TO_SHOT_CONTINUITY")
        self.assertIn("must never replace identity", handoff["rule"])

        post = self.provenance["post_production_reference"]
        self.assertEqual(post["status"], "KNOWLEDGE_ONLY")
        self.assertEqual(list(post["pipeline"]), list(POST_PRODUCTION_PIPELINE))
        self.assertEqual(
            sorted(post["owner_gates"]),
            ["API_CREDENTIALS", "INFRASTRUCTURE_RUNTIME_COMMITMENT", "PAID_VIDEO_GENERATION"],
        )
        self.assertEqual(post["generation_retry"], "BOUNDED")
        self.assertFalse(post["generation_failure_counts_as_pipeline_advance"])
        self.assertEqual(post["final_output_requirement"], "DURABLE_RETURNED_ARTIFACT")
        for key in ("executable_integration", "installed", "vendored", "wrapped"):
            with self.subTest(key=key):
                self.assertFalse(post[key])
        for stage in POST_PRODUCTION_PIPELINE:
            self.assertIn(stage, self.protocol_text)
        readme_text = CATALOG_README.read_text(encoding="utf-8")
        self.assertIn("never\n  installed, never vendored, never wrapped", readme_text)
        self.assertIn("POST_PRODUCTION_REFERENCE", readme_text)
        self.assertIn("MODEL_ADAPTER_CANDIDATE", readme_text)

    # ---------------------------------------------------------------- 11 projection

    def test_11_exactly_one_short_provider_projection_from_the_neutral_master_spec(self) -> None:
        projection = self.projection
        master = self.master_spec
        self.assertEqual(projection["artifact"], "PROVIDER_PROJECTION")
        self.assertEqual(projection["derived_from_spec_id"], master["spec_id"])
        self.assertEqual(projection["projection_number_for_this_validation"], 1)
        self.assertEqual(
            projection["direction"],
            "CANONICAL_MASTER_SPEC -> SHORT_PROVIDER_SPECIFIC_PROMPT",
        )
        self.assertTrue(projection["master_spec_remains_provider_neutral"])
        self.assertFalse(projection["master_spec_mutated_by_this_projection"])
        self.assertEqual(master["model_specific_projection"]["projections_authored_for_this_validation"], 1)

        prompt = projection["prompt_text"]
        self.assertTrue(prompt.strip())
        measurement = projection["prompt_text_measurement"]
        self.assertEqual(measurement["character_count"], len(prompt), "recorded measurement must not drift")
        self.assertEqual(measurement["sentence_count"], len([s for s in re.split(r"(?<=\.)\s+", prompt) if s.strip()]))
        self.assertTrue(measurement["measured_not_a_limit"])
        self.assertTrue(measurement["projection_is_shorter_than_master_spec"])
        self.assertLess(
            len(prompt),
            len(json.dumps(master, ensure_ascii=False)),
            "the projection must be materially shorter than the master spec",
        )

        # Flat prose: no field labels, no marker syntax, because the provider's
        # acceptance of labelled structured prompts is UNKNOWN.
        fmt = projection["format_decision"]
        self.assertEqual(fmt["structured_or_flat"], "FLAT_NATURAL_LANGUAGE_PROSE")
        self.assertEqual(fmt["marker_syntax_used"], "NONE")
        self.assertFalse(fmt["field_labels_emitted"])
        for field in TWELVE_FIELDS:
            self.assertNotIn(f"{field}:", prompt.lower())
        self.assertIn("does not assume", fmt["reason"])

        # Identity lock, both camera beats, light source, gating prohibition, end-state.
        self.assertIn("ki\u1ebfm", prompt)  # sword
        self.assertIn("khu\u00f4n m\u1eb7t", prompt)  # face
        self.assertIn("trang ph\u1ee5c", prompt)  # costume
        self.assertIn("ch\u1ec9 m\u1ed9t thanh ki\u1ebfm duy nh\u1ea5t", prompt)  # exactly one sword
        self.assertIn("\u0111u\u1ed5i", prompt)  # chase
        self.assertIn("v\u00f2ng cung", prompt)  # arc
        self.assertIn("ch\u00ednh di\u1ec7n", prompt)  # frontal
        self.assertIn("C\u1ea5m", prompt)  # prohibition clause present
        self.assertIn("k\u1ebft c\u1ea3nh", prompt.lower())  # declared end-state
        self.assertEqual(measurement["camera_beats_expressed"], 2)

        reduction = projection["reduction_record"]
        self.assertEqual(reduction["invented_facts"], [])
        self.assertTrue(reduction["compress_never_invent_respected"])
        self.assertTrue(reduction["dropped_fields"])
        self.assertTrue(reduction["compressed_fields"])
        self.assertTrue(reduction["reversible_to_master_spec"].startswith("YES"))

    def test_12_no_hard_coded_provider_prompt_length_or_control_constant(self) -> None:
        projection = self.projection
        profile = projection["target_provider_profile"]
        self.assertFalse(profile["verified_profile_available"])
        self.assertIsNone(profile["named_provider"])
        self.assertFalse(profile["hard_coded_prompt_length_constant_applied"])
        self.assertFalse(profile["hard_coded_duration_or_aspect_constant_applied"])
        self.assertEqual(profile["providers_with_hard_coded_limits"], [])
        for field in PROFILE_FIELDS:
            with self.subTest(field=field):
                self.assertEqual(
                    profile["profile_fields_used"][field],
                    "UNKNOWN_UNTIL_VERIFIED_PROFILE",
                )

        budget = projection["budget"]
        self.assertEqual(budget["budget_source"], "SUPPLIED_BY_CALLER_FOR_THIS_VALIDATION_ONLY")
        self.assertFalse(budget["budget_is_a_p2p_constant"])
        self.assertFalse(budget["verified_provider_profile_consulted"])

        proven_projection = self.provenance["provider_projection"]
        self.assertEqual(proven_projection["hard_coded_prompt_length_constants"], "NONE")
        self.assertEqual(proven_projection["providers_with_hard_coded_limits"], [])
        self.assertEqual(proven_projection["profiles_verified_at_integration"], 0)
        self.assertFalse(proven_projection["provider_api_implemented"])
        self.assertTrue(proven_projection["master_spec_provider_neutral"])
        self.assertEqual(len(proven_projection["profile_fields"]), len(PROFILE_FIELDS))
        self.assertIn("existing governed FACT_LEDGER -> Live Specs promotion only", proven_projection["runtime_authoritative_provider_data_path"])

        # Provider controls are declared, not written into prompt text.
        side = projection["provider_side_controls_not_in_prompt_text"]
        self.assertNotIn("12s", projection["prompt_text"])
        self.assertNotIn("2.35:1", projection["prompt_text"])
        self.assertTrue(side["reason"])

        # No permanent provider limit anywhere in the new artifacts.
        forbidden = re.compile(
            r"(?i)(arena|designarena|seedance|kling|wan|veo|sora|runway)[^.\n]{0,80}"
            r"(\bmax(imum)?\b|\blimit\b|characters?\b)[^.\n]{0,40}\b\d{2,}\b"
        )
        for path in (PROTOCOL, DERIVED, CATALOG_README, MASTER_SPEC_PATH, PROJECTION_PATH):
            with self.subTest(path=path.name):
                self.assertIsNone(forbidden.search(path.read_text(encoding="utf-8")))
        self.assertIn("No permanent hard-coded prompt-length limit", self.protocol_text)
        self.assertIn("P2P hard-codes no duration constant", self.protocol_text)
        self.assertIn("P2P adopts no numeric length constant for any provider", self.derived_text)

        # The caller-supplied controls are labelled as caller input, never P2P constants.
        controls = self.master_spec["caller_supplied_controls"]
        self.assertFalse(controls["p2p_hard_coded_constant"])
        self.assertFalse(controls["verified_provider_profile_used"])
        self.assertEqual(controls["provenance"], "SUPPLIED_BY_CALLER_FOR_THIS_VALIDATION_ONLY")

    def test_13_execution_status_is_prompt_text_only(self) -> None:
        execution = self.projection["execution_status"]
        self.assertFalse(execution["submitted_to_any_provider"])
        self.assertFalse(execution["provider_api_called"])
        self.assertFalse(execution["credentials_used"])
        self.assertFalse(execution["video_rendered"])
        self.assertFalse(execution["paid_video_generation_used"])
        self.assertIsNone(execution["artifact_returned_by_a_provider"])

        non_goals = self.master_spec["non_goals_verified_for_this_artifact"]
        for key, value in non_goals.items():
            with self.subTest(key=key):
                if isinstance(value, bool):
                    self.assertFalse(value)
                else:
                    self.assertEqual(value, [])

    # ---------------------------------------------------------------- 14 ledger

    def test_14_research_ledger_records_seven_repos_plus_one_reference_append_only(self) -> None:
        ledger = self.ledger
        self.assertEqual(ledger["schema_version"], "p2p-framework/research-adoption-ledger/1")
        self.assertEqual(len(ledger["records"]), BASELINE_LEDGER_RECORD_COUNT + len(NEW_RECORD_IDS))

        # Append-only: the 69 historical records and the top-level identity are untouched.
        self.assertEqual(_canon(ledger["records"][:BASELINE_LEDGER_RECORD_COUNT]), PRESERVED_LEDGER_RECORDS_HASH)
        self.assertEqual(
            _canon({k: v for k, v in ledger.items() if k not in ("records", "notes")}),
            PRESERVED_LEDGER_TOPLEVEL_HASH,
            "generated_at/generated_by/last_reviewed/baseline_identity must not be rewritten",
        )
        self.assertEqual(ledger["notes"][0], "Human projection: docs/RESEARCH-ADOPTION-LEDGER.md. On conflict this JSON wins.")
        self.assertEqual(len(ledger["notes"]), 3)

        vocabulary = set(ledger["status_vocabulary"])
        reference_shape = set(ledger["records"][0].keys())
        pinned_repos = {}
        for research_id in NEW_RECORD_IDS:
            with self.subTest(record=research_id):
                record = self.records[research_id]
                self.assertEqual(set(record.keys()), reference_shape)
                self.assertIn(record["status"], vocabulary)
                self.assertIn(record["status"], {"SELECTED", "RESEARCHED", "DEFERRED"})
                self.assertTrue(record["research_summary"].strip())
                self.assertTrue(record["selected_ideas"])
                self.assertTrue(record["rejected_ideas"])
                self.assertTrue(record["p2p_translation"].strip())
                self.assertTrue(record["evidence_pointers"])
                self.assertEqual(record["last_reviewed_at"], "2026-09-03T00:00:00Z")
                self.assertIn("issue #71", json.dumps(record, ensure_ascii=False))
                if record["source_type"] == "GITHUB_REPOSITORY":
                    self.assertIn(record["source_reference"], EXPECTED_PINS)
                    self.assertIn(EXPECTED_PINS[record["source_reference"]], record["source_version_or_commit"])
                    pinned_repos[record["source_reference"]] = record["research_id"]
                for pointer in record["evidence_pointers"]:
                    path = pointer.split(" ")[0]
                    if path.startswith(("docs/", "governance/", "tests/", ".p2p/")):
                        self.assertTrue((REPO_ROOT / path).exists(), pointer)

        self.assertEqual(len(pinned_repos), REPOS_REVIEWED, "all seven repositories must be pinned")
        self.assertEqual(set(pinned_repos), set(EXPECTED_PINS))

        # Treatments are the accepted classifications, not reopened ones.
        jacobye = self.records["RA-EXT-070"]
        self.assertIn("PRIMARY_METHOD_PROVENANCE", jacobye["p2p_translation"])
        self.assertEqual(jacobye["canonical_capability_ids"], [CAPABILITY_ID])
        self.assertEqual(jacobye["status"], "SELECTED")

        corpus = self.records["RA-EXT-071"]
        self.assertEqual(corpus["status"], "RESEARCHED")
        self.assertEqual(corpus["provenance_status"], "REPOSITORY_NOT_VENDORED")
        self.assertEqual(corpus["canonical_capability_ids"], [])
        self.assertIn("vendoring-any-third-party-prompt-text", corpus["rejected_ideas"])

        # Every runtime-bearing source explicitly rejects installation.
        no_install_rejections = {
            "RA-EXT-072": "runtime-installation",
            "RA-EXT-073": "runtime-installation",
            "RA-EXT-074": "runtime-installation",
            "RA-EXT-076": "installation",
        }
        for research_id, rejected_token in no_install_rejections.items():
            with self.subTest(record=research_id):
                self.assertIn(rejected_token, self.records[research_id]["rejected_ideas"])

        # Machine-readable no-install / no-weights facts in the registry entry.
        by_adoption = {
            item["adoption_record"]: item
            for item in self.provenance["knowledge_only_sources"]
        }
        for research_id in ("RA-EXT-072", "RA-EXT-073", "RA-EXT-074"):
            with self.subTest(source=research_id):
                self.assertFalse(by_adoption[research_id]["runtime_installed"])
                self.assertFalse(by_adoption[research_id]["vendored"])
        self.assertFalse(by_adoption["RA-EXT-072"]["model_weights_downloaded"])
        self.assertFalse(by_adoption["RA-EXT-074"]["checkpoint_downloaded"])
        self.assertFalse(by_adoption["RA-EXT-074"]["dataset_downloaded"])
        self.assertFalse(by_adoption["RA-EXT-071"]["vendored"])
        self.assertIn(
            "Third-party prompt corpus; NOASSERTION licence blocks executable projection",
            by_adoption["RA-EXT-071"]["reason_not_vendored"],
        )
        self.assertFalse(by_adoption["RA-EXT-076"]["installed"])
        self.assertFalse(by_adoption["RA-EXT-076"]["wrapped"])
        self.assertFalse(by_adoption["RA-EXT-076"]["vendored"])
        self.assertIsNone(by_adoption["RA-EXT-077"]["upstream_repository"])
        self.assertEqual(by_adoption["RA-EXT-077"]["source_type"], "SESSION_DERIVED_ARTIFACT")

        wan = self.records["RA-EXT-072"]
        self.assertIn("MODEL_ADAPTER_CANDIDATE", wan["p2p_translation"])
        self.assertIn("FUTURE_BACKEND", wan["p2p_translation"])
        self.assertEqual(wan["status"], "DEFERRED")
        self.assertIn("downloading-model-weights", wan["rejected_ideas"])

        vace = self.records["RA-EXT-073"]
        self.assertIn("conditioning and control-slot vocabulary only", vace["p2p_translation"].lower())

        recam = self.records["RA-EXT-074"]
        self.assertIn("BENCHMARK_ONLY", json.dumps(recam, ensure_ascii=False))
        self.assertIn("ai-video camera vocabulary only", recam["p2p_translation"].lower())

        consistency = self.records["RA-EXT-075"]
        self.assertIn("consistency taxonomy only", consistency["p2p_translation"].lower())
        self.assertIn("building-an-executable-consistency-engine", consistency["rejected_ideas"])

        moneyprinter = self.records["RA-EXT-076"]
        self.assertIn("POST_PRODUCTION_REFERENCE", moneyprinter["p2p_translation"])
        self.assertIn("FUTURE_BACKEND", moneyprinter["p2p_translation"])
        self.assertEqual(moneyprinter["status"], "DEFERRED")
        for rejected in ("installation", "vendoring", "wrapping-as-a-p2p-backend"):
            self.assertIn(rejected, moneyprinter["rejected_ideas"])

        skydive = self.records["RA-EXT-077"]
        self.assertEqual(skydive["source_type"], "INTERNAL_P2P_RESEARCH")
        self.assertIn("prompt-architecture-only", skydive["selected_ideas"])
        self.assertIn("REPOS_REVIEWED stays 7", skydive["notes"])

    def test_15_cc_by_4_attribution_upstream_identity_and_pin_are_preserved(self) -> None:
        primary = self.provenance["primary_method_provenance"]
        self.assertEqual(primary["upstream_repository"], JACOBYE_REPO)
        self.assertEqual(primary["upstream_commit"], JACOBYE_COMMIT)
        self.assertEqual(primary["upstream_tree"], JACOBYE_TREE)
        self.assertEqual(primary["upstream_default_branch"], "master")
        self.assertFalse(primary["vendored"])
        self.assertEqual(primary["copied_files"], [])
        self.assertEqual(primary["adoption_record"], "RA-EXT-070")

        licence = primary["license"]
        self.assertEqual(licence["kind"], "CC-BY-4.0")
        self.assertTrue(licence["attribution_required"])
        self.assertIn("Copyright (c) 2026 Jacob Ye", licence["copyright"])
        self.assertIn("CC BY 4.0", licence["notice"])
        self.assertIn("creativecommons.org/licenses/by/4.0", licence["notice"])
        self.assertEqual(licence["upstream_notice_file"], "NOTICE")
        self.assertIn(
            "Seedance 2.5 production reference by Serge Shima, smixs/visual-skills (CC BY 4.0)",
            licence["incorporated_upstream_credits_preserved"],
        )

        # The attribution travels in the durable knowledge artifact too.
        self.assertIn("Attribution notice (CC-BY-4.0 — must be preserved)", self.derived_text)
        self.assertIn("JACOB YE \u00b7 SEEDANCE PROMPT", self.derived_text)
        self.assertIn("Copyright (c) 2026 Jacob Ye", self.derived_text)
        self.assertIn(JACOBYE_COMMIT, self.derived_text)
        self.assertIn(JACOBYE_TREE, self.derived_text)
        self.assertIn(JACOBYE_REPO, self.derived_text)
        self.assertIn("smixs/visual-skills", self.derived_text)
        self.assertIn("MapleShaw/seedance2.0-prompt-skill", self.derived_text)

        # A bounded derived reference is sufficient: FORMULA.md is not copied.
        self.assertIn("not a copy of any upstream file", self.derived_text)
        self.assertIn("The full `FORMULA.md`. This bounded derived reference is sufficient.", self.derived_text)
        self.assertNotIn("JACOB SEEDANCE FILM FORMULA", self.derived_text)

        # Every pin is recorded in the durable derived reference.
        for repository, commit in EXPECTED_PINS.items():
            with self.subTest(repository=repository):
                self.assertIn(repository, self.derived_text)
                self.assertIn(commit, self.derived_text)

        # No third-party prompt corpus was vendored anywhere in the repository.
        vendor_root = REPO_ROOT / ".p2p" / "vendor"
        self.assertFalse(
            any("awesome-seedance" in p.name.lower() for p in vendor_root.rglob("*")),
            "the third-party prompt corpus must never be vendored",
        )

    # ---------------------------------------------------------------- 16 base

    def test_16_base_authority_is_the_known_main_sha(self) -> None:
        self.assertEqual(BASE_MAIN_SHA, "c1ddc4fdbc3bf6639a5f3e3f171a7fb5c1df6352")
        self.assertEqual(
            self.provenance["owner_authorization"],
            "GitHub Issue #71 (7roger89-web/P2P-upgrade-github-1)",
        )
        self.assertIn("P2P-VIDEO-RESEARCH-01", self.provenance["source"])
        self.assertEqual(self.provenance["CERTIFIED"], "P2P-VIDEO-CAPABILITY-INTEGRATION-01")
        self.assertEqual(self.capability.version, "1.0.0")


if __name__ == "__main__":
    unittest.main()
