# Digester

The digester takes pre-ingested records and breaks them down into atomic components stored in the knowledge graph. It creates record and claim nodes, identifies domain nodes (people, organisations, places, events, matters, objects), builds provenance chains, and scores evidence.

## Inputs

The digester accepts records in the Anomalica record interchange format - markdown files with YAML frontmatter and annotation blocks (see [ADR 0012](../decisions/0012-record-interchange-format.md)). It does not process raw source material directly. The ingester converts raw formats (PDFs, audio, video, ebooks, web pages) into the record format before the digester sees them.

## Processing

### Record creation

Each input file becomes a Record node in the knowledge graph. The record node is a pointer to the original material (URL, ISBN, archive identifier), not a copy. The digester also identifies the record's producer (a person or organisation), making them a source.

### Claim extraction

Records are decomposed into atomic claims - the smallest independently verifiable factual assertions. Each claim is linked to its source record with a precise location reference (page number, paragraph, timestamp) and a speaker (the person who made the assertion, which may differ from the record's producer).

### Domain node identification and linking

The digester identifies domain nodes mentioned in claims: people, organisations, places, events, matters, objects. Nodes are linked across records - "David Grusch" in one transcript and "Grusch" in another are resolved to the same node.

### Provenance chains

Every claim carries a provenance chain showing how it reached the knowledge graph. When multiple records contain the same claim, the digester traces whether they are genuinely independent or derived from a common origin.

Example: If CNN, BBC, and Reuters all report the same Pentagon press release, that is one first-hand claim (the press release) with three second-hand repetitions, not four independent corroborations. The provenance chain makes this visible.

Two claims genuinely corroborate each other only if their provenance chains do not share a common root.

### Evidence scoring

Evidence scores are algorithmic, not editorial. No human assigns a score. The scoring considers:

- Number of independent sources corroborating a claim (provenance chains must not share a root)
- Attestation depth of each corroborating claim (first-hand, second-hand, third-hand)
- Track record of the sources involved
- Whether claims have been contradicted and by whom
- Quality and type of evidence (sensor data, official documents, witness testimony, hearsay)

The specific scoring algorithm is an implementation detail. The principle is that scoring is transparent, reproducible, and free of editorial judgement.

## Outputs

The digester produces extraction markdown files - human-readable documents containing all extracted nodes and claims with their metadata, original excerpts, and provenance information. These files are reviewed by humans, committed to the anomalica-extractions repository, and then imported into the knowledge graph database (SQLite) by a deterministic process with no AI involvement.

The database is derived from the extraction files and can be rebuilt from scratch at any time. The extraction markdown files in the anomalica-extractions repository are the source of truth for the knowledge graph.

## Source properties

The knowledge graph accumulates properties for each source over time:

| Property | Description |
|----------|-------------|
| **Track record** | How claims from this source's records fare when scored against independent records. Derived from data, not assigned by editors. |
| **Correction behaviour** | Whether and how quickly this source corrects contradicted claims. Tracked as observable events. |
| **Independence** | Institutional and financial connections to subjects the source covers. Documented factually. |

These properties are not assigned - they emerge from the data as the graph grows.

## Testing strategy

The digester is tested against a small, focused corpus of records centred on four people who represent different source types:

| Person | Role | Source type |
|--------|------|-------------|
| **David Fravor** | Navy pilot, USS Nimitz 2004 | Direct eyewitness (first-hand claims) |
| **David Grusch** | Intelligence officer, UAP Task Force | Whistleblower (second-hand claims about programmes he was briefed on) |
| **Lue Elizondo** | Former head of AATIP | Insider who went public (mix of first-hand and second-hand) |
| **Ross Coulthart** | Investigative journalist, NewsNation | Reporter (second-hand/third-hand, interviews the other three) |

This combination exercises the full pipeline:

- **Ingestion across formats** - congressional transcripts (text), podcast interviews (audio), news articles (web), books (ebook/PDF)
- **Claim extraction** - eyewitness accounts, whistleblower allegations, journalist reporting
- **Provenance chains** - Coulthart interviews Grusch, then NewsNation publishes a segment, then podcasts discuss it. The digester must trace these back to one origin, not count them as independent corroboration.
- **Attestation levels** - Fravor's "I saw it" (first-hand), Grusch's "I was told about programmes" (second-hand), Coulthart's "Grusch told me" (second-hand reporting on second-hand claims)
- **Cross-referencing** - the same events and claims appear across multiple records from different sources
- **Contradictions** - official DoD positions contradict whistleblower testimony

The test corpus is intentionally small (5-8 records per person, roughly 20-30 records total) so that the output can be manually verified against known facts. A specific record manifest is maintained separately.
