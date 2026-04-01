# Claims as the atomic unit of knowledge

Date: 2026-03-20
Status: draft

## Context

Traditional knowledge bases and wikis store information as narrative articles. The editorial judgement about what to include, how to frame it, and what to emphasise is embedded in the prose. This makes it difficult to trace individual assertions back to their sources, cross-reference across topics, or algorithmically assess evidence quality.

## Decision

Use claims as the fundamental unit of knowledge, not articles. A claim is a single discrete assertion with attribution: who said it, when, where, what source, and what corroborating or contradicting claims exist.

Articles are generated from the knowledge graph by assembling related claims, not written as prose by editors. Every assertion in a generated article traces back to a specific claim in the graph.

Node types in the knowledge graph are divided into ingestion types (person, organisation, place, event, matter, object, record, claim) populated by the extraction pipeline, and post-analysis types (concept, pattern, classification) added later through user contributions or analytical processes. All nodes use UUIDs as primary keys. Domain nodes do not link directly to each other - every relationship passes through a claim. See [node types](../../architecture/node-types.md) for full definitions.

## Consequences

The platform's credibility rests on source traceability. Any reader can click through from an assertion in an article to the underlying claim, its source, and its evidence score. The knowledge graph is independently verifiable.

This approach requires a generation pipeline capable of creating and maintaining articles based on graph data which may change at any time, rather than a traditional editorial workflow.
