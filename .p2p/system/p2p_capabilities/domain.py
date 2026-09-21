"""Project domain vocabulary, source consumption roles, and domain provenance contracts.

Never an authority or persistence layer.

Required invariants:
- REPOSITORY != CAPABILITY
- AVAILABLE != SELECTED
- SELECTION_DOES_NOT_IMPLY_EXECUTABILITY
- REFERENCE != INSTALLED
- DATASET != METHODOLOGY_AUTHORITY
- ENGINEERING_PASS != DOMAIN_TRUTH
- CODE_PASS != LEGAL_AUTHORITY
- DETERMINISTIC_OUTPUT != PREDICTIVE_VALIDITY
- DOMAIN_APPLICABILITY != AUTHORITY
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Sequence


# ---------------------------------------------------------------------------
# 1. Canonical source consumption roles & invariants
# ---------------------------------------------------------------------------

SOURCE_ROLES: tuple[str, ...] = (
    "DEPENDENCY",                          # Runtime package / library linked in code
    "EXECUTABLE_ENGINE",                  # Calculation / evaluation / parsing engine
    "SKILL",                              # Packaged knowledge / instructions for AI agents
    "REFERENCE_IMPLEMENTATION",           # Reference architecture / implementation pattern
    "TECHNIQUE_REFERENCE",                # Isolated technique / pattern reference (not copied whole)
    "TOOL",                               # External CLI tool / linter / runner
    "STARTER",                            # Project starter / scaffolding template
    "DATASET",                            # Fixture / evaluation data (not methodology authority)
    "PRIMARY_OR_OFFICIAL_EVIDENCE_SOURCE",# Official / primary evidence source of truth
    "RESEARCH_ONLY",                      # Exploratory research dossier (no runtime adoption)
    "DEFER",                              # Deferred candidate
    "REJECT",                             # Rejected candidate (license, security, scope)
)

SOURCE_ROLE_ALIASES: dict[str, str] = {
    "LIBRARY": "DEPENDENCY",
    "DEPENDENCY_LIBRARY": "DEPENDENCY",
    "KNOWLEDGE_UNIT": "SKILL",
    "SKILL_KNOWLEDGE_UNIT": "SKILL",
    "EXTERNAL_TOOL": "TOOL",
    "TEMPLATE": "STARTER",
    "STARTER_TEMPLATE": "STARTER",
    "FIXTURE": "DATASET",
    "DATASET_FIXTURE": "DATASET",
    "PRIMARY_SOURCE": "PRIMARY_OR_OFFICIAL_EVIDENCE_SOURCE",
    "OFFICIAL_SOURCE": "PRIMARY_OR_OFFICIAL_EVIDENCE_SOURCE",
    "PRIMARY_OR_OFFICIAL_EVIDENCE": "PRIMARY_OR_OFFICIAL_EVIDENCE_SOURCE",
    "OFFICIAL_EVIDENCE": "PRIMARY_OR_OFFICIAL_EVIDENCE_SOURCE",
    "PATTERN_ONLY": "TECHNIQUE_REFERENCE",
    "REFERENCE_ONLY": "TECHNIQUE_REFERENCE",
    "DEFERRED": "DEFER",
    "REJECTED": "REJECT",
}

CORE_INVARIANTS: tuple[str, ...] = (
    "REPOSITORY_IS_NOT_CAPABILITY",
    "AVAILABLE_IS_NOT_SELECTED",
    "SELECTION_DOES_NOT_IMPLY_EXECUTABILITY",
    "REFERENCE_IS_NOT_INSTALLED",
    "DATASET_IS_NOT_METHODOLOGY_AUTHORITY",
    "ENGINEERING_PASS_IS_NOT_DOMAIN_TRUTH",
    "CODE_PASS_IS_NOT_LEGAL_AUTHORITY",
    "DETERMINISTIC_OUTPUT_IS_NOT_PREDICTIVE_VALIDITY",
    "DOMAIN_APPLICABILITY_IS_NOT_AUTHORITY",
)


def normalize_source_role(role: str) -> str:
    """Normalize a candidate source role to canonical vocabulary."""
    raw = str(role or "").strip().upper()
    resolved = SOURCE_ROLE_ALIASES.get(raw, raw)
    if resolved not in SOURCE_ROLES:
        raise ValueError(
            f"SOURCE_ROLE_INVALID: {role!r}. Must be one of {SOURCE_ROLES}"
        )
    return resolved


@dataclass(frozen=True)
class SourceRoleMetadata:
    """Structural consumption behavior of a source role.

    Authority (methodology or domain truth) is NOT granted globally by role name;
    it must be established by the specific DomainSourceRecord's explicit claims.
    """

    role: str
    is_executable: bool
    is_installable: bool
    requires_pinned_provenance: bool
    description: str


_ROLE_METADATA_TABLE: dict[str, SourceRoleMetadata] = {
    "DEPENDENCY": SourceRoleMetadata(
        role="DEPENDENCY",
        is_executable=True,
        is_installable=True,
        requires_pinned_provenance=True,
        description="Runtime package or library linked directly into project code.",
    ),
    "EXECUTABLE_ENGINE": SourceRoleMetadata(
        role="EXECUTABLE_ENGINE",
        is_executable=True,
        is_installable=False,
        requires_pinned_provenance=True,
        description="Deterministic calculation or parsing engine. Pass does not prove domain truth or predictive validity.",
    ),
    "SKILL": SourceRoleMetadata(
        role="SKILL",
        is_executable=False,
        is_installable=True,
        requires_pinned_provenance=True,
        description="Packaged knowledge unit or operational workflow guide for AI agents.",
    ),
    "REFERENCE_IMPLEMENTATION": SourceRoleMetadata(
        role="REFERENCE_IMPLEMENTATION",
        is_executable=False,
        is_installable=False,
        requires_pinned_provenance=True,
        description="Reference architecture or implementation pattern. Never installed or copied wholesale by default.",
    ),
    "TECHNIQUE_REFERENCE": SourceRoleMetadata(
        role="TECHNIQUE_REFERENCE",
        is_executable=False,
        is_installable=False,
        requires_pinned_provenance=True,
        description="Targeted technique or visual/algorithmic pattern reference. Not executable or installable.",
    ),
    "TOOL": SourceRoleMetadata(
        role="TOOL",
        is_executable=True,
        is_installable=False,
        requires_pinned_provenance=True,
        description="External CLI or workspace tool invoked for builds, checks, or queries. Version/provenance required.",
    ),
    "STARTER": SourceRoleMetadata(
        role="STARTER",
        is_executable=False,
        is_installable=False,
        requires_pinned_provenance=True,
        description="Starter template or scaffolding structure. Requires explicit adoption decision.",
    ),
    "DATASET": SourceRoleMetadata(
        role="DATASET",
        is_executable=False,
        is_installable=False,
        requires_pinned_provenance=True,
        description="Test fixture, evaluation corpus, or reference data. Never methodology or doctrinal authority.",
    ),
    "PRIMARY_OR_OFFICIAL_EVIDENCE_SOURCE": SourceRoleMetadata(
        role="PRIMARY_OR_OFFICIAL_EVIDENCE_SOURCE",
        is_executable=False,
        is_installable=False,
        requires_pinned_provenance=True,
        description="Primary official source of truth. Scope and domain of authority must be explicitly recorded.",
    ),
    "RESEARCH_ONLY": SourceRoleMetadata(
        role="RESEARCH_ONLY",
        is_executable=False,
        is_installable=False,
        requires_pinned_provenance=True,
        description="Independent exploratory research dossier. Strictly non-executable and not adopted in runtime.",
    ),
    "DEFER": SourceRoleMetadata(
        role="DEFER",
        is_executable=False,
        is_installable=False,
        requires_pinned_provenance=False,
        description="Candidate deferred from current task or workstream consideration. Intrinsically non-selectable.",
    ),
    "REJECT": SourceRoleMetadata(
        role="REJECT",
        is_executable=False,
        is_installable=False,
        requires_pinned_provenance=False,
        description="Candidate rejected due to license incompatibility, security risk, or scope mismatch. Intrinsically non-selectable.",
    ),
}


def get_source_role_metadata(role: str) -> SourceRoleMetadata:
    normalized = normalize_source_role(role)
    return _ROLE_METADATA_TABLE[normalized]


# ---------------------------------------------------------------------------
# 2. Domain source record & receipts
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DomainSourceRecord:
    source_id: str
    source_name: str
    domain: str
    source_role: str
    consumption_mode: str
    capabilities_provided: tuple[str, ...] = ()
    upstream_repo: str = ""
    pinned_ref: str = "UNKNOWN"
    license: str = "UNKNOWN"
    authority_scope: str = "NONE"
    authority_domains: tuple[str, ...] = ()
    methodology_authority: bool = False
    domain_truth_authority: bool = False
    limitations: tuple[str, ...] = ()
    school_or_jurisdiction: str = ""
    evidence_pointers: tuple[str, ...] = ()
    status: str = "ACTIVE"

    def __post_init__(self) -> None:
        normalized_role = normalize_source_role(self.source_role)
        object.__setattr__(self, "source_role", normalized_role)
        # Blockers 4: DEFER and REJECT are intrinsically non-selectable regardless of status
        if normalized_role in ("DEFER", "REJECT") and self.status == "ACTIVE":
            object.__setattr__(
                self, "status", "DEFERRED" if normalized_role == "DEFER" else "REJECTED"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "domain": self.domain,
            "source_role": self.source_role,
            "consumption_mode": self.consumption_mode,
            "capabilities_provided": list(self.capabilities_provided),
            "upstream_repo": self.upstream_repo,
            "pinned_ref": self.pinned_ref,
            "license": self.license,
            "authority_scope": self.authority_scope,
            "authority_domains": list(self.authority_domains),
            "methodology_authority": self.methodology_authority,
            "domain_truth_authority": self.domain_truth_authority,
            "limitations": list(self.limitations),
            "school_or_jurisdiction": self.school_or_jurisdiction,
            "evidence_pointers": list(self.evidence_pointers),
            "status": self.status,
        }


@dataclass(frozen=True)
class SelectedSourceItem:
    source_id: str
    source_name: str
    domain: str
    source_role: str
    consumption_mode: str
    capabilities_satisfied: tuple[str, ...]
    pinned_ref: str
    authority_scope: str
    limitations: tuple[str, ...]
    why_selected: str
    evidence_pointers: tuple[str, ...]
    school_or_jurisdiction: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "domain": self.domain,
            "source_role": self.source_role,
            "consumption_mode": self.consumption_mode,
            "capabilities_satisfied": list(self.capabilities_satisfied),
            "pinned_ref": self.pinned_ref,
            "authority_scope": self.authority_scope,
            "limitations": list(self.limitations),
            "why_selected": self.why_selected,
            "evidence_pointers": list(self.evidence_pointers),
            "school_or_jurisdiction": self.school_or_jurisdiction,
        }


@dataclass(frozen=True)
class UnselectedSourceItem:
    source_id: str
    source_name: str
    domain: str
    candidate_role: str
    why_not_selected: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "source_name": self.source_name,
            "domain": self.domain,
            "candidate_role": self.candidate_role,
            "why_not_selected": self.why_not_selected,
        }


@dataclass(frozen=True)
class DomainSourceSelectionReceipt:
    receipt_schema: str = "p2p-source-selection-receipt/1"
    task_id: str = ""
    domain: str = ""
    desired_outcome: str = ""
    selection_status: str = "BLOCKED"  # SATISFIED | PARTIAL_OPTIONAL | BLOCKED
    required_capabilities: tuple[str, ...] = ()
    satisfied_capabilities: tuple[str, ...] = ()
    unsatisfied_required_capabilities: tuple[str, ...] = ()
    optional_capabilities: tuple[str, ...] = ()
    unsatisfied_optional_capabilities: tuple[str, ...] = ()
    selected_sources: tuple[SelectedSourceItem, ...] = ()
    unselected_candidates: tuple[UnselectedSourceItem, ...] = ()
    authority_boundary_summary: tuple[str, ...] = ()
    invariants_enforced: tuple[str, ...] = CORE_INVARIANTS

    def to_dict(self) -> dict[str, Any]:
        return {
            "receipt_schema": self.receipt_schema,
            "task_id": self.task_id,
            "domain": self.domain,
            "desired_outcome": self.desired_outcome,
            "selection_status": self.selection_status,
            "required_capabilities": list(self.required_capabilities),
            "satisfied_capabilities": list(self.satisfied_capabilities),
            "unsatisfied_required_capabilities": list(self.unsatisfied_required_capabilities),
            "optional_capabilities": list(self.optional_capabilities),
            "unsatisfied_optional_capabilities": list(self.unsatisfied_optional_capabilities),
            "selected_sources": [s.to_dict() for s in self.selected_sources],
            "unselected_candidates": [u.to_dict() for u in self.unselected_candidates],
            "authority_boundary_summary": list(self.authority_boundary_summary),
            "invariants_enforced": list(self.invariants_enforced),
        }

    def compact_summary(self) -> str:
        pin_entries = [
            f"{s.source_id}:{s.pinned_ref or 'UNPINNED'}"
            for s in self.selected_sources
        ]
        lines = [
            f"DOMAIN={self.domain}",
            f"SELECTION_STATUS={self.selection_status}",
            f"CAPABILITIES_REQUIRED={','.join(self.required_capabilities)}",
            f"SATISFIED_CAPABILITIES={','.join(self.satisfied_capabilities)}",
            f"UNSATISFIED_REQUIRED_CAPABILITIES={','.join(self.unsatisfied_required_capabilities)}",
            f"OPTIONAL_CAPABILITIES={','.join(self.optional_capabilities)}",
            f"UNSATISFIED_OPTIONAL_CAPABILITIES={','.join(self.unsatisfied_optional_capabilities)}",
            f"SOURCES_SELECTED={','.join(s.source_id for s in self.selected_sources)}",
            f"SOURCE_ROLE_PER_SOURCE={','.join(f'{s.source_id}:{s.source_role}' for s in self.selected_sources)}",
            f"PIN_PROVENANCE={','.join(pin_entries)}",
            f"CONSUMPTION_MODE={','.join(f'{s.source_id}:{s.consumption_mode}' for s in self.selected_sources)}",
            f"WHY_SELECTED={'; '.join(f'{s.source_id} -> {s.why_selected}' for s in self.selected_sources)}",
            f"WHY_NOT_SELECTED={'; '.join(f'{u.source_id} -> {u.why_not_selected}' for u in self.unselected_candidates)}",
            f"LIMITATIONS_AUTHORITY_BOUNDARY={'; '.join(self.authority_boundary_summary)}",
        ]
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# 3. ProjectDomainModel
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ProjectDomainModel:
    domain: str
    users: tuple[str, ...] = field(default_factory=tuple)
    workflows: tuple[str, ...] = field(default_factory=tuple)
    vocabulary: tuple[str, ...] = field(default_factory=tuple)
    constraints: tuple[str, ...] = field(default_factory=tuple)
    provenance: str = "OWNER"
    known_sources: tuple[DomainSourceRecord, ...] = field(default_factory=tuple)
    subdomains: tuple[str, ...] = field(default_factory=tuple)

    def as_context(self) -> dict[str, Any]:
        value = asdict(self)
        value.update({
            "content_class": "CONTENT",
            "grants_permissions": False,
            "changes_quorum": False,
            "persistent": False,
        })
        return value

    def with_sources(self, sources: Sequence[DomainSourceRecord]) -> ProjectDomainModel:
        return ProjectDomainModel(
            domain=self.domain,
            users=self.users,
            workflows=self.workflows,
            vocabulary=self.vocabulary,
            constraints=self.constraints,
            provenance=self.provenance,
            known_sources=tuple(sources),
            subdomains=self.subdomains,
        )

    def get_sources_for_domain(self, domain_filter: str) -> tuple[DomainSourceRecord, ...]:
        df = domain_filter.lower().strip()
        return tuple(
            s for s in self.known_sources
            if s.domain.lower() == df or s.domain.lower().startswith(df + ".")
        )


# ---------------------------------------------------------------------------
# 4. Standard built-in domain source catalog (projected from durable truth)
# ---------------------------------------------------------------------------

def build_domain_source_catalog() -> tuple[DomainSourceRecord, ...]:
    """Provider-neutral canonical source catalog projected from durable truth surfaces.

    Reuses existing truth from:
    - docs/p2p-development/capability-catalog/ui-game-threejs/capability-catalog.json
    - source/chinese-metaphysics/README.md pinned submodule upstreams
    - Official Vietnamese legal portals of record (vbpl.vn, congbao.chinhphu.vn)

    Contains ZERO fabricated example repositories or synthetic proof fixtures.
    Proof-only synthetic fixtures are strictly isolated to tests.
    """
    return (
        # --- Domain: UI / Three.js (from capability-catalog.json) ---
        DomainSourceRecord(
            source_id="repo:three",
            source_name="Three.js core runtime library",
            domain="game.three",
            source_role="DEPENDENCY",
            consumption_mode="LINK_AS_DEPENDENCY",
            capabilities_provided=("three_rendering", "webgl_webgpu_runtime"),
            upstream_repo="mrdoob/three.js",
            pinned_ref="UNVERIFIED_VERSION",
            license="MIT",
            authority_scope="GRAPHICS_RENDERING_RUNTIME",
            evidence_pointers=("docs/p2p-development/capability-catalog/ui-game-threejs/capability-catalog.json",),
        ),
        DomainSourceRecord(
            source_id="skill:threejs",
            source_name="Three.js production skill & look-dev guidance",
            domain="game.three",
            source_role="SKILL",
            consumption_mode="READ_AS_SKILL",
            capabilities_provided=(
                "three_production_knowledge",
                "asset_preparation",
                "lookdev_workflow",
                "measurement_first_performance",
            ),
            upstream_repo="local:.agents/skills/threejs",
            pinned_ref="2.0.0",
            license="MIT",
            authority_scope="AGENT_OPERATIONAL_GUIDANCE",
            evidence_pointers=(".agents/skills/threejs/SKILL.md",),
        ),
        # CAND-GAME-UI-005 from capability-catalog.json (observed 2026-08-29)
        DomainSourceRecord(
            source_id="repo:three-mesh-bvh",
            source_name="three-mesh-bvh spatial query accelerator",
            domain="game.three.spatial_query",
            source_role="DEPENDENCY",
            consumption_mode="LINK_AS_DEPENDENCY",
            capabilities_provided=("game.three.spatial_query", "spatial_query"),
            upstream_repo="gkjohnson/three-mesh-bvh",
            pinned_ref="v0.9.14 (observed 2026-08-29)",
            license="MIT",
            authority_scope="RAYCASTING_SPATIAL_ACCELERATION",
            limitations=("SPECIALIST_CAPABILITY_DEMAND_TRIGGERED",),
            evidence_pointers=(
                "docs/p2p-development/capability-catalog/ui-game-threejs/capability-catalog.json",
                "governance/research-adoption-ledger.json",
            ),
        ),
        # CAND-GAME-UI-008 from capability-catalog.json & RA-EXT-039 (observed 2026-08-29)
        DomainSourceRecord(
            source_id="repo:three-pathfinding",
            source_name="three-pathfinding navigation library",
            domain="game.three.navigation",
            source_role="DEPENDENCY",
            consumption_mode="LINK_AS_DEPENDENCY",
            capabilities_provided=("game.three.navigation", "navigation"),
            upstream_repo="donmccurdy/three-pathfinding",
            pinned_ref="v1.3.0 (observed 2026-08-29)",
            license="MIT",
            authority_scope="NAVMESH_PATHFINDING",
            limitations=("SPECIALIST_CAPABILITY_DEMAND_TRIGGERED",),
            evidence_pointers=(
                "docs/p2p-development/capability-catalog/ui-game-threejs/capability-catalog.json",
                "governance/research-adoption-ledger.json",
            ),
        ),
        # CAND-GAME-UI-007 from capability-catalog.json & RA-EXT-038 (explicit license split preserved)
        DomainSourceRecord(
            source_id="repo:theatre-js",
            source_name="Theatre.js cinematic animation library",
            domain="game.three.cinematic",
            source_role="DEPENDENCY",
            consumption_mode="LINK_AS_DEPENDENCY",
            capabilities_provided=("game.three.cinematic", "cinematic"),
            upstream_repo="theatre-js/theatre",
            pinned_ref="UNVERIFIED_VERSION",
            license="Apache-2.0 (core), AGPL-3.0 (studio)",
            authority_scope="TIMELINE_CINEMATIC_ANIMATION",
            limitations=(
                "SPECIALIST_CAPABILITY_DEMAND_TRIGGERED",
                "LICENSE_SPLIT_CORE_APACHE_STUDIO_AGPL",
            ),
            evidence_pointers=(
                "docs/p2p-development/capability-catalog/ui-game-threejs/capability-catalog.json",
                "governance/research-adoption-ledger.json",
            ),
        ),
        # CAND-GAME-UI-018 from capability-catalog.json
        DomainSourceRecord(
            source_id="repo:threejsassets-game-hud",
            source_name="threejsassets game-hud layout reference",
            domain="ui.game_hud",
            source_role="REFERENCE_IMPLEMENTATION",
            consumption_mode="INSPECT_UI_PATTERN",
            capabilities_provided=("ui.game_hud", "hud_reference_layout"),
            upstream_repo="threejsassets/game-hud",
            pinned_ref="UNVERIFIED_VERSION",
            license="MIT",
            authority_scope="PRESENTATION_LAYOUT_REFERENCE_ONLY",
            limitations=("REFERENCE_NOT_INSTALLED",),
            evidence_pointers=(
                "docs/p2p-development/capability-catalog/ui-game-threejs/capability-catalog.json",
                "governance/research-adoption-ledger.json",
            ),
        ),
        # CAND-GAME-UI-017 from capability-catalog.json (license gated)
        DomainSourceRecord(
            source_id="repo:prnthh-react-three-game",
            source_name="prnthh/react-three-game reference",
            domain="game.three.scene_authoring",
            source_role="REJECT",
            consumption_mode="REJECTED_LICENSE_GATE",
            capabilities_provided=("game.three.scene_authoring",),
            upstream_repo="prnthh/react-three-game",
            pinned_ref="UNVERIFIED_VERSION",
            license="PFYL / VPL",
            authority_scope="NONE",
            status="REJECTED",
            limitations=("LICENSE_GATED_PROPRIETARY",),
            evidence_pointers=(
                "docs/p2p-development/capability-catalog/ui-game-threejs/capability-catalog.json",
                "governance/research-adoption-ledger.json",
            ),
        ),

        # --- Domain: VNLAW / Legal (authentic official evidence sources of record) ---
        DomainSourceRecord(
            source_id="official:vbpl_vn",
            source_name="Cơ sở dữ liệu Quốc gia về Văn bản Pháp luật (vbpl.vn)",
            domain="legal.vn",
            source_role="PRIMARY_OR_OFFICIAL_EVIDENCE_SOURCE",
            consumption_mode="QUERY_OFFICIAL_EVIDENCE",
            capabilities_provided=("official_legal_authority", "official_legal_text"),
            upstream_repo="https://vbpl.vn",
            pinned_ref="OFFICIAL_STATE_DATABASE",
            license="PUBLIC_LEGAL_DOCUMENTS_VN",
            authority_scope="OFFICIAL_LEGAL_PROMULGATED_TEXT",
            authority_domains=("legal.vn",),
            domain_truth_authority=True,
            methodology_authority=False,
            school_or_jurisdiction="VIETNAM_LAW",
            evidence_pointers=("governance/fact-ledger.json",),
            limitations=("REQUIRES_PRIMARY_PROVENANCE_CITATION",),
        ),
        DomainSourceRecord(
            source_id="official:congbao_gov_vn",
            source_name="Công báo Nước CHXHCN Việt Nam (congbao.chinhphu.vn)",
            domain="legal.vn",
            source_role="PRIMARY_OR_OFFICIAL_EVIDENCE_SOURCE",
            consumption_mode="QUERY_OFFICIAL_EVIDENCE",
            capabilities_provided=("official_legal_authority", "official_gazette_promulgation"),
            upstream_repo="http://congbao.chinhphu.vn",
            pinned_ref="OFFICIAL_GAZETTE_RECORDS",
            license="PUBLIC_LEGAL_DOCUMENTS_VN",
            authority_scope="OFFICIAL_GAZETTE_PROMULGATION",
            authority_domains=("legal.vn",),
            domain_truth_authority=True,
            methodology_authority=False,
            school_or_jurisdiction="VIETNAM_LAW",
            evidence_pointers=("governance/fact-ledger.json",),
        ),

        # --- Domain: Chinese Metaphysics (from source/chinese-metaphysics/README.md) ---
        DomainSourceRecord(
            source_id="repo:SylarLong/iztro",
            source_name="iztro Ziwei Doushu Calculation Engine",
            domain="metaphysics.ziwei",
            source_role="EXECUTABLE_ENGINE",
            consumption_mode="RUN_AS_ENGINE",
            capabilities_provided=("chart_calculation", "palace_star_facts", "mutagen_facts"),
            upstream_repo="SylarLong/iztro",
            pinned_ref="2c7ef9be669df7b19d1799f4dce335fed3794f78",
            license="MIT",
            authority_scope="DETERMINISTIC_CHART_FACTS_ONLY",
            authority_domains=("metaphysics.ziwei",),
            school_or_jurisdiction="IZTRO_CONVENTION",
            evidence_pointers=("source/chinese-metaphysics/research/iztro/RESEARCH.md",),
            limitations=(
                "DETERMINISTIC_OUTPUT_IS_NOT_PREDICTIVE_VALIDITY",
                "CALCULATION_ENGINE_IS_NOT_METHODOLOGY_AUTHORITY",
            ),
        ),
        DomainSourceRecord(
            source_id="repo:Linden-TR/ziwei-doushu-skill",
            source_name="ziwei-doushu-skill Zhongzhou school reference",
            domain="metaphysics.ziwei",
            source_role="SKILL",
            consumption_mode="READ_AS_SKILL",
            capabilities_provided=("school_methodology", "interpretation_reference"),
            upstream_repo="Linden-TR/ziwei-doushu-skill",
            pinned_ref="a842dd65dabdc4ce42ec9688b88ae876858a9977",
            license="MIT",
            authority_scope="SCHOOL_SPECIFIC_INTERPRETATION_GUIDE",
            authority_domains=("metaphysics.ziwei",),
            school_or_jurisdiction="ZHONGZHOU_PAI",
            evidence_pointers=("source/chinese-metaphysics/research/ziwei-doushu-skill/RESEARCH.md",),
            limitations=("SCHOOL_A_IS_NOT_SCHOOL_B", "DO_NOT_MERGE_WITH_OTHER_SCHOOLS"),
        ),
        DomainSourceRecord(
            source_id="repo:wuandyA/ziwei",
            source_name="wuandyA/ziwei Sanhe school alternative calculation",
            domain="metaphysics.ziwei",
            source_role="RESEARCH_ONLY",
            consumption_mode="ISOLATED_RESEARCH_DOSSIER",
            capabilities_provided=("alternative_ziwei_calculation",),
            upstream_repo="wuandyA/ziwei",
            pinned_ref="4531626403a0c645f1e538a9ed145ffec8799420",
            license="MIT",
            authority_scope="INDEPENDENT_RESEARCH_DOSSIER_ONLY",
            authority_domains=("metaphysics.ziwei",),
            school_or_jurisdiction="SANHE_PAI",
            evidence_pointers=("source/chinese-metaphysics/research/ziwei-wuandyA/RESEARCH.md",),
            limitations=("RESEARCH_ONLY", "ISOLATED_DOSSIER"),
        ),
        DomainSourceRecord(
            source_id="repo:muyen/meihua-yishu",
            source_name="meihua-yishu calculation engine",
            domain="metaphysics.meihua",
            source_role="EXECUTABLE_ENGINE",
            consumption_mode="RUN_AS_ENGINE",
            capabilities_provided=("meihua_hexagram_calculation",),
            upstream_repo="muyen/meihua-yishu",
            pinned_ref="8a9a5e0f482dd225bfe4a1c52c2ae5546228607a",
            license="MIT",
            authority_scope="MEIHUA_HEXAGRAM_CALCULATION_ONLY",
            authority_domains=("metaphysics.meihua",),
            school_or_jurisdiction="MEIHUA_YISHU",
            evidence_pointers=("source/chinese-metaphysics/research/meihua-yishu/RESEARCH.md",),
            limitations=(
                "DETERMINISTIC_OUTPUT_IS_NOT_PREDICTIVE_VALIDITY",
                "DO_NOT_MERGE_WITH_ZIWEI_OR_LIUYAO",
            ),
        ),
        DomainSourceRecord(
            source_id="repo:soom-lupulus/plum-app",
            source_name="plum-app Meihua divination application reference",
            domain="metaphysics.meihua",
            source_role="REFERENCE_IMPLEMENTATION",
            consumption_mode="INSPECT_UI_PATTERN",
            capabilities_provided=("meihua_app_reference",),
            upstream_repo="soom-lupulus/plum-app",
            pinned_ref="5965bdc8e9ca69a3cc7e96be6f1cc585d5032814",
            license="MIT",
            authority_scope="APPLICATION_REFERENCE_ONLY",
            authority_domains=("metaphysics.meihua",),
            school_or_jurisdiction="MEIHUA_YISHU",
            evidence_pointers=("source/chinese-metaphysics/research/plum-app/RESEARCH.md",),
            limitations=("REFERENCE_NOT_INSTALLED", "DO_NOT_MERGE_WITH_ZIWEI"),
        ),
        DomainSourceRecord(
            source_id="repo:xiaoshiyilangzhao1996-droid/yinyo-liuyao",
            source_name="yinyo-liuyao hexagram derivation engine",
            domain="metaphysics.liuyao",
            source_role="EXECUTABLE_ENGINE",
            consumption_mode="RUN_AS_ENGINE",
            capabilities_provided=("liuyao_hexagram_derivation",),
            upstream_repo="xiaoshiyilangzhao1996-droid/yinyo-liuyao",
            pinned_ref="1f67eea0ce5a2c49e6851e4eedce507f9c044dd9",
            license="MIT",
            authority_scope="LIUYAO_CALCULATION_ONLY",
            authority_domains=("metaphysics.liuyao",),
            school_or_jurisdiction="LIUYAO_NAJIA",
            evidence_pointers=("source/chinese-metaphysics/research/yinyo-liuyao/RESEARCH.md",),
            limitations=(
                "DETERMINISTIC_OUTPUT_IS_NOT_PREDICTIVE_VALIDITY",
                "DO_NOT_MERGE_WITH_ZIWEI_OR_MEIHUA",
            ),
        ),
        DomainSourceRecord(
            source_id="repo:Johnson-Jia/liuyao-divination",
            source_name="liuyao-divination method reference",
            domain="metaphysics.liuyao",
            source_role="REFERENCE_IMPLEMENTATION",
            consumption_mode="INSPECT_UI_PATTERN",
            capabilities_provided=("liuyao_app_reference",),
            upstream_repo="Johnson-Jia/liuyao-divination",
            pinned_ref="1a5a78b513c0e7b46dfb29f74043bcf978c32a3e",
            license="MIT",
            authority_scope="LIUYAO_REFERENCE_ONLY",
            authority_domains=("metaphysics.liuyao",),
            school_or_jurisdiction="LIUYAO_NAJIA",
            evidence_pointers=("source/chinese-metaphysics/research/liuyao-divination/RESEARCH.md",),
            limitations=("REFERENCE_NOT_INSTALLED", "DO_NOT_MERGE_WITH_ZIWEI_OR_MEIHUA"),
        ),
    )
