"""P2P Skill Consumption Wire — metadata discovery -> bounded match -> exact load.

This module is not a router.  It composes the canonical capability registry,
the existing single router, and exact repo files into one source-bound handoff.
No skill content is read during DISCOVERY; only selected SKILL.md entrypoints
are loaded.  Skills never widen task permissions or authority.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

try:  # package import in normal P2P runtime
    from .host_executor import HostCapabilityProfile, HostExecutorContractError
    from .host_selection import AVAILABLE, DISCOVERY_SCHEMA, HostDiscoveryRecord
    from .model import CapabilityManifest, load_registry
    from .routing import classify_capabilities
except ImportError:  # legacy focused tests import modules from this directory
    from host_executor import HostCapabilityProfile, HostExecutorContractError
    from host_selection import AVAILABLE, DISCOVERY_SCHEMA, HostDiscoveryRecord
    from model import CapabilityManifest, load_registry
    from routing import classify_capabilities


HANDOFF_SCHEMA = "p2p-skill-handoff/1"
RECEIPT_SCHEMA = "p2p-skill-consumption-receipt/1"
FANOUT_INHERITANCE_SCHEMA = "p2p-skill-fanout-inheritance/1"
MAX_SELECTED_SKILLS = 3
HOST_MODES = {
    "ARENA": "ARENA_EXACT_REPO_READ",
    "CODEX": "CODEX_NATIVE_PROJECT_SKILL",
}
GENERIC_REPO_READ_MODE = "GENERIC_EXACT_REPO_READ"
GENERIC_REPO_READ_EVIDENCE_MAX_AGE_SECONDS = 3600
GENERIC_REPO_READ_MAX_FUTURE_SKEW_SECONDS = 300
TRUSTED_REPO_READ_PROVENANCE_KINDS = frozenset({
    "AUTHENTICATED_GITHUB_CONNECTOR_EXACT_READ",
    "VERIFIED_LOCAL_REPO_EXACT_READ",
})
REPO_BOUND_ENVIRONMENTS = frozenset({
    "LOCAL_PROJECT",
    "REMOTE_COPY",
    "REMOTE_REPOSITORY",
})
_CLASS_RANK = {"PRIMARY": 3, "SECONDARY": 2, "SUPPORTING": 1}


class SkillConsumptionError(ValueError):
    pass


def _host_token(value: object) -> str:
    return (
        str(value or "").strip().upper()
        .replace("-", "_").replace(" ", "_")
    )


def _run_git(root: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=8,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if result.returncode:
        return None
    return result.stdout.strip()


def _normalize_github_repo(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().replace("\\", "/")
    lowered = normalized.lower()
    if lowered.startswith("git@github.com:"):
        slug = normalized.split(":", 1)[1]
    elif "github.com/" in lowered:
        index = lowered.find("github.com/") + len("github.com/")
        slug = normalized[index:]
    else:
        return None
    slug = slug.split("?", 1)[0].split("#", 1)[0].strip("/")
    if slug.lower().endswith(".git"):
        slug = slug[:-4]
    parts = slug.split("/")
    if len(parts) < 2:
        return None
    return "/".join(parts[:2]).lower()


def _canonical_repo_binding(root: Path) -> str | None:
    origin = _run_git(root, "remote", "get-url", "origin")
    return _normalize_github_repo(origin)


def _current_repo_revision(root: Path) -> str | None:
    revision = (_run_git(root, "rev-parse", "HEAD") or "").lower()
    return revision if re.fullmatch(r"[0-9a-f]{40}", revision) else None


def _strict_optional_text(value: object, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise SkillConsumptionError(f"{field}_INVALID")
    return value.strip()


def _coerce_host_discovery_record(
    value: HostDiscoveryRecord | Mapping[str, Any] | None,
) -> HostDiscoveryRecord | None:
    if value is None:
        return None
    if isinstance(value, HostDiscoveryRecord):
        record = value
    else:
        if not isinstance(value, Mapping):
            raise SkillConsumptionError("HOST_DISCOVERY_RECORD_INVALID")
        if value.get("schema") != DISCOVERY_SCHEMA:
            raise SkillConsumptionError("HOST_DISCOVERY_RECORD_SCHEMA_INVALID")
        raw_profile = value.get("profile")
        if not isinstance(raw_profile, Mapping):
            raise SkillConsumptionError("HOST_DISCOVERY_PROFILE_REQUIRED")
        if not isinstance(value.get("host_id"), str):
            raise SkillConsumptionError("HOST_DISCOVERY_HOST_ID_INVALID")
        if not isinstance(value.get("availability"), str):
            raise SkillConsumptionError("HOST_DISCOVERY_AVAILABILITY_INVALID")
        if not isinstance(value.get("observed_at"), str):
            raise SkillConsumptionError("HOST_DISCOVERY_OBSERVED_AT_INVALID")
        if not isinstance(value.get("provenance"), str):
            raise SkillConsumptionError("HOST_DISCOVERY_PROVENANCE_INVALID")
        if not isinstance(value.get("profile_version", "1"), str):
            raise SkillConsumptionError("HOST_DISCOVERY_PROFILE_VERSION_INVALID")
        if type(value.get("active", False)) is not bool:
            raise SkillConsumptionError("HOST_DISCOVERY_ACTIVE_BOOL_REQUIRED")
        if type(value.get("execution_transport_available", False)) is not bool:
            raise SkillConsumptionError(
                "HOST_DISCOVERY_EXECUTION_TRANSPORT_BOOL_REQUIRED"
            )
        burden = value.get("reconciliation_burden", 0)
        if type(burden) is not int or burden < 0:
            raise SkillConsumptionError(
                "HOST_DISCOVERY_RECONCILIATION_BURDEN_INVALID"
            )
        environment_binding = _strict_optional_text(
            value.get("environment_binding"), "HOST_DISCOVERY_ENVIRONMENT_BINDING"
        )
        project_binding = _strict_optional_text(
            value.get("project_binding"), "HOST_DISCOVERY_PROJECT_BINDING"
        )
        try:
            profile = HostCapabilityProfile.from_mapping(raw_profile)
            record = HostDiscoveryRecord(
                host_id=value["host_id"].strip(),
                profile=profile,
                availability=value["availability"].strip(),
                observed_at=value["observed_at"].strip(),
                provenance=value["provenance"].strip(),
                environment_binding=environment_binding,
                project_binding=project_binding,
                profile_version=value.get("profile_version", "1").strip(),
                active=value.get("active", False),
                reconciliation_burden=burden,
                execution_transport_available=value.get(
                    "execution_transport_available", False
                ),
            )
        except (HostExecutorContractError, TypeError, ValueError) as exc:
            raise SkillConsumptionError(
                f"HOST_DISCOVERY_RECORD_INVALID:{exc}"
            ) from exc

    if not isinstance(record.host_id, str) or not record.host_id.strip():
        raise SkillConsumptionError("HOST_DISCOVERY_HOST_ID_INVALID")
    if not isinstance(record.provenance, str) or not record.provenance.strip():
        raise SkillConsumptionError("HOST_DISCOVERY_PROVENANCE_INVALID")
    if not isinstance(record.observed_at, str) or not record.observed_at.strip():
        raise SkillConsumptionError("HOST_DISCOVERY_OBSERVED_AT_INVALID")
    if type(record.active) is not bool:
        raise SkillConsumptionError("HOST_DISCOVERY_ACTIVE_BOOL_REQUIRED")
    if type(record.execution_transport_available) is not bool:
        raise SkillConsumptionError(
            "HOST_DISCOVERY_EXECUTION_TRANSPORT_BOOL_REQUIRED"
        )
    if type(record.reconciliation_burden) is not int:
        raise SkillConsumptionError(
            "HOST_DISCOVERY_RECONCILIATION_BURDEN_INVALID"
        )
    return record


def _evidence_age_seconds(observed_at: str) -> tuple[int | None, str | None]:
    try:
        observed = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
    except ValueError:
        return None, "HOST_DISCOVERY_OBSERVED_AT_INVALID"
    if observed.tzinfo is None:
        return None, "HOST_DISCOVERY_OBSERVED_AT_TIMEZONE_REQUIRED"
    delta = (datetime.now(timezone.utc) - observed.astimezone(timezone.utc)).total_seconds()
    if delta < -GENERIC_REPO_READ_MAX_FUTURE_SKEW_SECONDS:
        return None, "HOST_DISCOVERY_EVIDENCE_FROM_FUTURE"
    return max(0, int(delta)), None


def _validate_repo_read_provenance(
    root: Path,
    record: HostDiscoveryRecord,
) -> str | None:
    expected_repo = _canonical_repo_binding(root)
    expected_revision = _current_repo_revision(root)
    if expected_repo is None:
        return "HOST_CANONICAL_REPO_BINDING_UNAVAILABLE"
    if expected_revision is None:
        return "HOST_CANONICAL_REPO_REVISION_UNAVAILABLE"

    match = re.fullmatch(
        r"([A-Z0-9_]+)\|repo=([^|]+)\|revision=([0-9a-fA-F]{40})",
        record.provenance.strip(),
    )
    if match is None:
        return "HOST_DISCOVERY_PROVENANCE_UNVERIFIED"
    kind, provenance_repo, provenance_revision = match.groups()
    if kind not in TRUSTED_REPO_READ_PROVENANCE_KINDS:
        return "HOST_DISCOVERY_PROVENANCE_UNVERIFIED"
    if provenance_repo.strip().lower() != expected_repo:
        return "HOST_DISCOVERY_PROVENANCE_REPO_MISMATCH"
    if provenance_revision.lower() != expected_revision:
        return "HOST_DISCOVERY_PROVENANCE_REVISION_MISMATCH"
    if not record.project_binding:
        return "HOST_PROJECT_BINDING_REQUIRED"
    if record.project_binding.strip().lower() != expected_repo:
        return "HOST_PROJECT_BINDING_MISMATCH"
    return None


def _resolve_skill_host_mode(
    root: Path,
    host_name: str,
    host_discovery_record: HostDiscoveryRecord | Mapping[str, Any] | None,
) -> tuple[str | None, str | None]:
    """Resolve generic skill transport only from current source-bound evidence."""
    native = HOST_MODES.get(host_name)
    if native is not None:
        return native, None

    record = _coerce_host_discovery_record(host_discovery_record)
    if record is None:
        return None, "HOST_DISCOVERY_RECORD_REQUIRED"

    profile_label = record.profile.host_label
    if not isinstance(profile_label, str) or not profile_label.strip():
        return None, "HOST_DISCOVERY_PROFILE_HOST_LABEL_REQUIRED"
    record_host = _host_token(record.host_id)
    profile_host = _host_token(profile_label)
    if record_host != profile_host:
        return None, "HOST_DISCOVERY_IDENTITY_MISMATCH"
    if record_host != host_name:
        return None, "HOST_DISCOVERY_RECORD_HOST_MISMATCH"

    if record.availability != AVAILABLE:
        return None, f"HOST_AVAILABILITY_{record.availability or 'UNKNOWN'}"
    provenance_reason = _validate_repo_read_provenance(root, record)
    if provenance_reason is not None:
        return None, provenance_reason
    if not record.execution_transport_available:
        return None, "HOST_EXECUTION_TRANSPORT_UNAVAILABLE"

    age, age_reason = _evidence_age_seconds(record.observed_at)
    if age_reason is not None:
        return None, age_reason
    if age is None or age > GENERIC_REPO_READ_EVIDENCE_MAX_AGE_SECONDS:
        return None, f"HOST_DISCOVERY_EVIDENCE_STALE:{age}"

    profile = record.profile
    read_state = profile.state("can_read_files")
    if read_state != "SUPPORTED":
        return None, f"HOST_FILE_READ_CAPABILITY_{read_state}"
    if profile.environment not in REPO_BOUND_ENVIRONMENTS:
        return None, f"HOST_ENVIRONMENT_NOT_REPO_BOUND:{profile.environment}"
    if record.environment_binding != profile.environment:
        return None, "HOST_ENVIRONMENT_BINDING_MISMATCH"
    return GENERIC_REPO_READ_MODE, None


def validate_cached_skill_handoff_host_evidence(
    root: str | Path,
    *,
    host: str,
    skill_handoff: Mapping[str, Any],
    host_discovery_record: HostDiscoveryRecord | Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Revalidate generic host evidence before reissuing an active-session prompt."""
    mode = str(skill_handoff.get("SKILL_HOST_MODE") or "")
    if mode != GENERIC_REPO_READ_MODE:
        return {"valid": True, "reason": None}
    try:
        resolved_mode, reason = _resolve_skill_host_mode(
            Path(root).resolve(),
            _host_token(host),
            host_discovery_record,
        )
    except SkillConsumptionError as exc:
        resolved_mode, reason = None, str(exc)
    return {
        "valid": resolved_mode == GENERIC_REPO_READ_MODE,
        "reason": reason,
    }


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

def _skill_alias(value: object) -> str:
    return (
        str(value or "").strip().lower().lstrip("@$")
        .replace("_", "-").replace(" ", "-")
    )


def _resolve_required_skill_ids(
    root: Path,
    required_skills: Iterable[str],
) -> tuple[str, ...]:
    """Resolve prompt-declared required skills to exact repo skill IDs.

    This validates existing metadata only; it does not create a second router.
    Every required skill must resolve before executor handoff.
    """
    raw_items = tuple(required_skills)
    if not raw_items:
        return ()
    if len(raw_items) > MAX_SELECTED_SKILLS:
        raise SkillConsumptionError("REQUIRED_SKILL_SET_LIMIT_EXCEEDED")

    aliases: dict[str, set[str]] = {}
    for manifest in _active_skill_manifests(root):
        aliases.setdefault(_skill_alias(manifest.capability_id), set()).add(
            manifest.capability_id
        )
    for record in _repo_skill_metadata(root):
        for alias in (record.skill_id, record.declared_name):
            key = _skill_alias(alias)
            if key:
                aliases.setdefault(key, set()).add(record.skill_id)

    resolved: list[str] = []
    for raw in raw_items:
        key = _skill_alias(raw)
        if not key:
            raise SkillConsumptionError("REQUIRED_SKILL_EMPTY")
        matches = aliases.get(key, set())
        if not matches:
            raise SkillConsumptionError(
                f"REQUIRED_SKILL_NOT_FOUND:{str(raw).strip()}"
            )
        if len(matches) != 1:
            raise SkillConsumptionError(
                f"REQUIRED_SKILL_AMBIGUOUS:{str(raw).strip()}"
            )
        skill_id = next(iter(matches))
        if skill_id not in resolved:
            resolved.append(skill_id)
    if len(resolved) > MAX_SELECTED_SKILLS:
        raise SkillConsumptionError("REQUIRED_SKILL_SET_LIMIT_EXCEEDED")
    return tuple(resolved)


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
    required_skills: Iterable[str] = (),
    host_discovery_record: HostDiscoveryRecord | Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Freeze one deterministic source-bound skill handoff for an executor.

    required_skills is a prompt-writer contract: every named skill must
    resolve, fit the bounded set, load exactly, and appear in the executor
    handoff. Narrative prose alone never satisfies this requirement.
    """
    project_root = Path(root).resolve()
    host_name = _host_token(host)
    native_mode = HOST_MODES.get(host_name)
    try:
        required_ids = _resolve_required_skill_ids(
            project_root, required_skills
        )
    except SkillConsumptionError as exc:
        return {
            "schema": HANDOFF_SCHEMA,
            "SKILL_CHECK": "BLOCKED",
            "REQUIRED_SKILLS": [],
            "SKILLS_CONSIDERED_METADATA_COUNT": 0,
            "SKILLS_SELECTED": [],
            "SKILL_LOAD_STAGE": "DISCOVERY",
            "SKILL_SOURCE_HASHES": {},
            "SKILL_SOURCE_PATHS": {},
            "SKILL_CONSUMPTION": "BLOCKED",
            "SKILL_HOST_MODE": native_mode or "UNRESOLVED",
            "MATERIAL_ALTERNATIVES_REJECTED": [],
            "REJECTION_REASON": [str(exc)],
            "PERMISSION_WIDENED": "NO",
            "SINGLE_ROUTER_REUSED": "YES",
        }
    combined_explicit = tuple(explicit_requests) + required_ids
    selection = select_skills_for_task(
        project_root,
        request_text,
        explicit_requests=combined_explicit,
    )
    missing_required = tuple(
        skill_id for skill_id in required_ids
        if skill_id not in selection.selected
    )
    if missing_required:
        return {
            "schema": HANDOFF_SCHEMA,
            "SKILL_CHECK": "BLOCKED",
            "REQUIRED_SKILLS": list(required_ids),
            "SKILLS_CONSIDERED_METADATA_COUNT": selection.considered_metadata_count,
            "SKILLS_SELECTED": list(selection.selected),
            "SKILL_LOAD_STAGE": "MATCH",
            "SKILL_SOURCE_HASHES": {},
            "SKILL_SOURCE_PATHS": {},
            "SKILL_CONSUMPTION": "BLOCKED",
            "SKILL_HOST_MODE": native_mode or "UNRESOLVED",
            "MATERIAL_ALTERNATIVES_REJECTED": list(selection.rejected),
            "REJECTION_REASON": [
                f"REQUIRED_SKILL_NOT_SELECTED:{skill_id}"
                for skill_id in missing_required
            ],
            "PERMISSION_WIDENED": "NO",
            "SINGLE_ROUTER_REUSED": "YES",
        }
    if not selection.selected:
        return {
            "schema": HANDOFF_SCHEMA,
            "SKILL_CHECK": "NO_MATCH",
            "REQUIRED_SKILLS": list(required_ids),
            "SKILLS_CONSIDERED_METADATA_COUNT": selection.considered_metadata_count,
            "SKILLS_SELECTED": [],
            "SKILL_LOAD_STAGE": "DISCOVERY",
            "SKILL_SOURCE_HASHES": {},
            "SKILL_SOURCE_PATHS": {},
            "SKILL_CONSUMPTION": "NO_SKILL_NEEDED",
            "SKILL_HOST_MODE": native_mode or "NOT_REQUIRED",
            "MATERIAL_ALTERNATIVES_REJECTED": list(selection.rejected),
            "REJECTION_REASON": list(selection.rejection_reasons),
            "PERMISSION_WIDENED": "NO",
            "SINGLE_ROUTER_REUSED": "YES",
        }
    try:
        mode, host_reason = _resolve_skill_host_mode(
            project_root, host_name, host_discovery_record
        )
    except SkillConsumptionError as exc:
        mode, host_reason = None, str(exc)
    if mode is None:
        return {
            "schema": HANDOFF_SCHEMA,
            "SKILL_CHECK": "BLOCKED",
            "REQUIRED_SKILLS": list(required_ids),
            "SKILLS_CONSIDERED_METADATA_COUNT": selection.considered_metadata_count,
            "SKILLS_SELECTED": list(selection.selected),
            "SKILL_LOAD_STAGE": "MATCH",
            "SKILL_SOURCE_HASHES": {},
            "SKILL_SOURCE_PATHS": {},
            "SKILL_CONSUMPTION": "BLOCKED",
            "SKILL_HOST_MODE": "UNSUPPORTED",
            "MATERIAL_ALTERNATIVES_REJECTED": list(selection.rejected),
            "REJECTION_REASON": [host_reason or "HOST_NOT_SUPPORTED_V1"],
            "PERMISSION_WIDENED": "NO",
            "SINGLE_ROUTER_REUSED": "YES",
        }
    try:
        loaded = load_selected_skills(root, selection.selected)
    except SkillConsumptionError as exc:
        return {
            "schema": HANDOFF_SCHEMA,
            "SKILL_CHECK": "BLOCKED",
            "REQUIRED_SKILLS": list(required_ids),
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
        "REQUIRED_SKILLS": list(required_ids),
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



def _frozen_skill_handoff_payload(
    handoff: Mapping[str, Any],
) -> dict[str, Any]:
    """Return the exact immutable subset ORCA candidates are allowed to share.

    Selection has already happened before fanout.  This function never routes,
    reselects, loads an extra skill, or grants permission; it only normalizes
    the source-bound handoff that every candidate must reference identically.
    """
    if not isinstance(handoff, Mapping):
        raise SkillConsumptionError("SKILL_HANDOFF_INVALID")
    if str(handoff.get("schema") or "") != HANDOFF_SCHEMA:
        raise SkillConsumptionError("SKILL_HANDOFF_SCHEMA_INVALID")
    check = str(handoff.get("SKILL_CHECK") or "")
    if check not in ("PASS", "NO_MATCH"):
        raise SkillConsumptionError("SKILL_HANDOFF_NOT_INHERITABLE")
    if str(handoff.get("PERMISSION_WIDENED") or "").upper() != "NO":
        raise SkillConsumptionError("SKILL_PERMISSION_WIDENING_REJECTED")
    if str(handoff.get("SINGLE_ROUTER_REUSED") or "").upper() != "YES":
        raise SkillConsumptionError("SKILL_SINGLE_ROUTER_INVARIANT_REQUIRED")

    selected = tuple(str(v) for v in (handoff.get("SKILLS_SELECTED") or ()))
    required = tuple(str(v) for v in (handoff.get("REQUIRED_SKILLS") or ()))
    if len(selected) != len(set(selected)):
        raise SkillConsumptionError("SKILL_SELECTED_SET_DUPLICATE")
    if len(required) != len(set(required)):
        raise SkillConsumptionError("REQUIRED_SKILL_SET_DUPLICATE")
    if any(skill_id not in selected for skill_id in required):
        raise SkillConsumptionError("REQUIRED_SKILL_SET_NOT_SELECTED")
    hashes = {
        str(k): str(v).lower()
        for k, v in dict(handoff.get("SKILL_SOURCE_HASHES") or {}).items()
    }
    paths = {
        str(k): str(v)
        for k, v in dict(handoff.get("SKILL_SOURCE_PATHS") or {}).items()
    }
    if check == "PASS":
        if not selected or str(handoff.get("SKILL_LOAD_STAGE") or "") != "LOAD":
            raise SkillConsumptionError("SKILL_HANDOFF_PASS_STATE_INVALID")
        if set(hashes) != set(selected) or set(paths) != set(selected):
            raise SkillConsumptionError("SKILL_HANDOFF_SOURCE_SET_MISMATCH")
        if any(re.fullmatch(r"[0-9a-f]{64}", digest) is None
               for digest in hashes.values()):
            raise SkillConsumptionError("SKILL_HANDOFF_SOURCE_HASH_INVALID")
        if any(not path or path.startswith(("/", "~")) for path in paths.values()):
            raise SkillConsumptionError("SKILL_HANDOFF_SOURCE_PATH_INVALID")
    else:
        if selected or hashes or paths:
            raise SkillConsumptionError("SKILL_NO_MATCH_MUST_BE_EMPTY")

    return {
        "schema": HANDOFF_SCHEMA,
        "SKILL_CHECK": check,
        "REQUIRED_SKILLS": list(required),
        "SKILLS_SELECTED": list(selected),
        "SKILL_LOAD_STAGE": str(
            handoff.get("SKILL_LOAD_STAGE") or "DISCOVERY"
        ),
        "SKILL_SOURCE_HASHES": hashes,
        "SKILL_SOURCE_PATHS": paths,
        "SKILL_HOST_MODE": str(handoff.get("SKILL_HOST_MODE") or ""),
        "SKILL_CONSUMPTION": str(handoff.get("SKILL_CONSUMPTION") or ""),
        "PERMISSION_WIDENED": "NO",
        "SINGLE_ROUTER_REUSED": "YES",
    }


def freeze_skill_handoff_for_orca_candidates(
    handoff: Mapping[str, Any],
    candidate_ids: Sequence[str],
) -> dict[str, Any]:
    """Bind one pre-fanout skill selection identically to every ORCA candidate.

    Candidates receive only a fingerprint reference to ONE frozen handoff.
    There is no candidate-local selection surface, so fanout cannot widen or
    swap the selected set without invalidating the inheritance record.
    """
    if isinstance(candidate_ids, (str, bytes, bytearray, dict, set, frozenset)):
        raise SkillConsumptionError("ORCA_CANDIDATE_IDS_INVALID")
    ids = tuple(str(value or "").strip() for value in candidate_ids)
    if not ids or any(not value for value in ids):
        raise SkillConsumptionError("ORCA_CANDIDATE_IDS_INVALID")
    if len(ids) != len(set(ids)):
        raise SkillConsumptionError("ORCA_CANDIDATE_IDS_DUPLICATE")
    try:
        from .orca_candidate_fanout import HARD_FANOUT_CAP
    except ImportError:
        from orca_candidate_fanout import HARD_FANOUT_CAP
    if len(ids) > HARD_FANOUT_CAP:
        raise SkillConsumptionError("ORCA_CANDIDATE_FANOUT_CAP_EXCEEDED")

    frozen = _frozen_skill_handoff_payload(handoff)
    fingerprint = hashlib.sha256(json.dumps(
        frozen,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
    return {
        "schema": FANOUT_INHERITANCE_SCHEMA,
        "FROZEN_SKILL_HANDOFF": frozen,
        "FROZEN_SKILL_HANDOFF_FINGERPRINT": fingerprint,
        "CANDIDATE_BINDINGS": [
            {
                "candidate_id": candidate_id,
                "skill_handoff_fingerprint": fingerprint,
            }
            for candidate_id in ids
        ],
        "CANDIDATE_SKILL_RESELECTION": "FORBIDDEN",
        "PERMISSION_WIDENED": "NO",
    }


def validate_orca_skill_inheritance(
    inheritance: Mapping[str, Any] | None,
    handoff: Mapping[str, Any],
    candidate_ids: Sequence[str],
) -> dict[str, Any]:
    """Fail closed when any ORCA candidate diverges from the frozen handoff."""
    try:
        expected = freeze_skill_handoff_for_orca_candidates(
            handoff, candidate_ids
        )
    except (SkillConsumptionError, TypeError, ValueError) as exc:
        return {
            "valid": False,
            "reason_codes": [f"EXPECTED_INHERITANCE_INVALID:{exc}"],
        }
    if not isinstance(inheritance, Mapping):
        return {
            "valid": False,
            "reason_codes": ["SKILL_FANOUT_INHERITANCE_MISSING"],
        }

    reasons: list[str] = []
    if inheritance.get("schema") != FANOUT_INHERITANCE_SCHEMA:
        reasons.append("SKILL_FANOUT_INHERITANCE_SCHEMA_INVALID")
    if inheritance.get("FROZEN_SKILL_HANDOFF") != expected[
            "FROZEN_SKILL_HANDOFF"]:
        reasons.append("FROZEN_SKILL_HANDOFF_MISMATCH")
    if str(inheritance.get("FROZEN_SKILL_HANDOFF_FINGERPRINT") or "") != (
            expected["FROZEN_SKILL_HANDOFF_FINGERPRINT"]):
        reasons.append("FROZEN_SKILL_HANDOFF_FINGERPRINT_MISMATCH")
    if list(inheritance.get("CANDIDATE_BINDINGS") or []) != expected[
            "CANDIDATE_BINDINGS"]:
        reasons.append("ORCA_CANDIDATE_SKILL_BINDING_MISMATCH")
    if str(inheritance.get("CANDIDATE_SKILL_RESELECTION") or "") != "FORBIDDEN":
        reasons.append("ORCA_CANDIDATE_RESELECTION_NOT_FORBIDDEN")
    if str(inheritance.get("PERMISSION_WIDENED") or "UNKNOWN").upper() != "NO":
        reasons.append("SKILL_PERMISSION_WIDENING_REJECTED")
    return {"valid": not reasons, "reason_codes": reasons}


def skill_handoff_prompt_lines(handoff: Mapping[str, Any]) -> tuple[str, ...]:
    """Serialize a frozen handoff without embedding skill bodies in the prompt."""
    check = str(handoff.get("SKILL_CHECK") or "BLOCKED")
    selected = tuple(str(v) for v in (handoff.get("SKILLS_SELECTED") or ()))
    hashes = handoff.get("SKILL_SOURCE_HASHES") or {}
    paths = handoff.get("SKILL_SOURCE_PATHS") or {}
    required = tuple(str(v) for v in (handoff.get("REQUIRED_SKILLS") or ()))
    lines = [
        "P2P_SKILL_HANDOFF:",
        f"SKILL_CHECK={check}",
        "REQUIRED_SKILLS=" + (",".join(required) if required else "NONE"),
        "SKILLS_SELECTED=" + (",".join(selected) if selected else "NONE"),
        f"SKILL_LOAD_STAGE={handoff.get('SKILL_LOAD_STAGE', 'DISCOVERY')}",
        f"SKILL_HOST_MODE={handoff.get('SKILL_HOST_MODE', 'UNSUPPORTED')}",
        "SKILL_PERMISSION_WIDENED=NO",
    ]
    if check == "PASS":
        lines.extend((
            "Every skill listed in REQUIRED_SKILLS is mandatory for this executor turn. Read and apply every required skill; omission is a failed handoff.",
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
    required_ids = tuple(str(v) for v in (handoff.get("REQUIRED_SKILLS") or ()))
    actual_ids = tuple(str(v) for v in (receipt.get("SKILLS_SELECTED") or ()))
    if any(skill_id not in expected_ids for skill_id in required_ids):
        reasons.append("REQUIRED_SKILL_SET_NOT_SELECTED")
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
    "HANDOFF_SCHEMA", "RECEIPT_SCHEMA", "FANOUT_INHERITANCE_SCHEMA",
    "MAX_SELECTED_SKILLS",
    "HOST_MODES", "SkillConsumptionError", "SkillSelection", "LoadedSkill",
    "RepoSkillMetadata",
    "select_skills_for_task", "load_selected_skills", "prepare_skill_handoff",
    "freeze_skill_handoff_for_orca_candidates",
    "validate_orca_skill_inheritance",
    "skill_handoff_prompt_lines", "validate_consumption_receipt",
]
