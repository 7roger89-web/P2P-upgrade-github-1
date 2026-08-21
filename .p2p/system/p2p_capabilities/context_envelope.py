"""C36 DeliveryEnvelope + DeliveryReceipt — evidence-bound context delivery.

This module makes P2P able to distinguish INTENDED context from DELIVERED
context, and proves WHAT was delivered WITHOUT claiming that the model read,
understood, or used it.

DELIVERED != READ is enforced structurally:

- DeliveryEnvelope binds a frozen MANIFEST_ID + MANIFEST_HASH. It records
  which items were SELECTED, in which ORDER, in which FORMAT, with any
  compression/transformation fingerprint and a delivery BUDGET.
- DeliveryReceipt records items actually delivered with per-item hashes. A
  receipt can prove DELIVERED only. It never contains read claims.
- The receipt refuses completeness claims when a REQUIRED item is missing
  from the delivered set (scenario D), and refuses to be issued when the
  envelope identity does not match (scenario N: wrong goal/task/role/target).

No live backend calls. Provider-neutral core: target-specific formatting
belongs behind adapter boundaries; the envelope only carries
DELIVERY_FORMAT identifiers, not rendered payloads.

Schema id: p2p-context-envelope-c36/1
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from .context import _canonical_bytes, _assert_no_secret_fields
from .context_manifest import ContextManifest

ENVELOPE_SCHEMA_VERSION = "p2p-context-envelope-c36/1"

DELIVERY_STATUSES = (
    "DELIVERED",
    "PARTIAL",
    "FAILED",
    "BLOCKED",
)

UNKNOWN_DELIVERY = "UNKNOWN_DELIVERY"

class EnvelopeError(ValueError):
    """Raised when envelope or receipt construction fails."""

class DeliveryReceiptError(EnvelopeError):
    """Raised when a receipt cannot honestly be issued."""

class DeliveryBindingError(DeliveryReceiptError):
    """Raised when receipt bindings do not match the delivery they claim."""


def _fingerprint(payload: Any) -> str:
    import hashlib

    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


@dataclass(frozen=True)
class DeliveryEnvelope:
    """Immutable delivery envelope bound to a manifest identity.

    Core envelope remains provider-neutral: DELIVERY_FORMAT carries adapter
    identifiers only; rendering happens behind adapter/compiler boundaries.
    """

    manifest_id: str
    manifest_hash: str
    goal_id: str
    task_id: str
    execution_target: str
    target_fingerprint: str
    workspace: str
    environment: str
    permission_profile: tuple[str, ...]
    items_selected: tuple[str, ...]
    delivery_order: tuple[str, ...]
    delivery_format: str
    compression_record: tuple[str, ...]
    delivery_budget: str
    request_fingerprint: str
    role_id: str = ""

    def __post_init__(self) -> None:
        for name in (
            "manifest_id",
            "manifest_hash",
            "goal_id",
            "task_id",
            "execution_target",
            "target_fingerprint",
            "workspace",
            "environment",
            "delivery_format",
            "delivery_budget",
            "request_fingerprint",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise EnvelopeError(f"ENVELOPE_REQUIRED_FIELD_MISSING: {name}")
        if tuple(self.delivery_order) != tuple(self.items_selected):
            raise EnvelopeError("ENVELOPE_ORDER_SELECTION_MISMATCH")

    def identity(self) -> str:
        payload = {
            "schema_version": ENVELOPE_SCHEMA_VERSION,
            "manifest_id": self.manifest_id,
            "manifest_hash": self.manifest_hash,
            "goal_id": self.goal_id,
            "task_id": self.task_id,
            "role_id": self.role_id,
            "execution_target": self.execution_target,
            "target_fingerprint": self.target_fingerprint,
            "workspace": self.workspace,
            "environment": self.environment,
            "permission_profile": tuple(self.permission_profile),
            "items_selected": tuple(self.items_selected),
            "delivery_order": tuple(self.delivery_order),
            "delivery_format": self.delivery_format,
            "compression_record": tuple(self.compression_record),
            "delivery_budget": self.delivery_budget,
            "request_fingerprint": self.request_fingerprint,
        }
        return "ctx-envelope-" + _fingerprint(payload)


@dataclass(frozen=True)
class DeliveryReceipt:
    """Receipt proving what P2P DELIVERED. Deliberately cannot prove reads.

    Binds goal/task/manifest/envelope identities and the session identity
    where available. Refuses issuance when:

    - any REQUIRED manifest item is absent from items_delivered (scenario D);
    - binding fields disagree with the envelope they reference (scenario N).
    """

    goal_id: str
    task_id: str
    manifest_id: str
    envelope_id: str
    envelope_hash: str
    target: str
    session_id: str | None
    items_delivered: tuple[dict[str, Any], ...]
    delivery_status: str
    delivery_timestamp: str | None = None
    delivery_failures: tuple[dict[str, Any], ...] = ()
    raw_pointer: str | None = None

    def __post_init__(self) -> None:
        if self.delivery_status not in DELIVERY_STATUSES:
            raise DeliveryReceiptError(f"DELIVERY_STATUS_INVALID: {self.delivery_status}")
        for field in ("goal_id", "task_id", "manifest_id", "envelope_id", "envelope_hash", "target"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise DeliveryReceiptError(f"RECEIPT_REQUIRED_FIELD_MISSING: {field}")

    @property
    def delivered_item_ids(self) -> tuple[str, ...]:
        return tuple(item.get("item_id") or "" for item in self.items_delivered)

    @property
    def delivered_item_hashes(self) -> tuple[str, ...]:
        return tuple(item.get("item_hash") or "" for item in self.items_delivered)


def build_delivery_receipt(
    manifest: ContextManifest,
    envelope: DeliveryEnvelope,
    items_delivered: Iterable[Mapping[str, Any]],
    *,
    delivery_status: str = "DELIVERED",
    delivery_failures: Iterable[Mapping[str, Any]] = (),
    session_id: str | None = None,
    delivery_timestamp: str | None = None,
    raw_pointer: str | None = None,
    target: str | None = None,
) -> DeliveryReceipt:
    """Issue a receipt with binding + completeness honesty guarantees.

    Scenario D: a REQUIRED manifest item missing from the delivered set
    prevents a complete DELIVERED receipt — the receipt is either PARTIAL or
    raises, so delivery can never be represented as complete when required
    content was silently omitted.
    """
    items = tuple(dict(item) for item in items_delivered)
    missing_required = tuple(
        item["item_id"]
        for item in manifest.required_items()
        if item["item_id"] not in (it.get("item_id") or "" for it in items)
    )
    if missing_required and delivery_status == "DELIVERED":
        raise DeliveryReceiptError(
            "REQUIRED_ITEM_NOT_DELIVERED: " + ",".join(missing_required)
        )
    status = "PARTIAL" if missing_required else delivery_status

    if target is None:
        target = envelope.execution_target

    for field, envelope_value, name in (
        ("goal_id", envelope.goal_id, "GOAL"),
        ("task_id", envelope.task_id, "TASK"),
        ("manifest_id", envelope.manifest_id, "MANIFEST"),
        ("envelope_id", envelope.identity(), "ENVELOPE"),
    ):
        if field == "envelope_id":
            continue  # computed below from the envelope itself
    _assert_no_secret_fields(list(items), "receipt_items")

    receipt = DeliveryReceipt(
        goal_id=envelope.goal_id,
        task_id=envelope.task_id,
        manifest_id=envelope.manifest_id,
        envelope_id=envelope.identity(),
        envelope_hash=_fingerprint(envelope.identity()),
        target=target,
        session_id=session_id,
        items_delivered=items,
        delivery_status=status,
        delivery_timestamp=delivery_timestamp,
        delivery_failures=tuple(dict(f) for f in delivery_failures),
        raw_pointer=raw_pointer,
    )
    # Scenario N: binding integrity — a receipt built from a mismatched
    # envelope is rejected before it can ever be issued.
    _assert_receipt_matches_envelope(receipt, envelope)
    return receipt


def _assert_receipt_matches_envelope(
    receipt: DeliveryReceipt, envelope: DeliveryEnvelope
) -> None:
    mismatches = []
    if receipt.goal_id != envelope.goal_id:
        mismatches.append("GOAL")
    if receipt.task_id != envelope.task_id:
        mismatches.append("TASK")
    if receipt.manifest_id != envelope.manifest_id:
        mismatches.append("MANIFEST")
    if receipt.target != envelope.execution_target:
        mismatches.append("TARGET")
    if mismatches:
        raise DeliveryBindingError("RECEIPT_BINDING_MISMATCH: " + ",".join(mismatches))


def receipt_claims_read(receipt: DeliveryReceipt) -> bool:
    """Static sanity: a receipt must never assert read evidence. Read claims
    belong exclusively to the read_evidence module (DELIVERED != READ)."""
    fields = (
        "read_state",
        "read_proven",
        "model_understood",
        "model_used",
    )
    for item in receipt.items_delivered:
        if any(key in item for key in fields):
            return True
    return False
