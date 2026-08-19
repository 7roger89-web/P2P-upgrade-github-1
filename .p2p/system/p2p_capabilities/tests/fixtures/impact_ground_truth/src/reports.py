# Synthetic fixture: reports module — second-hop dependent (orders -> core).
# Ground truth: core change affects orders (direct) and reports (transitive).
import src.orders as orders


def monthly_report(items: list) -> dict:
    order = orders.place_order(items)
    return {"month": "2026-08", "order_total": order["total"]}
