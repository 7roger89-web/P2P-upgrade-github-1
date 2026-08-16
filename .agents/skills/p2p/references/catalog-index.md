# Supplemental P2P Catalog Index

This index summarizes the Russian overview/catalog supplied by the user and
audited in full on 2026-08-07. It supplements the immutable 8.4.6-C release; it
does not replace the 152-file inventory or override current host rules.

## User-facing commands

- Quality modes: `Q:`, `AUTO:`, `MANUAL:`, `MAX:`.
- Direct roles: `T:`/`@TECTON:`, `I:`/`@IRIS:`, `A:`/`@ANON:`, `@AXIOM:`,
  `@VECTOR:`, `@DATOS:`; the release also defines ARCHITECTON and HELIOS.
- Tools: `/scope`, `/chain`, `/explore`, `/debug`, `/metrics`.
- Menu recovery phrase: `full ui menu`.

Use the native mappings in `modes.md`; never copy Claude/Grok-specific model,
temperature, proxy, tool-call, or hidden-reasoning behavior mechanically.

## Catalog sections

| Section | Capability families |
| --- | --- |
| 1 | 9-step/9D, RTF, CO-STAR, RISEN, CRISPE, CTCO, templates A–M, domain and prompt patterns |
| 2 | Step-by-step, Socratic questions, branching, reflection, critic pairs, ELI5/TLDR/checklists |
| 3 | Compression, cache/anchor, memory, decomposition, gates, scaffolds, SCOPE.HELM, context diagnostics |
| 4 | Grounding, freshness, honesty, prompt-injection defense, compliance checks |
| 5 | Karpathy mode, agent/tool budgets, ReAct+Stop, personas, migration, QUORUM and sub-QUORUMs |
| 6 | Writing/code/cross-validation pipelines, handoff protocol, cost estimation |
| 7 | Error Types A–P, Silent Degradation L1–L5, feedback loop, anti-pattern scanner |
| 8 | SIR routing, load formula, session metrics, ATLAS, CAPSULE, exploration and scope control |
| 9 | Humanized writing, tone spectrum, quality checks, UI replication |
| 10 | Arena tests, 0–100 score, dated model-error catalog G1–G20 (`HISTORICAL_ONLY: taxonomy, not runtime facts`) |
| 11 | Experimental RAG, reasoning, routing, compression, security, and optimization modules |

## Exact-name cautions

Names such as `COT_GUARD`, `LOW_TEMP_ANALYTICAL`, `WRITING_PIPELINE`, model
error codes, and vendor parameters are catalog labels. Before applying one:

1. locate the corresponding release module or user-supplied snapshot;
2. extract the transferable behavior;
3. verify any current product/model claim;
4. implement with native Codex/ChatGPT permissions and tools;
5. label preserved-only or experimental behavior honestly.

The portable package stores the exact user-supplied catalog text and its hash
under `source/supplemental/` for auditability.
