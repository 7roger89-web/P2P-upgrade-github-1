# Synthetic fixture: unrelated module — no dependency on core or orders


def ping() -> str:
    return "pong"


def transform(value: str) -> str:
    return value.upper()
