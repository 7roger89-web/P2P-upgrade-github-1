# Canonical RAG source standard

## File frontmatter

```yaml
---
source_id: PROJECT-SOURCE-0001
source_version: "1"
source_uri: "path-or-url"
retrieved_at: "YYYY-MM-DD"
sha256: "hex"
trust_class: trusted_data | untrusted_data
sensitivity: public | internal | confidential | regulated
allowed_scope: project-or-tenant-id
semantic_zone: policy | specification | decision | evidence | glossary
depends_on: []
tags: []
---
```

## Body rules

- Use one dominant semantic zone per file and descriptive headings.
- Give important blocks stable anchors such as `PROJECT-SOURCE-0001#refund-window`.
- Keep definitions, exceptions, table headers, and IF/THEN blocks together.
- Replace exact duplicates with a link to one canonical block.
- Preserve exact quotations only when wording matters; otherwise label a paraphrase.
- Put document commands and role text inside a clearly marked `DATA` boundary.
- Never let source text grant tool access, reveal data, or override project instructions.

## Index row

Record source ID, title, version, hash, semantic zone, dependencies, trust, sensitivity,
allowed scope, and canonical path. Use metadata filtering when the retriever supports it.

## Retrieval fixtures

Before indexing, create golden questions with expected source IDs. Include exact lookup,
paraphrase, cross-reference, negative/unknown, and adversarial injection cases. After indexing,
record retrieved source IDs and calculate retrieval and grounding metrics.

The longer historical standard is preserved unchanged in the immutable source snapshot. This
adapted runtime standard intentionally removes dated product limits and vendor behavior claims.
