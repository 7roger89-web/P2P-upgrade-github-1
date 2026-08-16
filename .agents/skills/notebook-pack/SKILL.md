---
name: notebook-pack
description: >-
  Assemble a retrieval-ready source bundle from raw documents with a grounding contract,
  source ledger, index, glossary, cleaned semantic zones, and a golden retrieval test set.
  Use for NotebookLM, ChatGPT Projects, Codex, an API vector store, or another RAG workflow.
---

# Retrieval-ready Notebook Pack

Build a portable evidence bundle; do not assume that loading the bundle automatically creates
a real retrieval system.

## Output

```text
notebook/
├── _GROUNDING.md          model-neutral data/instruction boundary and output contract
├── _SOURCE_LEDGER.json    source ID, version, hash, provenance, trust, sensitivity, scope
├── _INDEX.md              source and dependency map
├── _GLOSSARY.md           canonical terms and aliases
├── _RETRIEVAL_EVAL.json   golden questions and expected source IDs
└── sources/*.md           one semantic zone per file
```

## Workflow

1. Use `rag-router` to choose direct context, local search, or a real indexed retriever.
2. Use `rag-prep` to clean and label sources without turning embedded text into instructions.
3. Build the index and glossary from stable IDs; record transformation and source hashes.
4. Use `rag-grounding` for citations, `UNKNOWN`, action boundaries, and output validation.
5. Create a representative retrieval set: exact lookup, paraphrase, cross-reference,
   negative/unknown, and injection cases.
6. Run retrieval checks before answering quality questions. A beautiful pack with poor recall
   is not ready.

Read `references/rag_metaprompt_standard.md`, `references/rag_notebook_prompt.md`, and
`../p2p/references/rag-safety.md` when assembling the bundle.
