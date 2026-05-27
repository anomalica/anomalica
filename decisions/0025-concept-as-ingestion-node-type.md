# 0025. Concept as a first-class ingestion node type

Date: 2026-05-19
Status: accepted

Supersedes, if accepted: the classification in `architecture/node-types.md`
that places **Concept** under "Post-analysis types" (added later through
curation or a separate analytical process, not by the extraction pipeline).

## Context

`architecture/node-types.md` defines seven node types the extraction
pipeline produces at ingestion (person, organisation, place, event, matter,
object, record) plus claim as the connective tissue. It lists **Concept** -
a recurring idea, theme, or theoretical framework (reverse engineering, the
nuclear-and-unidentified-anomalous-phenomena correlation, the simulation
hypothesis) - as a *potential future* type, deliberately deferred to a
post-analysis layer on the grounds that concepts "require subjective
judgement to assign and are better suited to human curation, community
tagging, or a separate analytical pipeline than to initial artificial
intelligence extraction."

Two ways of producing concepts later were considered:

1. **Derive them by clustering claims.** Group claims by theme after the
   fact; a concept is whatever a cluster of claims has in common.
2. **Curate them by hand or a separate analytical pass over the graph.**

Both share a hidden assumption: that a concept's existence is contingent on
claims being *about* it. That assumption is false, and it is the reason to
revisit the deferral.

Worked example: **general relativity**. In the unidentified anomalous
phenomena corpus, general relativity is referenced constantly - "Einstein's
relativity predicts gravitational waves", "Pais claims a craft that bypasses
relativity" - but no source in the corpus asserts the claim "general
relativity is true". It is background that other claims point at. A
derive-by-clustering approach would surface nothing for it, because there is
no cluster of claims *about* general relativity. Yet it is plainly an
important node that many claims reference. The same holds for "reverse
engineering", "anti-gravity propulsion", and the simulation hypothesis.

This shows a concept behaves exactly like every other domain node. Area 51
is not derived from the claims that mention it; it is a first-class node
that claims reference. Person, organisation, place, event, matter, object,
record - all first-class, all referenced by claims, none constituted by
them. Concept is no different. Treating it as a derived or purely
post-analysis artefact makes it second-class for no principled reason.

There is also a cost consequence. A first-class node type that is **not**
extracted at ingestion cannot be added cheaply later: the claims in the
existing digests do not carry references to a node type that did not exist
when they were extracted, so introducing it requires re-running the
expensive extraction over every source. Deferring concept therefore does
not save work - it guarantees a full re-ingestion the day it is wanted.

The original concern behind the deferral - that concepts are fuzzier and
noisier to identify than "Area 51", risking over-extraction of every
abstract noun (gravity, secrecy, disclosure) - is real. But it is the same
class of problem already solved for objects with the "subject, not
illustration" boundary rule (extract a thing only if the document makes
assertions about it; not if it appears only as rhetorical comparison). It
is a boundary-rule problem to be managed in the extraction prompt, not a
reason to make concepts second-class.

## Decision

**Concept becomes the eighth ingestion node type, extracted by the pipeline
at the same time as the others, referenced by claims via node references,
with claims remaining the sole connective tissue.**

A **concept** is a named idea, theory, framework, phenomenon, or recurring
theme that the document treats as a thing in its own right - general
relativity, anti-gravity propulsion, reverse engineering of recovered craft,
the simulation hypothesis, the Pais Effect.

Boundary rule (to control the over-extraction risk the deferral worried
about):

- Extract a concept only if the document **refers to it as a named idea or
  theory**, not if an abstract word merely occurs. "He was sceptical" does
  not yield a "scepticism" concept. "Pais's work depends on the Pais Effect,
  a phenomenon he claims is real" does yield the "Pais Effect" concept.
- A concept must be **nameable and durable** - someone reading only the node
  name should know which idea it is, and it should be the same idea wherever
  it recurs across the corpus. This is the concept analogue of the place
  rule (specific and durable) and the object rule (subject, not
  illustration).
- Background concepts that are referenced but never asserted (general
  relativity) are still extracted - being referenced by a claim is
  sufficient; being the subject of an asserted claim is not required.

Concepts carry no truth status. "The simulation hypothesis" is a concept
node; whether anyone believes it is expressed through claims that reference
it, with their own attestation and provenance, exactly as for every other
node type.

## Consequences

- The extraction schema, prompt, and the benchmark golden sets gain an
  eighth type. The benchmark's "subject, not illustration" precision
  discipline extends to concepts.
- No re-ingestion is forced in the future for the *existence* of concepts,
  because they are captured from the first pass onward. (Records ingested
  before this decision would still need re-extraction to gain concept nodes
  - this is the unavoidable one-time cost of having deferred, and is the
  argument for accepting this decision before large-scale ingestion rather
  than after.)
- `architecture/node-types.md` is updated to move Concept from
  "Post-analysis types" into the ingestion types, with the boundary rule
  above. The post-analysis layer may still *refine* concepts (merging,
  hierarchy, community tagging); it is no longer the *source* of them.
- The post-analysis types that remain genuinely deferred (Pattern,
  Classification) are unaffected; this decision is specific to Concept and
  the reasoning that it is referenced rather than derived.

## Open questions for review

- Concept versus matter at the edges: "anti-gravity research" (an ongoing
  effort - matter) versus "anti-gravity propulsion" (the idea - concept).
  Both can legitimately exist as separate nodes about one subject, the same
  way the Rosetta Stone is both object and record. The prompt must give a
  crisp test; drafting that test is follow-on work.
- Whether the Pais Effect, under this decision, is a concept (the claimed
  phenomenon as an idea) - the working answer is yes, and it replaces the
  earlier "matter" placeholder and the "none" fallback.
