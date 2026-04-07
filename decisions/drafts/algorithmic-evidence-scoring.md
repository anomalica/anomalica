# Algorithmic evidence scoring

Date: 2026-03-20
Updated: 2026-03-21
Status: draft

## Context

Claims in the knowledge graph (a structured database of interconnected facts) need some form of quality assessment. Without it, a newcomer cannot distinguish between well-documented sensor data and an anonymous forum post. Existing platforms either present claims without assessment or rely on editorial judgement, which invites accusations of bias.

## Decision

Evidence scoring will be algorithmic, computed from properties of the knowledge graph rather than assigned by human editors. The methodology will be published, transparent, and open to community input. Anyone will be able to see why a claim received its score and propose changes to how scores are calculated.

Initial scoring factors (expected to evolve):

- **Source type weight** - different types of sources carry different weight. For example, sworn testimony carries more weight than a podcast interview, and a declassified government document carries more weight than an anonymous claim. The specific weights will be published and subject to revision.
- **Corroboration count** - the number of sources making the same or supporting claims.
- **Contradiction count** - the number of sources contradicting the claim.
- **Temporal consistency** - whether the claim has remained stable over time or has shifted.

These factors are a starting point. The scoring methodology is expected to evolve as the platform and community develop. Additional factors may be introduced as methods for measuring them are established. The methodology itself is the editorial product - individual scores are a consequence of applying it.

The output will be a numeric confidence score plus a human-readable tier label (such as verified, probable, disputed, legend, misidentified, hoax) derived from score ranges. The tier labels are presentation shortcuts, not editorial judgements.

## Consequences

No human will directly decide whether a claim is "verified" or "disputed." Verification and dispute happen through the normal pipeline: submitting corroborating or contradicting sources, which the knowledge graph engine processes and which then affect the score.

If someone disagrees with a score, they can examine the inputs that produced it. If the community believes the methodology itself needs adjustment, changes can be proposed and discussed publicly.
