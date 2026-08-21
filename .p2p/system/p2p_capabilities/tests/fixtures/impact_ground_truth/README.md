# Synthetic code-impact ground-truth fixture (FW04)

This fixture is a SYNTHETIC repository created solely for deterministic
code-impact evidence testing. It is NOT part of any owner project. The
correct blast radius is known in advance, so precision/recall/unknown
handling can be measured against ground truth.

## Expected impact for the canonical change (see core.py.old -> core.py.new)

The canonical change modifies function `calculate_total` inside
`src/core.py`. Ground truth:

| Item | Ground truth |
| --- | --- |
| changed symbol | `calculate_total` (body changed; `format_receipt` untouched) |
| direct caller | `src/orders.py` (`place_order` imports and calls `calculate_total`) |
| transitive dependent | none in this fixture (deliberately shallow to keep precision measurable) |
| unrelated file | `src/unrelated.py` (no import of core) |
| affected test | `tests/test_orders.py` (imports src.orders) |
| unaffected test | `tests/test_unrelated.py` (imports src.unrelated) |

No file in this fixture imports anything outside `src/` or `tests/`; the
import graph is closed and fully analyzable by the native AST pipeline.
