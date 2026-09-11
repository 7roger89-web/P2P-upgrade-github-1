# TT39 golden case — amendment/versioning proof

Status: `SPEC_READY_OFFICIAL_CHAIN_VERIFIED_NOT_YET_EXECUTED`

## Purpose

Use one real Vietnamese legal-document family to prove the core capability before any nationwide ingestion or AI-lawyer UI is attempted.

Initial family: `39/2016/TT-NHNN` and the official documents that change its operative reading.

## Official chain verified on 2026-09-11

Source of truth checked: CSDL quốc gia về văn bản pháp luật (`vbpl.vn`) and the issuing-authority view for Ngân hàng Nhà nước.

The official effectiveness history for `39/2016/TT-NHNN` currently records:

- `15/03/2017` — base circular becomes effective;
- `01/09/2023` — partially repealed and amended by `06/2023/TT-NHNN`;
- `01/07/2024` — partially repealed and amended by `12/2024/TT-NHNN`;
- `25/12/2025` — amended by `52/2025/TT-NHNN`.

Official source references:

- https://vbpl.vn/TW/Pages/vbpq-lichsu.aspx?ItemID=118230
- https://vbpl.vn/nganhangnhanuoc/Pages/vbpq-toanvan.aspx?ItemID=160901&dvid=326

The exact chain must still be rechecked at execution time because legal status is time-sensitive.

## Phase-1 concrete slice

Start with `06/2023/TT-NHNN`, effective `01/09/2023`, because one instrument gives three useful event shapes against the same base document:

1. **amend** — it amends point `c`, clause `6`, Article `2`;
2. **supplement** — it adds clause `12` to Article `2`;
3. **repeal** — it repeals clause `5`, Article `7`.

This is deliberately better than picking three unrelated examples: one official instrument exercises targeting, insertion and removal under one effective date and one provenance chain.

After those three operations pass, extend the same family to `12/2024/TT-NHNN` and `52/2025/TT-NHNN` only if doing so changes the decision about the temporal engine.

## Truth hierarchy

1. official Vietnamese legal database / issuing authority source;
2. official consolidated text where available;
3. official Pháp điển material where applicable;
4. external datasets/repositories only as discovery, parsing or evaluation aids.

An upstream repository or LLM output never outranks official legal text.

## Minimal input set

Collect only enough official material to prove the concrete slice:

- base `39/2016/TT-NHNN` metadata and full text;
- full official text of `06/2023/TT-NHNN`;
- effective date `01/09/2023`;
- pre-change text for point c clause 6 Article 2;
- structure around Article 2 so clause 12 can be inserted correctly;
- pre-change text/existence of clause 5 Article 7;
- an official consolidated or otherwise authoritative cross-check if available.

## Required normalized objects

```text
Document
Provision(article/clause/point)
LegalEvent(amend/supplement/repeal/...)
TextVersion(valid_from, valid_to, text, source_event)
Evidence(source_url, retrieved_at, source_span_or_locator)
```

No graph database is required to represent these objects in Phase 1.

## Acceptance tests

The vertical slice passes only if evidence proves all of the following:

1. **STRUCTURE** — the target legal text is split deterministically into the correct Article/Clause/Point hierarchy.
2. **TARGETING** — all three 06/2023 operations resolve to their intended target provision/parent.
3. **EVENT TYPE** — `amend`, `supplement`, and `repeal` remain distinct operations.
4. **EFFECTIVE TIME** — all three changes become operative on the official date `01/09/2023` unless the source states a more specific date.
5. **VERSIONING** — querying immediately before and on/after the effective date returns the correct version/state.
6. **TRACEABILITY** — every generated version/state transition points back to `06/2023/TT-NHNN` and its official evidence.
7. **CROSS-CHECK** — derived text agrees with an authoritative consolidated/cross-check source where one exists; mismatch is reported, never silently patched.
8. **DIFF UX CONTRACT** — the data is sufficient for a UI to highlight changed text and open a popup containing old text, new text/state, source document and effective date.

## Failure classifications

Use the smallest useful failure vocabulary:

- `SOURCE_GAP` — authoritative source missing/unavailable;
- `PARSE_ERROR` — structure extraction wrong;
- `TARGET_ERROR` — amendment points to wrong provision;
- `TEMPORAL_ERROR` — validity interval/effective date wrong;
- `TEXT_TRANSFORM_ERROR` — derived new text wrong;
- `CROSSCHECK_MISMATCH` — derived text disagrees with authoritative comparison;
- `LICENSE_BLOCKED` — an external artifact cannot legally be reused beyond research.

Do not create a new framework for failures unless this vocabulary proves insufficient in actual execution.

## Phase-1 stop condition

Stop when the three 06/2023 operations are reconstructed correctly across `01/09/2023`, with official evidence and a machine-readable old/new/state diff contract.

At that point the next decision is evidence-based: improve amendment parsing, extend the TT39 chain, or begin retrieval benchmarking. Do **not** automatically proceed to all three.
