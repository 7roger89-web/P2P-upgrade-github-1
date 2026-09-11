# P2P LEGAL VN — research foundation

Status: `CANDIDATE_UNPROMOTED`
Branch: `chatgpt/legal-research-foundation-01`

## Goal

Build the smallest evidence-backed foundation for a Vietnamese legal research/advisory product with:

1. official-source legal documents;
2. article/clause/point structure;
3. amendment/repeal/replacement relationships;
4. point-in-time text versions;
5. legal retrieval with provision-level citations;
6. an AI advisory layer only after the truth/retrieval layers are proven.

The first vertical slice is **not** a nationwide chatbot. It is one difficult amendment chain, using `39/2016/TT-NHNN` as the initial golden-case family, verified against official Vietnamese legal sources and consolidated texts where available.

## Boundary

This research area does **not** vendor upstream repositories into P2P. Upstreams are cloned into a separate local research workspace by `scripts/bootstrap_legal_research.py` and remain independently updateable.

Large legal datasets, HTML/PDF snapshots, Parquet/JSONL outputs and evaluation artifacts do not belong in this Git repository. They may later be archived in the Owner's Google Drive and imported into a runtime database only when a working vertical slice needs them.

Raw official-source data is immutable. Derived/processed data must record its source snapshot and parser version.

## Phase 1 upstreams

The canonical intake list is `upstreams.json`.

Priority order:

1. `tamnd/luatdo` — study legal component/version/event modeling and deterministic + constrained extraction patterns.
2. `th1nhng0/vietnamese-legal-documents` dataset — study VBPL ingestion and document-level legal relationships; dataset source, not vendored code.
3. `chisngooo/Vietnamese-Legal-Document-Retrieval` — study hybrid retrieval/reranking baseline.
4. `mlalab/VNLegalText` — relation-extraction/evaluation reference dataset.
5. `saladnga/ISODS-PhapDien-Crawler-Semantic-Search` — Pháp điển ingestion/search reference.
6. `tangbamiinh/traffic-law-assistant` — full-stack wiring reference, never the legal truth engine.

No upstream is adopted wholesale. Each receives one of: `ADOPT`, `ADAPT`, `REFERENCE`, `REJECT` only after evidence.

## Local bootstrap

From the P2P repository root:

```bash
python scripts/bootstrap_legal_research.py --list
python scripts/bootstrap_legal_research.py --dest ../p2p-legal-upstreams --dry-run
python scripts/bootstrap_legal_research.py --dest ../p2p-legal-upstreams
```

Each Git upstream is cloned into its own directory. Existing non-empty directories are never overwritten.

## Evaluation sequence

Do not evaluate every repo against every imaginable feature. Use the smallest sequence that can falsify the project thesis:

1. establish official TT39 document/amendment sources;
2. parse document -> article -> clause -> point;
3. model amendment events and effective dates;
4. reconstruct point-in-time text versions;
5. compare with official/consolidated truth;
6. only then benchmark retrieval;
7. only then add an answering model with provision-level citations.

See `TT39-GOLDEN-CASE.md` for acceptance conditions.

## Storage contract

```text
GitHub P2P
  code / schemas / tests / manifests / research findings

Google Drive (later, when needed)
  raw official snapshots / large datasets / processed snapshots / bulky eval artifacts

Runtime DB (only after the vertical slice proves a need)
  queryable documents / provisions / text versions / relationships / embeddings
```

Drive is durable data storage, not the production query database.

## License rule

Absence of a clear license means `RESEARCH_ONLY` by default. Reading and testing a public repository does not grant permission to copy its source or redistribute its dataset. `upstreams.json` records the current license signal and reuse boundary.

## Anti-overengineering gate

This phase passes only while all four remain true:

1. no simpler path reaches the same evidence;
2. each step adds capability or decision-useful evidence;
3. removing the step would weaken an acceptance condition;
4. work is on the legal truth/retrieval capability, not auxiliary infrastructure.

No Neo4j, OpenSearch, Kafka, multi-agent council, new service mesh, or nationwide ingestion is justified in Phase 1 merely because an upstream uses or mentions it.
