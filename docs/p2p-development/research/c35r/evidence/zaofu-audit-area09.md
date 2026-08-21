# Audit Findings: Area Group 9 — SQLite & Read-Model Projections

## 1. SQLite & Read-Model Projections Implementation

ZaoFu implements a robust event sourcing architecture where `events.jsonl` serves as the append-only source of truth, and SQLite is utilized as a read-model projection layer to facilitate high-frequency lookups and complex queries. The implementation is modular, separating the event logging mechanism from the projection engines.

The core event logging is managed by the `EventLog` class in `src/zf/core/events/log.py`. This class handles event appending, file rotation, and parsing of the `events.jsonl` file. To optimize lookups, it lazily builds an in-memory and on-disk index (`EventIndex` in `src/zf/core/events/index.py`) stored as `event_index.json`. This index tracks event IDs, task IDs, and dispatch actors, acting as a cache rather than a primary source of truth.

For artifact tracking, the system utilizes the artifact catalog managed by `src/zf/runtime/artifact_query/store.py` and `maintenance.py`. This module maintains a SQLite database named `read_model.sqlite`, specifically designed for tracking artifact metadata and lineage. It defines a schema including tables for `artifact_query_meta`, `artifact_object`, `artifact_locator`, and `artifact_occurrence`. The `catch_up_catalog` and `rebuild_catalog` functions in `maintenance.py` incrementally project events from the event log into this SQLite database.

Designed for the web dashboard, the web read model in `src/zf/web/projections/read_model.py` maintains another `read_model.sqlite` database optimized for high-frequency reads. It projects events into an `event_index` table and an `event_ref` table for tracking references. The `rebuild` function handles incremental catch-ups, using a single-flight mechanism (`_rebuild_single_flight`) to prevent concurrent rebuilds from causing performance bottlenecks.

## 2. Implementation Semantics

The core semantics revolve around the strict separation of write and read paths. In the write path, events are appended to `events.jsonl`. The `EventLog.append` method ensures atomicity and handles file rotation. An optional `EventIndex` is updated in-memory and periodically flushed to `event_index.json` to speed up initial lookups without blocking the append operation.

In the read path, the system relies on projections for complex queries, especially in the web UI and artifact tracking. These SQLite databases are populated by iterating through the `events.jsonl` file (or its archived segments) and applying specific projection logic. Both the artifact catalog and the web read model support incremental rebuilds. They track the last processed sequence number (cursor) in their metadata tables, allowing them to catch up only with new events rather than reprocessing the entire log every time.

Concurrency control is a critical aspect of the read path. The web read model uses `threading.Lock` and a single-flight pattern (`_rebuild_single_flight`) to ensure that only one rebuild thread operates on a specific SQLite database at a time. Other read requests either wait or are served from the existing projection, preventing performance degradation during high-traffic periods.

## 3. Coupling & Boundaries

The projection layers depend heavily on `EventLog` and `core.events.model.ZfEvent` to read and parse events. The `EventIndex` is decoupled via lazy imports to avoid circular dependencies within the core event system.

The `events.jsonl` file serves as the strict boundary for business truth. The SQLite databases (`read_model.sqlite`) and `event_index.json` are explicitly treated as cacheable, rebuildable projections. The code comments emphasize that these projections "never replace the append-only log as business truth."

The `src/zf/web/projections/` and `src/zf/runtime/projections/` directories act as a functional boundary. They consume events and output dictionary structures for the web UI or other runtime components, without leaking projection logic into the core orchestrator.

## 4. Maturity Signals

The implementation includes extensive error handling, catching exceptions like `sqlite3.Error` and `OSError`, which indicates a strong focus on robustness and fault tolerance. The presence of specific PRAGMA settings, such as `journal_mode=WAL` and `synchronous=NORMAL`, suggests careful tuning for concurrent access and durability.

Code comments provide deep insights into design decisions, explaining why single-flight rebuilds are necessary to prevent live-project full-site hangs and how the `EventIndex` avoids becoming a bottleneck. The use of Write-Ahead Logging (WAL) mode in SQLite, along with busy timeouts and background thread catch-ups, points towards a production-ready system designed to handle the high-frequency read patterns common in UI dashboards.

## 5. Provider Neutrality

**Assessment**: Provider-neutral

**Justification**: The SQLite read-model projections are entirely decoupled from any specific backend provider. They operate strictly on the generic `events.jsonl` log, projecting data structures (like artifacts or web UI state) independent of whether the underlying execution relies on OpenAI, Anthropic, or other providers.
