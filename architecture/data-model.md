# Data Model

See also: [node types](node-types.md), [terminology (decision 0012)](../decisions/0012-terminology.md)

## Core terms

| Term | Definition |
|------|-----------|
| **Source** | A role, not a node type. A person or organisation that produces records is a source. David Fravor is a Person node who is also a source because he has produced records (interviews, written statements). The New York Times is an Organisation node that is also a source. |
| **Record** | A node type. A specific artefact containing information: a podcast episode, document, transcript, article, video. A record is a pointer to the original material (URL, ISBN, archive identifier), not a copy. See [node types](node-types.md). |
| **Claim** | A node type. An atomic assertion extracted from a record, with a specific location within that record (timestamp, page, paragraph) and a speaker. The smallest unit of information in the knowledge graph (a structured database of interconnected facts) and the mechanism by which domain nodes (entries in the knowledge graph) are connected. See [node types](node-types.md). |
| **Directive** | A durable instruction for the assembler, extracted by artificial intelligence from human edits. Affects presentation only (style, grammar, disambiguation, formatting, naming). Cannot alter factual content. |

## Relationships

- A **person** or **organisation** produces one or more **records** (making them a source)
- A **record** contains one or more **claims**
- A **claim** has a **speaker** (the person who made the assertion, which may differ from the record's producer)
- A **claim** has a location within its record (timestamp, page number, paragraph)
- A **claim** is attributed to one or more **records** (the same claim may appear in multiple records, which may constitute corroboration if the provenance chains are independent)
- A **claim** references zero or more **domain nodes** (person, organisation, place, event, matter, object)
- Domain nodes do not link directly to each other. Every relationship passes through a claim.

## Claim attestation

Each claim carries an attestation level (how close the speaker was to what they are describing) describing the chain between the speaker and the events described:

| Level | Definition | Example |
|-------|-----------|---------|
| **First-hand** | The speaker directly observed or participated in what the claim describes. | "I saw an object hovering over the field." |
| **Second-hand** | The speaker is reporting what someone else directly observed. One step removed. | "My colleague told me he saw an object." |
| **Third-hand** | The speaker is reporting what someone heard from someone else. Two or more steps removed. | "There are reports from personnel who say colleagues witnessed an object." |

Attestation depth affects evidence scoring. A first-hand claim corroborated by another independent first-hand claim is stronger than a third-hand claim with no first-hand backing.

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
| Assembler | **Article** | Yes | Readable prose assembled from knowledge graph data in a specific language. Public-eligible images from ingests are copied into the assembler's output for serving on the site. |

## Storage

The source of truth for the knowledge graph is the collection of digests in the anomalica-digests repository. These are human-readable, version-controlled, and reviewable.

The SQLite database (a lightweight file-based database) is rebuilt from the digests by a deterministic import process. It serves as the query and distribution format - downloadable, torrentable, and verifiable - but is derived data, not primary. If deleted, it can be rebuilt. Embedding vectors are stored separately from core data to keep the primary download small.
