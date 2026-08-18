"""C36 ContextCache — evidence-bound context reuse with provenance.

A cache entry is NOT a second source of truth. It is a memoization record
bound to:

  CONTENT_HASH | SOURCE_POINTER | SOURCE_REVISION | AUTHORITY_CLASS |
  CREATED_AT | FRESHNESS_POLICY | TRANSFORMATION_FINGERPRINT

Rules:

- CACHE_HIT requires identity AND freshness evidence: same source revision
  and content hash as the authoritative source. Same path/name is not enough
  (scenario F: same path, different authoritative content -> STALE).
- Authoritative REQUIRED context with stale content fails CLOSED: never
  silently reused (scenario F, prompt: "STALE_CACHE must fail closed for
  authoritative required context").
- Cache miss is not an error (CACHE_MISS is normal).
- Transformations (summary/compression/chunking) preserve source pointers,
  source hashes, transformation_id/version, output hash, and measurable
  coverage. Transformed context is never claimed lossless without proof.
- Freshness policies: STRICT (any revision change invalidates),
  DAILY_DIGEST, SESSION, NEVER_STALE (allowed only for non-authoritative).

No live backend calls. Deterministic by construction; time-dependent
freshness uses explicit timestamps supplied by the caller, so tests can
advance "time" without wall-clock dependence.
"""
from __future__ import annotations

import hashlib
from typing import Any, Iterable, Mapping

from .context import _canonical_bytes

CACHE_SCHEMA_VERSION = "p2p-context-cache-c36/1"

FRESHNESS_POLICIES = ("STRICT", "DAILY_DIGEST", "SESSION", "NEVER_STALE")

CACHE_DECISIONS = ("CACHE_HIT_VERIFIED", "CACHE_MISS", "CACHE_STALE_REJECTED")

AUTHORITATIVE_CLASSES = ("AUTHORITATIVE", "EVIDENCE")


class ContextCacheError(ValueError):
    """Raised when cache entry or decision is malformed."""

class StaleCacheError(ContextCacheError):
    """Raised when an authoritative required cache entry is stale (fail closed)."""


def _fingerprint(payload: Any) -> str:
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def make_cache_entry(
    *,
    content_hash: str,
    source_pointer: str,
    source_revision: str,
    authority_class: str,
    created_at: str,
    freshness_policy: str = "STRICT",
    transformation_fingerprint: str | None = None,
) -> dict[str, Any]:
    """Create a cache entry with full identity provenance."""
    if freshness_policy not in FRESHNESS_POLICIES:
        raise ContextCacheError(f"FRESHNESS_POLICY_INVALID: {freshness_policy}")
    if not content_hash or not source_pointer or not source_revision or not authority_class or not created_at:
        raise ContextCacheError("CACHE_ENTRY_REQUIRED_FIELD_MISSING")
    identity_fields = (content_hash, source_pointer, source_revision, authority_class,
                       freshness_policy, transformation_fingerprint or "")
    return {
        "schema": CACHE_SCHEMA_VERSION,
        "content_hash": content_hash,
        "source_pointer": source_pointer,
        "source_revision": source_revision,
        "authority_class": authority_class,
        "created_at": created_at,
        "freshness_policy": freshness_policy,
        "transformation_fingerprint": transformation_fingerprint,
        "cache_identity": "ctx-cache-" + _fingerprint(identity_fields),
    }


def cache_entry_is_fresh(
    entry: Mapping[str, Any],
    current_source_revision: str,
    current_content_hash: str,
    current_timestamp: str | None = None,
) -> bool:
    """Identity + freshness evidence required for a valid hit (scenario G).

    Same path/name alone never validates a hit (scenario F)."""
    if entry.get("source_revision") != current_source_revision:
        return False
    if entry.get("content_hash") != current_content_hash:
        return False
    policy = entry.get("freshness_policy", "STRICT")
    if policy == "NEVER_STALE":
        return True
    if policy == "STRICT":
        return True  # revision + hash already matched above
    if policy == "SESSION":
        return entry.get("session_timestamp", "") == (current_timestamp or "")
    if policy == "DAILY_DIGEST":
        return (entry.get("created_at") or "")[:10] == (current_timestamp or "")[:10]
    return False


def verify_cache(
    entry: Mapping[str, Any],
    current_source_revision: str,
    current_content_hash: str,
    item_required: bool = False,
    item_authority: str | None = None,
    current_timestamp: str | None = None,
) -> dict[str, Any]:
    """Scenario F/G: verified hit vs stale rejection.

    Authoritative required context that fails freshness fails CLOSED:
    StaleCacheError instead of a silent MISS with reuse.
    """
    if not entry:
        return {"decision": "CACHE_MISS"}
    fresh = cache_entry_is_fresh(entry, current_source_revision, current_content_hash, current_timestamp)
    if fresh:
        return {"decision": "CACHE_HIT_VERIFIED", "cache_identity": entry.get("cache_identity")}
    is_authoritative_required = (
        item_required and (item_authority in AUTHORITATIVE_CLASSES)
    )
    if is_authoritative_required:
        raise StaleCacheError("AUTHORITATIVE_REQUIRED_CONTEXT_STALE_REJECTED")
    return {"decision": "CACHE_STALE_REJECTED"}


def make_transformation_provenance(
    *,
    source_pointers: tuple[str, ...],
    source_hashes: tuple[str, ...],
    transformation_id: str,
    transformation_version: str,
    output_hash: str,
    coverage: str = "UNKNOWN",
    lossless_claim: bool = False,
) -> dict[str, Any]:
    """Scenario H: summarize/compress/chunk while preserving provenance.

    ``lossless_claim`` may be True only with explicit proof (a deterministic
    round-trip verification record); otherwise transformed context is never
    claimed lossless.
    """
    if not source_pointers or not source_hashes or not transformation_id or not transformation_version or not output_hash:
        raise ContextCacheError("TRANSFORMATION_PROVENANCE_REQUIRED_FIELD_MISSING")
    if len(source_pointers) != len(source_hashes):
        raise ContextCacheError("TRANSFORMATION_SOURCE_HASH_MISMATCH")
    fingerprint = _fingerprint((
        tuple(source_pointers), tuple(source_hashes),
        transformation_id, transformation_version, coverage,
        str(output_hash),
    ))
    return {
        "schema": "p2p-transformation-provenance-c36/1",
        "source_pointers": list(source_pointers),
        "source_hashes": list(source_hashes),
        "transformation_id": transformation_id,
        "transformation_version": transformation_version,
        "output_hash": output_hash,
        "coverage": coverage,
        "lossless": bool(lossless_claim),
        "provenance_fingerprint": "ctx-xform-" + fingerprint,
    }
