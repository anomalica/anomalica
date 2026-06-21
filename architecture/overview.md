# Architecture Overview

This is a living document. It reflects the current state of the system architecture and is updated as the design evolves. For the reasoning behind specific decisions, see the [architecture decision records](../decisions/). For detailed component documentation, see the linked pages below.

## Pipeline

```
raw sources --> ingester --> ingests (access-gated git repo)
(audio, video,                   |
 ebooks, PDFs,                   v
 scanned docs,               digester --> digests (public git repo)    [human review via workbench]
 web pages)                      |
                                 v
                             assimilator --> knowledge graph (SQLite)
                                 |
                                 v
                             synthesiser --> briefs (one per page, language-neutral)
                                 |
                                 v
                             assembler --> content (articles, media) --> site (static HTML)
                                 ^
                                 |
                             directives (extracted from human edits on the site;
                             meaning-altering edits rejected)
```

## Repositories

| Repository | Purpose |
|-----------|---------|
| **anomalica** | Organisation-level decisions, architecture, and documentation |
| **ingester** | Raw source material to structured text (audio, video, ebooks, PDFs, scanned documents) |
| **ingests** | Ingester output, access-gated per record by the source's copyright status (some records are copyrighted, others public domain or openly licensed) |
| **digester** | Artificial intelligence extraction from ingests, producing one digest per record (no graph). Planned: N model-variants per ingest reconciled into one canonical digest ([decision 0039](../decisions/0039-multi-model-digestion-canonical-reconciliation.md)) |
| **digests** | Reviewed digests - the source of truth for the knowledge graph (a structured database of interconnected facts) |
| **assimilator** | Builds and maintains the unified SQLite knowledge graph from digests: import, entity resolution, scoring, corroboration, embeddings, search, export |
| **anomalica-common** | Shared library: the digest interchange (data model + YAML I/O) and the Claude transport + spend gate, single-sourced so the digester and assimilator cannot drift |
| **assembler** | Article assembly from knowledge graph data, directive application |
| **content** | Output: assembled articles and associated media |
| **site** | Hugo static site, consumes content |
| **workbench** | Review application for correcting ingests and digests (Svelte 5 single-page application) |
| **brand** | Shared visual identity: logos, colour palette, fonts, design tokens |

## Data flow

The ingester writes ingests to the access-controlled ingests repository. The digester reads from that repository, extracts claims and nodes, and writes digests to the public digests repository. Both the ingester and digester need access to the ingests repository; public exposure of any individual ingest is then gated by that record's copyright status. (Planned direction: the digester may run several models per ingest and a reconciliation stage builds one canonical digest from them; only the canonical is assimilated - [decision 0039](../decisions/0039-multi-model-digestion-canonical-reconciliation.md).)

Human review happens through the workbench, which can correct both ingests and digests. Corrections are committed to the appropriate repository with the reviewer's identity as the git author.

The assimilator reads the digests and builds and maintains the unified knowledge graph database (SQLite, a lightweight file-based database) from them. The database is derived data, not the source of truth - if it is deleted, the assimilator rebuilds it from the digests.

The synthesiser reads the graph, decides which pages should exist, and emits one language-neutral brief per page (the graph slice that feeds that page). The assembler writes each page's prose from its brief alone - it does not read the graph (decision 0036). The brief's input hash is the per-page staleness unit and the audit hash 0010 mandates.

Digests are publicly readable on the git hosting platform but are not rendered as pages on the site. The site presents assembled articles only. Each article's references link back to both the original source material and the digest, giving readers a path to verify claims or report errors via the repository's issue tracker. Corrections to digests trigger a database rebuild and article reassembly.

## Component Documentation

- [Ingester](ingester.md) - raw source material to structured text, speaker diarisation, voice identification
- [Digester](digester.md) - per-record extraction from ingests, producing digests (no graph)
- [Assimilator](assimilator.md) - builds and maintains the knowledge graph from digests (import, entity resolution, scoring, corroboration, search, export)
- [Graph schema](graph-schema.md) - the knowledge-graph SQLite tables (the assimilator builds them; the assembler reads them)
- [Digester pipeline](digester-pipeline.md) - end-to-end digestion, review, import, reconciliation (note: import, reconciliation, and graph merging now belong to the assimilator; this page predates the split and needs a refresh)
- [Embeddings](embeddings.md) - vector generation, model selection, storage separation, re-embedding
- [Data model](data-model.md) - sources, records, claims, attestation, terminology
- [Node types](node-types.md) - knowledge graph node type definitions and classification rules
- [Brief format](brief-format.md) - the synthesise -> assemble interchange (one brief per page; the writer's sole input)
- [Assembler](assembler.md) - the writer: brief -> per-language prose + directives
- [Artificial intelligence constraints](ai-constraints.md) - boundaries on artificial intelligence involvement across all components
- [Review workbench](review-workbench.md) - separate application for reviewing and correcting ingests and digests
- [Test corpus](../context/test-corpus.md) - focused record set for testing the pipeline
