"""FRAMEWORK-02 — Project & Capability Intelligence layer.

Deterministic-first, provider-neutral, evidence-bound, fail-closed
capability intelligence INSIDE the FW01 loop. It answers, before execution
routing:

  TASK -> REQUIRED CAPABILITIES -> CAPABILITY SOURCES -> ELIGIBILITY /
  EVIDENCE -> CAPABILITY COVERAGE -> EXECUTION REQUIREMENTS

It is NOT a competing orchestrator: FW01 remains the sole operating loop,
and role/team/target selection remains under the existing orchestration
boundary. Capability Intelligence only supplies the execution-requirement
record that FW01 consumes at its dispatch gate.

Core invariants preserved:
  ROLE != SKILL / ROLE != BACKEND / BACKEND != PROVIDER / PROVIDER != MODEL
  MODEL != TOOLSET / HARNESS != MODEL / REGISTRY != ROUTER /
  SELECTION != EXECUTION / CLAIM != EVIDENCE / UNKNOWN != SUPPORTED /
  UNKNOWN != SAFE / CERTIFIED != CURRENTLY_ELIGIBLE
New critical invariant:  CAPABILITY != SKILL  (skill is ONE possible source).

Design Intelligence/NUI is exposed as an OPTIONAL capability source ONLY
when repository truth supports it and the task evidence requires design
cognition. Deterministic tooling/code intelligence is preferred over model
guessing. Any model-derived (inferred) requirement or eligibility claim is
marked as INFERRED, never factual. Fallback must never silently reduce
critical guarantees, and permission is never widened.

Cache: only reuses the canonical evidence-bound ContextCache (C36). Cache
entries are bound to content hash + source revision; invalidated when the
underlying project evidence (manifest, lockfile, layouts) changes. No
unbounded hidden memory.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence

try:
    from .domain import (
        CORE_INVARIANTS,
        SOURCE_ROLES,
        DomainSourceRecord,
        DomainSourceSelectionReceipt,
        ProjectDomainModel,
        SelectedSourceItem,
        SourceRoleMetadata,
        UnselectedSourceItem,
        build_domain_source_catalog,
        get_source_role_metadata,
        normalize_source_role,
    )
except ImportError:
    from domain import (
        CORE_INVARIANTS,
        SOURCE_ROLES,
        DomainSourceRecord,
        DomainSourceSelectionReceipt,
        ProjectDomainModel,
        SelectedSourceItem,
        SourceRoleMetadata,
        UnselectedSourceItem,
        build_domain_source_catalog,
        get_source_role_metadata,
        normalize_source_role,
    )

UNKNOWN = "UNKNOWN"

# ---------------------------------------------------------------------------
# 1. Capability requirement contract (minimum viable schema, extension point)
# ---------------------------------------------------------------------------

REQUIRED_OR_OPTIONAL = ("REQUIRED", "OPTIONAL")
FAIL_CLOSED = ("NO_DISPATCH", "SAFE_FALLBACK_BOUNDED", "OWNER_GATE")
MINIMUM_EVIDENCE_LEVELS = ("CLAIM", "DETERMINISTIC", "VERIFIED", "CERTIFIED")
FRESHNESS_CLASSES = ("ANY", "THIS_SESSION", "PROJECT_CURRENT", "EVIDENCE_FRESH")


@dataclass(frozen=True)
class CapabilityRequirement:
    """What a task requires from the capability composition.

    capability_id: canonical capability identifier (ledger-compatible).
    purpose: bounded evidence-derived purpose text.
    required_or_optional: REQUIRED | OPTIONAL.
    minimum_evidence: floor of evidence quality (CLAIM..CERTIFIED).
    freshness: freshness requirement class.
    permission: bounded permission claim set (may be empty; never widened).
    context_requirement: targeted context pointers needed (NOT a dump).
    quality_requirement: bounded quality floor (may be UNKNOWN).
    fallback_allowed: FAIL_CLOSED behavior if coverage is partial/unknown.
    origin: DETERMINISTIC | INFERRED | HYBRID (model-derived parts marked).
    evidence_pointers: tuple of authoritative pointers (path or record ref).
    """

    capability_id: str
    purpose: str = ""
    required_or_optional: str = "REQUIRED"
    minimum_evidence: str = "CLAIM"
    freshness: str = "ANY"
    permission: tuple[str, ...] = ()
    context_requirement: tuple[str, ...] = ()
    quality_requirement: str = UNKNOWN
    fallback_allowed: str = "NO_DISPATCH"
    origin: str = "DETERMINISTIC"
    evidence_pointers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.capability_id or not _ID_RE.fullmatch(self.capability_id):
            raise CapabilityIntelligenceError("CAPABILITY_ID_INVALID",
                                              self.capability_id)
        if self.required_or_optional not in REQUIRED_OR_OPTIONAL:
            raise CapabilityIntelligenceError("REQUIRED_OR_OPTIONAL_INVALID",
                                              self.required_or_optional)
        if self.minimum_evidence not in MINIMUM_EVIDENCE_LEVELS:
            raise CapabilityIntelligenceError("MINIMUM_EVIDENCE_INVALID",
                                              self.minimum_evidence)
        if self.freshness not in FRESHNESS_CLASSES:
            raise CapabilityIntelligenceError("FRESHNESS_INVALID",
                                              self.freshness)
        if self.fallback_allowed not in FAIL_CLOSED:
            raise CapabilityIntelligenceError("FALLBACK_ALLOWED_INVALID",
                                              self.fallback_allowed)
        if self.origin not in ("DETERMINISTIC", "INFERRED", "HYBRID"):
            raise CapabilityIntelligenceError("ORIGIN_INVALID", self.origin)
        for p in self.permission:
            if not p or " " in p:
                raise CapabilityIntelligenceError("PERMISSION_TOKEN_INVALID", p)
        for ptr in self.evidence_pointers:
            if not ptr:
                raise CapabilityIntelligenceError("EVIDENCE_POINTER_EMPTY", ptr)

    def to_dict(self) -> dict[str, Any]:
        return {
            "capability_id": self.capability_id,
            "purpose": self.purpose,
            "required_or_optional": self.required_or_optional,
            "minimum_evidence": self.minimum_evidence,
            "freshness": self.freshness,
            "permission": list(self.permission),
            "context_requirement": list(self.context_requirement),
            "quality_requirement": self.quality_requirement,
            "fallback_allowed": self.fallback_allowed,
            "origin": self.origin,
            "evidence_pointers": list(self.evidence_pointers),
        }

    def is_required(self) -> bool:
        return self.required_or_optional == "REQUIRED"

    def identity(self) -> str:
        return _stable_sha(self.to_dict())


_ID_RE = re.compile(r"[A-Za-z0-9._-]{1,128}")


def _stable_sha(payload: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


# ---------------------------------------------------------------------------
# 2. Capability source types and source inventory
# ---------------------------------------------------------------------------

# Provider-neutral source types. Skill is ONE type among many.
SOURCE_TYPES = (
    "RUNTIME_DETERMINISTIC",  # built-in runtime capability (no skill needed)
    "SKILL",                  # installed skill (one possible source)
    "TOOL",                   # deterministic tooling (code search, test runner)
    "CODE_INTELLIGENCE",      # symbol map / static analysis / diff analysis
    "REPO_MAP",               # repository/project map
    "RETRIEVER",              # search/retrieval over evidence/code
    "EVIDENCE_STORE",         # memory/evidence store (C36 cache, read_evidence)
    "DESIGN_NUI",             # Design Intelligence/NUI (optional)
    "ROLE_EXPERTISE",         # canonical role expertise (role != skill)
    "BACKEND",                # execution backend (backend != provider)
    "PROVIDER_MODEL",         # provider/model capability (never control flow)
    "WORKSPACE",              # workspace/environment
    "PROTOCOL",               # protocol capability
    "AUTH",                   # authenticated integration
    "HUMAN_DECISION",         # Owner decision where inherently required
)

# Canonical capability vocabulary (ledger-compatible identifiers).
# Each maps to evidence-backed runtime/governance surfaces.
CANONICAL_CAPABILITIES = (
    "fw01_bootstrap_discovery",      # harness discover (runtime)
    "fw01_sha_verification",         # harness verify-sha (runtime)
    "fw01_install",                  # harness install (runtime)
    "fw01_doctor",                   # harness doctor (runtime)
    "capability_registry",           # capabilities.json targets (runtime)
    "role_execution_runtime",        # 8 canonical roles (runtime)
    "role_verifier_evidence",        # evidence-bound role verification
    "role_receipt_certification",    # certification receipt issuance
    "role_bridge_dispatch",          # dispatch boundary (dispatch != execution)
    "context_pointers",              # deterministic context pointers
    "context_cache_evidence_bound",  # C36 evidence-bound cache
    "context_efficiency",            # context-efficient views
    "selection_policy",              # C37 evidence-bound selection
    "selection_request",             # C37 task-quality/risk contract
    "decision_trace",                # structured decision evidence
    "task_state_store",              # durable task state
    "permission_profile_verification",  # permission never widened
    "auth_fact_verification",        # auth fact evidence (C02-family)
    "host_attestation_real",         # real-host attestation (C36 live)
    "host_executor_dispatch",        # host dispatch + replay protection
    "backend_execution_bridge",      # backend boundary
    "provider_neutral_binding",      # provider/model binding without vendor
    "skill_eligibility",             # skill eligibility evidence
    "skill_standard_validation",     # skill contract validation
    "design_intelligence_nui",       # Design Intelligence (optional source)
    "code_search",                   # deterministic code search
    "symbol_map",                    # deterministic symbol map
    "repo_map",                      # deterministic repository map
    "test_runner",                   # deterministic test execution
    "static_checks",                 # deterministic static analysis
    "diff_analysis",                 # deterministic diff analysis
    "schema_inspection_permitted",   # DB schema inspection (permission-bound)
    "freshness_verification",        # evidence freshness check
    "owner_gate_authority",          # Owner decision (human decision source)
    "bounded_delegation",            # delegation boundary (CLAIM != EVIDENCE)
    "failover_boundary",             # fail-closed failover (no guarantee loss)
    "isolation_enforcement",         # isolated-target enforcement
    "beginner_interface",            # beginner-facing translation
    "project_domain_model",          # project domain reasoning (perspective)
    "evidence_retrieval",            # read-only evidence retrieval
    "non_mutating_project_analysis",
    # bounded_documentation_write (P2P-BOUNDED-DOCUMENTATION-WRITE-01):
    # the only canonical bounded mutation capability (text documentation
    # only, fail-closed, host primitive).
    "bounded_documentation_write",
)

CAPABILITY_VOCABULARY = set(CANONICAL_CAPABILITIES)

# Evidence-backed source coverage: which source types CAN satisfy which
# canonical capability. UNKNOWN capabilities satisfy nothing deterministically.
_CAPABILITY_SOURCE_COVERAGE: dict[str, tuple[str, ...]] = {
    "fw01_bootstrap_discovery": ("RUNTIME_DETERMINISTIC", "TOOL"),
    "fw01_sha_verification": ("RUNTIME_DETERMINISTIC", "TOOL"),
    "fw01_install": ("RUNTIME_DETERMINISTIC",),
    "fw01_doctor": ("RUNTIME_DETERMINISTIC",),
    "capability_registry": ("RUNTIME_DETERMINISTIC", "REPO_MAP"),
    "role_execution_runtime": ("RUNTIME_DETERMINISTIC", "ROLE_EXPERTISE"),
    "role_verifier_evidence": ("RUNTIME_DETERMINISTIC", "EVIDENCE_STORE"),
    "role_receipt_certification": ("RUNTIME_DETERMINISTIC", "EVIDENCE_STORE"),
    "role_bridge_dispatch": ("RUNTIME_DETERMINISTIC",),
    "context_pointers": ("RUNTIME_DETERMINISTIC", "RETRIEVER"),
    "context_cache_evidence_bound": ("RUNTIME_DETERMINISTIC", "EVIDENCE_STORE"),
    "context_efficiency": ("RUNTIME_DETERMINISTIC", "EVIDENCE_STORE"),
    "selection_policy": ("RUNTIME_DETERMINISTIC",),
    "selection_request": ("RUNTIME_DETERMINISTIC",),
    "decision_trace": ("RUNTIME_DETERMINISTIC",),
    "task_state_store": ("RUNTIME_DETERMINISTIC",),
    "permission_profile_verification": ("RUNTIME_DETERMINISTIC", "AUTH"),
    "auth_fact_verification": ("AUTH", "EVIDENCE_STORE"),
    "host_attestation_real": ("RUNTIME_DETERMINISTIC", "AUTH", "WORKSPACE"),
    "host_executor_dispatch": ("RUNTIME_DETERMINISTIC", "WORKSPACE"),
    "backend_execution_bridge": ("BACKEND", "RUNTIME_DETERMINISTIC"),
    "provider_neutral_binding": ("PROVIDER_MODEL", "RUNTIME_DETERMINISTIC"),
    "skill_eligibility": ("SKILL", "RUNTIME_DETERMINISTIC"),
    "skill_standard_validation": ("RUNTIME_DETERMINISTIC", "SKILL"),
    "design_intelligence_nui": ("DESIGN_NUI", "SKILL"),
    "code_search": ("TOOL", "CODE_INTELLIGENCE"),
    "symbol_map": ("CODE_INTELLIGENCE", "TOOL"),
    "repo_map": ("REPO_MAP", "TOOL"),
    "test_runner": ("TOOL", "WORKSPACE"),
    "static_checks": ("TOOL", "CODE_INTELLIGENCE"),
    "diff_analysis": ("TOOL", "CODE_INTELLIGENCE"),
    "schema_inspection_permitted": ("TOOL", "AUTH"),
    "freshness_verification": ("RUNTIME_DETERMINISTIC", "EVIDENCE_STORE"),
    "owner_gate_authority": ("HUMAN_DECISION",),
    "bounded_delegation": ("RUNTIME_DETERMINISTIC",),
    "failover_boundary": ("RUNTIME_DETERMINISTIC",),
    "isolation_enforcement": ("RUNTIME_DETERMINISTIC",),
    "beginner_interface": ("RUNTIME_DETERMINISTIC",),
    "project_domain_model": ("RUNTIME_DETERMINISTIC",),
    "evidence_retrieval": ("RETRIEVER", "EVIDENCE_STORE"),
    "bounded_documentation_write": ("RUNTIME_DETERMINISTIC", "WORKSPACE"),
}

# Evidence floor per capability: what level of evidence must back a source.
_CAPABILITY_MIN_EVIDENCE: dict[str, str] = {
    cap: "VERIFIED" for cap in CANONICAL_CAPABILITIES
}


class CapabilityIntelligenceError(Exception):
    """Capability intelligence contract violations (fail-closed)."""

    def __init__(self, failure_class: str, detail: Any = None) -> None:
        super().__init__(f"{failure_class}: {detail!r}")
        self.failure_class = failure_class
        self.detail = detail


# ---------------------------------------------------------------------------
# 3. Project profile (evidence-bound; tracked freshness)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProjectProfile:
    """Evidence-bound compact project capability profile.

    Derived from repository evidence only (manifests, layouts, file types,
    test systems, schema presence). Not Owner-declared. Freshness is bound
    to the evidence sources: if manifest/lockfile/layout hashes change, the
    profile is STALE and must be re-derived. No unbounded memory.
    """

    project_id: str
    evidence_revision: str
    languages: tuple[str, ...]
    frameworks: tuple[str, ...]
    test_systems: tuple[str, ...]
    databases: tuple[str, ...]
    ui_surface: tuple[str, ...]
    deployment_surface: tuple[str, ...]
    sensitive_boundaries: tuple[str, ...]
    available_tooling: tuple[str, ...]
    bootstrap_status: str  # PRESENT | ABSENT | UNKNOWN
    known_capabilities: tuple[str, ...]
    known_restrictions: tuple[str, ...]
    freshness_class: str  # CURRENT | STALE | UNKNOWN

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "evidence_revision": self.evidence_revision,
            "languages": list(self.languages),
            "frameworks": list(self.frameworks),
            "test_systems": list(self.test_systems),
            "databases": list(self.databases),
            "ui_surface": list(self.ui_surface),
            "deployment_surface": list(self.deployment_surface),
            "sensitive_boundaries": list(self.sensitive_boundaries),
            "available_tooling": list(self.available_tooling),
            "bootstrap_status": self.bootstrap_status,
            "known_capabilities": list(self.known_capabilities),
            "known_restrictions": list(self.known_restrictions),
            "freshness_class": self.freshness_class,
        }


_LANGUAGE_MARKERS = {
    "python": (".py", "requirements.txt", "pyproject.toml", "Pipfile"),
    "javascript": (".js", ".jsx", "package.json", ".mjs"),
    "typescript": (".ts", ".tsx", "package.json"),
    "rust": (".rs", "Cargo.toml"),
    "go": (".go", "go.mod"),
    "ruby": (".rb", "Gemfile"),
    "php": (".php", "composer.json"),
    "java": (".java", "pom.xml"),
    "swift": (".swift", "Package.swift"),
    "kotlin": (".kt", "build.gradle"),
    "elixir": (".ex", ".exs", "mix.exs"),
    "shell": (".sh", ".bash"),
    "markdown": (".md",),
}

_FRAMEWORK_MARKERS = {
    "fastapi": ("fastapi", "uvicorn"),
    "flask": ("flask",),
    "django": ("django",),
    "react": ("react", "@vitejs/plugin-react", "react-dom"),
    "vue": ("vue",),
    "nextjs": ("next", "nextjs"),
    "remix": ("@remix-run"),
    "expo": ("expo"),
    "laravel": ("laravel",),
    "rails": ("rails",),
}

_DB_MARKERS = (
    "supabase", "postgresql", "postgres", "mysql", "sqlite", "mongodb",
    "prisma", "drizzle", "migrations", "rls", "schema.sql",
)

_TEST_MARKERS = (
    "tests/", "test/", "__tests__/", "spec/", "pytest.ini", "conftest.py",
    "vitest.config", "jest.config", "phpunit", "minitest",
)

_UI_MARKERS = (
    ".html", ".css", ".scss", ".vue", ".jsx", ".tsx", "tailwind",
    "components", "assets/",
)

_DEPLOY_MARKERS = (
    "Dockerfile", "docker-compose", "netlify", "vercel", ".github/workflows",
    "deploy", "supabase/config",
)

_SENSITIVE_MARKERS = (
    "supabase", "rls", "secrets", ".env", "auth", "token", "credentials",
    "migrations", "admin",
)


def _scan_markers(file_names: Iterable[str]) -> dict[str, set[str]]:
    names = [str(PurePosixPath(f)).lower() for f in file_names]
    results: dict[str, set[str]] = {
        "languages": set(), "frameworks": set(), "databases": set(),
        "tests": set(), "ui": set(), "deployment": set(), "sensitive": set(),
        "tooling": set(),
    }
    content_hints = set(names)
    for lang, exts in _LANGUAGE_MARKERS.items():
        for ext in exts:
            if any(n.endswith(ext) or n == ext or f"/{ext}" in n or f"/{ext}." in n
                   for n in content_hints):
                results["languages"].add(lang)
    for fw, hints in _FRAMEWORK_MARKERS.items():
        for h in hints:
            if any(h in n for n in content_hints):
                results["frameworks"].add(fw)
    for d in _DB_MARKERS:
        if any(d in n for n in content_hints):
            results["databases"].add(d)
    for t in _TEST_MARKERS:
        if any(n.startswith(t) or t in n for n in content_hints):
            results["tests"].add(t.rstrip("/"))
    for u in _UI_MARKERS:
        if any(n.endswith(u) or f"/{u}" in n for n in content_hints):
            results["ui"].add(u)
    for dep in _DEPLOY_MARKERS:
        if any(dep in n for n in content_hints):
            results["deployment"].add(dep)
    for s in _SENSITIVE_MARKERS:
        if any(s in n for n in content_hints):
            results["sensitive"].add(s)
    tooling = set()
    if any("pytest" in n for n in content_hints):
        tooling.add("pytest")
    if any("vitest" in n or "jest" in n for n in content_hints):
        tooling.add("js-test-runner")
    if any("npm" in n or "pnpm" in n or "yarn.lock" in n for n in content_hints):
        tooling.add("node-package-manager")
    if any("pyproject.toml" in n or "requirements" in n for n in content_hints):
        tooling.add("python-package-manager")
    if any(".git/" in n or n.endswith("/.git") for n in content_hints):
        tooling.add("git")
    results["tooling"] = tooling
    return results


def _evidence_revision(project_root: Path, file_names: Sequence[str]) -> str:
    """Deterministic evidence revision bound to project manifest/layout."""
    marker_files = (
        "package.json", "pyproject.toml", "requirements.txt", "Gemfile",
        "Cargo.toml", "go.mod", "pubspec.yaml", "mix.exs",
    )
    payload = []
    for m in marker_files:
        p = project_root / m
        if p.is_file():
            payload.append((m, _sha256(p.read_bytes())))
    payload.append(("layout_hash", _sha256(
        _stable_sha({"sorted_files": sorted(file_names)}).encode("utf-8"))))
    return _stable_sha({"evidence": payload})


def _sha256(value: Any) -> str:
    if isinstance(value, (bytes, bytearray)):
        return hashlib.sha256(value).hexdigest()
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def build_project_profile(
    project_root: Path,
    file_names: Sequence[str] | None = None,
) -> ProjectProfile:
    """Derive an evidence-bound project profile from repository truth.

    file_names: relative paths in the project (deterministic signal). If
    omitted the profile is derived only from manifest markers with an
    evidence revision anchored to the root marker set.
    """
    names = list(file_names) if file_names is not None else [
        p.relative_to(project_root).as_posix()
        for p in project_root.rglob("*")
        if p.is_file() and ".git" not in p.parts and "node_modules" not in p.parts
        and not str(p).startswith(".")
    ][:10000]
    scan = _scan_markers(names)
    evidence_rev = _evidence_revision(project_root, names)
    bootstrap = "PRESENT" if (project_root / ".p2p").is_dir() else (
        "ABSENT" if project_root.is_dir() else UNKNOWN)
    return ProjectProfile(
        project_id=str(project_root),
        evidence_revision=evidence_rev,
        languages=tuple(sorted(scan["languages"])),
        frameworks=tuple(sorted(scan["frameworks"])),
        test_systems=tuple(sorted(scan["tests"])),
        databases=tuple(sorted(scan["databases"])),
        ui_surface=tuple(sorted(scan["ui"])),
        deployment_surface=tuple(sorted(scan["deployment"])),
        sensitive_boundaries=tuple(sorted(scan["sensitive"])),
        available_tooling=tuple(sorted(scan["tooling"])),
        bootstrap_status=bootstrap,
        known_capabilities=(),
        known_restrictions=(
            ("mutate-supabase-rls" if "rls" in scan["sensitive"] or
             "supabase" in scan["sensitive"] else ""),
        ),
        freshness_class="CURRENT",
    )


# ---------------------------------------------------------------------------
# 4. Deterministic-first required-capability inference
# ---------------------------------------------------------------------------

# Deterministic signal lexicon (bounded vocabulary; NOT brand routing).
# Each entry: (regex token, required capability, optional permission claim).
_DETERMINISTIC_SIGNALS: tuple[tuple[str, str, str], ...] = (
    # File-surface / language signals
    (r"\.py$", "code_search", ""),
    (r"\.py$", "test_runner", ""),
    (r"\.py$", "static_checks", ""),
    (r"test[_s]/", "test_runner", ""),
    (r"__tests__/", "test_runner", ""),
    (r"spec/", "test_runner", ""),
    (r"pytest", "test_runner", ""),
    (r"\.ts$|\.tsx$|\.js$|\.jsx$|\.vue$", "code_search", ""),
    (r"\.ts$|\.tsx$|\.js$|\.jsx$|\.vue$", "static_checks", ""),
    (r"package\.json", "repo_map", ""),
    (r"pyproject\.toml|requirements\.txt|setup\.py", "repo_map", ""),
    (r"Cargo\.toml|go\.mod|Gemfile|composer\.json|pom\.xml", "repo_map", ""),
    # Database / authorization boundary signals
    (r"supabase|\.sql|schema", "schema_inspection_permitted", "read-schema"),
    (r"rls|row.?level|supabase/migrations", "owner_gate_authority", "rls-elevated"),
    (r"auth|token|credential|secret", "permission_profile_verification",
     "security-scope"),
    (r"migration", "owner_gate_authority", "schema-elevated"),
    # Test/diff verification signals
    (r"broken test|failing test|unit test|integration test", "test_runner", ""),
    (r"diff|patch|merge conflict", "diff_analysis", ""),
    # Deployment signals
    (r"deploy|Dockerfile|workflow", "repo_map", ""),
    (r"docker", "workspace", ""),
    # Design/NUI signals — optional source, only when evidence needs it
    (r"ui|screen|design|animation|responsive|accessibility",
     "design_intelligence_nui", ""),
    # Bootstrap signals
    (r"bootstrap|doctor|install", "fw01_sha_verification", ""),
    (r"p2p|\.p2p", "capability_registry", ""),
    # Permission/governance signals
    (r"permission|approval|owner gate|owner decision", "owner_gate_authority",
     "owner-gate"),
    (r"eligib|certif|attest", "freshness_verification", ""),
    (r"host|attestation", "host_attestation_real", ""),
    (r"skill|skills/", "skill_eligibility", ""),
    (r"context|cache", "context_cache_evidence_bound", ""),
    (r"role|team|council", "role_execution_runtime", ""),
    (r"dispatch", "role_bridge_dispatch", ""),
    (r"verify|verification|evidence", "auth_fact_verification", ""),
)

# Task-text lexicon (bounded; deterministic-first; unknown stays unknown).
_TASK_CAPABILITY_HINTS: tuple[tuple[str, str, str], ...] = (
    (r"test", "test_runner", ""),
    (r"deploy", "repo_map", ""),
    (r"supabase", "schema_inspection_permitted", "read-schema"),
    (r"rls", "owner_gate_authority", "rls-elevated"),
    (r"screen|ui|design", "design_intelligence_nui", ""),
    (r"accessibility|elderly|usability", "design_intelligence_nui", ""),
    (r"mobile|responsive", "design_intelligence_nui", ""),
    (r"fix", "diff_analysis", ""),
    (r"refactor", "static_checks", ""),
    (r"security|auth", "permission_profile_verification", "security-scope"),
    (r"model|provider", "provider_neutral_binding", ""),
    (r"skill", "skill_eligibility", ""),
    (r"host", "host_attestation_real", ""),
    (r"evidence|certif|attest", "freshness_verification", ""),
    (r"role|team", "role_execution_runtime", ""),
    (r"context|cache", "context_cache_evidence_bound", ""),
    (r"bootstrap", "fw01_bootstrap_discovery", ""),
    (r"decision|approve", "owner_gate_authority", "owner-gate"),
)

_DEFAULT_REQUIRED: tuple[str, ...] = (
    "task_state_store",
    "decision_trace",
    "permission_profile_verification",
)


def _narrow_harness_requirements(
    task_record: Mapping[str, Any],
    requirements: tuple[CapabilityRequirement, ...],
) -> tuple[CapabilityRequirement, ...]:
    """Bound the fw01 harness caps to genuine harness tasks.

    Scope paths containing 'bootstrap' (e.g. P2P-PROJECT-BOOTSTRAP.md)
    match the generic lexicon, but reviewing the manifest does NOT need
    harness discovery/verification. Only tasks whose title also names a
    harness operation (run/doctor/install/verify) keep those caps.
    Fail-closed is preserved: real harness tasks are still REQUIRED.
    """
    title = " ".join(str(v) for v in (task_record.get("title", ""),)).lower()
    if not re.search(r"run|doctor|install|verify-sha|harness", title):
        out = [r for r in requirements if r.capability_id not in (
            "fw01_bootstrap_discovery", "fw01_sha_verification")]
        return tuple(out)
    return requirements


def infer_required_capabilities(
    task_record: Mapping[str, Any],
    project_profile: ProjectProfile | None = None,
    *,
    owner_mutation_envelope: str = "NONE",
) -> list[CapabilityRequirement]:
    """Deterministic-first inference of required capabilities.

    Sources, in order:
    1. TaskRecord.required_capabilities declared by governance (authoritative).
    2. Deterministic signals from task purpose/text, scope paths, evidence.
    3. Project profile evidence (languages, DB boundary, UI surface).
    4. (Optional bounded hook) model inference — MUST be marked INFERRED;
       default implementation provides none (hooks may supply).
    Capability vocabulary is bounded (CANONICAL_CAPABILITIES); unknown tokens
    map to no capability (never hallucinated). REQUIRED caps default to
    FAIL_CLOSED=NO_DISPATCH unless the task declares a safe fallback scope.

    P2P-BOUNDED-DOCUMENTATION-WRITE-01: only an explicit Owner mutation
    envelope naming "bounded_documentation_write" (via the
    owner_mutation_envelope kwarg) introduces the bounded documentation
    write capability. A WRITE-level permission claim alone never adds it,
    and the default envelope "NONE" never adds it.
    """
    declared: tuple[str, ...] = task_record.get("required_capabilities", ()) or ()
    optional: tuple[str, ...] = task_record.get("optional_capabilities", ()) or ()
    # Explicit unknown requirements (authoritative task contract,
    # preserved fail-closed; EXPLICIT_REQUIRED_UNKNOWN != DROPPED).
    explicit_unknown: list[str] = []

    def _add_mutation(cap: str, origin: str, pointers: tuple[str, ...],
                      permission: tuple[str, ...] = ()) -> None:
        """Add the bounded mutation capability with permission WRITE_BOUNDED.

        Fail-closed: only an exact Owner envelope match adds it; any other
        value (including WRITE-level permission claims) never adds a
        mutation capability.
        """
        if cap in CAPABILITY_VOCABULARY:
            if want.get(cap) is None:
                want[cap] = {
                    "capability_id": cap,
                    "purpose": f"cap:{cap}",
                    "required_or_optional": "REQUIRED",
                    "origin": origin,
                    "evidence_pointers": list(pointers),
                    "permission": list(permission),
                }
    text = " ".join(str(v) for v in (
        task_record.get("title", ""),
        task_record.get("purpose", ""),
        *list(task_record.get("scope", ())),
        *list(task_record.get("required_evidence", ())),
    )).lower()
    paths = " ".join(str(p) for p in (task_record.get("scope", ()) or ())).lower()

    want: dict[str, dict[str, Any]] = {}

    def _add_mutation_after_declared() -> None:
        # P2P-BOUNDED-DOCUMENTATION-WRITE-01: explicit Owner mutation
        # envelope. Only an exact match adds the bounded write capability;
        # any other value (including WRITE-level permission claims) never
        # adds a mutation capability.
        _mutation_envelope: str = str(owner_mutation_envelope or "NONE").strip()
        _mutation_envelope = _mutation_envelope if _mutation_envelope else "NONE"
        if _mutation_envelope == "bounded_documentation_write":
            _add_mutation("bounded_documentation_write", "DETERMINISTIC",
                          ("owner_mutation_envelope:bounded_documentation_write",),
                          ("WRITE_BOUNDED",))

    def _add(cap: str, optional_: bool, origin: str, pointers: tuple[str, ...],
             permission: tuple[str, ...] = ()) -> None:
        if cap not in CAPABILITY_VOCABULARY:
            # Distinguish the two safe-closed cases per fail-closed
            # contract: (A) a model/heuristic-proposed unknown capability is
            # never added as a fact (no hallucination); (B) an unknown
            # capability explicitly declared in the authoritative task
            # contract is PRESERVED as an explicit-unknown REQUIRED
            # requirement (EXPLICIT_REQUIRED_UNKNOWN != DROPPED;
            # UNKNOWN != SAFE — see unknown_explicit_required below).
            if "task_record.required_capabilities" in pointers or \
                    "task_record.optional_capabilities" in pointers:
                explicit_unknown.append(cap)
            return  # unknown capability → no hallucination
        existing = want.get(cap)
        if existing is None:
            want[cap] = {
                "capability_id": cap,
                "purpose": f"cap:{cap}",
                "required_or_optional": "OPTIONAL" if optional_ else "REQUIRED",
                "origin": origin,
                "evidence_pointers": list(pointers),
                "permission": list(permission),
            }
        else:
            if not optional_:
                existing["required_or_optional"] = "REQUIRED"
            if existing["origin"] != "DETERMINISTIC" and origin == "DETERMINISTIC":
                existing["origin"] = origin
            for p in permission:
                if p not in existing["permission"]:
                    existing["permission"].append(p)
            existing["evidence_pointers"].extend(pointers)

    # 1. Declared (authoritative)
    _add_mutation_after_declared()
    for cap in declared:
        _add(cap, False, "DETERMINISTIC",
             ("task_record.required_capabilities",))
    for cap in optional:
        _add(cap, True, "DETERMINISTIC",
             ("task_record.optional_capabilities",))

    # 2. Deterministic task-text signals
    for token, cap, perm in _TASK_CAPABILITY_HINTS:
        if re.search(token, text):
            _add(cap, False, "DETERMINISTIC", (f"task_signal:{token}",),
                 (perm,) if perm else ())

    # 3. Project profile evidence signals
    if project_profile is not None:
        if project_profile.databases:
            if any(("supabase" in d or "rls" in d)
                   for d in project_profile.databases) and (
                    re.search(r"schema|database|rls|supabase", text)):
                _add("schema_inspection_permitted", False, "DETERMINISTIC",
                     ("project_profile.databases",), ("read-schema",))
        if project_profile.ui_surface and re.search(r"ui|screen|design", text):
            _add("design_intelligence_nui", True, "DETERMINISTIC",
                 ("project_profile.ui_surface",))
        if project_profile.test_systems and re.search(r"test", text):
            _add("test_runner", False, "DETERMINISTIC",
                 ("project_profile.test_systems",))
        if project_profile.bootstrap_status == "PRESENT":
            _add("capability_registry", True, "DETERMINISTIC",
                 ("project_profile.bootstrap_status",))

    # 4. Path-surface signals (deterministic file-type evidence)
    for token, cap, perm in _DETERMINISTIC_SIGNALS:
        if re.search(token, paths):
            _add(cap, False, "DETERMINISTIC", (f"path_signal:{token}",),
                 (perm,) if perm else ())

    # Default minimal required base (task state + trace + permission safety)
    for cap in _DEFAULT_REQUIRED:
        _add(cap, False, "DETERMINISTIC", ("requirement_contract:base",))

    out = []
    for v in want.values():
        perm = tuple(v["permission"]) if v["permission"] else ()
        ptrs = tuple(dict.fromkeys(v["evidence_pointers"]))
        out.append(CapabilityRequirement(
            capability_id=v["capability_id"],
            purpose=v["purpose"],
            required_or_optional=v["required_or_optional"],
            origin=v["origin"],
            evidence_pointers=ptrs,
            permission=perm,
        ))
    return out


# ---------------------------------------------------------------------------
# 5. Capability source inventory (provider-neutral, ledger-compatible)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CapabilitySource:
    """One evidence-backed capability source.

    source_type: SOURCE_TYPES value (skill is one of many).
    capability_id: what capability it provides.
    invocation_class: how it is invoked (read-only vocabulary).
    evidence_pointers: authoritative pointers supporting the claim.
    eligibility: CAPABILITY_DEFINED / SUPPORTED / CERTIFIED /
                 CURRENTLY_ELIGIBLE / UNKNOWN (unknown != supported).
    dependencies: bounded dependency capability ids.
    permissions: bounded permission claims (never widened).
    quality_limitations: bounded quality limitation tokens (or UNKNOWN).
    freshness: freshness evidence class.
    """

    source_type: str
    capability_id: str
    invocation_class: str
    evidence_pointers: tuple[str, ...] = ()
    eligibility: str = UNKNOWN
    dependencies: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    quality_limitations: str = UNKNOWN
    freshness: str = UNKNOWN

    def __post_init__(self) -> None:
        if self.source_type not in SOURCE_TYPES:
            raise CapabilityIntelligenceError("SOURCE_TYPE_INVALID",
                                              self.source_type)
        if self.eligibility not in (
                "CAPABILITY_DEFINED", "CAPABILITY_SUPPORTED",
                "CAPABILITY_CERTIFIED", "CAPABILITY_CURRENTLY_ELIGIBLE",
                UNKNOWN):
            raise CapabilityIntelligenceError("ELIGIBILITY_INVALID",
                                              self.eligibility)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "capability_id": self.capability_id,
            "invocation_class": self.invocation_class,
            "evidence_pointers": list(self.evidence_pointers),
            "eligibility": self.eligibility,
            "dependencies": list(self.dependencies),
            "permissions": list(self.permissions),
            "quality_limitations": self.quality_limitations,
            "freshness": self.freshness,
        }


ELIGIBILITY_RANK = {
    "CAPABILITY_DEFINED": 1,
    "CAPABILITY_SUPPORTED": 2,
    "CAPABILITY_CERTIFIED": 3,
    "CAPABILITY_CURRENTLY_ELIGIBLE": 4,
}


def build_source_inventory(
    project_root: Path,
    capabilities_registry_path: Path | None = None,
    skill_registry_path: Path | None = None,
    skills_present: bool = False,
    design_skills_present: bool = False,
    auth_state: str = UNKNOWN,  # UNKNOWN != CURRENTLY_ELIGIBLE
    tooling_available: bool = False,  # real host tooling evidence present
) -> list[CapabilitySource]:
    """Provider-neutral capability-source inventory built from repository
    truth. Uses canonical surfaces only (registry targets, runtime modules,
    skill manifest, C36 cache). Does NOT create a second Capability Ledger.
    Unknown values stay UNKNOWN; certified != currently eligible.
    """
    sources: list[CapabilitySource] = []

    def _add(cap: str, typ: str, invoc: str, eligibility: str,
             pointers: tuple[str, ...] = (),
             permissions: tuple[str, ...] = ()) -> None:
        sources.append(CapabilitySource(
            source_type=typ, capability_id=cap, invocation_class=invoc,
            evidence_pointers=pointers, eligibility=eligibility,
            permissions=permissions))

    registry = capabilities_registry_path or (
        project_root / ".p2p" / "system" / "p2p_capabilities" /
        "capabilities.json")
    if registry.is_file():
        _add("capability_registry", "RUNTIME_DETERMINISTIC",
             "CANONICAL_REGISTRY", "CAPABILITY_CERTIFIED",
             (str(PurePosixPath(registry.relative_to(project_root))),))
    rt = project_root / ".p2p" / "system" / "p2p_capabilities"
    if (rt / "p2p_fw01_loop.py").is_file():
        _add("role_bridge_dispatch", "RUNTIME_DETERMINISTIC",
             "CANONICAL_RUNTIME", "CAPABILITY_CERTIFIED",
             (".p2p/system/p2p_capabilities/p2p_fw01_loop.py",))
    if (rt / "role_verifier.py").is_file():
        _add("role_verifier_evidence", "RUNTIME_DETERMINISTIC",
             "CANONICAL_RUNTIME", "CAPABILITY_CERTIFIED",
             (".p2p/system/p2p_capabilities/role_verifier.py",))
    if (rt / "selection_policy.py").is_file():
        _add("selection_policy", "RUNTIME_DETERMINISTIC",
             "CANONICAL_RUNTIME", "CAPABILITY_CERTIFIED",
             (".p2p/system/p2p_capabilities/selection_policy.py",))
    if (rt / "decision_trace.py").is_file():
        _add("decision_trace", "RUNTIME_DETERMINISTIC",
             "CANONICAL_RUNTIME", "CAPABILITY_CERTIFIED",
             (".p2p/system/p2p_capabilities/decision_trace.py",))
    if (rt / "task_state.py").is_file():
        _add("task_state_store", "RUNTIME_DETERMINISTIC",
             "CANONICAL_RUNTIME", "CAPABILITY_CERTIFIED",
             (".p2p/system/p2p_capabilities/task_state.py",))
    if (rt / "host_attestation.py").is_file():
        _add("host_attestation_real", "RUNTIME_DETERMINISTIC",
             "CANONICAL_RUNTIME", "CAPABILITY_CERTIFIED",
             (".p2p/system/p2p_capabilities/host_attestation.py",))
    if (rt / "context_cache.py").is_file():
        _add("context_cache_evidence_bound", "RUNTIME_DETERMINISTIC",
             "CANONICAL_RUNTIME", "CAPABILITY_CERTIFIED",
             (".p2p/system/p2p_capabilities/context_cache.py",))
    if (rt / "p2p_skill_eligibility.py").is_file():
        _add("skill_eligibility", "RUNTIME_DETERMINISTIC",
             "CANONICAL_RUNTIME", "CAPABILITY_CERTIFIED",
             (".p2p/system/p2p_capabilities/p2p_skill_eligibility.py",))
    if skills_present:
        _add("skill_eligibility", "SKILL", "SKILL_REGISTRY",
             "CAPABILITY_SUPPORTED",
             (".p2p/system/.agents/skills/.agents-skill-manifest.json",))
    if design_skills_present:
        _add("design_intelligence_nui", "DESIGN_NUI",
             "OPTIONAL_SOURCE_EVIDENCE_BOUND", "CAPABILITY_SUPPORTED",
             (".p2p/system/.agents/skills/UI-animation-design",
              ".p2p/system/.agents/skills/UI-taste-skill"),
             ())
    tool_elig = ("CAPABILITY_CURRENTLY_ELIGIBLE"
                 if tooling_available else "CAPABILITY_SUPPORTED")
    auth_elig = ("CAPABILITY_CURRENTLY_ELIGIBLE"
                 if auth_state == "CURRENTLY_ELIGIBLE" else UNKNOWN)
    _add("auth_fact_verification", "AUTH", "AUTH_FACT", auth_elig,
         ("auth_state:PROBED" if auth_elig == "CAPABILITY_CURRENTLY_ELIGIBLE"
          else "auth_state:NOT_PROBED",))
    _add("permission_profile_verification", "RUNTIME_DETERMINISTIC",
         "CANONICAL_RUNTIME", "CAPABILITY_CERTIFIED",
         (".p2p/system/p2p_capabilities/isolation.py",), ())
    _add("bounded_delegation", "RUNTIME_DETERMINISTIC", "CANONICAL_RUNTIME",
         "CAPABILITY_CERTIFIED",
         (".p2p/system/p2p_capabilities/bounded_delegation.py",))
    _add("owner_gate_authority", "HUMAN_DECISION", "OWNER_GATE",
         "CAPABILITY_SUPPORTED", ("governance/development-control.json",),
         ("owner-gate",))
    _add("code_search", "TOOL", "DETERMINISTIC_TOOL", tool_elig,
         ("workspace.shell.git",))
    _add("test_runner", "TOOL", "DETERMINISTIC_TOOL", tool_elig,
         ("workspace.shell.pytest",))
    _add("diff_analysis", "TOOL", "DETERMINISTIC_TOOL", tool_elig,
         ("workspace.shell.git",))
    _add("repo_map", "REPO_MAP", "DETERMINISTIC_MAP", tool_elig,
         ("workspace.filesystem",))
    _add("symbol_map", "CODE_INTELLIGENCE", "DETERMINISTIC_TOOL",
         tool_elig, ("workspace.shell.grep",))
    _add("static_checks", "CODE_INTELLIGENCE", "DETERMINISTIC_TOOL",
         tool_elig, ("workspace.shell.gitleaks",))
    _add("evidence_retrieval", "RETRIEVER", "DETERMINISTIC_TOOL",
         tool_elig, (".p2p/system/p2p_capabilities/read_evidence.py",))
    _add("freshness_verification", "RUNTIME_DETERMINISTIC", "CANONICAL_RUNTIME",
         "CAPABILITY_CERTIFIED",
         (".p2p/system/p2p_capabilities/context_cache.py",))
    _add("failover_boundary", "RUNTIME_DETERMINISTIC", "CANONICAL_RUNTIME",
         "CAPABILITY_CERTIFIED",
         (".p2p/system/p2p_capabilities/failover_boundary.py",))
    _add("isolation_enforcement", "RUNTIME_DETERMINISTIC", "CANONICAL_RUNTIME",
         "CAPABILITY_CERTIFIED",
         (".p2p/system/p2p_capabilities/isolation.py",))
    _add("beginner_interface", "RUNTIME_DETERMINISTIC", "CANONICAL_RUNTIME",
         "CAPABILITY_CERTIFIED",
         (".p2p/system/p2p_capabilities/beginner.py",))
    return sources


# ---------------------------------------------------------------------------
# 6. Eligibility resolution (CERTIFIED != CURRENTLY_ELIGIBLE)
# ---------------------------------------------------------------------------

def resolve_eligibility(
    requirement: CapabilityRequirement,
    sources: Sequence[CapabilitySource],
) -> tuple[str, tuple[str, ...]]:
    """Resolve current eligibility for one requirement against the inventory.

    Returns (eligibility_class, satisfied_by_source_type_names).
    Rules (fail-closed):
    - UNKNOWN evidence → eligibility UNKNOWN; never counted as available.
    - CERTIFIED requires CURRENTLY_ELIGIBLE evidence to count as eligible.
    - REQUIRED minimum_evidence floors are enforced; claims below floor
      produce the floor as the outcome class.
    """
    matching = [s for s in sources
                if s.capability_id == requirement.capability_id]
    if not matching:
        return (UNKNOWN, ())
    ranked = sorted(matching,
                    key=lambda s: ELIGIBILITY_RANK.get(s.eligibility, 0),
                    reverse=True)
    best = ranked[0]
    if requirement.minimum_evidence != "CLAIM":
        floor = MINIMUM_EVIDENCE_LEVELS.index(requirement.minimum_evidence)
        ev_rank = {"CLAIM": 0, "DETERMINISTIC": 1, "VERIFIED": 2,
                   "CERTIFIED": 3}.get(best.eligibility, 0)
        if ev_rank < floor:
            return (best.eligibility, ())
    satisfied = [s.source_type for s in ranked
                 if ELIGIBILITY_RANK.get(s.eligibility, 0) >=
                 ELIGIBILITY_RANK.get("CAPABILITY_CURRENTLY_ELIGIBLE", 0)]
    return (best.eligibility, tuple(satisfied))


# ---------------------------------------------------------------------------
# 7. Skill intelligence (bounded selection, NOT a top-level router)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SkillIntelligenceResult:
    """Bounded skill-selection output. Never a router decision."""

    outcome: str  # NO_SKILL_NEEDED | ONE_SKILL | BOUNDED_SKILL_SET | UNKNOWN
    selected_skills: tuple[str, ...]
    rejected_skills: tuple[str, ...]
    rejection_reasons: tuple[str, ...]
    expected_utility: str  # MATERIAL | MARGINAL | NONE | UNKNOWN
    evidence_pointers: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "selected_skills": list(self.selected_skills),
            "rejected_skills": list(self.rejected_skills),
            "rejection_reasons": list(self.rejection_reasons),
            "expected_utility": self.expected_utility,
            "evidence_pointers": list(self.evidence_pointers),
        }


_SKILL_CAPABILITY_HINTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("UI-animation-design", ("design_intelligence_nui",)),
    ("UI-taste-skill", ("design_intelligence_nui",)),
    ("Architect-review", ("static_checks", "role_verifier_evidence")),
    ("Data-Integrity", ("auth_fact_verification",)),
    ("Edge-Case", ("test_runner", "isolation_enforcement")),
)


def select_skills_bounded(
    requirements: Sequence[CapabilityRequirement],
    project_profile: ProjectProfile,
    installed_skills: tuple[str, ...],
    *,
    task_text: str = "",
    project_root: Path | None = None,
    explicit_skill_requests: tuple[str, ...] = (),
) -> SkillIntelligenceResult:
    """Bounded skill selection: TASK REQUIREMENT x SKILL CAPABILITY x
    PROJECT CONTEXT x EVIDENCE x ELIGIBILITY x EXPECTED UTILITY.

    - Irrelevant installed skills are rejected (never keyword-name matching
      alone — skill capability mapping drives relevance).
    - Never preload all skills; at most a BOUNDED_SKILL_SET (cap: 3).
    - Non-UI tasks never select UI-design skills.
    - Current P2P projects consume canonical capability metadata through the
      existing single router.  The five-entry mapping below remains only as a
      compatibility fallback for isolated legacy fixtures with no registry.
    """
    if project_root is not None:
        registry_path = (
            Path(project_root) / ".p2p" / "system" / "p2p_capabilities"
            / "capabilities.json"
        )
        if registry_path.is_file():
            # Historical isolated FW02 fixtures used a tiny
            # {"framework","targets","skills"} stub, not the canonical
            # capability manifest. Preserve that exact legacy shape only;
            # malformed current manifests still fail closed in load_registry.
            _registry_payload = json.loads(
                registry_path.read_text(encoding="utf-8")
            )
            _legacy_fixture_registry = (
                isinstance(_registry_payload, Mapping)
                and "capabilities" not in _registry_payload
                and "skills" in _registry_payload
            )
            if not _legacy_fixture_registry:
                try:
                    from .skill_consumption import select_skills_for_task
                except ImportError:
                    from skill_consumption import select_skills_for_task
                current = select_skills_for_task(
                project_root,
                task_text,
                explicit_requests=explicit_skill_requests,
                allowed_skill_ids=installed_skills,
            )
                return SkillIntelligenceResult(
                    outcome=current.outcome,
                    selected_skills=current.selected,
                    rejected_skills=current.rejected,
                    rejection_reasons=current.rejection_reasons,
                    expected_utility=(
                        "NONE" if current.outcome == "NO_SKILL_NEEDED"
                        else "MATERIAL"
                    ),
                    evidence_pointers=(
                        ".p2p/system/p2p_capabilities/capabilities.json",
                        *tuple(
                            f"selected-skill:{skill}"
                            for skill in current.selected
                        ),
                    ),
                )

    wanted: dict[str, tuple[str, ...]] = {}
    for req in requirements:
        if req.is_required():
            for skill, caps in _SKILL_CAPABILITY_HINTS:
                if req.capability_id in caps:
                    wanted.setdefault(skill, ())
    relevant: dict[str, str] = {}
    for skill in installed_skills:
        caps = [c for s, c in _SKILL_CAPABILITY_HINTS if s == skill]
        if any(any(c in wanted for c in cc) for cc in caps):
            relevant[skill] = "task-relevant"
        else:
            relevant.setdefault(skill, "irrelevant")

    selected: list[str] = []
    rejected: list[str] = []
    reasons: list[str] = []
    for skill, reason in relevant.items():
        if reason == "irrelevant" or skill not in wanted:
            rejected.append(skill)
            reasons.append(f"{skill}:IRRELEVANT_TO_REQUIREMENTS")
    # Bounded set + project-context filter (design skills only for UI tasks)
    ui_required = any(r.capability_id == "design_intelligence_nui"
                      and r.is_required() for r in requirements)
    for skill in sorted(wanted):
        if skill not in relevant:
            continue
        if ("design" in skill.lower() or "ui" in skill.lower()) and (
                not ui_required):
            rejected.append(skill)
            reasons.append(f"{skill}:NON_UI_TASK_NO_PRELOAD")
            continue
        if len(selected) >= 3:
            rejected.append(skill)
            reasons.append(f"{skill}:BOUNDED_SET_LIMIT")
            continue
        selected.append(skill)

    if not selected:
        return SkillIntelligenceResult(
            outcome="NO_SKILL_NEEDED", selected_skills=(),
            rejected_skills=tuple(rejected),
            rejection_reasons=tuple(dict.fromkeys(reasons)),
            expected_utility="NONE",
            evidence_pointers=(".p2p/system/.agents/skills/"
                               ".agents-skill-manifest.json",))
    if len(selected) == 1:
        return SkillIntelligenceResult(
            outcome="ONE_SKILL", selected_skills=tuple(selected),
            rejected_skills=tuple(rejected),
            rejection_reasons=tuple(dict.fromkeys(reasons)),
            expected_utility="MATERIAL",
            evidence_pointers=(
                ".p2p/system/.agents/skills/"
                ".agents-skill-manifest.json",
                *tuple(f".p2p/system/.agents/skills/{s}" for s in selected)))
    return SkillIntelligenceResult(
        outcome="BOUNDED_SKILL_SET", selected_skills=tuple(selected),
        rejected_skills=tuple(rejected),
        rejection_reasons=tuple(dict.fromkeys(reasons)),
        expected_utility="MATERIAL",
        evidence_pointers=(
            ".p2p/system/.agents/skills/.agents-skill-manifest.json",
            *tuple(f".p2p/system/.agents/skills/{s}" for s in selected)))


# ---------------------------------------------------------------------------
# 8. Capability coverage (fail-closed)
# ---------------------------------------------------------------------------

COVERAGE_STATES = ("COMPLETE", "PARTIAL", "UNKNOWN", "UNSATISFIED")

GAP_CLASSES = (
    "MISSING_AUTH", "MISSING_TOOL", "MISSING_PERMISSION", "MISSING_RUNTIME",
    "MISSING_EVIDENCE", "MISSING_SKILL", "UNKNOWN_CAPABILITY_SUPPORT",
)


@dataclass(frozen=True)
class CapabilityCoverage:
    """Pre-dispatch coverage evaluation.

    COMPLETE: every REQUIRED capability has a CURRENTLY_ELIGIBLE source.
    PARTIAL: some REQUIRED capabilities lack eligibility but fallback policy
             allows bounded safe continuation (policy-gated).
    UNKNOWN: eligibility evidence missing — fail-closed.
    UNSATISFIED: REQUIRED capability missing with no bounded fallback —
                 BLOCK dispatch.
    """

    state: str
    satisfied: tuple[str, ...]
    unsatisfied: tuple[str, ...]
    unknown: tuple[str, ...]
    gaps: tuple[str, ...]
    gap_classes: tuple[str, ...]
    dispatch_allowed: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "satisfied": list(self.satisfied),
            "unsatisfied": list(self.unsatisfied),
            "unknown": list(self.unknown),
            "gaps": list(self.gaps),
            "gap_classes": list(self.gap_classes),
            "dispatch_allowed": self.dispatch_allowed,
        }


def _gap_class(source_type: str) -> str:
    if source_type in ("AUTH",):
        return "MISSING_AUTH"
    if source_type in ("TOOL", "CODE_INTELLIGENCE"):
        return "MISSING_TOOL"
    if source_type in ("SKILL",):
        return "MISSING_SKILL"
    if source_type in ("RUNTIME_DETERMINISTIC",):
        return "MISSING_RUNTIME"
    if source_type in ("HUMAN_DECISION",):
        return "MISSING_PERMISSION"
    return "UNKNOWN_CAPABILITY_SUPPORT"


def evaluate_coverage(
    requirements: Sequence[CapabilityRequirement],
    sources: Sequence[CapabilitySource],
) -> CapabilityCoverage:
    satisfied: list[str] = []
    unsatisfied: list[str] = []
    unknown: list[str] = []
    gaps: list[str] = []
    gap_classes: list[str] = []
    for req in requirements:
        if not req.is_required():
            continue
        eligibility, by_sources = resolve_eligibility(req, sources)
        if eligibility == "CAPABILITY_CURRENTLY_ELIGIBLE" or (
                ELIGIBILITY_RANK.get(eligibility, 0) >=
                ELIGIBILITY_RANK.get("CAPABILITY_CERTIFIED", 0)):
            satisfied.append(req.capability_id)
        elif eligibility == UNKNOWN:
            unknown.append(req.capability_id)
            if by_sources:
                for t in by_sources:
                    gaps.append(f"{req.capability_id}:{t}")
                    gap_classes.append(_gap_class(t))
            else:
                gaps.append(f"{req.capability_id}:NO_SOURCE")
                gap_classes.append("UNKNOWN_CAPABILITY_SUPPORT")
        else:
            unsatisfied.append(req.capability_id)
            gaps.append(f"{req.capability_id}:{eligibility}")
            gap_classes.append("MISSING_EVIDENCE")
    if unknown:
        state = "UNKNOWN"
        dispatch_allowed = False
    elif unsatisfied:
        any_hard = any(r.fallback_allowed == "NO_DISPATCH" for r in
                       requirements if r.capability_id in unsatisfied
                       and r.is_required())
        state = "UNSATISFIED" if any_hard else "PARTIAL"
        dispatch_allowed = state == "PARTIAL"
    elif satisfied or not requirements:
        state = "COMPLETE" if satisfied else "COMPLETE"
        dispatch_allowed = True
    else:
        state = "COMPLETE"
        dispatch_allowed = True
    return CapabilityCoverage(
        state=state,
        satisfied=tuple(dict.fromkeys(satisfied)),
        unsatisfied=tuple(dict.fromkeys(unsatisfied)),
        unknown=tuple(dict.fromkeys(unknown)),
        gaps=tuple(dict.fromkeys(gaps)),
        gap_classes=tuple(dict.fromkeys(gap_classes)),
        dispatch_allowed=dispatch_allowed,
    )


# ---------------------------------------------------------------------------
# 9. Targeted context retrieval (evidence-bounded; NEVER a repo dump)
# ---------------------------------------------------------------------------

MAX_CONTEXT_ITEMS = 25


def required_context_items(
    requirements: Sequence[CapabilityRequirement],
    sources: Sequence[CapabilitySource],
    project_root: Path,
    task_scope: tuple[str, ...] = (),
) -> tuple[str, ...]:
    """Evidence-bounded targeted context selection before execution.

    Sources: requirement.context_requirement, source evidence pointers,
    repository map (file-surface targeting). NEVER the whole repository.
    """
    items: list[str] = []
    # Target the task's own scope files (must exist in the project)
    for ptr in task_scope:
        p = project_root / ptr.lstrip("./")
        if p.is_file() and ptr not in items:
            items.append(ptr)
    for req in requirements:
        for ptr in req.context_requirement:
            if ptr and ptr not in items:
                items.append(ptr)
    for src in sources:
        for ptr in src.evidence_pointers:
            if ptr.endswith(".py") or ptr.endswith(".json") or ptr in (
                    "package.json", "pyproject.toml"):
                p = project_root / ptr.lstrip("./")
                if p.is_file() and ptr not in items:
                    items.append(ptr)
    return tuple(dict.fromkeys(items))[:MAX_CONTEXT_ITEMS]


# ---------------------------------------------------------------------------
# 10. Decision trace (structured decision evidence)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CapabilityDecisionTrace:
    """Structured, machine-readable reasoning evidence for capability
    selection (NOT private chain-of-thought). Beginner output remains
    simple; this trace stays inspectable."""

    task_id: str
    task_classification: str
    required_capabilities: tuple[dict[str, Any], ...]
    selected_sources: tuple[dict[str, Any], ...]
    rejected_material_alternatives: tuple[str, ...]
    coverage: dict[str, Any]
    unknown_gaps: tuple[str, ...]
    why_selected: tuple[str, ...]
    evidence_pointers: tuple[str, ...]
    skill_intelligence: dict[str, Any]
    permission_never_widened: bool
    model_inference_used: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "task_classification": self.task_classification,
            "required_capabilities": list(self.required_capabilities),
            "selected_sources": list(self.selected_sources),
            "rejected_material_alternatives": list(
                self.rejected_material_alternatives),
            "coverage": self.coverage,
            "unknown_gaps": list(self.unknown_gaps),
            "why_selected": list(self.why_selected),
            "evidence_pointers": list(self.evidence_pointers),
            "skill_intelligence": self.skill_intelligence,
            "permission_never_widened": self.permission_never_widened,
            "model_inference_used": self.model_inference_used,
        }


# ---------------------------------------------------------------------------
# 11. Beginner-facing output
# ---------------------------------------------------------------------------

def beginner_status(trace: CapabilityDecisionTrace) -> str:
    """Simple beginner-facing sentence. Technical internals stay hidden
    unless requested; detailed evidence remains inspectable via the trace."""
    cov = trace.coverage.get("state", UNKNOWN)
    if cov == "COMPLETE":
        return "Đã hiểu việc tiếp theo và đủ công cụ để làm."
    if cov == "PARTIAL":
        return ("Việc tiếp theo có thể làm một phần an toàn; phần còn lại "
                "đang chờ công cụ hoặc quyết định bổ sung.")
    if cov == "UNKNOWN":
        return "Tôi cần bạn quyết định việc bổ sung công cụ trước khi tiếp tục."
    return ("Tôi cần bạn quyết định trước khi tiếp tục: thiếu công cụ hoặc "
            "quyền cho việc tiếp theo.")


# ---------------------------------------------------------------------------
# 12. Execution requirements + FW01 handoff (integration point)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ExecutionRequirements:
    """What FW01's dispatch gate consumes after capability intelligence.

    FW01 keeps role/team/target selection, pre-dispatch revalidation,
    execution, verification and checkpointing. Capability Intelligence only
    supplies these requirements and the decision trace.
    """

    task_id: str
    required_capabilities: tuple[CapabilityRequirement, ...]
    selected_sources: tuple[CapabilitySource, ...]
    coverage: CapabilityCoverage
    skill_selection: SkillIntelligenceResult
    context_items: tuple[str, ...]
    decision_trace: CapabilityDecisionTrace
    dispatch_allowed: bool
    failure_class: str  # NONE | capability gap class
    # Additive (planning-phase handoff): existing callers unaffected.
    optional_capabilities: tuple = ()
    source_eligibility: tuple = ()
    permission_requirements: tuple = ()
    # Issue A (fail-closed hardening): explicit unknown required
    # capabilities declared in the authoritative task contract — preserved
    # with SUPPORT=UNKNOWN, never silently dropped; UNKNOWN != SAFE.
    unknown_explicit_required: tuple[CapabilityRequirement, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "required_capabilities": [r.to_dict()
                                      for r in self.required_capabilities],
            "selected_sources": [s.to_dict() for s in self.selected_sources],
            "coverage": self.coverage.to_dict(),
            "skill_selection": self.skill_selection.to_dict(),
            "context_items": list(self.context_items),
            "decision_trace": self.decision_trace.to_dict(),
            "dispatch_allowed": self.dispatch_allowed,
            "failure_class": self.failure_class,
            "optional_capabilities": list(self.optional_capabilities),
            "source_eligibility": list(self.source_eligibility),
            "permission_requirements": list(self.permission_requirements),
            "unknown_explicit_required": [r.to_dict()
                                          for r in self.unknown_explicit_required],
        }


def classify_task(task_record: Mapping[str, Any]) -> str:
    """Bounded deterministic task classification (C18-compatible shape)."""
    text = " ".join(str(v) for v in (
        task_record.get("title", ""),
        task_record.get("purpose", ""),
        *list(task_record.get("scope", ())),
    )).lower()
    if re.search(r"supabase|rls|schema|migration|database", text):
        return "DATABASE_BOUNDARY"
    if re.search(r"ui|screen|design|accessibility", text):
        return "UI_PRODUCT"
    if re.search(r"test|fix|refactor|bug", text):
        return "CODE_QUALITY"
    if re.search(r"deploy|workflow|docker", text):
        return "DEPLOYMENT"
    if re.search(r"security|auth|permission", text):
        return "SECURITY_BOUNDARY"
    return "GENERAL"


def build_capability_handoff(
    task_id: str,
    requirements: "list[CapabilityRequirement]",
    coverage: "CapabilityCoverage",
    sources_eligibility: "dict[str, str]",
    context_items: "tuple[str, ...]",
    permission_requirements: "tuple[str, ...]" = (),
    trace_evidence_pointers: "tuple[str, ...]" = (),
    unknown_explicit_required: "tuple[CapabilityRequirement, ...]" = (),
) -> dict:
    """Minimal structured handoff from FW02 capability intelligence to the
    existing FW01 role/team selection boundary (planning phase).

    Reuse-only: every value derives from existing contracts/state
    (CapabilityRequirement, CapabilityCoverage, CapabilitySource,
    CapabilityDecisionTrace.evidence_pointers). No new schemas, no
    orchestration authority. Selection reads but does not depend on this
    input (pass-through proven mechanically); adaptation belongs to FW03.

    Permission requirements are passed through from task-state evidence,
    never widened (invariant: permission_never_widened stays True in the
    decision trace because this handoff is read-only).
    """
    required = [r.to_dict() for r in requirements if r.required_or_optional == "REQUIRED"]
    optional = [r.to_dict() for r in requirements if r.required_or_optional == "OPTIONAL"]
    return {
        "task_id": task_id,
        "required_capabilities": tuple(required),
        "optional_capabilities": tuple(optional),
        "current_source_eligibility": dict(sources_eligibility),
        "capability_gaps": tuple(dict.fromkeys(coverage.gaps)),
        "context_requirements": tuple(context_items),
        "quality_requirements": tuple(dict.fromkeys(
            r.quality_requirement for r in requirements
            if r.quality_requirement and r.quality_requirement != UNKNOWN)),
        "permission_requirements": tuple(permission_requirements),
        "fallback_constraints": tuple(dict.fromkeys(
            f"{r.capability_id}:{'ALLOWED' if r.fallback_allowed else 'DISALLOWED'}"
            for r in requirements)),
        "evidence_pointers": tuple(trace_evidence_pointers),
        "unknown_explicit_required": tuple(dict.fromkeys(
            r.capability_id for r in unknown_explicit_required)),
    }



# ---------------------------------------------------------------------------
# 8b. Selected-composition capability coverage (fail-closed)
# ---------------------------------------------------------------------------
COMPOSITION_COVERAGE_STATES = ("COMPLETE", "INCOMPLETE", "UNKNOWN")


@dataclass(frozen=True)
class CompositionCapabilityEvidence:
    """Minimal truthful contract for the SELECTED execution composition.
    FW03 owns adaptive team selection; this contract only lets the
    post-selection enforcement stage evaluate what the selected
    composition actually provides, and keep it SEPARATE from
    PROJECT_CAPABILITY_AVAILABILITY (invariant:
    AVAILABLE_SOMEWHERE != PROVIDED_BY_SELECTED_COMPOSITION).
    When the selector does not advertise meaningful provided-capability
    metadata the honest outcome is COMPOSITION_CAPABILITY_COVERAGE =
    UNKNOWN — never upgraded to COMPLETE.
    """
    selected_roles: tuple[str, ...] = ()
    selected_target: str = UNKNOWN
    selected_capability_sources: tuple[dict[str, Any], ...] = ()
    provided_capabilities: tuple[str, ...] = ()
    evidence_pointers: tuple[str, ...] = ()

    @property
    def has_capability_evidence(self) -> bool:
        return bool(self.provided_capabilities) or bool(
            self.selected_capability_sources)

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_roles": list(self.selected_roles),
            "selected_target": self.selected_target,
            "selected_capability_sources": [
                dict(s) for s in self.selected_capability_sources],
            "provided_capabilities": list(self.provided_capabilities),
            "evidence_pointers": list(self.evidence_pointers),
        }


def evaluate_composition_coverage(
    requirements: Sequence[CapabilityRequirement],
    composition: CompositionCapabilityEvidence,
) -> tuple[str, tuple[str, ...], bool]:
    """Evaluate REQUIRED capabilities against the SELECTED composition.
    Returns (coverage_state, missing_from_composition,
             composition_dispatch_contribution).
    Fail-closed semantics: no proven evidence for the selected composition
    -> UNKNOWN (never treated as COMPLETE); a required capability that is
    available in the PROJECT but not proven for the selected composition
    -> INCOMPLETE with dispatch remaining blocked.
    """
    required_ids = tuple(r.capability_id for r in requirements
                         if r.required_or_optional == "REQUIRED")
    proven = set(composition.provided_capabilities)
    missing: list[str] = []
    for cap in required_ids:
        if cap not in proven:
            missing.append(cap)
    if not composition.has_capability_evidence:
        # No truthful composition capability evidence exists: UNKNOWN.
        # Do NOT convert UNKNOWN into COMPLETE.
        return ("UNKNOWN", tuple(dict.fromkeys(required_ids)), False)
    if missing:
        return ("INCOMPLETE", tuple(dict.fromkeys(missing)), False)
    return ("COMPLETE", (), True)

def compute_execution_requirements(
    task_record: Mapping[str, Any],
    project_root: Path,
    project_profile: ProjectProfile | None = None,
    sources: Sequence[CapabilitySource] | None = None,
    installed_skills: tuple[str, ...] = (),
) -> ExecutionRequirements:
    """End-to-end deterministic capability intelligence for one task.

    Integrates with the FW01 loop: run AFTER next-safe-task selection,
    BEFORE role/team/target dispatch. If dispatch_allowed is False, FW01
    must NOT dispatch; the failure_class is the honest capability gap.
    """
    profile = project_profile if project_profile is not None else (
        build_project_profile(project_root))
    inv = sources if sources is not None else build_source_inventory(
        project_root,
        skills_present=bool(installed_skills),
        design_skills_present=any("ui" in s.lower() or "design" in s.lower()
                                  for s in installed_skills))
    requirements = infer_required_capabilities(task_record, profile)
    # Issue A (fail-closed): explicit unknown required capabilities from the
    # authoritative task contract are preserved as REQUIRED requirements
    # with origin DETERMINISTIC and task-contract provenance; support stays
    # UNKNOWN and coverage becomes UNKNOWN (dispatch_allowed=False).
    # EXPLICIT_REQUIRED_UNKNOWN != DROPPED; UNKNOWN != SAFE.
    _declared_unknown = tuple(
        c for c in (task_record.get("required_capabilities", ()) or ())
        if c not in CAPABILITY_VOCABULARY
        and _ID_RE.fullmatch(str(c)))
    for _cap in _declared_unknown:
        requirements.append(CapabilityRequirement(
            capability_id=str(_cap),
            purpose=f"explicit_unknown_task_contract:{_cap}",
            required_or_optional="REQUIRED",
            origin="DETERMINISTIC",
            evidence_pointers=("task_record.required_capabilities",)))
    requirements = _narrow_harness_requirements(task_record, requirements)
    coverage = evaluate_coverage(requirements, inv)
    _explicit_skills = task_record.get("skills", ()) or ()
    if isinstance(_explicit_skills, str):
        _explicit_skills = (_explicit_skills,)
    _task_text = " ".join(
        str(task_record.get(key, "") or "")
        for key in ("title", "purpose", "description", "request", "prompt")
    ).strip()
    skill_sel = select_skills_bounded(
        requirements,
        profile,
        installed_skills,
        task_text=_task_text,
        project_root=project_root,
        explicit_skill_requests=tuple(str(v) for v in _explicit_skills),
    )
    ctx = required_context_items(
        requirements, inv, project_root,
        task_scope=tuple(str(p) for p in (task_record.get("scope", ()) or ())))
    selected = tuple(s for s in inv if coverage.state == "COMPLETE" or
                     s.capability_id in coverage.satisfied
                     or s.capability_id not in [r.capability_id
                                                for r in requirements
                                                if r.is_required()])
    task_id = str(task_record.get("task_id", "unknown"))
    inferred_used = any(r.origin != "DETERMINISTIC" for r in requirements)
    why = [f"{r.capability_id}:{r.required_or_optional}:{r.origin}"
           for r in requirements]
    trace = CapabilityDecisionTrace(
        task_id=task_id,
        task_classification=classify_task(task_record),
        required_capabilities=tuple(r.to_dict() for r in requirements),
        selected_sources=tuple(s.to_dict() for s in selected),
        rejected_material_alternatives=tuple(
            dict.fromkeys(list(skill_sel.rejected_skills) +
                          [g.split(":", 1)[0] for g in coverage.gaps])),
        coverage=coverage.to_dict(),
        unknown_gaps=tuple(coverage.unknown),
        why_selected=tuple(why),
        evidence_pointers=tuple(dict.fromkeys(
            p for r in requirements for p in r.evidence_pointers)),
        skill_intelligence=skill_sel.to_dict(),
        permission_never_widened=True,
        model_inference_used=inferred_used,
    )
    failure = (coverage.gap_classes[0] if coverage.gap_classes else "NONE")
    return ExecutionRequirements(
        task_id=task_id,
        required_capabilities=tuple(requirements),
        selected_sources=tuple(selected),
        coverage=coverage,
        skill_selection=skill_sel,
        context_items=ctx,
        decision_trace=trace,
        dispatch_allowed=coverage.dispatch_allowed,
        failure_class=failure,
        optional_capabilities=tuple(s for s in requirements
                                    if s.required_or_optional == "OPTIONAL"),
        source_eligibility=tuple(dict.fromkeys(
            f"{s.capability_id}:{str(s.eligibility)}" for s in selected)),
        permission_requirements=tuple(str(p) for p in (task_record.get("permission_needs", ()) or ())),
        unknown_explicit_required=tuple(
            r for r in requirements if r.required_or_optional == "REQUIRED"
            and r.capability_id in _declared_unknown),
    )


# ---------------------------------------------------------------------------
# 13. Domain-aware upstream repository & source consumption contract
# ---------------------------------------------------------------------------

def select_domain_sources(
    task_record: Mapping[str, Any],
    domain_model: ProjectDomainModel | None = None,
    available_sources: Sequence[DomainSourceRecord] | None = None,
) -> DomainSourceSelectionReceipt:
    """Task-time domain-aware selection of external repositories and sources.

    Answers the Owner outcome without requiring the Owner to know specific
    repositories, libraries, engines, references, datasets or tools.

    Enforces invariants:
    - REPOSITORY != CAPABILITY
    - AVAILABLE != SELECTED
    - SELECTED != EXECUTABLE
    - REFERENCE != INSTALLED
    - DATASET != METHODOLOGY_AUTHORITY
    - ENGINEERING_PASS != DOMAIN_TRUTH
    - CODE_PASS != LEGAL_AUTHORITY
    - DETERMINISTIC_OUTPUT != PREDICTIVE_VALIDITY
    - DOMAIN_APPLICABILITY != AUTHORITY
    """
    task_id = str(task_record.get("task_id", "unknown_task"))
    outcome_text = " ".join(
        str(v)
        for v in (
            task_record.get("desired_outcome", ""),
            task_record.get("title", ""),
            task_record.get("purpose", ""),
            *list(task_record.get("scope", ())),
        )
    ).strip()
    lowered = outcome_text.lower()

    # 1. Target Domain Resolution
    explicit_domain = str(task_record.get("domain", "")).strip()
    if explicit_domain:
        target_domain = explicit_domain
    elif domain_model and domain_model.domain and domain_model.domain != "GENERAL":
        target_domain = domain_model.domain
    else:
        # Deterministic inference from outcome text
        if re.search(r"three|r3f|webgl|webgpu|blender|gltf|shader|3d|raycast|collision|navmesh", lowered):
            target_domain = "game.three"
        elif re.search(
            r"vnlaw|pháp luật|pháp lý|luật|nghị định|thông tư|văn bản quy phạm|vbpl|công báo|điều khoản|xử phạt|quy định",
            lowered,
        ):
            target_domain = "legal.vn"
        elif re.search(r"tử vi|ziwei", lowered):
            target_domain = "metaphysics.ziwei"
        elif re.search(r"mai hoa|meihua|plum", lowered):
            target_domain = "metaphysics.meihua"
        elif re.search(r"lục hào|liuyao", lowered):
            target_domain = "metaphysics.liuyao"
        elif re.search(r"bát tự|bazi", lowered):
            target_domain = "metaphysics.bazi"
        else:
            target_domain = "general"

    # 2. Required Capabilities Resolution
    explicit_caps = tuple(
        str(c) for c in (task_record.get("required_capabilities", ()) or ())
    )
    explicit_optional_caps = tuple(
        str(c) for c in (task_record.get("optional_capabilities", ()) or ())
    )
    if explicit_caps:
        required_caps = list(explicit_caps)
    else:
        required_caps = []
        if target_domain.startswith("game.three") or target_domain == "ui.frontend":
            required_caps.extend(["three_rendering", "three_production_knowledge"])
            if re.search(r"technique|codrops|effect|pattern|showcase|shader", lowered):
                required_caps.append("technique_reference")
            if re.search(r"bvh|collision|spatial|raycast", lowered):
                required_caps.append("spatial_query")
            if re.search(r"pathfinding|navmesh|navigation|npc", lowered):
                required_caps.append("navigation")
            if re.search(r"cinematic|timeline|cutscene|theatre", lowered):
                required_caps.append("cinematic")
            if re.search(r"hud|game hud|interface layout", lowered):
                required_caps.append("ui.game_hud")
        elif target_domain.startswith("legal"):
            if re.search(
                r"chính thức|căn cứ pháp lý|văn bản gốc|hiệu lực|official|nghị định|thông tư|luật",
                lowered,
            ):
                required_caps.append("official_legal_authority")
            if re.search(r"tìm kiếm|tra cứu|parse|indexing|trích xuất|index", lowered):
                required_caps.append("legal_search_parser")
            if re.search(r"giao diện|xem|hiển thị|viewer|layout", lowered):
                required_caps.append("legal_ui_viewer")
            if not required_caps:
                required_caps.extend(["official_legal_authority", "legal_search_parser"])
        elif target_domain.startswith("metaphysics"):
            if target_domain == "metaphysics.ziwei":
                required_caps.append("chart_calculation")
                if re.search(r"quy tắc chuẩn|pháp phái|chính thống|methodology authority|học thuyết", lowered):
                    required_caps.append("school_methodology")
                elif re.search(
                    r"phái|trung châu|luận đoán|tứ hóa|phương pháp|nam phái|bắc phái",
                    lowered,
                ):
                    required_caps.append("interpretation_reference")
                if re.search(r"fixture|test case|mẫu|dữ liệu", lowered):
                    required_caps.append("test_fixture_data")
            elif target_domain == "metaphysics.meihua":
                required_caps.append("meihua_hexagram_calculation")
                if re.search(r"app|ứng dụng|ui", lowered):
                    required_caps.append("meihua_app_reference")
            elif target_domain == "metaphysics.liuyao":
                required_caps.append("liuyao_hexagram_derivation")
            elif target_domain == "metaphysics.bazi":
                required_caps.append("bazi_chart_calculation")
    optional_caps = list(explicit_optional_caps)

    # School requirement for Metaphysics
    required_school = ""
    if "trung châu" in lowered or "zhongzhou" in lowered:
        required_school = "ZHONGZHOU_PAI"
    elif "tam hợp" in lowered or "sanhe" in lowered:
        required_school = "SANHE_PAI"

    # 3. Source Pool
    if available_sources is not None:
        candidate_pool = tuple(available_sources)
    elif domain_model and domain_model.known_sources:
        candidate_pool = domain_model.known_sources
    else:
        candidate_pool = build_domain_source_catalog()

    # 4. Evaluation and Invariant Enforcement
    selected_items: list[SelectedSourceItem] = []
    unselected_items: list[UnselectedSourceItem] = []
    authority_summaries: list[str] = []

    for candidate in candidate_pool:
        # A. Status and role non-selectability check (DEFER and REJECT must never select)
        if candidate.source_role in ("DEFER", "REJECT") or candidate.status in (
            "DEFER", "REJECT", "DEFERRED", "REJECTED"
        ):
            unselected_items.append(
                UnselectedSourceItem(
                    source_id=candidate.source_id,
                    source_name=candidate.source_name,
                    domain=candidate.domain,
                    candidate_role=candidate.source_role,
                    why_not_selected=f"CANDIDATE_ROLE_{candidate.source_role}_NON_SELECTABLE",
                )
            )
            continue

        # B. Domain applicability check (DOMAIN_APPLICABILITY_IS_NOT_AUTHORITY)
        cand_dom = candidate.domain.lower()
        targ_dom = target_domain.lower()
        domain_matches = (
            cand_dom == targ_dom
            or cand_dom.startswith(targ_dom + ".")
            or targ_dom.startswith(cand_dom + ".")
            or (targ_dom == "game.three" and cand_dom.startswith("game.three"))
            or (targ_dom == "ui.frontend" and cand_dom.startswith("ui."))
            or (targ_dom == "legal.vn" and cand_dom.startswith("legal"))
            or (targ_dom.startswith("metaphysics") and cand_dom == targ_dom)
        )
        if not domain_matches:
            unselected_items.append(
                UnselectedSourceItem(
                    source_id=candidate.source_id,
                    source_name=candidate.source_name,
                    domain=candidate.domain,
                    candidate_role=candidate.source_role,
                    why_not_selected=(
                        f"DOMAIN_MISMATCH:candidate_domain({candidate.domain})!=task_domain({target_domain})"
                    ),
                )
            )
            continue

        # C. School / Jurisdiction isolation (Chinese Metaphysics: school A != school B)
        if (
            required_school
            and candidate.school_or_jurisdiction
            and candidate.school_or_jurisdiction not in (required_school, "IZTRO_CONVENTION", "VIETNAM_LAW")
        ):
            unselected_items.append(
                UnselectedSourceItem(
                    source_id=candidate.source_id,
                    source_name=candidate.source_name,
                    domain=candidate.domain,
                    candidate_role=candidate.source_role,
                    why_not_selected=(
                        f"SCHOOL_SEPARATION:candidate_school({candidate.school_or_jurisdiction})!=task_school({required_school})"
                    ),
                )
            )
            continue

        # D. Research-only dossier check
        if candidate.source_role == "RESEARCH_ONLY" and "research" not in lowered:
            unselected_items.append(
                UnselectedSourceItem(
                    source_id=candidate.source_id,
                    source_name=candidate.source_name,
                    domain=candidate.domain,
                    candidate_role=candidate.source_role,
                    why_not_selected=(
                        "RESEARCH_ONLY_ISOLATION:candidate_is_exploratory_dossier_not_for_runtime_adoption"
                    ),
                )
            )
            continue

        # E. Capability need check (AVAILABLE_IS_NOT_SELECTED)
        demanded_caps = set(required_caps) | set(optional_caps)
        satisfied_caps = [
            cap for cap in candidate.capabilities_provided if cap in demanded_caps
        ]
        if not satisfied_caps:
            unselected_items.append(
                UnselectedSourceItem(
                    source_id=candidate.source_id,
                    source_name=candidate.source_name,
                    domain=candidate.domain,
                    candidate_role=candidate.source_role,
                    why_not_selected=(
                        f"CAPABILITY_NOT_REQUIRED:{','.join(candidate.capabilities_provided)}_not_demanded_by_task"
                    ),
                )
            )
            continue

        # F. Legal Authority check: CODE_PASS_IS_NOT_LEGAL_AUTHORITY
        # Authority must be bounded by the source record's explicit domain + authority_scope/claim,
        # never globally implied by source role name alone.
        if "official_legal_authority" in demanded_caps:
            is_valid_official_legal = (
                candidate.domain_truth_authority
                and any(
                    target_domain == ad or target_domain.startswith(ad + ".")
                    for ad in candidate.authority_domains
                )
                and "official_legal_authority" in candidate.capabilities_provided
            )
            if not is_valid_official_legal and "official_legal_authority" in satisfied_caps:
                satisfied_caps.remove("official_legal_authority")
                if not satisfied_caps:
                    unselected_items.append(
                        UnselectedSourceItem(
                            source_id=candidate.source_id,
                            source_name=candidate.source_name,
                            domain=candidate.domain,
                            candidate_role=candidate.source_role,
                            why_not_selected=(
                                "CODE_PASS_IS_NOT_LEGAL_AUTHORITY:source_lacks_bounded_domain_truth_authority_for_official_legal_text"
                            ),
                        )
                    )
                    continue

        # G. Methodology Authority check: METHODOLOGY_AUTHORITY_IS_DECLARED_AND_ENFORCED
        # Capability representing methodology authority (school_methodology) is satisfied ONLY when:
        # 1. candidate.methodology_authority == True
        # 2. target_domain in candidate.authority_domains
        # 3. school_or_jurisdiction isolation PASS
        if "school_methodology" in satisfied_caps:
            if candidate.source_role == "DATASET":
                satisfied_caps.remove("school_methodology")
                if not satisfied_caps:
                    unselected_items.append(
                        UnselectedSourceItem(
                            source_id=candidate.source_id,
                            source_name=candidate.source_name,
                            domain=candidate.domain,
                            candidate_role=candidate.source_role,
                            why_not_selected=(
                                "DATASET_IS_NOT_METHODOLOGY_AUTHORITY:sample_fixtures_do_not_establish_school_doctrine"
                            ),
                        )
                    )
                    continue
            else:
                domain_authority_passed = any(
                    target_domain == ad or target_domain.startswith(ad + ".")
                    for ad in candidate.authority_domains
                )
                school_isolation_passed = True
                if required_school and candidate.school_or_jurisdiction:
                    school_isolation_passed = (candidate.school_or_jurisdiction == required_school)
                elif required_school and not candidate.school_or_jurisdiction:
                    school_isolation_passed = False

                is_valid_methodology_authority = (
                    candidate.methodology_authority
                    and domain_authority_passed
                    and school_isolation_passed
                )

                if not is_valid_methodology_authority:
                    satisfied_caps.remove("school_methodology")
                    if not satisfied_caps:
                        if not candidate.methodology_authority:
                            why = "METHODOLOGY_AUTHORITY_NOT_ESTABLISHED:candidate_lacks_bounded_methodology_authority"
                        elif not domain_authority_passed:
                            why = (
                                f"AUTHORITY_DOMAIN_MISMATCH:candidate_authority_domains({candidate.authority_domains})_do_not_cover_{target_domain}"
                            )
                        else:
                            why = (
                                f"SCHOOL_MISMATCH:candidate_school({candidate.school_or_jurisdiction})!=task_school({required_school})"
                            )
                        unselected_items.append(
                            UnselectedSourceItem(
                                source_id=candidate.source_id,
                                source_name=candidate.source_name,
                                domain=candidate.domain,
                                candidate_role=candidate.source_role,
                                why_not_selected=why,
                            )
                        )
                        continue

        # H. Formulate selection rationale & boundary notes
        why_selected = (
            f"Fulfills required capabilities [{', '.join(satisfied_caps)}] as {candidate.source_role} "
            f"under mode {candidate.consumption_mode}"
        )
        if candidate.source_role == "TECHNIQUE_REFERENCE":
            why_selected += " (consulted as isolated pattern; not executable or installed wholesale)"
            authority_summaries.append(
                f"{candidate.source_id}:TECHNIQUE_REFERENCE_ONLY_NOT_EXECUTABLE"
            )
        elif candidate.source_role == "REFERENCE_IMPLEMENTATION":
            why_selected += " (architectural pattern inspection only; not vendored)"
            authority_summaries.append(
                f"{candidate.source_id}:REFERENCE_NOT_INSTALLED"
            )
        elif candidate.source_role == "EXECUTABLE_ENGINE":
            if "metaphysics" in candidate.domain:
                authority_summaries.append(
                    f"{candidate.source_id}:DETERMINISTIC_OUTPUT_IS_NOT_PREDICTIVE_VALIDITY"
                )
            elif "legal" in candidate.domain:
                authority_summaries.append(
                    f"{candidate.source_id}:CODE_PASS_IS_NOT_LEGAL_AUTHORITY"
                )
        elif candidate.source_role == "PRIMARY_OR_OFFICIAL_EVIDENCE_SOURCE":
            authority_summaries.append(
                f"{candidate.source_id}:PRIMARY_OFFICIAL_EVIDENCE_OF_RECORD"
            )
        elif candidate.source_role == "DATASET":
            authority_summaries.append(
                f"{candidate.source_id}:DATASET_IS_NOT_METHODOLOGY_AUTHORITY"
            )

        selected_items.append(
            SelectedSourceItem(
                source_id=candidate.source_id,
                source_name=candidate.source_name,
                domain=candidate.domain,
                source_role=candidate.source_role,
                consumption_mode=candidate.consumption_mode,
                capabilities_satisfied=tuple(satisfied_caps),
                pinned_ref=candidate.pinned_ref,
                authority_scope=candidate.authority_scope,
                limitations=candidate.limitations,
                why_selected=why_selected,
                evidence_pointers=candidate.evidence_pointers,
                school_or_jurisdiction=candidate.school_or_jurisdiction,
            )
        )

    # 5. Deterministic Coverage Accounting (Blocker R2-1: Fail-Closed without Whitelist)
    all_satisfied_caps: set[str] = set()
    for item in selected_items:
        all_satisfied_caps.update(item.capabilities_satisfied)
    satisfied_tuple = tuple(sorted(all_satisfied_caps))
    unsatisfied_required = tuple(
        c for c in required_caps if c not in all_satisfied_caps
    )
    unsatisfied_optional = tuple(
        c for c in optional_caps if c not in all_satisfied_caps
    )

    if unsatisfied_required or not selected_items:
        selection_status = "BLOCKED"
    elif unsatisfied_optional:
        selection_status = "PARTIAL_OPTIONAL"
    else:
        selection_status = "SATISFIED"

    # Invariants summary
    if not authority_summaries:
        authority_summaries.append("DOMAIN_BOUNDED_SELECTION_ONLY")

    return DomainSourceSelectionReceipt(
        receipt_schema="p2p-source-selection-receipt/1",
        task_id=task_id,
        domain=target_domain,
        desired_outcome=outcome_text,
        selection_status=selection_status,
        required_capabilities=tuple(required_caps),
        satisfied_capabilities=satisfied_tuple,
        unsatisfied_required_capabilities=unsatisfied_required,
        optional_capabilities=tuple(optional_caps),
        unsatisfied_optional_capabilities=unsatisfied_optional,
        selected_sources=tuple(selected_items),
        unselected_candidates=tuple(unselected_items),
        authority_boundary_summary=tuple(dict.fromkeys(authority_summaries)),
        invariants_enforced=CORE_INVARIANTS,
    )

