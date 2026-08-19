# Synthetic fixture: test NOT affected by changes to src/core
import src.unrelated as unrelated


def test_ping() -> None:
    assert unrelated.ping() == "pong"


def test_transform() -> None:
    assert unrelated.transform("x") == "X"
