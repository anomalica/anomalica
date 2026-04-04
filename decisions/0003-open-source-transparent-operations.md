# 0003. Open source with transparent operations

Date: 2026-03-21
Status: accepted

## Context

The platform's credibility depends on being verifiable. Users need to be able to confirm that the evidence scoring methodology works as described, that the assembly pipeline does not introduce bias, and that the infrastructure is what it claims to be.

## Decision

All code, documentation, and operational decisions will be public. The project operates under a GitHub organisation (github.com/anomalica) with repositories for each component:

- **anomalica** - organisation-level decisions, architecture, and documentation (this repository)
- **anomalica-ingester** - raw source material to structured text (audio, video, ebooks, PDFs, scanned documents)
- **anomalica-digester** - AI extraction from records, producing reviewable markdown files
- **anomalica-extractions** - reviewed extraction markdown files, the source of truth for the knowledge graph
- **anomalica-assembler** - article assembly from knowledge graph data, directive application
- **anomalica-content** - the output: assembled articles and associated media
- **anomalica-site** - the Hugo static site, consumes content from anomalica-content

Decisions are recorded as Architecture Decision Records in `decisions/`. Tasks and ongoing work are tracked via GitHub Issues. Conversations and open questions use GitHub Discussions.

Security does not rely on obscurity. The submission system, encryption, and conditional release are all designed to be secure with full source code visibility.

The only private elements are credentials, API keys, and the CLAUDE.md files that contain references to the founder's personal vault.

## Consequences

Anyone can audit the code, the methodology, and the decision-making process. Contributors can understand the project without asking - the documentation answers "why" as well as "what." The transparent history from founding onwards builds trust incrementally.
