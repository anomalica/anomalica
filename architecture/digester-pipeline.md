# Digester Pipeline

This document describes how the digester processes records and integrates them into the knowledge graph. See [digester.md](digester.md) for what the digester does; this document covers how it does it.

## Pipeline stages

### 1. Extraction

Each record is sent to an AI model (Claude) which reads the text and extracts:

- **Domain nodes** - people, organisations, places, events, matters, objects mentioned in the record
- **Claims** - atomic assertions, each with a speaker, claim type, attestation level, and references to the nodes it mentions

Extraction is independent per document. It does not require access to the knowledge graph and can be parallelised across any number of records using the Anthropic batch API.

The output is a self-contained extraction result per record. At this point, node names are whatever the AI chose from the source text ("Commander Fravor", "Fravor", "David Fravor" could all appear).

### 2. Integration

Each extraction result is integrated into the knowledge graph one at a time, sequentially. The order matters because each integration changes the graph, and subsequent integrations need to see those changes.

For each extracted node, the digester attempts to match it against existing nodes in the graph:

1. **Exact name match** - check whether a node with this name and type already exists, including aliases
2. **Fuzzy name match** - use Levenshtein distance to find close variants ("K. Day" vs "Kevin Day", "Sgt Fravor" vs "David Fravor"). This catches typos, abbreviations, and minor formatting differences
3. **Claim-based matching** - if neither name match finds a candidate, embed the claims associated with the extracted node and search for similar claims already in the graph. If a cluster of similar claims are attached to an existing node of the same type, that node is likely the same thing. This handles the case where two documents describe the same event with completely different names.

If a match is found, the extracted name is stored as an alias of the canonical node. If no match is found, a new node is created.

Claims are then stored and linked to the resolved nodes.

### 3. Reconciliation

A separate maintenance pass that can run at any time, independently of ingestion. It walks the graph looking for nodes that should be merged:

- Nodes of the same type whose claims overlap significantly
- Nodes whose names are similar but were not caught during integration (perhaps because they were ingested in different batches or the graph context was different at the time)

Proposed merges can be reviewed before being applied. When a merge is confirmed, one node becomes the canonical and the other becomes an alias. All claims pointing to the alias are relinked to the canonical. No data is lost - the alias name is preserved and continues to work for future lookups.

## Aliases

An alias is a name that points to a canonical node. "Commander Fravor", "CDR Fravor", "Fravor", and "David Fravor" can all be aliases pointing to the same Person node whose canonical name is "David Fravor".

Aliases accumulate over time as more records are processed. They serve two purposes:

- **Lookup** - when a new document mentions "Fravor", the alias table resolves it to the canonical node instantly
- **Provenance** - the alias preserves the exact name used in the source record, even though the graph stores everything under the canonical name

## Graph merging

Two independently produced knowledge graphs can be merged by combining their contents and running a reconciliation pass.

The merge itself is naive - all nodes, claims, and records from both graphs are combined into one. Since every node uses a UUID, there are no primary key collisions. The result will contain duplicates: "David Fravor" from graph A and "Commander Fravor" from graph B as separate nodes, each with their own claims.

The reconciliation pass then resolves these duplicates using the same matching logic as integration (exact name, fuzzy name, claim-based embedding similarity). Merged nodes become aliases of a chosen canonical.

This enables distributed operation. Multiple people or machines can run the digester independently on different source material, producing separate graphs. Those graphs can be merged and reconciled at any time without coordinating during ingestion.

## Batch processing

For large ingestion runs (tens or hundreds of records), the pipeline works as follows:

1. Parse all records
2. Send all extractions to the AI batch API in parallel
3. When results return, integrate them sequentially against the graph
4. Run a reconciliation pass to catch any cross-document duplicates the sequential integration missed

The expensive step (AI extraction) is parallelised. The cheap step (database integration) is sequential. The reconciliation pass is a safety net, not a primary mechanism.

## Node matching tools

Each matching approach has different strengths:

| Tool | Good for | Bad for |
|------|----------|---------|
| Exact match and aliases | Known names, previously seen variants | New name variants never seen before |
| Levenshtein distance | Typos, abbreviations, minor formatting | Completely different names for the same thing |
| Claim embedding similarity | Same meaning expressed in different words | Short strings with little semantic content (names) |

Embedding similarity works well for comparing claims (full sentences) but poorly for comparing node names. Short names like "Kevin Day" and "David Fravor" are semantically similar to an embedding model (both are person names in a military context) even though they are completely different people. Claims provide enough textual content for the model to distinguish meaning.

## Domain and infrastructure extraction

The digester produces two separate databases from the same source records.

### Domain database

Claims about anomalous phenomena: what happened, who witnessed it, what was investigated, what was covered up, who was involved and what qualifies them. This is the public-facing knowledge graph that feeds the assembler and becomes the website content.

The test for whether a claim belongs in the domain database: would it appear on the website? If someone visits a page about a person, event, or organisation, is this information that helps them understand the phenomena? If yes, it's domain.

Career histories, credibility-establishing facts, and programme details are domain even though they aren't directly about anomalous events. "Brown held a top secret Sensitive Compartmented Information clearance from the Defence Intelligence Agency" goes on Brown's page because it establishes why his testimony matters.

### Infrastructure database

Claims about the information ecosystem: who interviewed whom, which podcasts discuss which topics, who recommends or dismisses what sources, sentiment about other media, casual mentions of other records or sources. This is operational intelligence used for deciding what to ingest next, understanding biases, and mapping the network of information flow.

The test: would it appear on the website? If not, it's infrastructure. "Jeremy Corbell and George Knapp conducted the interview" is infrastructure. "This podcast references the Telepathy Tapes positively" is infrastructure.

### Two separate extraction passes

Domain and infrastructure extraction run as separate passes over the same source record, with different prompts optimised for different tasks.

Reasons for separate passes rather than a single combined pass:

- **No forced binary.** Something genuinely borderline can appear in both databases independently, which is useful signal rather than a forced classification.
- **Different prompts.** Domain extraction looks for testimony, evidence, events, programmes. Infrastructure extraction looks for inter-source references, career context, sentiment, network connections. These are different tasks.
- **Infrastructure is optional.** A FOIA document probably contains zero infrastructure content. A podcast transcript contains lots. The infrastructure pass can be skipped for document types where it would produce nothing.

Both databases use the same schema and share node identifiers so they can be joined when needed.
