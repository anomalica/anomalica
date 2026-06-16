# 0011. Claims as the atomic unit of knowledge

Date: 2026-03-20
Status: accepted

## Context

Traditional knowledge bases and wikis store information as narrative articles. A knowledge graph is a structured database of interconnected facts. The editorial judgement about what to include, how to frame it, and what to emphasise is embedded in the prose. This makes it difficult to trace individual assertions back to their sources, cross-reference across topics, or algorithmically assess evidence quality.

## Decision

Use claims as the fundamental unit of knowledge, not articles. A claim is a single discrete assertion with attribution: who said it, when, where, what source, and what corroborating or contradicting claims exist.

Articles are generated from the knowledge graph by assembling related claims, not written as prose by editors. Every assertion in a generated article traces back to a specific claim in the graph.

All nodes use universally unique identifiers as primary keys, and domain nodes do not link directly to each other - every relationship passes through a claim. The node types and their current taxonomy are defined in [node types](../../architecture/node-types.md).

## Consequences

The platform's credibility rests on source traceability. Any reader can click through from an assertion in an article to the underlying claim, its source, and its evidence score. The knowledge graph is independently verifiable.

This approach requires a generation pipeline capable of creating and maintaining articles based on graph data which may change at any time, rather than a traditional editorial workflow.
