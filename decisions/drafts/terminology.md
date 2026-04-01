# Draft: Platform terminology

Date: 2026-03-23
Status: draft

## Context

The platform's documentation, code, and user-facing content need a consistent vocabulary. Several terms - particularly "source" - are ambiguous when used informally. Inconsistent terminology across ADRs, specs, and code would create confusion for contributors and users.

This ADR establishes canonical terms for the core concepts that appear throughout the project.

## Decision

### Core data model terms

| Term | Definition | Examples |
|------|-----------|----------|
| **Source** | A role, not a node type. A person or organisation that produces records is a source. Sources have a track record that builds over time as their claims are scored against independent records. | GEIPAN, Ross Coulthart, the US Navy, a specific witness, The Black Vault, Nature (journal) |
| **Record** | A node type. A specific artefact that contains information. A record has a date, a reference (URL, ISBN, archive identifier), a format, and a producer (person or organisation). Records are pointers to the original material, not copies - the platform does not host copyrighted or confidential content. | A podcast episode, a FOIA document, a congressional transcript, a news article, a book, a video, a case file |
| **Claim** | An atomic assertion extracted from a record. The smallest unit of information in the knowledge graph and the mechanism by which domain nodes are connected. Each claim traces back to a specific record from a specific source. Claims carry an attestation level (first-hand, second-hand, third-hand) and a claim type (observation, testimony, hearsay, opinion, measurement, administrative). See [node types](../../architecture/node-types.md). | "Radar confirmed an object travelling at 1,200 km/h at 09:14 on 2024-03-15", "David Grusch held a TS/SCI clearance", "The object was observed for approximately 12 minutes" |

### Relationships

- A **person** or **organisation** produces one or more **records** (making them a source)
- A **record** contains one or more **claims**
- A **claim** has a **speaker** (the person who made the assertion) and a location within its record (timestamp, page, paragraph)
- A **claim** is attributed to one or more **records** (the same claim may appear in multiple records, which may constitute corroboration if the provenance chains are independent)
- A **claim** references zero or more **domain nodes** (person, organisation, place, event, matter, object)
- Domain nodes do not link directly to each other - every relationship passes through a claim

### Source properties

Properties that accumulate over time as data flows through the knowledge graph:

| Property | Description |
|----------|-------------|
| **Track record** | How do claims from this source's records fare when scored against independent records? Derived from data, not assigned by editors. |
| **Correction behaviour** | Does this source issue corrections when claims are contradicted? How quickly? Tracked as observable events. |
| **Independence** | Institutional and financial connections to subjects the source covers. Documented factually, not scored as good or bad. |

### Content role terms

| Term | Definition |
|------|-----------|
| **Assemble** | What AI does with knowledge graph data to produce articles. The AI arranges existing claims, attributions, and relationships into readable prose. It does not create information. |
| **Directive** | A durable instruction for the assembler, extracted by AI from human edits. Directives affect presentation only (style, grammar, disambiguation, formatting, naming conventions) and cannot alter the meaning of an article. Meaning-altering edits are rejected; factual corrections must be submitted as records through the digestion pipeline. Directives persist across article reassemblies and may be scoped to an article, topic, or language. |

### Record classification

A record's classification depends on its relationship to the events it describes:

| Classification | Definition | Examples |
|----------------|-----------|----------|
| **Primary** | First-hand account or original data. The record originates from direct observation or participation. | Witness testimony, sensor data, official investigation reports, FOIA-released documents, photographs taken at the scene |
| **Secondary** | Reporting on or analysis of primary records. The record interprets or summarises first-hand material. | News articles based on interviews, documentaries, analytical papers |
| **Tertiary** | Commentary on secondary records. The record discusses other people's reporting or analysis. | Opinion columns, podcast discussions about news articles, social media commentary |

A single record may contain a mix of classifications. A news article might include a direct witness quote (primary record material), the journalist's summary of events (secondary), and editorial framing (tertiary).

Note: record classification (primary/secondary/tertiary) describes the record's relationship to events. Claim attestation (first-hand/second-hand/third-hand) describes the speaker's proximity to what they are asserting. These are related but distinct concepts. A primary record (original FOIA document) may contain second-hand claims (an official reporting what a witness told them).

## Consequences

All ADRs, specs, code, and user-facing documentation should use these terms consistently. When a new concept needs a name, it should be added here before being used elsewhere.

This is a living document during the draft phase. Once accepted, changes require a new ADR that supersedes this one.
