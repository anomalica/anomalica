# Architecture Overview

This is a living document. It reflects the current state of the system architecture and is updated as the design evolves. For the reasoning behind specific decisions, see the [ADRs](../decisions/). For detailed component documentation, see the linked pages below.

## Pipeline

```
any raw format ──> anomalica-ingester ──> structured text with metadata
(audio, video, ebooks,                            |
PDFs, scanned docs,                               v
web pages)                                anomalica-digester ──> extraction markdown
                                                                        |
                                                                  human review
                                                                        |
                                                                        v
                                                              anomalica-extractions (git)
                                                                        |
                                                                  rebuild database
                                                                        |
                                          directives ───────────────────┤
                                                                        v
                                                                anomalica-assembler
                                                                        |
                                                                        v
                                                                anomalica-content (articles, media)
                                                                        |
                                                                        v
                                                                anomalica-site (static HTML)

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
| **anomalica-ingester** | Raw source material to structured text (audio, video, ebooks, PDFs, scanned documents) |
| **anomalica-digester** | AI extraction from records, producing reviewable markdown files |
| **anomalica-extractions** | Reviewed extraction markdown files - the source of truth for the knowledge graph |
| **anomalica-assembler** | Article assembly from knowledge graph data, directive application |
| **anomalica-content** | Output: assembled articles and associated media |
| **anomalica-site** | Hugo static site, consumes anomalica-content |

## Data flow

The digester produces human-readable extraction markdown files. These are reviewed (and corrected if necessary), then committed to the anomalica-extractions repository. The knowledge graph database (SQLite) is rebuilt deterministically from these files at any time. The database is derived data, not the source of truth - if it is deleted, it can be rebuilt from the extraction files.

## Component Documentation

- [Ingester](ingester.md) - raw source material to structured text, speaker diarisation, voice identification
- [Digester](digester.md) - AI extraction from records to reviewable markdown
- [Digester pipeline](digester-pipeline.md) - extraction, review, import, reconciliation, graph merging
- [Embeddings](embeddings.md) - vector generation, model selection, storage separation, re-embedding
- [Data model](data-model.md) - sources, records, claims, attestation, terminology
- [Node types](node-types.md) - knowledge graph node type definitions and classification rules
- [Assembler](assembler.md) - article assembly, directives, languages
- [AI constraints](ai-constraints.md) - boundaries on AI involvement across all components
- [Test corpus](../context/test-corpus.md) - focused record set for testing the pipeline
