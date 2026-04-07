# 0004. Open source with transparent operations

Date: 2026-03-21
Status: accepted

## Context

The platform's credibility depends on being verifiable. Users need to be able to confirm that the evidence scoring methodology works as described, that the assembly pipeline does not introduce bias, and that the infrastructure is what it claims to be.

## Decision

All code, documentation, and operational decisions will be public. The project is hosted on a public git platform with repositories for each component:

- **anomalica** - organisation-level decisions, architecture, and documentation (this repository)
- **anomalica-ingester** - raw source material to structured text (audio, video, ebooks, PDFs, scanned documents)
- **anomalica-digester** - artificial intelligence extraction from ingests, producing digests
- **anomalica-digests** - reviewed digests, the source of truth for the knowledge graph (a structured database of interconnected facts)
- **anomalica-assembler** - article assembly from knowledge graph data, directive application
- **anomalica-content** - the output: assembled articles and associated media
- **anomalica-site** - the Hugo static site, consumes content from anomalica-content

Decisions are recorded as architecture decision records in `decisions/`. Tasks and ongoing work are tracked via the hosting platform's issue tracker. Conversations and open questions use the platform's discussion features.

Security does not rely on obscurity. The submission system, encryption, and conditional release are all designed to be secure with full source code visibility.

The only private elements are credentials, application programming interface keys, and the CLAUDE.md files that contain references to the founder's personal vault.

## Consequences

Anyone can audit the code, the methodology, and the decision-making process. Contributors can understand the project without asking - the documentation answers "why" as well as "what." The transparent history from founding onwards builds trust incrementally.
