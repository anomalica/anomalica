# Architecture Overview

This is a living document. It reflects the current state of the system architecture and is updated as the design evolves. For the reasoning behind specific decisions, see the [ADRs](../decisions/). For detailed component documentation, see the linked pages below.

## Pipeline

```
any raw format ──> anomalica-ingester ──> structured text with metadata
(audio, video, ebooks,                            |
PDFs, scanned docs,                               v
web pages)                                anomalica-digester ──> knowledge graph (SQLite)
                                                                            |
                                          directives ───────────────────────┤
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
| **anomalica-digester** | Claim extraction, knowledge graph building, evidence scoring |
| **anomalica-assembler** | Article assembly from knowledge graph data, directive application |
| **anomalica-content** | Output: assembled articles and associated media |
| **anomalica-site** | Hugo static site, consumes anomalica-content |

## Component Documentation

- [Ingester](ingester.md) - raw source material to structured text, speaker diarisation, voice identification
- [Digester](digester.md) - claim extraction, node linking, provenance chains, evidence scoring
- [Digester pipeline](digester-pipeline.md) - extraction, integration, reconciliation, graph merging, domain vs infrastructure databases
- [Embeddings](embeddings.md) - vector generation, model selection, storage separation, re-embedding
- [Data model](data-model.md) - sources, records, claims, attestation, terminology
- [Node types](node-types.md) - knowledge graph node type definitions
- [Assembler](assembler.md) - article assembly, directives, languages
- [AI constraints](ai-constraints.md) - boundaries on AI involvement across all components
- [Test corpus](../context/test-corpus.md) - focused record set for testing the pipeline
