# Anomalica

Encyclopaedia of anomalous phenomena.

An international, jurisdiction-independent reference platform. Structured information with full source attribution, algorithmic evidence scoring, and 30 languages.

Website: [anomalica.is](https://anomalica.is) (not yet live)

## This Repository

Organisation-level decisions, architecture, and documentation. For code, see the other repositories under this organisation.

## Decisions

Architecture Decision Records following the [ADR format](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions). Each record is immutable once accepted. To change a decision, a new record is created that supersedes the old one.

| ADR | Decision |
|-----|----------|
| [0001](decisions/0001-record-decisions.md) | Record decisions as ADRs |
| [0002](decisions/0002-project-founding.md) | Build an international reference platform for anomalous phenomena |
| [0003](decisions/0003-open-source-transparent-operations.md) | Open source with transparent operations |
| [0004](decisions/0004-transparent-ai-use.md) | Transparent use of AI with independent verification |
| [0005](decisions/0005-licensing.md) | MIT licence for code, CC0 for data |
| [0006](decisions/0006-name-anomalica.md) | Name the platform Anomalica |
| [0007](decisions/0007-domain-strategy.md) | Domain registration strategy |
| [0008](decisions/0008-static-site-architecture.md) | Serve the platform as a static website |
| [0009](decisions/0009-sqlite-storage.md) | Use SQLite for knowledge graph storage |
| [0010](decisions/0010-content-traceable-to-sources.md) | Content traceable to sources |
| [0011](decisions/0011-neutral-voice-no-editorial-content.md) | Neutral voice with no editorial content |
| [0012](decisions/0012-record-interchange-format.md) | Markdown with YAML annotations as record interchange format |
| [0013](decisions/0013-thirty-languages.md) | Supported languages |
| [0014](decisions/0014-auditable-assembly.md) | Auditable article assembly |
| [0015](decisions/0015-website-analytics.md) | Website analytics with GoatCounter |

Draft decisions in progress can be found in [decisions/drafts/](decisions/drafts/).

## Architecture

Living documents that reflect the current state of the system. See [architecture/](architecture/).

- [Overview](architecture/overview.md) - pipeline, repositories, component index
- [Ingester](architecture/ingester.md) - raw source material to structured text
- [Digester](architecture/digester.md) - claim extraction, provenance chains, evidence scoring
- [Data model](architecture/data-model.md) - sources, records, claims, terminology
- [Assembler](architecture/assembler.md) - article assembly, directives, languages
- [AI constraints](architecture/ai-constraints.md) - boundaries on AI involvement

## Related Repositories

- **anomalica-ingester** - raw source material to structured text (audio, video, ebooks, PDFs, scanned documents)
- **anomalica-digester** - claim extraction, knowledge graph building, evidence scoring
- **anomalica-assembler** - article assembly from knowledge graph, directive application
- **anomalica-content** - assembled articles and associated media
- **anomalica-site** - Hugo static site

## Contact

mark@anomalica.is
