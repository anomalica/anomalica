# Data Model

See also: [node types](node-types.md). This document is the canonical home for platform terminology.

## Core terms

| Term | Definition |
|------|-----------|
| **Source** | A role, not a node type. A person or organisation that produces records is a source. David Fravor is a Person node who is also a source because he has produced records (interviews, written statements). The New York Times is an Organisation node that is also a source. |
| **Record** | A node type. A specific artefact containing information: a podcast episode, document, transcript, article, video. A record is a pointer to the original material (URL, ISBN, archive identifier), not a copy. See [node types](node-types.md). |
| **Claim** | A node type. An atomic assertion extracted from a record, with a specific location within that record (timestamp, page, paragraph) and a speaker. The smallest unit of information in the knowledge graph (a structured database of interconnected facts) and the mechanism by which domain nodes (entries in the knowledge graph) are connected. See [node types](node-types.md). |
| **Directive** | A durable instruction for the assembler, extracted by artificial intelligence from human edits. Affects presentation only (style, grammar, disambiguation, formatting, naming). Cannot alter factual content. |
| **Assemble** | What the assembler's artificial intelligence does with knowledge-graph data to produce articles: arrange existing claims, attributions, and relationships into readable prose. It does not create information. |

## Relationships

- A **person** or **organisation** produces one or more **records** (making them a source)
- A **record** contains one or more **claims**
- A **claim** has a **speaker** (the person who made the assertion, which may differ from the record's producer)
- A **claim** has a location within its record (timestamp, page number, paragraph)
- A **claim** is attributed to one or more **records** (the same claim may appear in multiple records, which may constitute corroboration if the provenance chains are independent)
- A **claim** references zero or more **domain nodes** (person, organisation, place, event, matter, object)
- Domain nodes do not link directly to each other. Every relationship passes through a claim.

## Record provenance: who made a record versus who made a claim

A record's provenance is recorded in three fields:

- **`publisher`** (record frontmatter) - the entity that created the content (a channel, outlet, or committee), not the hosting platform.
- **`creators`** (record frontmatter) - the human creator(s): a document's author, a video or podcast host or presenter, a channel owner who is a named person. Person names in canonical "Last, First Middle" form.
- **`speaker`** (per claim) - who asserted a specific claim, which may differ from the record's creator (a guest on a host's podcast; a witness quoted in an article).

The **source** role (the person or organisation that produced the record) is the `publisher` and/or the `creators`. The `speaker` is claim-level, not record-level. All three may coincide (a solo essay) or all differ (a guest interviewed on a hosted show published by a channel).

## Source properties

Properties that accumulate as data flows through the knowledge graph, derived from data rather than assigned by editors:

| Property | Description |
|----------|-------------|
| **Track record** | How claims from this source's records fare when scored against independent records. |
| **Correction behaviour** | Whether and how quickly the source issues corrections when its claims are contradicted. Tracked as observable events. |
| **Independence** | Institutional and financial connections to the subjects the source covers. Documented factually, not scored as good or bad. |

## Claim attestation

Each claim carries an attestation level (how close the speaker was to what they are describing) describing the chain between the speaker and the events described:

| Level | Definition | Example |
|-------|-----------|---------|
| **First-hand** | The speaker directly observed or participated in what the claim describes. | "I saw an object hovering over the field." |
| **Second-hand** | The speaker is reporting what someone else directly observed. One step removed. | "My colleague told me he saw an object." |
| **Third-hand** | The speaker is reporting what someone heard from someone else. Two or more steps removed. | "There are reports from personnel who say colleagues witnessed an object." |

Attestation depth affects evidence scoring. A first-hand claim corroborated by another independent first-hand claim is stronger than a third-hand claim with no first-hand backing.

## Record classification

A record's classification describes its relationship to the events it covers - distinct from a claim's attestation, which describes the speaker's proximity to what they assert:

| Classification | Definition | Examples |
|----------------|-----------|----------|
| **Primary** | First-hand account or original data - direct observation or participation. | Witness testimony, sensor data, official investigation reports, Freedom of Information Act releases, scene photographs |
| **Secondary** | Reporting on or analysis of primary records. | News articles based on interviews, documentaries, analytical papers |
| **Tertiary** | Commentary on secondary records. | Opinion columns, podcast discussions of news articles, social-media commentary |

A single record may mix classifications: a news article can carry a direct witness quote (primary), the journalist's summary (secondary), and editorial framing (tertiary). Record classification (primary/secondary/tertiary) and claim attestation (first/second/third-hand) are related but distinct - a primary record (an original Freedom of Information Act document) may contain second-hand claims (an official reporting what a witness said).

## Claim types

Each claim carries a type describing the nature of the assertion. See [node types](node-types.md) for the full list: observation, testimony, hearsay, opinion, measurement, administrative.

Claim type is orthogonal to attestation level. A claim can be first-hand opinion, second-hand testimony, or third-hand hearsay about a measurement.

## Provenance chains

Every claim has a provenance chain (the path a claim took from its original source to the knowledge graph). Provenance chains are used to determine genuine independence when assessing corroboration.

Two claims corroborate each other only if their provenance chains do not share a common root. Ten outlets all reporting the same press release is one source, not ten.

## Pipeline outputs

Each pipeline stage has a named output:

| Stage | Output | Shareable | Description |
|-------|--------|-----------|-------------|
| Ingester | **Ingest** | No (copyright) | The record converted to structured text with metadata, plus any extracted media (images today; figures from PDFs and video keyframes later). Contains the actual content. |
| Digester | **Digest** | Yes | Claims, nodes, and provenance extracted from one ingest. No copyrighted content. |
| Assimilator | **Knowledge graph** | Yes (derived) | The unified SQLite graph built from all digests: cross-record entity resolution, provenance, scoring, embeddings. Derived data, rebuildable from the digests. |
| Assembler | **Article** | Yes | Readable prose assembled from knowledge graph data in a specific language. Public-eligible images from ingests are copied into the assembler's output for serving on the site. |

## Storage

The source of truth for the knowledge graph is the collection of digests in the digests repository. These are human-readable, version-controlled, and reviewable.

The SQLite database (a lightweight file-based database) is built and maintained by the assimilator, which imports the digests into the graph (see [assimilator.md](assimilator.md)). It serves as the query and distribution format - downloadable, torrentable, and verifiable - but is derived data, not primary. If deleted, it can be rebuilt from the digests. Embedding vectors are stored separately from core data to keep the primary download small.
