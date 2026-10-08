"""Deterministic checks for P2P_FRONTEND_UPSTREAM_INTAKE_01.

Verifies the first curated P2P frontend upstream capability pack:

* frontend-development is a thin hub (no one-project stack as universal law);
* frontend-design is a context-fit wrapper over vendored PracticalSwan v2;
* the four vendored upstream units retain their required child files;
* the react-doctor adapter is pinned, optional, and honestly scoped;
* the three skill mirrors plus manifests stay consistent;
* the existing package/install machinery delivers the pack to a synthetic
  project where a repo-scoped executor can discover it;
* no parallel router/registry/package-manager/daemon was introduced;
* no moving remote-``main`` prompt dependency exists in canonical behavior;
* the research-adoption-ledger batch RA-EXT-082..RA-EXT-091 is durable.

Read-only except for disposable fixtures under ``.tmp/``. Never executes
external tools (no npx, no curl, no network).
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
TEMP_PARENT = REPO_ROOT / ".tmp"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import doctor as p2p_doctor  # noqa: E402
import package_release  # noqa: E402
import p2p_skill_profile  # noqa: E402


CANONICAL = REPO_ROOT / ".agents" / "skills"
MIRRORS = [
    REPO_ROOT / ".claude" / "skills",
    REPO_ROOT / ".p2p" / "system" / ".agents" / "skills",
]
MANIFESTS = [
    REPO_ROOT / ".agents" / "skills" / ".agents-skill-manifest.json",
    REPO_ROOT / ".claude" / "skills" / ".claude-skill-manifest.json",
    REPO_ROOT / ".p2p" / "system" / ".agents" / "skills" / ".agents-skill-manifest.json",
]

PACK_SKILLS = (
    "frontend-design",
    "frontend-development",
    "react-best-practices",
    "composition-patterns",
    "frontend-code-review",
    "baseline-ui",
    "react-doctor",
)

TOUCHED_SKILLS = PACK_SKILLS + ("UI-animation-design",)

BATCH_IDS = [f"RA-EXT-{n:03d}" for n in range(82, 92)]
LEDGER_PATH = REPO_ROOT / "governance" / "research-adoption-ledger.json"
LEDGER_MD_PATH = REPO_ROOT / "docs" / "RESEARCH-ADOPTION-LEDGER.md"
REPORT_PATH = (
    REPO_ROOT / "docs" / "p2p-development" / "research"
    / "P2P-FRONTEND-UPSTREAM-INTAKE-01.md"
)

UPSTREAM_SHAS = {
    "vercel-labs/agent-skills": "063bee94c3f4df8453406c830b0a7df0f2860278",
    "PracticalSwan/agent-skills": "ff6d12f61e8250dd1b988e101a482f6adc05c451",
    "DNM03/frontend-code-review": "033d1c5d8bccc311fc3c4362690a482016651b96",
    "ibelick/ui-skills": "c5bcd86450b3582ba25204c622b9213b07464938",
    "millionco/react-doctor": "499a0208fca5c0422b713bdedf2b83fcc8e29d20",
    "pbakaus/impeccable": "f2c7051853848826aac2f4646581d62a732155ad",
    "microsoft/skills": "f7d8a83e55ab7bf125cb1134e892302c2344592e",
    "emilkowalski/skills": "85e8e2363b713506e1d5b6e07a0eb2da66be1bc3",
    "vercel-labs/design-systems-to-agent-skills": "0e541bc7a8eb8e86e6b1c93fac7cf21588d487da",
    "TanStack/table": "21d713fc4947d2a08cc2136bb055889a61412ded",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def aggregate_fallback(files: dict[str, str]) -> str:
    """Documented aggregate scheme for intake-touched manifest entries.

    Anvien's original aggregate algorithm is opaque (no in-repo generator);
    per-file hashes remain the authoritative verification surface. Touched
    entries recompute the aggregate deterministically from current per-file
    hashes so the manifest stays self-consistent; see the intake report.
    """
    blob = "\n".join(f"{k}\n{v.split(':')[1]}" for k, v in sorted(files.items()))
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def temporary_directory(prefix: str) -> tempfile.TemporaryDirectory[str]:
    TEMP_PARENT.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(dir=TEMP_PARENT, prefix=prefix)


class FrontendDevelopmentHubTests(unittest.TestCase):
    """§11A: one-project stack must not read as universal P2P law."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = CANONICAL / "frontend-development" / "SKILL.md"
        cls.text = cls.skill.read_text(encoding="utf-8")

    def test_project_specific_markers_absent_from_hub(self) -> None:
        for marker in (
            "MUI v7", "useMuiSnackbar", "TanStack Router",
            "~components", "~features", "~types", "@/hooks",
            "SuspenseLoader", "useSuspenseQuery",
        ):
            self.assertNotIn(marker, self.text, f"hub still universalizes: {marker}")

    def test_legacy_project_resources_removed(self) -> None:
        resources = CANONICAL / "frontend-development" / "resources"
        self.assertFalse(resources.exists(), "legacy one-project resources/ still present")

    def test_hub_routes_without_imposing_stack(self) -> None:
        for marker in (
            "PROJECT_INSTALLED_VERSION_SPECIFIC_GUIDANCE",
            "CENTRAL_GENERIC_LIBRARY_GUIDANCE",
            "react-best-practices",
            "composition-patterns",
            "frontend-code-review",
            "baseline-ui",
            "react-doctor",
            "Backend-only task",
        ):
            self.assertIn(marker, self.text, f"hub missing: {marker}")
        self.assertIn("NEVER impose a generic stack", self.text)

    def test_hub_is_thin(self) -> None:
        self.assertLessEqual(len(self.text.splitlines()), 120, "hub is not thin")


class FrontendDesignWrapperTests(unittest.TestCase):
    """§5A: context-fit direction; BOLD must not stay universal."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.text = (CANONICAL / "frontend-design" / "SKILL.md").read_text(encoding="utf-8")

    def test_universal_bold_rule_removed(self) -> None:
        for marker in (
            "commit to a BOLD aesthetic direction",
            "What makes this UNFORGETTABLE",
            "Pick an extreme",
            "NEVER converge on common choices",
        ):
            self.assertNotIn(marker, self.text, f"loud-universal rule remains: {marker}")

    def test_wrapper_defines_p2p_boundary(self) -> None:
        for marker in (
            "p2p-uiux",
            "upstream-frontend-design-v2.md",
            "Project Design-System Precedence",
            "Runtime Evidence Contract",
            "NEEDS_EVIDENCE",
        ):
            self.assertIn(marker, self.text, f"wrapper missing: {marker}")

    def test_vendored_upstream_body_and_supports_present(self) -> None:
        root = CANONICAL / "frontend-design"
        body = (root / "upstream-frontend-design-v2.md").read_text(encoding="utf-8")
        self.assertIn("fitness for context, not adherence to one visual style", body)
        self.assertIn("Design Mode Router", body)
        self.assertTrue((root / "references" / "accessibility-checklist.md").is_file())
        self.assertTrue((root / "scripts" / "contrast-checker.py").is_file())
        self.assertTrue((root / "LICENSE.txt").is_file())

    def test_upstream_relative_links_resolve(self) -> None:
        root = CANONICAL / "frontend-design"
        self.assertTrue((root / "references" / "accessibility-checklist.md").is_file())
        self.assertTrue((root / "scripts" / "contrast-checker.py").is_file())


class VendoredUnitTests(unittest.TestCase):
    """§11B: vendored units retain their required child files."""

    def test_react_best_practices_unit_complete(self) -> None:
        root = CANONICAL / "react-best-practices"
        self.assertTrue((root / "SKILL.md").is_file())
        self.assertTrue((root / "AGENTS.md").is_file())
        rules = sorted((root / "rules").glob("*.md"))
        self.assertGreaterEqual(len(rules), 70, f"rule files: {len(rules)}")
        for required in (
            "rules/async-parallel.md",
            "rules/bundle-barrel-imports.md",
            "rules/rerender-memo.md",
            "rules/server-cache-react.md",
        ):
            self.assertTrue((root / required).is_file(), required)
        skill = (root / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: vercel-react-best-practices", skill)

    def test_composition_patterns_unit_complete(self) -> None:
        root = CANONICAL / "composition-patterns"
        rules = sorted((root / "rules").glob("*.md"))
        self.assertGreaterEqual(len(rules), 8, f"rule files: {len(rules)}")
        for required in (
            "rules/architecture-compound-components.md",
            "rules/state-context-interface.md",
            "rules/patterns-explicit-variants.md",
        ):
            self.assertTrue((root / required).is_file(), required)

    def test_frontend_code_review_unit_complete(self) -> None:
        root = CANONICAL / "frontend-code-review"
        for required in (
            "SKILL.md",
            "references/checklist.md",
            "references/react.md",
            "references/nextjs-app-router.md",
            "references/data-fetching.md",
            "references/frontend-security.md",
            "references/ui-ux-accessibility.md",
            "references/performance-seo.md",
            "references/typescript.md",
            "references/i18n.md",
            "references/output-format.md",
            "references/sources.md",
            "examples/good-review.md",
            "examples/bad-review.md",
        ):
            self.assertTrue((root / required).is_file(), required)

    def test_baseline_ui_unit_complete(self) -> None:
        text = (CANONICAL / "baseline-ui" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("name: baseline-ui", text)
        self.assertIn("aria-label", text)

    def test_find_animation_opportunities_present(self) -> None:
        path = CANONICAL / "UI-animation-design" / "find-animation-opportunities" / "SKILL.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("name: find-animation-opportunities", text)
        router = (CANONICAL / "UI-animation-design" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("find-animation-opportunities", router)


class ReactDoctorAdapterTests(unittest.TestCase):
    """§11H: pinned, optional, honestly scoped; never a PASS machine."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.text = (CANONICAL / "react-doctor" / "SKILL.md").read_text(encoding="utf-8")

    def test_pinned_version_is_canonical(self) -> None:
        self.assertIn("react-doctor@0.9.14", self.text)
        self.assertIn("499a0208fca5c0422b713bdedf2b83fcc8e29d20", self.text)

    def test_latest_and_remote_playbook_prohibited(self) -> None:
        self.assertIn("NEVER use `react-doctor@latest`", self.text)
        self.assertIn("NEVER fetch the upstream remote triage playbook", self.text)
        self.assertNotIn("https://www.react.doctor/prompts/", self.text)
        self.assertNotIn("npx react-doctor@latest", self.text)

    def test_evidence_scoped_to_what_tool_proves(self) -> None:
        for marker in (
            "complete",
            "analyzedFileCount",
            "SCORE_UNAVAILABLE",
            "does NOT",
            "prove visual correctness",
        ):
            self.assertIn(marker, self.text, f"adapter missing: {marker}")

    def test_unavailable_downgrades_without_blocking(self) -> None:
        for marker in (
            "REACT_DOCTOR_UNAVAILABLE",
            "NEVER convert unavailability into PASS",
            "never loads this skill",
        ):
            self.assertIn(marker, self.text, f"adapter missing: {marker}")


class NoMovingRemotePromptTests(unittest.TestCase):
    """§11G: canonical behavior must not depend on moving remote `main`."""

    def skill_texts(self) -> dict[str, str]:
        texts: dict[str, str] = {}
        for skill in TOUCHED_SKILLS:
            for path in sorted((CANONICAL / skill).rglob("*")):
                if path.is_file():
                    texts[f"{skill}/{path.relative_to(CANONICAL / skill).as_posix()}"] = (
                        path.read_text(encoding="utf-8", errors="replace")
                    )
        return texts

    def test_no_live_remote_main_prompt_dependency(self) -> None:
        forbidden = (
            "raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main",
            "https://www.react.doctor/prompts/",
            "npx ui-skills start",
            "npx @tanstack/intent@latest",
            "curl --fail --silent --show-error",
        )
        texts = self.skill_texts()
        for relative, text in texts.items():
            for marker in forbidden:
                self.assertNotIn(marker, text, f"{relative} embeds moving remote: {marker}")

    def test_latest_occurrences_are_prohibitions_only(self) -> None:
        texts = self.skill_texts()
        for relative, text in texts.items():
            for lineno, line in enumerate(text.splitlines(), start=1):
                if "@latest" in line:
                    window = "\n".join(text.splitlines()[max(0, lineno - 3):lineno + 2])
                    self.assertTrue(
                        "NEVER" in window or "Prohibit" in window or "prohibit" in window,
                        f"{relative}:{lineno} uses @latest outside a prohibition",
                    )


class ProjectionMirrorTests(unittest.TestCase):
    """§11C: canonical source plus consistent mirrors and hashes."""

    def test_mirrors_byte_identical(self) -> None:
        for skill in TOUCHED_SKILLS:
            canonical_files = {
                p.relative_to(CANONICAL / skill)
                for p in (CANONICAL / skill).rglob("*") if p.is_file()
            }
            for mirror in MIRRORS:
                mirror_files = {
                    p.relative_to(mirror / skill)
                    for p in (mirror / skill).rglob("*") if p.is_file()
                }
                self.assertEqual(mirror_files, canonical_files, f"{mirror} {skill} file set")
                for relative in sorted(canonical_files):
                    self.assertEqual(
                        (mirror / skill / relative).read_bytes(),
                        (CANONICAL / skill / relative).read_bytes(),
                        f"mirror diverged: {mirror}/{skill}/{relative}",
                    )

    def test_manifest_per_file_hashes_match_content(self) -> None:
        for manifest_path in MANIFESTS:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            for skill in TOUCHED_SKILLS:
                entry = data["skills"][skill]
                actual = {
                    p.relative_to(CANONICAL / skill).as_posix(): "sha256:" + sha256_file(p)
                    for p in sorted((CANONICAL / skill).rglob("*")) if p.is_file()
                }
                self.assertEqual(entry["files"], actual, f"{manifest_path} {skill} files")
                self.assertEqual(entry["fileCount"], len(actual), f"{skill} fileCount")

    def test_manifest_entry_counts_match_skill_files(self) -> None:
        for manifest_path in MANIFESTS:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            for skill in TOUCHED_SKILLS:
                expected = len(list((CANONICAL / skill).rglob("SKILL.md")))
                self.assertEqual(
                    data["skills"][skill]["entryCount"], expected, f"{skill} entryCount"
                )

    def test_touched_aggregates_follow_documented_scheme(self) -> None:
        for manifest_path in MANIFESTS:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            for skill in TOUCHED_SKILLS:
                entry = data["skills"][skill]
                self.assertEqual(
                    entry["hash"], aggregate_fallback(entry["files"]),
                    f"{manifest_path} {skill} aggregate",
                )


class PackageInstallProofTests(unittest.TestCase):
    """§11D/E: packaged artifacts install into a synthetic project."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = temporary_directory("p2p-frontend-intake-01-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.stage = Path(cls.temp.name) / "stage"
        cls.project = Path(cls.temp.name) / "synthetic-project"
        package_release.copy_selected(REPO_ROOT, cls.stage)
        cls.project.mkdir(parents=True)
        (cls.project / "package.json").write_text(
            json.dumps({"dependencies": {"react": "^19.0.0", "next": "^16.0.0"}}),
            encoding="utf-8",
        )
        # Reproduce the current install.sh/install.ps1 project-fit contract:
        # a React project receives the full curated frontend pack.
        skills_source = cls.stage / ".agents" / "skills"
        receipt = p2p_skill_profile.build_receipt(cls.project, skills_source)
        cls.asserted_profile = receipt["profile"]
        target = cls.project / ".agents" / "skills"
        target.mkdir(parents=True)
        for name in receipt["selected_skills"]:
            source = skills_source / str(name)
            shutil.copytree(source, target / source.name)

    def test_react_fixture_uses_react_profile(self) -> None:
        self.assertEqual(
            self.asserted_profile,
            p2p_skill_profile.PROFILE_FRONTEND_REACT,
        )

    def test_release_ships_the_curated_pack(self) -> None:
        for skill in PACK_SKILLS:
            self.assertIn(skill, package_release.RELEASE_SKILLS, skill)
            self.assertTrue(
                (self.stage / ".agents" / "skills" / skill / "SKILL.md").is_file(), skill
            )

    def test_synthetic_project_receives_nested_references(self) -> None:
        skills = self.project / ".agents" / "skills"
        nested = (
            "react-best-practices/rules/async-parallel.md",
            "react-best-practices/rules/rerender-memo.md",
            "composition-patterns/rules/architecture-compound-components.md",
            "frontend-code-review/references/output-format.md",
            "frontend-code-review/examples/good-review.md",
            "frontend-design/upstream-frontend-design-v2.md",
            "frontend-design/references/accessibility-checklist.md",
            "frontend-design/scripts/contrast-checker.py",
        )
        for relative in nested:
            self.assertTrue((skills / relative).is_file(), relative)

    def test_repo_scoped_executor_discovers_entrypoints(self) -> None:
        # Repo-scoped: only the synthetic project tree is readable here.
        skills = self.project / ".agents" / "skills"
        discovered: dict[str, str] = {}
        for entry in sorted(skills.iterdir()):
            skill_md = entry / "SKILL.md"
            if entry.is_dir() and skill_md.is_file():
                text = skill_md.read_text(encoding="utf-8")
                self.assertTrue(text.startswith("---\n"), entry.name)
                discovered[entry.name] = text
        for skill in PACK_SKILLS:
            self.assertIn(skill, discovered, f"entrypoint not discoverable: {skill}")
            self.assertIn("description:", discovered[skill], skill)

    def test_doctor_validates_packaged_skills(self) -> None:
        for skill in PACK_SKILLS:
            self.assertIn(skill, p2p_doctor.EXPECTED_SKILLS, skill)
        report = p2p_doctor.Report()
        p2p_doctor.check_skills(self.stage, report)
        failures = [item for item in report.items if item["level"] == "FAIL"]
        self.assertEqual(failures, [], f"doctor failures: {failures}")
        self.assertTrue(
            any(item["check"] == "skills-count" and item["level"] == "PASS"
                for item in report.items),
            "doctor skills-count did not PASS",
        )


class NoParallelArchitectureTests(unittest.TestCase):
    """§11F: no second router/registry/package-manager/daemon/state store."""

    @classmethod
    def setUpClass(cls) -> None:
        changed: set[str] = set()
        status = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "status", "--porcelain", "--untracked-files=all"],
            capture_output=True, text=True, check=False,
        )
        for line in status.stdout.splitlines():
            if not line.strip():
                continue
            entry = line[3:]
            if " -> " in entry:  # renames contribute both sides
                changed.update(part.strip() for part in entry.split(" -> "))
            else:
                changed.add(entry.strip().strip('"'))
        branch_diff = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "diff", "--name-only", "origin/main...HEAD", "--"],
            capture_output=True, text=True, check=False,
        )
        changed.update(
            line.strip() for line in branch_diff.stdout.splitlines() if line.strip()
        )
        cls.changed = sorted(changed)

    def test_change_set_contains_only_allowed_surfaces(self) -> None:
        allowed_prefixes = (
            ".agents/skills/",
            ".claude/skills/",
            ".p2p/system/.agents/skills/",
            "AGENTS.md",
            "CLAUDE.md",
            "scripts/package_release.py",
            "scripts/doctor.py",
            "governance/research-adoption-ledger.json",
            "docs/RESEARCH-ADOPTION-LEDGER.md",
            "docs/p2p-development/research/P2P-FRONTEND-UPSTREAM-INTAKE-01.md",
            "tests/test_p2p_frontend_upstream_intake_01.py",
            # Issue #254 Arena FAST_CANARY runtime enforcement. It extends the
            # existing Control Tower prompt/session lifecycle, the existing
            # MODEL_CANARY_GATE_V1 / OWNER_CONTINUATION_GATE_V1 policy, and the
            # existing execution ledger. No second Control Tower, router,
            # daemon, scheduler, benchmark service, score database, telemetry
            # platform, project registry, or parallel state store is created.
            "scripts/p2p_control_tower.py",
            "scripts/generate_arena_canary_proofs.py",
            ".p2p/system/p2p_capabilities/control_tower_handoff.py",
            ".p2p/system/p2p_capabilities/owner_goal.py",
            "tests/test_p2p_arena_canary_runtime.py",
            "tests/test_p2p_arena_canary_baseline_gap.py",
            "tests/test_p2p_arena_canary_install_inheritance.py",
            "tests/test_p2p_owner_goal_one_command.py",
            "docs/p2p-development/CONTROL-TOWER-SESSION-HANDOFF.md",
            "evidence/p2p-arena-canary-runtime-254/",
            # Tower-directed same-PR repair (PR #211): hermeticize the
            # control-tower context-assembly fixtures against ambient repo
            # state (P2P_PROJECT_ROOT isolation; zero production changes).
            "tests/test_p2p_control_tower_context_assembly.py",
            # PR #214 install-time project-fit capability provisioning. This
            # workstream owns stack-evidence -> packaged skill profile
            # selection at install time; it is not an upstream intake surface
            # and adds no router, registry, daemon, or network fetcher.
            ".github/workflows/p2p-shield-ci-slice.yml",
            "docs/p2p-development/P2P-DEVELOPMENT-CHARTER.md",
            "docs/p2p-development/P2P-PROJECT-BOOTSTRAP.md",
            "install.sh",
            "install.ps1",
            "scripts/p2p_skill_profile.py",
            "tests/test_p2p_project_fit_capability_provisioning.py",
            # Issue #224 bounded web/browser reverse evidence foundation. It
            # extends the existing single capability registry with four
            # declared routes plus one data-only post-route reference bridge;
            # it adds no second router, registry, daemon, service, installer,
            # MCP registration, or network/runtime activation.
            ".p2p/system/p2p_capabilities/capabilities.json",
            ".p2p/system/p2p_capabilities/web_reverse_reference.py",
            "docs/plans/2026-09-21-p2p-web-reverse-foundation-01/",
            "tests/test_p2p_web_reverse_reference.py",
            ".github/workflows/web-reverse-foundation-focused.yml",
            # Issue #293 capability-drift revalidation sweep. The helper is a
            # deterministic read-only evidence classifier over the existing
            # capability index; it creates no router, registry, daemon,
            # scheduler, execution path, network probe service, or second
            # state store. Only the exact Issue-#293 surfaces are permitted.
            "scripts/p2p_capability_drift_sweep.py",
            "tests/test_p2p_capability_drift_sweep.py",
            "docs/p2p-development/capability-ledger/capability-drift-sweep.json",
            "docs/p2p-development/capability-ledger/capability-index.json",
            "docs/p2p-development/reports/P2P-CAPABILITY-DRIFT-SWEEP-01-REPORT.md",
            "governance/p2p-development-roadmap.json",
            "docs/P2P-DEVELOPMENT-ROADMAP.md",
            "docs/p2p-development/current-roadmap.md",
            "reports/planner/P2P-PLANNER-RUN-10.json",
            # Issue #298 skill-consumption wire. Reuses the existing canonical
            # capability registry + single router; adds one bounded
            # consumption module and exact source-bound host receipts.
            ".agents/skills/scope-reality-check/",
            ".p2p/system/p2p_capabilities/skill_consumption.py",
            ".p2p/system/p2p_capabilities/capability_intelligence.py",
            ".p2p/system/p2p_capabilities/p2p_skill_eligibility.py",
            ".p2p/system/p2p_capabilities/p2p_fw01_loop.py",
            ".p2p/system/p2p_capabilities/control_tower_handoff.py",
            "tests/test_p2p_skill_consumption_wire.py",
            # Issue #308 extends the EXISTING read-only Quality Intelligence
            # post-execution surface. No new evaluator service/store/router.
            ".p2p/system/p2p_capabilities/quality_intelligence.py",
            # Issue #309 extends the EXISTING portable-law projector and
            # managed-project sync wrapper so repo-scoped executors can read a
            # bounded source-bound operator-skill projection from the target
            # repository. No second router, registry, daemon, scheduler, or
            # background sync service is introduced.
            "scripts/p2p_portable_law_projection.py",
            "scripts/p2p_sync_managed_projects.py",
            "tests/test_p2p_portable_law_projection.py",
            "tests/test_p2p_self_law_propagation_and_fast_sync.py",
            # Owner-directed Anvien retirement: bounded policy/install surfaces
            # only. No replacement router/index/daemon/provider is introduced.
            ".p2p/system/AGENTS.md",
            ".p2p/system/CLAUDE.md",
            ".p2p/system/.claude/skills/.claude-skill-manifest.json",
            "docs/p2p-development/P2P-AGENTS-INSTALL.md",
            # Issue #327 prompt-writer skill routing extends the existing
            # Supreme-Law / prompt-serialization / portable-projection path.
            # These are policy/test surfaces, not a second router or registry.
            "docs/p2p-development/P2P-OPERATIONS-NOTEBOOK.md",
            "tests/test_p2p_prompt_serialization_contract.py",
            "scripts/check_instruction_contract.py",
        )
        forbidden_fragments = (
            "router", "registry", "daemon", "sync", "installer", "package_manager",
            "orchestrat", "scheduler", "manifest",
        )
        # Fully vendored upstream units: their (upstream-owned) filenames are
        # governed by the intake-report matrix + blob verification, not by the
        # P2P-authored parallel-architecture smell check (e.g. upstream
        # `async-*.md` rules or `nextjs-app-router.md` would false-positive).
        vendored_unit_dirs = (
            "react-best-practices/",
            "composition-patterns/",
            "frontend-code-review/",
            "baseline-ui/",
            "UI-animation-design/find-animation-opportunities/",
        )
        vendored_unit_files = {
            "frontend-design/upstream-frontend-design-v2.md",
            "frontend-design/references/accessibility-checklist.md",
            "frontend-design/scripts/contrast-checker.py",
            "frontend-design/LICENSE.txt",
            "frontend-design/LICENSE-APACHE-2.0.txt",
            "frontend-design/LICENSE-GITHUB-MIT.txt",
            "frontend-design/THIRD_PARTY_NOTICES.md",
        }
        skill_roots = (
            ".agents/skills/",
            ".claude/skills/",
            ".p2p/system/.agents/skills/",
        )
        violations = []
        for path in self.changed:
            if path.startswith(".tmp/") or "/__pycache__/" in path:
                continue
            if not path.startswith(allowed_prefixes):
                violations.append(f"unexpected surface: {path}")
                continue
            lowered = path.lower()
            is_vendored_bytes = any(
                path == root + leaf
                for root in skill_roots
                for leaf in vendored_unit_files
            ) or any(
                path.startswith(root + unit)
                for root in skill_roots
                for unit in vendored_unit_dirs
            )
            if path.endswith(".py") and path not in {
                "scripts/package_release.py",
                "scripts/doctor.py",
                "tests/test_p2p_frontend_upstream_intake_01.py",
                # Tower-directed same-PR repair (PR #211): hermeticity-only.
                "tests/test_p2p_control_tower_context_assembly.py",
                # PR #214: the single deterministic project-fit profile
                # selector shared by install.sh and install.ps1.
                "scripts/p2p_skill_profile.py",
                "tests/test_p2p_project_fit_capability_provisioning.py",
                # Issue #224: a data-only post-route reference bridge plus its
                # focused test. The bridge holds pins, license boundaries and
                # fail-closed flags; it routes nothing and executes nothing.
                ".p2p/system/p2p_capabilities/web_reverse_reference.py",
                "tests/test_p2p_web_reverse_reference.py",
                ".agents/skills/frontend-design/scripts/contrast-checker.py",
                ".claude/skills/frontend-design/scripts/contrast-checker.py",
                ".p2p/system/.agents/skills/frontend-design/scripts/contrast-checker.py",
                # Issue #254: Arena FAST_CANARY runtime enforcement extends the
                # existing Control Tower prompt/session lifecycle and its
                # existing execution ledger. No new capability module, router,
                # daemon, scheduler, or second state store is introduced.
                "scripts/p2p_control_tower.py",
                ".p2p/system/p2p_capabilities/control_tower_handoff.py",
                ".p2p/system/p2p_capabilities/owner_goal.py",
                "tests/test_p2p_arena_canary_runtime.py",
                "tests/test_p2p_arena_canary_baseline_gap.py",
                "tests/test_p2p_arena_canary_install_inheritance.py",
                "tests/test_p2p_owner_goal_one_command.py",
                "scripts/generate_arena_canary_proofs.py",
                # Issue #293 capability-drift revalidation sweep: the bounded
                # deterministic read-only audit helper plus its focused test.
                "scripts/p2p_capability_drift_sweep.py",
                "tests/test_p2p_capability_drift_sweep.py",
                # Issue #298: one bounded consumption seam plus modifications
                # to existing selection/eligibility/FW01/Control Tower paths.
                ".p2p/system/p2p_capabilities/skill_consumption.py",
                ".p2p/system/p2p_capabilities/capability_intelligence.py",
                ".p2p/system/p2p_capabilities/p2p_skill_eligibility.py",
                ".p2p/system/p2p_capabilities/p2p_fw01_loop.py",
                ".p2p/system/p2p_capabilities/control_tower_handoff.py",
                "tests/test_p2p_skill_consumption_wire.py",
                # Issue #308: existing read-only post-execution Quality
                # Intelligence surface; no new runtime authority.
                ".p2p/system/p2p_capabilities/quality_intelligence.py",
                # Issue #309: existing foreground projector/sync surfaces.
                "scripts/p2p_portable_law_projection.py",
                "scripts/p2p_sync_managed_projects.py",
                "tests/test_p2p_portable_law_projection.py",
                "tests/test_p2p_self_law_propagation_and_fast_sync.py",
                # Issue #327 adds regression coverage to the existing
                # prompt-serialization contract; no executable capability is added.
                "tests/test_p2p_prompt_serialization_contract.py",
                # Owner-directed Anvien retirement updates the EXISTING
                # static instruction contract checker; no runtime is added.
                "scripts/check_instruction_contract.py",
            }:
                violations.append(f"unexpected python surface: {path}")
            issue_309_existing_transport_surfaces = {
                "scripts/p2p_portable_law_projection.py",
                "scripts/p2p_sync_managed_projects.py",
                "tests/test_p2p_portable_law_projection.py",
                "tests/test_p2p_self_law_propagation_and_fast_sync.py",
            }
            if (
                path not in issue_309_existing_transport_surfaces
                and not is_vendored_bytes
                and any(fragment in lowered for fragment in forbidden_fragments)
            ):
                if "skill-manifest" not in lowered and "RESEARCH-ADOPTION-LEDGER" not in path:
                    violations.append(f"parallel-architecture smell: {path}")
        self.assertEqual(violations, [], "\n".join(violations))

    def test_no_new_executable_capability_modules(self) -> None:
        # Issue #224: exactly one new capability-package module is permitted,
        # and only as the bounded data-only reference bridge. It exposes pins,
        # license boundaries and fail-closed flags; it contains no router,
        # executor, installer, network or subprocess primitive. Any other new
        # `.py` under `p2p_capabilities/` still fails closed.
        permitted_capability_modules = {
            ".p2p/system/p2p_capabilities/web_reverse_reference.py",
            # Issue #254 modifies the EXISTING Control Tower handoff module
            # instead of adding a parallel capability module.
            ".p2p/system/p2p_capabilities/control_tower_handoff.py",
            ".p2p/system/p2p_capabilities/owner_goal.py",
            # Issue #298: bounded skill-consumption composition seam. It calls
            # the existing router and canonical registry; it is not a router,
            # registry, scheduler, daemon, or second state store.
            ".p2p/system/p2p_capabilities/skill_consumption.py",
            ".p2p/system/p2p_capabilities/capability_intelligence.py",
            ".p2p/system/p2p_capabilities/p2p_skill_eligibility.py",
            ".p2p/system/p2p_capabilities/p2p_fw01_loop.py",
            # Issue #308 modifies the EXISTING read-only Quality Intelligence
            # module instead of creating a second evaluator/learning system.
            ".p2p/system/p2p_capabilities/quality_intelligence.py",
        }
        for path in self.changed:
            self.assertFalse(
                path.startswith(".p2p/system/p2p_capabilities/")
                and path.endswith(".py")
                and path not in permitted_capability_modules,
                f"new capability module: {path}",
            )
            self.assertFalse(
                path.startswith("scripts/") and path.endswith(".py")
                and path not in {
                    "scripts/package_release.py",
                    "scripts/doctor.py",
                    # PR #214: one deterministic profile selector consumed by
                    # both installers. It reads packaged skill names only and
                    # exposes no domain/source-selection surface.
                    "scripts/p2p_skill_profile.py",
                    # Issue #254: the EXISTING foreground Control Tower CLI is
                    # extended with FAST_CANARY trigger, ingest grading and the
                    # Owner-continuation command. It adds no new entrypoint.
                    "scripts/p2p_control_tower.py",
                    # Issue #254: evidence generator for the generated Arena
                    # prompt proofs. It reads and prints; it routes nothing.
                    "scripts/generate_arena_canary_proofs.py",
                    # Issue #293 capability-drift revalidation sweep. The
                    # helper is a deterministic read-only evidence classifier
                    # over the existing capability index; it creates no
                    # router, registry, daemon, scheduler, execution path,
                    # network probe service, or second state store.
                    "scripts/p2p_capability_drift_sweep.py",
                    # Issue #309 modifies two EXISTING foreground transport
                    # scripts. Neither is a new executor/router/service.
                    "scripts/p2p_portable_law_projection.py",
                    "scripts/p2p_sync_managed_projects.py",
                    # Owner-directed Anvien retirement updates the EXISTING
                    # static instruction contract checker; no new executable
                    # capability/runtime path is created.
                    "scripts/check_instruction_contract.py",
                },
                f"new script surface: {path}",
            )


class RoutingBoundaryTests(unittest.TestCase):
    """§11I/J: backend-only stays clean; p2p-uiux untouched by this task."""

    def test_backend_only_avoids_frontend_loading(self) -> None:
        hub = (CANONICAL / "frontend-development" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Backend-only task: load NOTHING", hub)
        design = (CANONICAL / "frontend-design" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Backend-only", design)
        doctor_text = (CANONICAL / "react-doctor" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Backend-only work never loads this skill", doctor_text)

    def test_p2p_uiux_skill_untouched(self) -> None:
        for argv in (
            ["status", "--porcelain", "--", ".agents/skills/p2p-uiux/SKILL.md"],
            ["diff", "HEAD", "--name-only", "--", ".agents/skills/p2p-uiux/SKILL.md"],
        ):
            result = subprocess.run(
                ["git", "-C", str(REPO_ROOT), *argv],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(
                result.stdout.strip(), "",
                f"p2p-uiux SKILL.md must stay untouched (git {' '.join(argv)})",
            )

    def test_progressive_disclosure_markers(self) -> None:
        hub = (CANONICAL / "frontend-development" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Do not make every UI task load every frontend skill", hub)


class ResearchLedgerBatchTests(unittest.TestCase):
    """Ledger batch RA-EXT-082..RA-EXT-091: durable, unique, valid."""

    REQUIRED_RECORD_FIELDS = (
        "research_id", "source_name", "source_type", "source_reference",
        "source_version_or_commit", "provenance_status", "research_summary",
        "selected_ideas", "rejected_ideas", "p2p_translation", "status",
        "evidence_pointers", "last_reviewed_at",
    )

    @classmethod
    def setUpClass(cls) -> None:
        cls.ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
        cls.records = {r["research_id"]: r for r in cls.ledger["records"]}
        cls.vocab = set(cls.ledger["status_vocabulary"])

    def test_no_duplicate_research_ids(self) -> None:
        ids = [r["research_id"] for r in self.ledger["records"]]
        self.assertEqual(len(ids), len(set(ids)), "duplicate research_id in ledger")

    def test_batch_records_present_exactly_once(self) -> None:
        for rid in BATCH_IDS:
            self.assertIn(rid, self.records, f"missing ledger record: {rid}")

    def test_batch_statuses_use_ledger_vocabulary(self) -> None:
        for rid in BATCH_IDS:
            self.assertIn(self.records[rid]["status"], self.vocab, rid)

    def test_batch_records_provenance_complete(self) -> None:
        for rid in BATCH_IDS:
            record = self.records[rid]
            for field in self.REQUIRED_RECORD_FIELDS:
                self.assertIn(field, record, f"{rid} missing field {field}")
            self.assertTrue(record["source_reference"].startswith("https://github.com/"))
            self.assertTrue(record["source_version_or_commit"].strip())
            self.assertTrue(record["research_summary"].strip())

    def test_rights_recorded_per_repo(self) -> None:
        for rid in BATCH_IDS:
            blob = json.dumps(self.records[rid]).lower()
            self.assertTrue(
                "mit" in blob or "apache-2.0" in blob or "rights-unspecified" in blob,
                f"{rid} has no license/rights statement",
            )

    def test_batch_shas_match_observed_upstream(self) -> None:
        expected = {
            "RA-EXT-082": UPSTREAM_SHAS["vercel-labs/agent-skills"],
            "RA-EXT-083": UPSTREAM_SHAS["PracticalSwan/agent-skills"],
            "RA-EXT-084": UPSTREAM_SHAS["DNM03/frontend-code-review"],
            "RA-EXT-085": UPSTREAM_SHAS["ibelick/ui-skills"],
            "RA-EXT-086": UPSTREAM_SHAS["millionco/react-doctor"],
            "RA-EXT-087": UPSTREAM_SHAS["pbakaus/impeccable"],
            "RA-EXT-088": UPSTREAM_SHAS["microsoft/skills"],
            "RA-EXT-089": UPSTREAM_SHAS["emilkowalski/skills"],
            "RA-EXT-090": UPSTREAM_SHAS["vercel-labs/design-systems-to-agent-skills"],
            "RA-EXT-091": UPSTREAM_SHAS["TanStack/table"],
        }
        for rid, sha in expected.items():
            self.assertIn(sha, self.records[rid]["source_version_or_commit"], rid)

    def test_ledger_md_projection_documents_batch(self) -> None:
        text = LEDGER_MD_PATH.read_text(encoding="utf-8")
        for rid in BATCH_IDS:
            self.assertIn(rid, text, f"md projection missing {rid}")

    def test_durable_report_exists_with_matrix_and_shas(self) -> None:
        text = REPORT_PATH.read_text(encoding="utf-8")
        for sha in UPSTREAM_SHAS.values():
            self.assertIn(sha, text, f"report missing upstream SHA {sha[:12]}")
        for marker in (
            "COPY_AS_IS", "REFERENCE_ONLY", "DEFER",
            "UPSTREAM_REPO", "P2P_TARGET",
        ):
            self.assertIn(marker, text, f"report missing matrix marker: {marker}")


if __name__ == "__main__":
    unittest.main()
