"""C36 ContextManifest — evidence-bound context requirements.

C36 makes context delivery and efficiency auditable. The manifest is the
deterministic, identity-bearing record of WHAT a task requires before any
context is retrieved, packaged, or delivered.

Design rules (per C36 prompt):

- Deterministic identity: identical requirements + source state -> identical
  manifest id/hash. identity() is computed from canonical JSON over sorted
  fields and content hashes only; no timestamps, no randomness.
- Authority classification: items carry an AUTHORITY_CLASS distinguishing
  AUTHORITATIVE, DERIVED, REFERENCE, EVIDENCE, HISTORICAL, UNTRUSTED_EXTERNAL.
  Retrieved external/reference data is context, never automatic authority;
  external input can never silently override canonical project truth.
- Binds to goal/task/role/project/workspace/environment and SOURCE_REVISION.
- Required vs optional, delta_allowed, freshness per item.
- Reuses context.py fingerprinting/pointer normalisation; does not create a
  parallel context authority (all hashing delegates to context_fingerprint).
- No live backend calls. No embedding of large bodies: items carry
  source_pointer + content_hash, not full files.

Schema id: p2p-context-manifest-c36/1
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

from .context import (
    _assert_no_secret_fields,
    _canonical_bytes,
    _normalise_pointer,
    _normalise_pointers,
    context_fingerprint,
)

MANIFEST_SCHEMA_VERSION = "p2p-context-manifest-c36/1"

AUTHORITY_CLASSES = (
    "AUTHORITATIVE",
    "DERIVED",
    "REFERENCE",
    "EVIDENCE",
    "HISTORICAL",
    "UNTRUSTED_EXTERNAL",
)

AUTHORITATIVE_AUTHORITY_CLASSES = ("AUTHORITATIVE", "EVIDENCE")

REQUIRED_OPTIONAL = ("REQUIRED", "OPTIONAL")

class ManifestError(ValueError):
    """Raised when manifest construction or validation fails."""

class ManifestIdentityError(ManifestError):
    """Raised when an identity contract is violated."""

@dataclass(frozen=True)
class ContextManifest:
    """Deterministic record of the context a task requires.

    Field contract mirrors the C36 target pipeline stage "CONTEXT MANIFEST":

      MANIFEST_ID              — deterministic sha256 identity (see identity())
      SCHEMA_VERSION           — MANIFEST_SCHEMA_VERSION
      GOAL_ID / TASK_ID        — governance binding (required text)
      ROLE_ID                  — role binding (optional, task-local default "")
      PROJECT_BINDING          — project identifier (required text)
      WORKSPACE_BINDING        — working directory identity (required text)
      ENVIRONMENT_BINDING      — runtime/environment identity (required text)
      SOURCE_REVISION          — commit/revision the requirements were built on
      CONTEXT_REQUIREMENT_REVISION — revision of the requirement spec itself
      CONTEXT_ITEMS            — frozen list of item dicts
    """

    goal_id: str
    task_id: str
    project_binding: str
    workspace_binding: str
    environment_binding: str
    source_revision: str
    context_requirement_revision: str
    items: tuple[dict[str, Any], ...] = ()
    role_id: str = ""
    schema_version: str = MANIFEST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name in (
            "goal_id",
            "task_id",
            "project_binding",
            "workspace_binding",
            "environment_binding",
            "source_revision",
            "context_requirement_revision",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ManifestError(f"MANIFEST_REQUIRED_BINDING_MISSING: {name}")
        if len(self.goal_id) > 128 or len(self.task_id) > 128:
            raise ManifestError("MANIFEST_BINDING_TOO_LONG")
        normalised = [_normalise_manifest_item(item, index) for index, item in enumerate(self.items)]
        if normalised != list(self.items):
            object.__setattr__(self, "items", tuple(normalised))
        _assert_no_secret_fields({"goal_id": self.goal_id, "items": list(self.items)}, "manifest")

    def identity(self) -> str:
        """Deterministic manifest identity.

        Hashes only identity-bearing fields (bindings, revisions, schema,
        per-item required/delta/freshness/authority/pointer/hash). Content
        bodies are never embedded; the identity changes when the underlying
        authoritative content hash changes (scenario B: source change).
        """
        payload = {
            "schema_version": self.schema_version,
            "goal_id": self.goal_id,
            "task_id": self.task_id,
            "role_id": self.role_id,
            "project_binding": self.project_binding,
            "workspace_binding": self.workspace_binding,
            "environment_binding": self.environment_binding,
            "source_revision": self.source_revision,
            "context_requirement_revision": self.context_requirement_revision,
            "items": tuple(
                {
                    "item_id": item["item_id"],
                    "authority_class": item["authority_class"],
                    "required": item["required"],
                    "delta_allowed": item["delta_allowed"],
                    "freshness": item["freshness"],
                    "source_pointer": item["source_pointer"],
                    "content_hash": item["content_hash"],
                    "expected_use": item["expected_use"],
                }
                for item in self.items
            ),
        }
        return "ctx-manifest-" + context_fingerprint(payload)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "goal_id": self.goal_id,
            "task_id": self.task_id,
            "role_id": self.role_id,
            "project_binding": self.project_binding,
            "workspace_binding": self.workspace_binding,
            "environment_binding": self.environment_binding,
            "source_revision": self.source_revision,
            "context_requirement_revision": self.context_requirement_revision,
            "manifest_identity": self.identity(),
            "items": [dict(item) for item in self.items],
        }

    def required_items(self) -> tuple[dict[str, Any], ...]:
        return tuple(item for item in self.items if item["required"])

    def optional_items(self) -> tuple[dict[str, Any], ...]:
        return tuple(item for item in self.items if not item["required"])

    def frozen(self) -> "ContextManifest":
        """Freeze the manifest: identity is fixed after build. Same object
        contract (frozen dataclass) already prevents mutation; this makes the
        intent explicit for Decision Trace logging."""
        return self


def _normalise_manifest_item(raw: Any, index: int) -> dict[str, Any]:
    """Validate and normalise one context requirement item.

    Required per item: item_id, source_pointer, source_type, authority_class,
    content_hash (hash of the authoritative source bytes — changes when the
    source changes), required/optional, delta_allowed, freshness,
    relevance_reason, scope_binding, permission_class, expected_use.
    """
    if not isinstance(raw, Mapping):
        raise ManifestError(f"MANIFEST_ITEM_NOT_A_MAPPING: {index}")
    item = dict(raw)
    required_fields = (
        "item_id",
        "source_pointer",
        "source_type",
        "authority_class",
        "content_hash",
        "required",
        "delta_allowed",
        "freshness",
        "relevance_reason",
        "scope_binding",
        "permission_class",
        "expected_use",
    )
    for field in required_fields:
        if field not in item or item[field] in ("", None):
            raise ManifestError(f"MANIFEST_ITEM_REQUIRED_FIELD_MISSING: {field}")
    if item["authority_class"] not in AUTHORITY_CLASSES:
        raise ManifestError(f"AUTHORITY_CLASS_INVALID: {item['authority_class']}")
    if item["required"] not in REQUIRED_OPTIONAL:
        raise ManifestError(f"REQUIRED_OPTIONAL_INVALID: {item['required']}")
    if not isinstance(item["delta_allowed"], bool):
        raise ManifestError("DELTA_ALLOWED_INVALID")
    if not isinstance(item["content_hash"], str) or len(item["content_hash"]) != 64:
        raise ManifestError("CONTENT_HASH_INVALID")
    return {
        "item_id": str(item["item_id"])[:128],
        "source_pointer": str(item["source_pointer"])[:2048],
        "source_type": str(item["source_type"])[:64],
        "authority_class": str(item["authority_class"]),
        "content_hash": str(item["content_hash"]),
        "required": item["required"],
        "delta_allowed": item["delta_allowed"],
        "freshness": str(item["freshness"])[:64],
        "relevance_reason": str(item["relevance_reason"])[:512],
        "scope_binding": str(item["scope_binding"])[:256],
        "permission_class": str(item["permission_class"])[:64],
        "expected_use": str(item["expected_use"])[:128],
    }


def build_context_manifest(**fields: Any) -> ContextManifest:
    """Factory that forwards keyword fields to ContextManifest with safe
    item normalisation. Mirrors C35 builder patterns (build_role_execution_
    contract) without importing them."""
    items = fields.pop("items", None) or ()
    return ContextManifest(items=tuple(items), **fields)


def manifest_item_content_hash(content: Any) -> str:
    """Hash authoritative source bytes the same way identity() does, so a
    source-content change produces a different content_hash (scenario B)."""
    _assert_no_secret_fields(content, "manifest_item_content")
    return context_fingerprint(content)


def manifests_identical(first: ContextManifest, second: ContextManifest) -> bool:
    """Determinism check (scenario A): same requirements + source state ->
    same identity. Identity comparison only; to_dict equality would also
    require equal field ordering noise."""
    return first.identity() == second.identity()
