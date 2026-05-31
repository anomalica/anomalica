# Architecture Overview

This is a living document. It reflects the current state of the system architecture and is updated as the design evolves. For the reasoning behind specific decisions, see the [architecture decision records](../decisions/). For detailed component documentation, see the linked pages below.

## Pipeline

```
any raw format ──> ingester ──> ingests (private git repo)
(audio, video, ebooks,                            |
PDFs, scanned docs,                               v
web pages)                                digester ──> digests (public git repo)
                                                                        |
                                                human review via ───────┤
                                                workbench     |
                                                                  rebuild database
                                                                        |
                                          directives ───────────────────┤
                                                                        v
                                                                assembler
                                                                        |
                                                                        v
                                                                content (articles, media)
                                                                        |
                                                                        v
                                                                site (static HTML)

                                          human edits article on site
                                                      |
                                                      v
                                          AI extracts presentational directives
                                          (meaning-altering edits rejected)
```

## Repositories

| Repository | Purpose |
|-----------|---------|
| **anomalica** | Organisation-level decisions, architecture, and documentation |
| **ingester** | Raw source material to structured text (audio, video, ebooks, PDFs, scanned documents) |
| **ingests** | Ingester output (private - contains copyrighted source material) |
| **digester** | Artificial intelligence extraction from ingests, producing digests |
| **digests** | Reviewed digests - the source of truth for the knowledge graph (a structured database of interconnected facts) |
| **assembler** | Article assembly from knowledge graph data, directive application |
| **content** | Output: assembled articles and associated media |
| **site** | Hugo static site, consumes content |
| **workbench** | Review application for correcting ingests and digests (Svelte 5 single-page application) |
| **brand** | Shared visual identity: logos, colour palette, fonts, design tokens |

## Data flow

The ingester writes ingests to the private ingests repository. The digester reads from that repository, extracts claims and nodes, and writes digests to the public digests repository. Both the ingester and digester need access to the private repository.

Human review happens through the workbench, which can correct both ingests and digests. Corrections are committed to the appropriate repository with the reviewer's identity as the git author.

The knowledge graph database (SQLite, a lightweight file-based database) is rebuilt deterministically from the digests at any time. The database is derived data, not the source of truth - if it is deleted, it can be rebuilt from the digests.

Digests are publicly readable on the git hosting platform but are not rendered as pages on the site. The site presents assembled articles only. Each article's references link back to both the original source material and the digest, giving readers a path to verify claims or report errors via the repository's issue tracker. Corrections to digests trigger a database rebuild and article reassembly.

## Component Documentation

- [Ingester](ingester.md) - raw source material to structured text, speaker diarisation, voice identification
- [Digester](digester.md) - claim extraction from ingests, producing digests
- [Digester pipeline](digester-pipeline.md) - digestion, review, import, reconciliation, graph merging
- [Embeddings](embeddings.md) - vector generation, model selection, storage separation, re-embedding
- [Data model](data-model.md) - sources, records, claims, attestation, terminology
- [Node types](node-types.md) - knowledge graph node type definitions and classification rules
- [Assembler](assembler.md) - article assembly, directives, languages
- [Artificial intelligence constraints](ai-constraints.md) - boundaries on artificial intelligence involvement across all components
- [Review workbench](review-workbench.md) - separate application for reviewing and correcting ingests and digests
- [Test corpus](../context/test-corpus.md) - focused record set for testing the pipeline
