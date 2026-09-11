# Upstream finding — `th1nhng0/vietnamese-legal-documents`

Reviewed: `2026-09-11`
Source: Hugging Face dataset sourced from `vbpl.vn`
Dataset release observed: 2026 portal refresh / 2.0.0 lineage
License signal: `CC BY 4.0`
Provisional verdict: `ADOPT` for bulk research ingestion, **not** as final legal authority

## Current useful shape

The current dataset exposes five configs. The three active configs relevant to Phase 1 are:

| Config | Rows | Role |
| --- | ---: | --- |
| `metadata` | 171,556 | document identity, dates, authority, effect status |
| `relationships` | 1,033,255 | directed legal/citation relationships |
| `content` | 170,824 | raw HTML document bodies |

The current release uses string IDs because the refreshed VBPL portal includes numeric, UUID and portal-prefixed identifiers. Consumers must not assume integer keys.

## Why this is valuable

The dataset is already separated into exactly the order P2P should ingest it:

1. metadata first;
2. relationship graph second;
3. full text only when required.

This means Phase 1 does **not** need to download or parse every legal text simply to discover the TT39 amendment family.

The relationship table plus metadata can cheaply establish candidate amendment/citation edges before content parsing begins.

## Storage/size implication

Observed published sizes for the active data files are roughly:

- metadata: ~15 MB download;
- relationships: ~9 MB download;
- content: ~785 MB compressed, several GB expanded/raw;
- full repository/dataset footprint: multiple GB.

Therefore the correct Phase-1 order is metadata + relationships first. Full content is fetched only for the selected golden-case documents.

Do not copy the whole dataset into the P2P Git repository.

## Data-quality boundaries

The dataset card itself records important limits:

- it is a snapshot, not a live legal mirror;
- official effect status can lag real legal changes;
- 732 metadata rows currently have no active HTML content row;
- relationship targets may point outside the current live metadata snapshot;
- coverage is bounded by what VBPL has digitized/indexed.

Therefore:

```text
DATASET_DISCOVERY != AUTHORITATIVE_LEGAL_STATUS
```

Every legal conclusion or point-in-time state used by the product must be cross-checked against current official sources.

## License/reuse decision

The published dataset card currently declares `CC BY 4.0` for the compiled dataset. P2P may use it under those terms with attribution, but should still preserve:

- source URL;
- dataset revision/snapshot date;
- attribution;
- raw immutable snapshot hash when downloaded.

This does not convert third-party legal advice or non-official annotations into authoritative law.

## Phase-1 ingestion decision

Do **not** download the entire `content` config yet.

For TT39:

1. query/filter `metadata` for `39/2016/TT-NHNN`, `06/2023/TT-NHNN`, `12/2024/TT-NHNN`, `52/2025/TT-NHNN`;
2. inspect their `relationships` edges;
3. fetch only those official/current full texts needed by the golden slice;
4. save exact source/retrieval evidence;
5. compare dataset relationships against current VBPL history.

If those joins and relationship labels prove reliable enough for discovery, keep the dataset as the bulk acquisition layer. If not, use its crawler/API implementation as a reference and query the current VBPL source directly.

## Evidence inspected

- dataset card and current Data Studio metadata;
- 2026 portal-refresh release notes;
- published Parquet/config row counts and file-size metadata.

The dataset is useful precisely because it lets us postpone the expensive part. Downloading all content before the TT39 slice proves anything would be data-hoarding disguised as engineering.
