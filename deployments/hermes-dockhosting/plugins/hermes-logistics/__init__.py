"""Hermes plugin: read-only Logistics connector.

Registers three read-only tools with the Hermes tool registry:

* ``logistics_today_work``        -> today's actionable Logistics items
* ``logistics_freight_rate_lookup`` -> current/recent freight rate for a route
* ``logistics_shipment_status``   -> exact current status of a shipment

The tools execute real, read-only MongoDB queries via :mod:`connector`. This
plugin adds no mutation capability, no separate service, and no MCP server.
"""

from __future__ import annotations

import os
import sys

# If Hermes loads this directory as a package, sibling imports still resolve
# because the package root is on sys.path during import. The directory name
# contains a hyphen, so we avoid ``from . import`` and use plain imports.
_PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))
if _PLUGIN_DIR not in sys.path:
    sys.path.insert(0, _PLUGIN_DIR)

import schemas as _schemas  # noqa: E402
import tools as _tools  # noqa: E402


def register(ctx):
    """Hermes plugin entry point: wire the three read-only tools."""
    for schema in _schemas.ALL_SCHEMAS:
        tool_name = schema["name"]
        # Handlers have the Hermes signature (params, **kwargs).
        ctx.register_tool(
            name=tool_name,
            toolset="logistics",
            schema=schema,
            handler=_tools.HANDLERS[tool_name],
        )


__all__ = ["register"]
