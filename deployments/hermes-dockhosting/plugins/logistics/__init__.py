"""Hermes Logistics read-only integration plugin (HERMES_LOGISTICS_READONLY_001).

Bundled backend plugin: answers three Logistics questions from the authoritative
logistics-work-desk MongoDB using a dedicated read-only credential.

  - logistics_today_work      "Hôm nay tôi có việc gì?"        (tasks)
  - logistics_freight_rate    "Cước X → Y container Z?"        (rate_cards, structured lookup)
  - logistics_shipment_status "Lô hàng <ID> hiện thế nào?"     (shipments)

Read-only by design: the connector exposes find/find_one only, over an
allowlist of three collections, and the deployment supplies a read-only
credential (LOGISTICS_MONGO_URI_READONLY / LOGISTICS_MONGO_DB_NAME). Tools stay
hidden from the model until that credential is configured (check_fn gates
schema exposure). See deployments/hermes-dockhosting/README-logistics.md.
"""

from __future__ import annotations

from . import tools as _tools


def register(ctx) -> None:
    """Register the three Logistics read-only tools (called by the plugin loader)."""
    for spec in _tools.TOOL_REGISTRATIONS:
        ctx.register_tool(**spec)
