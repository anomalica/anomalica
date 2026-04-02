# 0009. Use SQLite for knowledge graph storage

Date: 2026-03-20
Status: accepted

## Context

The knowledge graph needs a storage layer. The platform's resilience model requires that the entire dataset be portable, distributable, and independent of any running server.

## Decision

Use SQLite. The database file is the distribution format - it can be copied, torrented, mirrored, and downloaded directly from the website. No server to maintain or defend. The write patterns for editorial content (batch ingestion by a small team) are well within SQLite's capabilities.

The knowledge graph may be split across multiple SQLite files for practical reasons. Embedding vectors used for similarity detection are large and can be recomputed, so they will likely be stored in a separate database from the core data. This keeps the primary download small and focused on the information that matters.

If public submissions (Phase 2) generate high concurrent write volume, a hosted database may be introduced as an intermediary to buffer incoming submissions until they can be processed and fed into the SQLite files.

## Consequences

The public can download the complete knowledge graph as a file. Anyone can build their own viewer, run their own analysis, or verify the scoring methodology against the raw data. If the platform ceases operation, the data survives in every copy.
