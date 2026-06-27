# Anomalica

Encyclopaedia of anomalous phenomena.

An international, jurisdiction-independent reference platform. Structured information with full source attribution, algorithmic evidence scoring, and 30 languages.

Website: [anomalica.is](https://anomalica.is) (not yet live)

## This Repository

Organisation-level decisions, architecture, and documentation. For code, see the other repositories under this organisation.

## Decisions

Decisions are routed by concern - see [0001](decisions/0001-record-decisions.md) for the scheme. Architecture decisions live as numbered records in `decisions/`; other decisions live in the home that fits them:

- **Governance & founding** (aims, name, funding, licensing, languages, disclosure policy): [guides/governance.md](guides/governance.md)
- **Editorial & voice** (plain language, neutral voice, AI-use disclosure): [guides/editorial-style.md](guides/editorial-style.md)
- **Data model, terminology & taxonomy** (node types, naming, claim and extraction conventions): [architecture/data-model.md](architecture/data-model.md) and [architecture/node-types.md](architecture/node-types.md)
- **Operations & infrastructure** (domains, hosting, analytics): the `operations` repository
- **Visual identity** (logos, palette, design tokens): the `brand` repository (`brand/visual-identity.md`)

Architecture decision records follow the format context / decision / consequences, and are maintained rather than frozen: corrections and clarifications are edited in place (git tracks the history); a material change is a dated amendment or a superseding record.

| # | Decision |
|---|----------|
| [0001](decisions/0001-record-decisions.md) | How and where decisions are recorded |
| [0008](decisions/0008-content-traceable-to-sources.md) | Content traceable to sources |
| [0010](decisions/0010-auditable-assembly.md) | Auditable article assembly |
| [0011](decisions/0011-claims-as-atomic-unit.md) | Claims as the atomic unit of knowledge |
| [0014](decisions/0014-static-site-architecture.md) | Serve the platform as a static website |
| [0015](decisions/0015-hosting-resilience.md) | Graceful degradation and data survivability |
| [0016](decisions/0016-sqlite-storage.md) | Use SQLite for knowledge graph storage |
| [0018](decisions/0018-network-driven-ingestion.md) | Network-driven ingestion |
| [0019](decisions/0019-record-interchange-format.md) | Markdown with YAML annotations as record interchange format |
| [0020](decisions/0020-canonical-english-embeddings.md) | Canonical English normalisation for embeddings |
| [0021](decisions/0021-content-review-lifecycle.md) | Content review lifecycle (draft) |
| [0027](decisions/0027-digest-interchange-format.md) | Digest interchange format |
| [0031](decisions/0031-per-record-inspection-pages.md) | Per-record extraction inspection pages (draft) |

Gaps in the numbering are expected: records that moved to another home keep their slot empty rather than being renumbered. Draft decisions in progress are in [decisions/drafts/](decisions/drafts/).

## Architecture

Living documents that reflect the current state of the system. See [architecture/](architecture/).

- [Overview](architecture/overview.md) - pipeline, repositories, component index
- [Ingester](architecture/ingester.md) - raw source material to ingests (structured text)
- [Digester](architecture/digester.md) - ingests to digests (claims, nodes, provenance)
- [Data model](architecture/data-model.md) - sources, records, claims, terminology
- [Node types](architecture/node-types.md) - the knowledge-graph taxonomy
- [Assembler](architecture/assembler.md) - article assembly, directives, languages
- [AI constraints](architecture/ai-constraints.md) - boundaries on AI involvement

## Guides

Living, freely-edited guides for the non-architecture concerns:

- [Governance charter](guides/governance.md) - what Anomalica is, funding, licensing, languages, disclosure
- [Editorial style](guides/editorial-style.md) - plain language, neutral voice, AI-use disclosure

## Related Repositories

- **ingester** - raw source material to ingests (audio, video, ebooks, PDFs, scanned documents)
- **digester** - ingests to digests (claim extraction, evidence scoring)
- **digests** - reviewed digests, the source of truth for the knowledge graph
- **assembler** - article assembly from knowledge graph, directive application
- **content** - assembled articles and associated media
- **site** - Hugo static site

## Contact

support@anomalica.is
