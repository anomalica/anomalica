# 0034. Split the digester: extraction versus graph assimilation, with a shared contract library

Date: 2026-06-16
Status: accepted

## Context

The digester had grown two genuinely different jobs under one roof:

1. **Extraction** - take a reviewed record, run the two-pass artificial-intelligence extraction, and produce a digest: a YAML file of nodes, claims, and provenance (the interchange format in 0027). This is per-record, AI-heavy, and idempotent on a single source.
2. **Graph assimilation** - take the digests and build and maintain the unified SQLite knowledge graph: import, entity resolution and matching, AI-assisted entity merges, scoring, AI-assisted cross-record corroboration, embeddings and hybrid search, Obsidian export, and the digest-maintenance passes. This is cross-corpus, stateful, and runs over the whole graph.

The two differ in inputs, failure modes, cost profile, and cadence. Bundling them made the digester's responsibilities and command-line surface sprawl, and coupled per-record extraction to cross-corpus graph operations that fail and scale differently - the same conflation that the taxonomy work flagged for pattern discovery (per-record extraction must not be entangled with cross-corpus analysis).

Two things both halves must agree on were at risk of drifting if duplicated: the digest interchange format (0027), and the Claude transport plus its spend gate (the operations billing policy).

## Decision

Split the digester into two repositories plus a shared library.

- **digester** - extraction only. Input: a reviewed record. Output: a digest YAML file (0027). Produces no graph. Command-line surface: `extract`, `batch-extract`, `coverage`.
- **assimilator** (new) - builds and maintains the unified SQLite knowledge graph from digest YAML files. Owns: import (digest YAML to database), entity resolution and matching, scoring, `corroborate` (AI-assisted cross-record same-fact verification - the one AI-assisted graph pass wired today), embeddings and hybrid search, Obsidian export, and the digest-maintenance passes (reclassify-documents, normalise-names, migrate-refs-delimiter, rewire-refs, backfill-record-fields). It also holds `consolidate` (AI-assisted claim de-duplication) as a library function, present but not yet wired to a command. Command-line surface: `assimilate` (incremental fold into the existing graph), `import`, `rebuild` (clean slate), `stats`, `show`, `embed`, `corroborate`, `search`, `export-obsidian`, plus the maintenance passes. The knowledge-graph database is a single SQLite file (currently `~/.local/share/digester/knowledge.db`; it relocates to `~/.local/share/assimilator/knowledge.db` with the split, overridable via `ASSIMILATOR_DB`); its schema is in [architecture/graph-schema.md](../architecture/graph-schema.md).
- **anomalica-common** (new shared library) - single-sources the two contracts both repos must agree on: the digest interchange (the data model and its YAML read/write, per 0027) and the Claude transport plus spend gate (per the operations billing policy). Single-sourcing prevents the format and the billing gate drifting between the two repositories.

The pipeline becomes: ingester -> digester (digest YAML) -> assimilator (knowledge graph) -> assembler -> content -> site, with the workbench as the review hub.

## Consequences

- The digester's surface shrinks to extraction; the assimilator owns everything graph-related. Each has one job, one failure profile, one cost profile.
- The digest YAML (0027) is now an explicit inter-repository contract - the digester produces it, the assimilator consumes it - single-sourced in anomalica-common so it cannot drift between them.
- The billing transport and spend gate (operations policy) is single-sourced in anomalica-common, so both repositories enforce the same gate identically.
- The knowledge-graph database moves to the assimilator (`~/.local/share/assimilator/knowledge.db`). The data-model description "the database is rebuilt from the digests by a deterministic import" now describes the assimilator's import, not the digester's.
- Consumers that read the graph (assembler, workbench, the Obsidian export) point at the assimilator's database.
- Detailed module lists and command-line surfaces live in `architecture/assimilator.md` and the trimmed `architecture/digester.md`, kept grounded against the implementation.

## Scope

Amends the digester architecture (`architecture/digester.md` trims to extraction-only; new `architecture/assimilator.md`) and the pipeline in `architecture/overview.md` and `architecture/data-model.md`. It does not change the digest interchange format (0027) itself - it relocates the format's implementation into anomalica-common.
