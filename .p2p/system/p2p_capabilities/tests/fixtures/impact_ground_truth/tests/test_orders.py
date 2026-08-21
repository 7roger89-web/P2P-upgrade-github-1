# Synthetic fixture: test that IS affected by changes to src/core (via orders)
import src.orders as orders


def test_place_order_sums_prices() -> None:
    result = orders.place_order([{"price": 10.0}])
    assert result["status"] == "placed"


def test_cancel_order() -> None:
    result = orders.cancel_order("o-1")
    assert result["status"] == "cancelled"
