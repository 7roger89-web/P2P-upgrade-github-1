# Synthetic fixture: core module (post-change canonical state for FW04 impact tests)


def format_receipt(total: float) -> str:
    """Untouched symbol for changed-symbol precision measurement."""
    return f"TOTAL {total:.2f}"


def calculate_total(items: list) -> float:
    """CHANGED symbol in the canonical ground-truth mutation."""
    subtotal = sum(item.get("price", 0.0) for item in items)
    tax = subtotal * 0.1
    return round(subtotal + tax, 2)


def describe_product(name: str) -> str:
    """Second untouched symbol."""
    return f"product: {name}"
