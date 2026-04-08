# Anomalica

Encyclopaedia of anomalous phenomena.

An international, jurisdiction-independent reference platform. Structured information with full source attribution, algorithmic evidence scoring, and 30 languages.

Website: [anomalica.is](https://anomalica.is) (not yet live)

## This Repository

Organisation-level decisions, architecture, and documentation. For code, see the other repositories under this organisation.

## Decisions

Decision records following the [architecture decision record format](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions). Each record is immutable once accepted. To change a decision, a new record is created that supersedes the old one.

| # | Decision |
|---|----------|
| [0001](decisions/0001-record-decisions.md) | Record decisions |
| [0002](decisions/0002-project-founding.md) | Build an international reference platform for anomalous phenomena |
| [0003](decisions/0003-name-anomalica.md) | Name the platform Anomalica |
| [0004](decisions/0004-open-source-transparent-operations.md) | Open source with transparent operations |
| [0005](decisions/0005-licensing.md) | MIT licence for code, CC0 for data |
| [0006](decisions/0006-plain-language.md) | Plain language in all documents |
| [0007](decisions/0007-neutral-voice-no-editorial-content.md) | Neutral voice with no editorial content |
| [0008](decisions/0008-content-traceable-to-sources.md) | Content traceable to sources |
| [0009](decisions/0009-transparent-ai-use.md) | Transparent use of artificial intelligence with independent verification |
| [0010](decisions/0010-auditable-assembly.md) | Auditable article assembly |
| [0011](decisions/0011-claims-as-atomic-unit.md) | Claims as the atomic unit of knowledge |
| [0012](decisions/0012-terminology.md) | Platform terminology |
| [0013](decisions/0013-domain-strategy.md) | Domain registration strategy |
| [0014](decisions/0014-static-site-architecture.md) | Serve the platform as a static website |
| [0015](decisions/0015-hosting-resilience.md) | Hosting strategy and graceful degradation |
| [0016](decisions/0016-sqlite-storage.md) | Use SQLite for knowledge graph storage |
| [0017](decisions/0017-website-analytics.md) | Website analytics with GoatCounter |
| [0018](decisions/0018-network-driven-ingestion.md) | Network-driven ingestion |
| [0019](decisions/0019-record-interchange-format.md) | Markdown with YAML annotations as record interchange format |
| [0020](decisions/0020-canonical-english-embeddings.md) | Canonical English normalisation for embeddings |
| [0021](decisions/0021-content-review-lifecycle.md) | Content review lifecycle |
| [0022](decisions/0022-thirty-languages.md) | Supported languages |
| [0023](decisions/0023-person-naming-convention.md) | Person naming convention |
| [0024](decisions/0024-visual-identity.md) | Visual identity |

Draft decisions in progress can be found in [decisions/drafts/](decisions/drafts/).

## Architecture

Living documents that reflect the current state of the system. See [architecture/](architecture/).

- [Overview](architecture/overview.md) - pipeline, repositories, component index
- [Ingester](architecture/ingester.md) - raw source material to ingests (structured text)
- [Digester](architecture/digester.md) - ingests to digests (claims, nodes, provenance)
- [Data model](architecture/data-model.md) - sources, records, claims, terminology
- [Assembler](architecture/assembler.md) - article assembly, directives, languages
- [AI constraints](architecture/ai-constraints.md) - boundaries on AI involvement

## Related Repositories

- **anomalica-ingester** - raw source material to ingests (audio, video, ebooks, PDFs, scanned documents)
- **anomalica-digester** - ingests to digests (claim extraction, evidence scoring)
- **anomalica-digests** - reviewed digests, the source of truth for the knowledge graph
- **anomalica-assembler** - article assembly from knowledge graph, directive application
- **anomalica-content** - assembled articles and associated media
- **anomalica-site** - Hugo static site

## Contact

mark@anomalica.is
