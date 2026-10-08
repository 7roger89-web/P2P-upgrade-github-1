from __future__ import annotations

from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"PATCH_SOURCE_MISMATCH:{label}:count={count}")
    return text.replace(old, new, 1)


selector_path = Path("src/ane_context_harness/retrieval/selector.py")
selector = selector_path.read_text(encoding="utf-8")

selector = replace_once(
    selector,
    "_PER_FILE_FRACTION = 0.25  # per-file maximum allocation of budget\n",
    "_PER_FILE_FRACTION = 0.25  # per-file maximum allocation of budget\n"
    "_NAMED_SYMBOL_MANDATORY_MAX_CHUNKS = 8\n",
    "selector-constant",
)

selector = replace_once(
    selector,
    """    # mandatory flags
    explicit_set = set(p.replace("\\\\", "/") for p in explicit_paths)
    mandatory_idx = set()
    authority_fired: set = set()
""",
    """    # A single broad task word such as "context" or "capability" can
    # match hundreds of symbols in a large repository. Such a match remains
    # useful for ranking, but it must not silently turn the corpus mandatory.
    from .structural import matched_symbol_terms
    matched_terms_by_idx = {}
    symbol_term_fanout = {}
    for i, c in enumerate(chunks):
        matched = matched_symbol_terms(c, task_terms)
        matched_terms_by_idx[i] = matched
        for term in matched:
            symbol_term_fanout[term] = symbol_term_fanout.get(term, 0) + 1

    # mandatory flags
    explicit_set = set(p.replace("\\\\", "/") for p in explicit_paths)
    mandatory_idx = set()
    authority_fired: set = set()
    broad_symbol_terms: set = set()
""",
    "selector-fanout-index",
)

selector = replace_once(
    selector,
    """        # symbol directly named in task — own symbol for symbol-scoped chunks,
        # full file symbol list for file-level chunks (metadata.file_symbols);
        # micro/generic terms (to/is/for/test) never trigger retention
        from .structural import matched_symbol_terms
        if matched_symbol_terms(c, task_terms):
            mandatory_idx.add(i)
            score_by_id[c.chunk_id].mandatory = True
            if "named_symbol" not in score_by_id[c.chunk_id].selection_reasons:
                score_by_id[c.chunk_id].selection_reasons.append("named_symbol")
""",
    """        # symbol directly named in task — own symbol for symbol-scoped chunks,
        # full file symbol list for file-level chunks (metadata.file_symbols).
        # Broad task words remain ranking signals but do not get unconditional
        # retention across large symbol fanouts.
        matched = matched_terms_by_idx.get(i, set())
        bounded = {
            term for term in matched
            if symbol_term_fanout.get(term, 0)
            <= _NAMED_SYMBOL_MANDATORY_MAX_CHUNKS
        }
        broad_symbol_terms.update(matched - bounded)
        if bounded:
            mandatory_idx.add(i)
            score_by_id[c.chunk_id].mandatory = True
            if "named_symbol" not in score_by_id[c.chunk_id].selection_reasons:
                score_by_id[c.chunk_id].selection_reasons.append("named_symbol")
""",
    "selector-named-symbol",
)

selector = replace_once(
    selector,
    """        "authority_flags": sorted(authority_fired),
    }
""",
    """        "authority_flags": sorted(authority_fired),
        "named_symbol_mandatory_max_chunks":
            _NAMED_SYMBOL_MANDATORY_MAX_CHUNKS,
        "named_symbol_term_fanout": {
            term: symbol_term_fanout[term]
            for term in sorted(symbol_term_fanout)
        },
        "named_symbol_broad_terms": sorted(broad_symbol_terms),
    }
""",
    "selector-diagnostics",
)

selector_path.write_text(selector, encoding="utf-8")

pipeline_path = Path("src/ane_context_harness/pipeline.py")
pipeline = pipeline_path.read_text(encoding="utf-8")
pipeline = replace_once(
    pipeline,
    """        sel_tokens = sum(tokens_mod.count(e["content"]) for e in pkg.evidence)
        reduction = ((cand_tokens - sel_tokens) / cand_tokens * 100.0) if cand_tokens else 0.0
""",
    """        sel_tokens = sum(tokens_mod.count(e["content"]) for e in pkg.evidence)
        # Normal retrieval treats the caller's output budget as a real
        # boundary. Explicit paths and developer-crowned authority remain
        # deliberate overrides; full-context mode is intentionally uncut.
        hard_pin_override = any(
            {"explicit_path", "authority"}
            & set(e.get("selection_reasons") or [])
            for e in pkg.evidence
        )
        if (
            not request.options.get("full_context")
            and sel_tokens > max_budget
            and not hard_pin_override
        ):
            raise ValueError(
                "context pack exceeded hard token budget: "
                f"selected={sel_tokens} budget={max_budget}"
            )
        reduction = ((cand_tokens - sel_tokens) / cand_tokens * 100.0) if cand_tokens else 0.0
""",
    "pipeline-hard-budget",
)
pipeline_path.write_text(pipeline, encoding="utf-8")

print("ANE_PATCH_APPLICATION=PASS")
