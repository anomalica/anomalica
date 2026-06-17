# 0035. First public artefact: a proof of method, distinct from the scored-encyclopaedia launch

Date: 2026-06-17
Status: accepted

## Context

A launch-readiness audit found that nothing in the architecture or decisions defined what the first public thing is - no "first public", milestone, or MVP target exists. The project's no-MVP stance (foundation-right-before-publishing) is why, but it left no concrete target to build toward, and it conflated two genuinely different milestones: proving the method works end to end, versus launching a credible scored encyclopaedia.

The second milestone needs the evidence-scoring methodology - the differentiator - which is still undefined (the algorithmic-evidence-scoring draft is a factor list with no algorithm or graph schema). The first milestone does not. Separating them gives a near-term, achievable public target without waiting on the hardest open design.

## Decision

Two distinct public phases.

### Phase 1 - Proof of method (the first public artefact)

The first public artefact is ONE entity article, assembled from the knowledge graph and published to the site, with:

- **A fully inspectable evidence trail.** Every assertion traces to its claim, each claim to its source record, with the per-record inspection page (0031) walkable - a reader can follow the whole chain from prose to source.
- **The evidence score disclosed as provisional.** Where a score would appear, it is shown as "scoring methodology in development", never a fabricated or placeholder number. The platform does not publish a credibility figure it cannot stand behind.
- **An entity chosen so the taxonomy migration is off the critical path** - a Person or Event (for example David Fravor, or the 2004 Nimitz encounter), whose public sections exist in both the old and current taxonomies.

This proves the pipeline walks end to end - raw source, ingest, digest, graph, assembled article, published, references resolving, evidence trail inspectable - the method, not the verdict.

### Phase 2 - Scored encyclopaedia (the later launch)

The credible, scored encyclopaedia launch. It requires the evidence-scoring methodology defined and implemented, so claims carry real, data-derived, published scores and tiers. Phase 2 is explicitly gated on the differentiator that Phase 1 deliberately ships without.

## Consequences

- Phase 1 is a concrete, near-term target that demonstrates the method without waiting on scoring (the hardest open design).
- The honesty line is structural: a provisional "in development" score is shown, never a fabricated number.
- Phase 1's critical path (per the launch audit): re-digest the chosen source onto the current taxonomy; confirm the site renders a Person or Event article; ensure the inspection page (0031) and the references resolve. None of it needs scoring.
- Phase 2 keeps the bar high: the distinguishing claim (data-derived credibility) is made only when it is real.
- The actual publish and deploy of Phase 1 remain Mark's gate; this record defines the target, not the go-live.

## Scope

Defines the first-public milestone (a gap the launch audit found). Relates to 0031 (per-record inspection pages), 0010 (auditable assembly / inspectable trail), the algorithmic-evidence-scoring draft (the Phase 2 gate), and the node-types taxonomy (the Person/Event choice keeps the migration off the critical path).
