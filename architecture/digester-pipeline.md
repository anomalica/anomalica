# Digester Pipeline

This document describes how the digester processes records and integrates them into the knowledge graph (a structured database of interconnected facts). See [digester.md](digester.md) for what the digester does; this document covers how it does it.

## Pipeline stages

### 1. Digestion (artificial intelligence)

Each ingest is sent to an artificial intelligence model (Claude) which reads the text and extracts nodes and claims. Two separate extraction passes run on each document:

- **Domain extraction** - claims about the phenomena: testimony, evidence, events, programmes, investigations
- **Infrastructure extraction** - claims about the information ecosystem: who produced the content, inter-source references, career backgrounds, network connections

Digestion is independent per document and can be parallelised across any number of ingests using the Anthropic batch application programming interface.

The output is one digest per ingest - a human-readable markdown file containing all extracted nodes, domain claims, and infrastructure claims with their metadata, original excerpts, and provenance information (the path each claim took from its original source to the knowledge graph).

### 2. Import (deterministic, no artificial intelligence)

Digests are imported into the database by a deterministic parser. No artificial intelligence is involved and no human review is required before import. The import process:

- Creates record and node entries from the markdown
- Matches nodes against existing entries using exact name, alias, and Levenshtein distance
- Stores claims with all their metadata and node references
- Preserves the universally unique identifiers from the markdown so that re-importing an edited file updates in place

The database can be rebuilt from scratch at any time by importing all digests from the digests repository.

### 3. Reconciliation

A separate maintenance pass that can run at any time, independently of ingestion. It walks the graph looking for nodes that should be merged:

- Nodes of the same type whose claims overlap significantly
- Nodes whose names are similar but were not caught during integration (perhaps because they were ingested in different batches or the graph context was different at the time)

Proposed merges can be reviewed before being applied. When a merge is confirmed, one node becomes the canonical and the other becomes an alias. All claims pointing to the alias are relinked to the canonical. No data is lost - the alias name is preserved and continues to work for future lookups.

## Human review and correction

Human review is not a pipeline stage. It can happen at any time - before import, after import, weeks later, or never. The system works without it. Review improves quality when it happens but does not gate the pipeline.

Digests live in the digests git repository. Every edit is tracked in the commit history, which serves as the audit trail for corrections. When a correction is made to a digest:

1. The corrected digest is committed to the repository
2. The database is rebuilt from the updated digests
3. Any articles affected by the change are reassembled

Digests are publicly readable on the git hosting platform. When a reader spots an error in an article, they can follow the reference links to the digest and report the problem via the repository's issue tracker. Corrections flow through the digests, not through direct database edits or article overrides.

## Aliases

An alias is a name that points to a canonical node. "Commander Fravor", "CDR Fravor", "Fravor", and "David Fravor" can all be aliases pointing to the same Person node whose canonical name is "Fravor, David" ([person naming](node-types.md#person)).

Aliases accumulate over time as more records are processed. They serve two purposes:

- **Lookup** - when a new document mentions "Fravor", the alias table resolves it to the canonical node instantly
- **Provenance** - the alias preserves the exact name used in the source record, even though the graph stores everything under the canonical name

## Graph merging

Two independently produced knowledge graphs can be merged by combining their contents and running a reconciliation pass.

The merge itself is naive - all nodes, claims, and records from both graphs are combined into one. Since every node uses a universally unique identifier, there are no primary key collisions. The result will contain duplicates: "Fravor, David" from graph A and "Commander Fravor" from graph B as separate nodes, each with their own claims.

The reconciliation pass then resolves these duplicates using the same matching logic as integration (exact name, fuzzy name, claim-based embedding similarity - where embeddings are vector representations that capture meaning, allowing comparison of semantically similar text). Merged nodes become aliases of a chosen canonical.

This enables distributed operation. Multiple people or machines can run the digester independently on different source material, producing separate graphs. Those graphs can be merged and reconciled at any time without coordinating during ingestion.

## Batch processing

For large ingestion runs (tens or hundreds of records), the pipeline works as follows:

1. Parse all ingests
2. Send all ingests to the artificial intelligence batch interface in parallel (produces digests)
3. Review the digests (human step)
4. Import digests sequentially into the database
5. Run a reconciliation pass to catch any cross-document duplicates

The expensive step (artificial intelligence digestion) is parallelised. The cheap step (database import) is sequential. The reconciliation pass is a safety net, not a primary mechanism.

## Node matching tools

Each matching approach has different strengths:

| Tool | Good for | Bad for |
|------|----------|---------|
| Exact match and aliases | Known names, previously seen variants | New name variants never seen before |
| Levenshtein distance | Typos, abbreviations, minor formatting | Completely different names for the same thing |
| Claim embedding similarity | Same meaning expressed in different words | Short strings with little semantic content (names) |

Embedding similarity works well for comparing claims (full sentences) but poorly for comparing node names. Short names like "Day, Kevin" and "Fravor, David" are semantically similar to an embedding model (both are person names in a military context) even though they are completely different people. Claims provide enough textual content for the model to distinguish meaning.

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
- **Infrastructure is optional.** A Freedom of Information Act document probably contains zero infrastructure content. A podcast transcript contains lots. The infrastructure pass can be skipped for document types where it would produce nothing.

Both databases use the same schema and share node identifiers so they can be joined when needed.
