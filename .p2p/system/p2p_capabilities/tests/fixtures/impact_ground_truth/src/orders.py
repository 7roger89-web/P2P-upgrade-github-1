# Synthetic fixture: orders module — DIRECT CALLER of core.calculate_total.
# Imports core.calculate_total by name to prove scope-exact symbol evidence:
# only the `calculate_total` import usage comes from core, while `place_order`
# is locally defined (tests that local names are not falsely attributed).
from src.core import calculate_total


def place_order(items: list) -> dict:
    total = calculate_total(items)
    return {"status": "placed", "total": total}


def calculate_total(items: list) -> float:
    """Local function named the same as the imported core symbol — precision
    test: native AST analysis must not confuse local definitions with the
    imported symbol's source. The symbol `calculate_total` is locally defined
    here; the import proves core is a dependency of this module."""
    return sum(item.get("price", 0.0) for item in items)


def cancel_order(order_id: str) -> dict:
    return {"status": "cancelled", "order_id": order_id}
