"""P2P Skill Consumption Wire — metadata discovery -> bounded match -> exact load.

This module is not a router.  It composes the canonical capability registry,
the existing single router, and exact repo files into one source-bound handoff.
No skill content is read during DISCOVERY; only selected SKILL.md entrypoints
are loaded.  Skills never widen task permissions or authority.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

try:  # package import in normal P2P runtime
    from .model import CapabilityManifest, load_registry
    from .routing import classify_capabilities
except ImportError:  # legacy focused tests import modules from this directory
    from model import CapabilityManifest, load_registry
    from routing import classify_capabilities


HANDOFF_SCHEMA = "p2p-skill-handoff/1"
RECEIPT_SCHEMA = "p2p-skill-consumption-receipt/1"
MAX_SELECTED_SKILLS = 3
HOST_MODES = {
    "ARENA": "ARENA_EXACT_REPO_READ",
    "CODEX": "CODEX_NATIVE_PROJECT_SKILL",
}
_CLASS_RANK = {"PRIMARY": 3, "SECONDARY": 2, "SUPPORTING": 1}


class SkillConsumptionError(ValueError):
    pass


@dataclass(frozen=True)
class SkillSelection:
    outcome: str
    considered_metadata_count: int
    selected: tuple[str, ...]
    rejected: tuple[str, ...]
    rejection_reasons: tuple[str, ...]
    route: Mapping[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "considered_metadata_count": self.considered_metadata_count,
            "selected": list(self.selected),
            "rejected": list(self.rejected),
            "rejection_reasons": list(self.rejection_reasons),
            "route": dict(self.route),
        }


@dataclass(frozen=True)
class LoadedSkill:
    capability_id: str
    relative_path: str
    sha256: str
    content: str

    def to_dict(self, *, include_content: bool = False) -> dict[str, Any]:
        result = {
            "capability_id": self.capability_id,
            "relative_path": self.relative_path,
            "sha256": self.sha256,
        }
        if include_content:
            result["content"] = self.content
        return result


@dataclass(frozen=True)
class RepoSkillMetadata:
    """Minimal metadata for repo-native skills that lack capability admission."""

    skill_id: str
    declared_name: str
    relative_path: str


def _repo_skill_metadata(root: Path) -> tuple[RepoSkillMetadata, ...]:
    """Discover top-level project skills without loading their instruction body.

    Repo-native skills outside the canonical capability registry are explicit-
    invocation-only.  Reading the YAML frontmatter name mirrors native skill
    discovery while avoiding implicit authority or a second persisted registry.
    """
    skills_dir = root / ".agents" / "skills"
    if not skills_dir.is_dir():
        return ()
    records: list[RepoSkillMetadata] = []
    for directory in sorted(skills_dir.iterdir(), key=lambda p: p.name.lower()):
        entrypoint = directory / "SKILL.md"
        if not directory.is_dir() or not entrypoint.is_file():
            continue
        declared = directory.name
        try:
            with entrypoint.open(
                "r", encoding="utf-8", errors="replace"
            ) as handle:
                first = handle.readline()
                if first.strip() == "---":
                    for index, line in enumerate(handle, start=1):
                        if line.strip() == "---":
                            break
                        if line.lower().startswith("name:"):
                            value = line.split(":", 1)[1].strip().strip("'\"")
                            if value:
                                declared = value
                        if index >= 64:
                            break
        except OSError:
            continue
        records.append(RepoSkillMetadata(
            skill_id=directory.name,
            declared_name=declared,
            relative_path=entrypoint.relative_to(root).as_posix(),
        ))
    return tuple(records)


def _explicit_repo_skill_ids(
    request_text: str,
    explicit_requests: Iterable[str],
    records: Sequence[RepoSkillMetadata],
) -> set[str]:
    """Resolve only explicit $skill/@skill requests for repo-native metadata."""
    requested = {
        str(value or "").strip().lower().lstrip("@$").replace("_", "-")
        for value in explicit_requests
        if str(value or "").strip()
    }
    text = str(request_text or "").lower()
    selected: set[str] = set()
    for record in records:
        aliases = {
            record.skill_id.lower(),
            record.declared_name.lower(),
            record.skill_id.lower().replace("_", "-"),
            record.declared_name.lower().replace("_", "-"),
        }
        aliases = {alias for alias in aliases if alias}
        if requested & aliases:
            selected.add(record.skill_id)
            continue
        for alias in aliases:
            pattern = r"(?<![a-z0-9_-])[$@]" + re.escape(alias) + (
                r"(?=$|[\s,;:.!?()\[\]{}])"
            )
            if re.search(pattern, text):
                selected.add(record.skill_id)
                break
    return selected


def _registry_path(root: Path) -> Path:
    return root / ".p2p" / "system" / "p2p_capabilities" / "capabilities.json"


def _active_skill_manifests(root: Path) -> tuple[CapabilityManifest, ...]:
    registry = load_registry(_registry_path(root))
    return tuple(
        manifest for manifest in registry["parsed"]
        if manifest.type == "SKILL" and manifest.status == "ACTIVE"
    )


def _normalise_explicit(
    explicit_requests: Iterable[str],
    manifests: Sequence[CapabilityManifest],
) -> set[str]:
    by_lower = {m.capability_id.lower(): m.capability_id for m in manifests}
    result: set[str] = set()
    for raw in explicit_requests:
        value = str(raw or "").strip().lower()
        value = value.lstrip("@$")
        aliases = {
            value,
            value.replace("_", "-"),
            value.replace(" ", "-"),
        }
        for alias in aliases:
            if alias in by_lower:
                result.add(by_lower[alias])
    return result


def select_skills_for_task(
    root: str | Path,
    request_text: str,
    *,
    explicit_requests: Iterable[str] = (),
    allowed_skill_ids: Iterable[str] | None = None,
    limit: int = MAX_SELECTED_SKILLS,
) -> SkillSelection:
    """Select at most three skills without creating a second router.

    Canonical ACTIVE skills use the existing P2P router. Repo-native skills
    that have no capability admission are discoverable by frontmatter metadata
    but are explicit-invocation-only ($skill/@skill). Their instruction bodies
    are not loaded until selection.
    """
    project_root = Path(root).resolve()
    repo_metadata = _repo_skill_metadata(project_root)
    manifests = _active_skill_manifests(project_root)
    if allowed_skill_ids is not None:
        allowed = {str(value) for value in allowed_skill_ids if str(value)}
        manifests = tuple(
            manifest for manifest in manifests
            if manifest.capability_id in allowed
        )
    if limit < 1 or limit > MAX_SELECTED_SKILLS:
        raise SkillConsumptionError("SKILL_SELECTION_LIMIT_INVALID")
    explicit = _normalise_explicit(explicit_requests, manifests)
    repo_explicit = _explicit_repo_skill_ids(
        request_text, explicit_requests, repo_metadata
    )
    route = classify_capabilities(str(request_text or ""), manifests)
    manifest_by_id = {m.capability_id: m for m in manifests}
    result_by_id = {
        str(item.get("capability_id")): item
        for item in route.get("results", ())
        if isinstance(item, Mapping)
    }
    candidates: list[tuple[int, int, str]] = []
    rejected: list[str] = []
    reasons: list[str] = []
    for manifest in manifests:
        item = result_by_id.get(manifest.capability_id, {})
        classification = str(item.get("classification") or "NOT_APPLICABLE")
        positive = tuple(item.get("positive_triggers") or ())
        if manifest.capability_id in explicit:
            candidates.append((4, int(item.get("value") or 0), manifest.capability_id))
            continue
        if manifest.invocation_class == "USER_REQUESTED" and not positive:
            rejected.append(manifest.capability_id)
            reasons.append(f"{manifest.capability_id}:USER_REQUEST_REQUIRED")
            continue
        rank = _CLASS_RANK.get(classification, 0)
        if rank:
            candidates.append((rank, int(item.get("value") or 0), manifest.capability_id))
        else:
            rejected.append(manifest.capability_id)
            reason_codes = tuple(item.get("reason_codes") or ())
            reason = reason_codes[0] if reason_codes else "NO_MATCH"
            reasons.append(f"{manifest.capability_id}:{reason}")
    for record in repo_metadata:
        if record.skill_id in repo_explicit:
            # Explicit repo invocation is a deterministic user request.  When
            # the same ID is also canonical the later ranking deduplicates it;
            # when it is not admitted, it remains explicit-only.
            candidates.append((4, 0, record.skill_id))

    candidates.sort(key=lambda value: (-value[0], -value[1], value[2]))
    selected_list: list[str] = []
    overflow: list[str] = []
    for _, _, skill_id in candidates:
        if skill_id in selected_list:
            continue
        if len(selected_list) < limit:
            selected_list.append(skill_id)
        else:
            overflow.append(skill_id)
    selected = tuple(selected_list)
    for capability_id in overflow:
        rejected.append(capability_id)
        reasons.append(f"{capability_id}:BOUNDED_SET_LIMIT")
    if not selected:
        outcome = "NO_SKILL_NEEDED"
    elif len(selected) == 1:
        outcome = "ONE_SKILL"
    else:
        outcome = "BOUNDED_SKILL_SET"
    # Keep a compact metadata-only route snapshot; never attach manifest bodies.
    compact_route = {
        "schema": route.get("schema"),
        "selected": list(route.get("selected") or ()),
        "single_router": bool(route.get("single_router")),
    }
    return SkillSelection(
        outcome=outcome,
        considered_metadata_count=(
            len(manifests)
            + sum(
                1 for record in repo_metadata
                if record.skill_id not in {m.capability_id for m in manifests}
            )
        ),
        selected=selected,
        rejected=tuple(dict.fromkeys(rejected)),
        rejection_reasons=tuple(dict.fromkeys(reasons)),
        route=compact_route,
    )


def _safe_repo_path(root: Path, relative: str) -> Path:
    value = str(relative or "").strip().replace("\\", "/")
    if not value or value.startswith(("/", "~")):
        raise SkillConsumptionError("SKILL_ENTRYPOINT_PATH_INVALID")
    candidate = (root / value).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise SkillConsumptionError("SKILL_ENTRYPOINT_PATH_TRAVERSAL") from exc
    return candidate


def _entrypoint_for(root: Path, manifest: CapabilityManifest) -> str:
    raw = manifest.raw
    provenance = raw.get("UPSTREAM_PROVENANCE")
    provenance = provenance if isinstance(provenance, Mapping) else {}
    integration = provenance.get("integration")
    integration = integration if isinstance(integration, Mapping) else {}
    entrypoint = str(integration.get("entrypoint") or "").strip()
    base = str(
        provenance.get("vendor_path")
        or provenance.get("source_path")
        or provenance.get("path")
        or ""
    ).strip()
    candidates: list[str] = []
    if entrypoint and base:
        candidates.append(f"{base.rstrip('/')}/{entrypoint.lstrip('/')}")
    for pointer in manifest.context_pointers:
        if str(pointer).replace("\\", "/").lower().endswith("/skill.md"):
            candidates.append(str(pointer))
    candidates.append(f".agents/skills/{manifest.capability_id}/SKILL.md")
    for relative in dict.fromkeys(candidates):
        path = _safe_repo_path(root, relative)
        if path.is_file():
            return path.relative_to(root).as_posix()
    raise SkillConsumptionError(
        f"SKILL_ENTRYPOINT_MISSING:{manifest.capability_id}"
    )


def load_selected_skills(
    root: str | Path,
    selected_ids: Sequence[str],
) -> tuple[LoadedSkill, ...]:
    """Load only exact selected SKILL.md files and verify declared hashes."""
    project_root = Path(root).resolve()
    manifests = {
        manifest.capability_id: manifest
        for manifest in _active_skill_manifests(project_root)
    }
    repo_skills = {
        record.skill_id: record
        for record in _repo_skill_metadata(project_root)
    }
    loaded: list[LoadedSkill] = []
    for capability_id in selected_ids:
        skill_id = str(capability_id)
        manifest = manifests.get(skill_id)
        repo_record = repo_skills.get(skill_id)
        if manifest is not None:
            relative = _entrypoint_for(project_root, manifest)
        elif repo_record is not None:
            relative = repo_record.relative_path
        else:
            raise SkillConsumptionError(f"SKILL_ENTRYPOINT_UNKNOWN:{capability_id}")
        path = _safe_repo_path(project_root, relative)
        raw = path.read_bytes()
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise SkillConsumptionError(
                f"SKILL_ENTRYPOINT_NOT_UTF8:{capability_id}"
            ) from exc
        actual = hashlib.sha256(raw).hexdigest()
        provenance = (
            manifest.raw.get("UPSTREAM_PROVENANCE")
            if manifest is not None else {}
        )
        provenance = provenance if isinstance(provenance, Mapping) else {}
        integration = provenance.get("integration")
        integration = integration if isinstance(integration, Mapping) else {}
        expected = str(integration.get("entrypoint_sha256") or "").lower()
        if expected and expected != actual:
            raise SkillConsumptionError(
                f"SKILL_ENTRYPOINT_HASH_MISMATCH:{capability_id}"
            )
        loaded.append(LoadedSkill(
            capability_id=capability_id,
            relative_path=relative,
            sha256=actual,
            content=content,
        ))
    return tuple(loaded)


def prepare_skill_handoff(
    root: str | Path,
    request_text: str,
    *,
    host: str,
    explicit_requests: Iterable[str] = (),
) -> dict[str, Any]:
    """Freeze one deterministic source-bound skill handoff for an executor."""
    host_name = str(host or "").strip().upper()
    mode = HOST_MODES.get(host_name)
    selection = select_skills_for_task(
        root, request_text, explicit_requests=explicit_requests
    )
    if mode is None:
        return {
            "schema": HANDOFF_SCHEMA,
            "SKILL_CHECK": "BLOCKED",
            "SKILLS_CONSIDERED_METADATA_COUNT": selection.considered_metadata_count,
            "SKILLS_SELECTED": list(selection.selected),
            "SKILL_LOAD_STAGE": "MATCH" if selection.selected else "DISCOVERY",
            "SKILL_SOURCE_HASHES": {},
            "SKILL_SOURCE_PATHS": {},
            "SKILL_CONSUMPTION": "BLOCKED",
            "SKILL_HOST_MODE": "UNSUPPORTED",
            "MATERIAL_ALTERNATIVES_REJECTED": list(selection.rejected),
            "REJECTION_REASON": ["HOST_NOT_SUPPORTED_V1"],
            "PERMISSION_WIDENED": "NO",
            "SINGLE_ROUTER_REUSED": "YES",
        }
    if not selection.selected:
        return {
            "schema": HANDOFF_SCHEMA,
            "SKILL_CHECK": "NO_MATCH",
            "SKILLS_CONSIDERED_METADATA_COUNT": selection.considered_metadata_count,
            "SKILLS_SELECTED": [],
            "SKILL_LOAD_STAGE": "DISCOVERY",
            "SKILL_SOURCE_HASHES": {},
            "SKILL_SOURCE_PATHS": {},
            "SKILL_CONSUMPTION": "NO_SKILL_NEEDED",
            "SKILL_HOST_MODE": mode,
            "MATERIAL_ALTERNATIVES_REJECTED": list(selection.rejected),
            "REJECTION_REASON": list(selection.rejection_reasons),
            "PERMISSION_WIDENED": "NO",
            "SINGLE_ROUTER_REUSED": "YES",
        }
    try:
        loaded = load_selected_skills(root, selection.selected)
    except SkillConsumptionError as exc:
        return {
            "schema": HANDOFF_SCHEMA,
            "SKILL_CHECK": "BLOCKED",
            "SKILLS_CONSIDERED_METADATA_COUNT": selection.considered_metadata_count,
            "SKILLS_SELECTED": list(selection.selected),
            "SKILL_LOAD_STAGE": "MATCH",
            "SKILL_SOURCE_HASHES": {},
            "SKILL_SOURCE_PATHS": {},
            "SKILL_CONSUMPTION": "LOAD_FAILED",
            "SKILL_HOST_MODE": mode,
            "MATERIAL_ALTERNATIVES_REJECTED": list(selection.rejected),
            "REJECTION_REASON": [str(exc)],
            "PERMISSION_WIDENED": "NO",
            "SINGLE_ROUTER_REUSED": "YES",
        }
    return {
        "schema": HANDOFF_SCHEMA,
        "SKILL_CHECK": "PASS",
        "SKILLS_CONSIDERED_METADATA_COUNT": selection.considered_metadata_count,
        "SKILLS_SELECTED": [item.capability_id for item in loaded],
        "SKILL_LOAD_STAGE": "LOAD",
        "SKILL_SOURCE_HASHES": {
            item.capability_id: item.sha256 for item in loaded
        },
        "SKILL_SOURCE_PATHS": {
            item.capability_id: item.relative_path for item in loaded
        },
        "SKILL_CONSUMPTION": "EXPECTED",
        "SKILL_HOST_MODE": mode,
        "MATERIAL_ALTERNATIVES_REJECTED": list(selection.rejected),
        "REJECTION_REASON": list(selection.rejection_reasons),
        "PERMISSION_WIDENED": "NO",
        "SINGLE_ROUTER_REUSED": "YES",
    }


def skill_handoff_prompt_lines(handoff: Mapping[str, Any]) -> tuple[str, ...]:
    """Serialize a frozen handoff without embedding skill bodies in the prompt."""
    check = str(handoff.get("SKILL_CHECK") or "BLOCKED")
    selected = tuple(str(v) for v in (handoff.get("SKILLS_SELECTED") or ()))
    hashes = handoff.get("SKILL_SOURCE_HASHES") or {}
    paths = handoff.get("SKILL_SOURCE_PATHS") or {}
    lines = [
        "P2P_SKILL_HANDOFF:",
        f"SKILL_CHECK={check}",
        "SKILLS_SELECTED=" + (",".join(selected) if selected else "NONE"),
        f"SKILL_LOAD_STAGE={handoff.get('SKILL_LOAD_STAGE', 'DISCOVERY')}",
        f"SKILL_HOST_MODE={handoff.get('SKILL_HOST_MODE', 'UNSUPPORTED')}",
        "SKILL_PERMISSION_WIDENED=NO",
    ]
    if check == "PASS":
        lines.extend((
            "Before substantive task execution, read ONLY the exact selected SKILL.md entrypoints below.",
            "After selection, deep-load only references/scripts explicitly declared by those selected skills and only when materially required; never load an unselected skill.",
            "Verify each entrypoint SHA-256 equals the frozen expected hash before using it.",
            "On a missing file or hash mismatch, fail closed with SKILL_CONSUMPTION=LOAD_FAILED; do not substitute or widen the selected set.",
            "Supreme Law / Owner / permissions / task contract outrank all skill guidance.",
        ))
        for capability_id in selected:
            lines.append(
                "SKILL_SOURCE="
                f"{capability_id}|PATH={paths.get(capability_id, '')}"
                f"|SHA256={hashes.get(capability_id, '')}"
            )
        lines.extend((
            "Terminal return must include SKILL_CONSUMPTION_RECEIPT with exact selected ids, hashes, LOAD stage, host mode, CONSUMED, and PERMISSION_WIDENED=NO.",
        ))
    elif check == "NO_MATCH":
        lines.append(
            "No relevant eligible skill was selected. Do not preload unrelated skills. "
            "Terminal return uses SKILL_CONSUMPTION=NO_SKILL_NEEDED."
        )
    else:
        lines.append(
            "Skill handoff is blocked. Do not claim a skill was consumed and do not widen the skill set."
        )
    return tuple(lines)


def validate_consumption_receipt(
    handoff: Mapping[str, Any],
    receipt: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Validate executor self-report against the frozen source-bound handoff."""
    if not isinstance(receipt, Mapping):
        return {"valid": False, "reason_codes": ["SKILL_CONSUMPTION_RECEIPT_MISSING"]}
    reasons: list[str] = []
    if receipt.get("schema") not in (None, RECEIPT_SCHEMA):
        reasons.append("SKILL_CONSUMPTION_RECEIPT_SCHEMA_INVALID")
    expected_check = str(handoff.get("SKILL_CHECK") or "BLOCKED")
    expected_ids = tuple(str(v) for v in (handoff.get("SKILLS_SELECTED") or ()))
    actual_ids = tuple(str(v) for v in (receipt.get("SKILLS_SELECTED") or ()))
    if actual_ids != expected_ids:
        reasons.append("SKILL_SELECTED_SET_MISMATCH")
    if dict(receipt.get("SKILL_SOURCE_HASHES") or {}) != dict(
        handoff.get("SKILL_SOURCE_HASHES") or {}
    ):
        reasons.append("SKILL_SOURCE_HASH_MISMATCH")
    if str(receipt.get("SKILL_HOST_MODE") or "") != str(
        handoff.get("SKILL_HOST_MODE") or ""
    ):
        reasons.append("SKILL_HOST_MODE_MISMATCH")
    if str(receipt.get("PERMISSION_WIDENED") or "UNKNOWN").upper() != "NO":
        reasons.append("SKILL_PERMISSION_WIDENING_REJECTED")
    if expected_check == "PASS":
        if str(receipt.get("SKILL_LOAD_STAGE") or "") != "LOAD":
            reasons.append("SKILL_LOAD_STAGE_MISMATCH")
        if str(receipt.get("SKILL_CONSUMPTION") or "") != "CONSUMED":
            reasons.append("SKILL_NOT_CONSUMED")
    elif expected_check == "NO_MATCH":
        if str(receipt.get("SKILL_CONSUMPTION") or "") != "NO_SKILL_NEEDED":
            reasons.append("SKILL_NO_MATCH_RECEIPT_INVALID")
    else:
        reasons.append("SKILL_HANDOFF_WAS_BLOCKED")
    return {"valid": not reasons, "reason_codes": reasons}


__all__ = [
    "HANDOFF_SCHEMA", "RECEIPT_SCHEMA", "MAX_SELECTED_SKILLS",
    "HOST_MODES", "SkillConsumptionError", "SkillSelection", "LoadedSkill",
    "RepoSkillMetadata",
    "select_skills_for_task", "load_selected_skills", "prepare_skill_handoff",
    "skill_handoff_prompt_lines", "validate_consumption_receipt",
]
