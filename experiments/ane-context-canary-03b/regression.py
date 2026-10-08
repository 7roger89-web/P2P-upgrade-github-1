from __future__ import annotations

from ane_context_harness.indexing.chunking import lex_terms
from ane_context_harness.retrieval.structural import aggregate_scores
from ane_context_harness.retrieval.selector import select_evidence
from ane_context_harness.schemas import RepositoryChunk


WEIGHTS = {
    "lexical_weight": 0.35,
    "symbol_weight": 0.25,
    "path_weight": 0.15,
    "dependency_weight": 0.10,
    "test_pair_weight": 0.10,
    "git_recency_weight": 0.05,
    "diversity_lambda": 0.25,
    "top_k_for_diversity": 60,
}


def chunk(cid: str, symbol: str, text: str) -> RepositoryChunk:
    terms = lex_terms(text)
    return RepositoryChunk(
        chunk_id=cid,
        repository_id="r",
        path=f"src/{cid}.py",
        language="python",
        start_line=1,
        end_line=2,
        symbol=symbol,
        content_hash="h",
        estimated_tokens=len(terms),
        lexical_terms=tuple(terms),
        content=text,
        metadata={},
    )


# Broad symbol word: before the patch every matching chunk became mandatory.
broad = [
    chunk(str(i), f"capability_handler_{i}", f"def capability_handler_{i} value")
    for i in range(20)
]
scores = aggregate_scores(
    broad, "fix capability behavior", [], WEIGHTS,
    [1.0 - i * 0.01 for i in range(len(broad))],
)
selected, diag = select_evidence(
    broad, scores, "fix capability behavior", token_budget=30,
    explicit_paths=[], weights=WEIGHTS,
)
assert diag["named_symbol_term_fanout"]["capability"] == 20, diag
assert "capability" in diag["named_symbol_broad_terms"], diag
assert diag["mandatory_count"] == 0, diag
assert sum(c.estimated_tokens for c in selected) <= 30, diag

# Rare task term still gets direct symbol retention.
rare = [
    chunk("discount", "calculate_discount", "def calculate_discount value"),
    chunk("inventory", "inventory_loader", "def inventory_loader value"),
]
rare_scores = aggregate_scores(rare, "discount fix", [], WEIGHTS, [1.0, 0.2])
rare_selected, rare_diag = select_evidence(
    rare, rare_scores, "discount fix", token_budget=20,
    explicit_paths=[], weights=WEIGHTS,
)
assert any(c.symbol == "calculate_discount" for c in rare_selected), rare_diag
assert rare_diag["named_symbol_term_fanout"]["discount"] == 1, rare_diag

print("ANE_BOUNDED_SELECTOR_REGRESSION=PASS")
