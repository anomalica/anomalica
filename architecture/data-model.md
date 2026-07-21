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
- A **claim** references zero or more **domain nodes** (person, organisation, project, place, event, object, document, topic)
- Domain nodes do not link directly to each other. Every relationship passes through a claim.

## Record provenance: who made a record versus who made a claim

A record's source-origin metadata lives in one `provenance` block ([record-format.md](record-format.md#provenance), [decision 0043](../decisions/0043-canonical-provenance-block.md)) - `publisher`, `creators`, `published_date`, `source_url`, `identifiers`, `collection`, and the rest. Two roles matter for who-said-what:

- **`provenance.publisher`** - the entity that created the source (a channel, outlet, or committee), not the hosting platform.
- **`provenance.creators`** - the human creator(s): a document's author, a video or podcast host or presenter, a named channel owner. Person names in natural order.
- **`speaker`** (per claim) - who asserted a specific claim, which may differ from the record's creator (a guest on a host's podcast; a witness quoted in an article).

The **source** role (the person or organisation that produced the record) is `provenance.publisher` and/or `provenance.creators`. The `speaker` is claim-level, not record-level. All three may coincide (a solo essay) or all differ (a guest interviewed on a hosted show published by a channel).

**Provenance carries to claims.** A claim's authoritative provenance is a reference to its source record - the `record_id` it already carries - so the record's `provenance` block is the single source of truth and the corroboration logic (independence by provenance root) is unaffected. On top, the digest may denormalise `publisher` + `published_date` + `collection` onto a claim as a RENDER CACHE (recomputed on re-digest, never authoritative), so an article renders "from a 1949 Department of Energy document" without a join. A subject's incident place and date are claims about place and event nodes - never provenance.

## Source properties

Properties that accumulate as data flows through the knowledge graph, derived from data rather than assigned by editors:

| Property | Description |
|----------|-------------|
| **Track record** | How claims from this source's records fare when scored against independent records. |
| **Correction behaviour** | Whether and how quickly the source issues corrections when its claims are contradicted. Tracked as observable events. |
| **Independence** | Institutional and financial connections to the subjects the source covers. Documented factually, not scored as good or bad. |

## Record unit: whole containers versus scoped excerpts

Most sources map to one record. The exception is a large CONTAINER whose relevant content is a small, cited fraction - a defence appropriations act (~1700 pages) cited only for its UAP provisions, an omnibus report, a hearing appendix. Two units are possible, and the choice is by relevance DENSITY, not size:

- **Whole-container record** - the container's full text is the record body, and sub-parts are located nodes and claims within it. Right when the container is mostly SIGNAL: a UAP FOIA release, a UAP hearing. (The Elizondo resignation letter is not a separate record; it is held-within the FOIA release that reproduces it, located by page range - so a FOIA is a whole-container record even though it "contains" letters.)
- **Scoped excerpt record** - the record body is only the relevant sections; the FULL container is archived as the original for verifiability. Right when the container is mostly NOISE: a budget statute cited for three UAP sections, where extracting the whole act floods review with irrelevant statute and pays extraction on 1700 pages to keep 20.

The test is **whole when extracting the container is mostly signal, excerpt when it is mostly noise.** Size is a symptom, not the criterion: a short mostly-irrelevant source may excerpt, a long mostly-relevant one stays whole.

A scoped excerpt record is **body-anchored regardless of the container's media type**: its `content_hash` is over the extracted excerpt (so two excerpts of one act are distinct records), and `source_hash` addresses the full archived container - the same two-hash pattern web and ebook records already use ([record-format.md](record-format.md), [format-specs.yaml](../reference/format-specs.yaml) `chain`). Provenance names the container and the scope: `publisher` (issuing body), `identifiers` (the public-law or report number), `source_url` (the full act), and the record title carries the sections ("NDAA FY2023 - UAP provisions, secs. 6801-6803"). A different section becoming relevant later is a new excerpt record from the same archived original - nothing is re-acquired, and completeness lives in the archive rather than in every record.

The whole-versus-excerpt call is a **human judgement made at acquisition** - relevance density is not something the ingester can infer from a file, so it cannot decide noise-from-signal itself. It reaches the handler as an explicit **excerpt directive** on the source, carrying the section scope (e.g. `excerpt: {scope: "secs. 6801-6803"}`). That directive does two things: it selects the sections the handler extracts, and it switches the handler to body-anchoring (name by the excerpt-body hash, write `source_hash` over the full archived container - the web/ebook mode, applied to a PDF). Absent the directive a source ingests WHOLE, which is the safe default - a missing directive under-excerpts (a larger but complete record), never silently drops relevant content. The same scope string becomes the record's title suffix and the provenance section-naming.

## Claim attestation

Each claim carries an attestation level (how close the speaker was to what they are describing) describing the chain between the speaker and the events described:

| Level | Definition | Example |
|-------|-----------|---------|
| **First-hand** | The speaker directly observed or participated in what the claim describes. | "I saw an object hovering over the field." |
| **Second-hand** | The speaker is reporting what someone else directly observed. One step removed. | "My colleague told me he saw an object." |
| **Third-hand** | The speaker is reporting what someone heard from someone else. Two or more steps removed. | "There are reports from personnel who say colleagues witnessed an object." |

Attestation depth affects evidence scoring. A first-hand claim corroborated by another independent first-hand claim is stronger than a third-hand claim with no first-hand backing.

Attestation is **derived from the provenance chain**, not judged by feel ([0044](../decisions/0044-claim-provenance-chain-is-required.md)): `origin_kind: speaker` with an empty relay is `first_hand`; one remove is `second_hand`; two or more removes is `third_hand`; `unattributed` has no evidential stance and omits it.

**Grade by the whole chain, not by the last mouth it passed through.** A speaker naming their immediate contact does not make a claim second-hand if that contact was themselves relaying someone else - count the removes. An assertion reaching the speaker as a forwarded email from an anonymous source is `third_hand`, however confidently the speaker names the person who forwarded it.

## Claim text and load-bearing attribution

A claim's `text` normally states the bare fact, with the speaker held in the structured `speaker` field - naming the relayer in the text would turn the graph into a pile of quotations rather than portable facts. That rule holds **only where the speaker is a conduit** for something that stands independently of who relayed it.

It reverses where the attribution is load-bearing - `origin_kind: anonymous`, or `type: hearsay`, or an attestation of `second_hand`/`third_hand`. There, **the attribution goes inside the `text`** ([0044](../decisions/0044-claim-provenance-chain-is-required.md)).

The reason is not stylistic. For such a claim, the proposition is not a fact about the world and is not what the source establishes; the fact about the world is *that someone asserted it*. Stripping the attribution does not tidy the claim, it changes what the claim says - from a true statement about an assertion into a false statement about reality. `text` is what flows into articles, so a claim must be safe read alone; safety cannot depend on every consumer, forever, remembering to check a sidecar field.

## Only sincere assertions are claims

Exhaustive extraction means never skimming and never curating for importance. It does not mean literalising every sentence spoken. A claim is extracted only where the source **sincerely asserts** a fact. The following are not claims, even though the words appear verbatim in the source: jokes, deadpan, irony and running bits (comedic self-description is not biography, and deadpan gives no signal a joke is underway); hypotheticals and rhetorical questions; statements quoted in order to be rejected; and hyperbole or figures of speech, which are never converted into measurements.

Omitting a joke costs little. Asserting one as fact manufactures a false fact, which is the worst output this system can produce.

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

The chain is a **required** field on every claim ([0044](../decisions/0044-claim-provenance-chain-is-required.md)) - the extraction schema will not accept a claim without it, so "where did this come from?" is a question the model must answer rather than one it may skip:

```yaml
provenance_chain:
  origin_kind: anonymous        # speaker | named | anonymous | document | unattributed
  origin: "a person claiming to work inside the Defense Intelligence Agency"
  relay:                        # ordered, origin -> speaker; empty when the speaker IS the origin
    - "an email"
    - "an intermediary known to the speaker"
```

| `origin_kind` | The root of the chain |
|---------------|----------------------|
| `speaker` | The speaker originated it - they observed it, did it, or hold it. `relay` is empty. |
| `named` | An identifiable person, organisation, or document. It is a node, and must also appear in `refs`. |
| `anonymous` | An unnamed or unidentifiable source. **It cannot be a node** (see [node types](node-types.md)), so this field is the only place it can survive. |
| `document` | A document or record the speaker is reading from or citing. |
| `unattributed` | The source asserts it with no attribution offered - ordinary narration. |

`origin_kind` is what corroboration keys on. An `anonymous` root matters most: because an anonymous actor can never be a node, dropping the chain does not merely lose detail - it silently promotes an anonymous assertion into an institutional one ("an anonymous person claiming to work inside the Defense Intelligence Agency said X" collapses into "the Defense Intelligence Agency said X").

This claim-level chain is distinct from the record's `provenance` block ([0043](../decisions/0043-canonical-provenance-block.md)): provenance says where the **document** came from (publisher, dates, URL); the provenance chain says who, **inside** the document, asserted the claim and through whom it reached the speaker. A claim has both.

## Pipeline outputs

Each pipeline stage has a named output:

| Stage | Output | Shareable | Description |
|-------|--------|-----------|-------------|
| Ingester | **Ingest** | No (copyright) | The record converted to structured text with metadata, plus any extracted media (images today; figures from PDFs and video keyframes later). Contains the actual content. |
| Digester | **Digest** | Yes | Claims, nodes, and provenance extracted from one ingest. No copyrighted content. Planned: N model-variants reconciled into one derived canonical digest per ingest; only the canonical is assimilated ([decision 0039](../decisions/0039-multi-model-digestion-canonical-reconciliation.md)). |
| Assimilator | **Knowledge graph** | Yes (derived) | The unified SQLite graph built from all digests: cross-record entity resolution, provenance, scoring, embeddings. Derived data, rebuildable from the digests. |
| Assembler | **Article** | Yes | Readable prose assembled from knowledge graph data in a specific language. Public-eligible images from ingests are copied into the assembler's output for serving on the site. |

## Storage

The source of truth for the knowledge graph is the collection of digests in the digests repository. These are human-readable, version-controlled, and reviewable.

The SQLite database (a lightweight file-based database) is built and maintained by the assimilator, which imports the digests into the graph (see [assimilator.md](assimilator.md)). It serves as the query and distribution format - downloadable, torrentable, and verifiable - but is derived data, not primary. If deleted, it can be rebuilt from the digests. Embedding vectors are stored separately from core data to keep the primary download small.

The assimilator MAINTAINS the graph, it does not merely import it. Import is mechanical (claims by record). Maintenance is a curation pass whose primary signal is PROVENANCE OVERLAP: each claim carries `record_id` + `location_in_record`, so the same source with an overlapping location is a DUPLICATE (collapsed by supersede - the worse claim retired, the better kept), while different sources asserting the same fact are CORROBORATION (both kept, linked, counting as independent support). This operationalises the load-bearing invariant - count independence by provenance root, never by claim-count - and is the [0038](../decisions/0038-graph-curation-replayable-ledger.md) curation layer extended from nodes to claims (cases provenance cannot settle go through the cheap-model judge + confirm machinery; see [decision 0039](../decisions/0039-multi-model-digestion-canonical-reconciliation.md)).
