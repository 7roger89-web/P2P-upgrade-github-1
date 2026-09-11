# TT39 golden case — amendment/versioning proof

Status: `SPEC_READY_NOT_YET_EXECUTED`

## Purpose

Use one real Vietnamese legal-document family to prove the core capability before any nationwide ingestion or AI-lawyer UI is attempted.

Initial family: `39/2016/TT-NHNN` and the official documents that amend, repeal, replace, suspend, guide, consolidate, or otherwise change the operative reading of its provisions.

Do not trust remembered amendment lists. The exact chain must be discovered from official current sources during execution and recorded with source URLs and retrieval dates.

## Truth hierarchy

1. official Vietnamese legal database / issuing authority source;
2. official consolidated text where available;
3. official Pháp điển material where applicable;
4. external datasets/repositories only as discovery, parsing or evaluation aids.

An upstream repository or LLM output never outranks official legal text.

## Minimal input set

Collect only enough official material to prove one non-trivial chain:

- base document metadata and full text;
- at least one amending event affecting a concrete provision;
- effective date of that event;
- the target Article/Clause/Point before the event;
- the target Article/Clause/Point after the event;
- an official consolidated or otherwise authoritative cross-check if available.

## Required normalized objects

```text
Document
Provision(article/clause/point)
LegalEvent(amend/repeal/replace/suspend/...)
TextVersion(valid_from, valid_to, text, source_event)
Evidence(source_url, retrieved_at, source_span_or_locator)
```

No graph database is required to represent these objects in Phase 1.

## Acceptance tests

The vertical slice passes only if evidence proves all of the following:

1. **STRUCTURE** — the target legal text is split deterministically into the correct Article/Clause/Point hierarchy.
2. **TARGETING** — an amendment instruction resolves to the intended target provision, not merely the document.
3. **EVENT TYPE** — the system distinguishes at least amendment/replacement/repeal when those types occur in the selected chain.
4. **EFFECTIVE TIME** — the event has an explicit effective date backed by an official source.
5. **VERSIONING** — querying a date before and after the event returns the correct text version.
6. **TRACEABILITY** — every generated version points back to the source legal event and official evidence.
7. **CROSS-CHECK** — derived current text agrees with an authoritative consolidated/cross-check source where one exists; any mismatch is reported, not silently patched.
8. **DIFF UX CONTRACT** — the data is sufficient for a UI to highlight changed text and open a popup containing old text, new text, source document and effective date.

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

Stop the phase when one non-trivial TT39 provision can be reconstructed correctly across time with official evidence and a machine-readable old/new diff contract.

At that point the next decision is evidence-based: improve amendment parsing, scale ingestion, or begin retrieval benchmarking. Do **not** automatically proceed to all three.
