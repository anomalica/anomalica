# 0036. Synthesise stage: the brief as the writer's sole input

Date: 2026-06-20
Status: accepted

## Context

The assembler currently does two jobs in one stage: it reads the knowledge graph directly (selecting an entity's claims, clustering related nodes, ordering them) and writes the prose. That couples deterministic selection with generative writing, and it leaves 0008 (content traceable to sources - the writer invents nothing) enforced only by prompt instruction: a writer that can see the whole graph can, in principle, pull in anything. It also gives no clean per-page staleness unit and no clean place to make the multilingual split (select once, write many).

A new stage separates selection from writing.

## Decision

A new pipeline stage, **synthesise**, sits between assimilate (the graph) and assemble (the writer):

```
ingest -> digest -> assimilate -> synthesise -> assemble
```

### The synthesiser

Reads the knowledge graph and:

- clusters it;
- applies an "enough corroborated information across enough independent sources to deserve a page" threshold to decide the **set of pages that should exist**;
- emits one **brief** per page.

Selection is deterministic and produces no prose. The synthesiser, not the writer, decides what pages exist and which facts each page is built from.

### The brief

A brief is a language-neutral YAML document (schema `anomalica/brief/1`, the same serialisation as the digest) holding exactly the graph slice that feeds ONE page - the nodes, the selected claims with their provenance, and the relationships - before any prose. The field-level format is specified in [architecture/brief-format.md](../architecture/brief-format.md).

### The brief is the writer's sole input

The assembler (writer) is given the brief and nothing else - it does not read the graph. It renders the brief's facts into per-language prose, applying directives. It selects nothing, clusters nothing, reads no graph.

### One object, three roles

The brief's input hash IS the audit hash 0010 already mandates for the "knowledge-graph data" prompt component - not a parallel scheme. The single brief object serves as the writer's input, the per-page staleness/diff unit (reassemble a page only when its brief's inputs changed), and the audit record (0010's prompt-component hash). It is also the staleness primitive for the scheduling model's "Something changed?" step - so the brief is the shared staleness primitive across synthesise and scheduling, not solely an assembly input.

## Why

- **0008 enforceable by construction.** The writer cannot see the graph, only the brief, so it provably invents nothing - 0008 becomes a structural guarantee, not a prompt instruction.
- **Per-page staleness.** Hash the brief's inputs; reassemble only the pages whose slice changed.
- **Clean multilingual split.** Select facts once (the language-neutral brief); write N languages from the one brief (per translation-directives).
- **Deterministic selection, AI confined to prose.** What exists and what facts feed it is deterministic; the model only writes.

## Dependency: the threshold is gated on evidence scoring

The page-existence threshold ("enough corroborated information across enough independent sources") is wired to the evidence score, which is still a draft ([algorithmic-evidence-scoring](drafts/algorithmic-evidence-scoring.md)) and not pinned. The stage's STRUCTURE (synthesise -> brief -> writer) can be built now; the FINAL selection behaviour - the threshold - cannot be finalised until evidence scoring is pinned. For the first public proof (0035 Phase 1) pages are hand-chosen (a Person or Event), so the brief mechanism is exercised without a data-driven threshold; the data-driven threshold is a Phase 2 concern alongside scoring. The brief reserves a page-level evidence block (`page.evidence{score, tier, independent_sources}`) as the surface where the page score lands and where the public score surfaces - neutral/"in development" until scoring pins, per 0035. It is documented in [architecture/brief-format.md](../architecture/brief-format.md) and built when scoring is pinned.

## Consequences

- **The assembler shrinks to a pure writer**: brief -> per-language prose + directives. It no longer selects, clusters, or reads the graph directly. Its current direct-graph-read input contract (documented in assembler.md) is the interim behaviour, superseded by brief-input once the synthesiser lands.
- **The site's architecture diagram (`pipeline.mmd` + `architecture.yaml`) gains the synthesise node** - that is the single source for the pipeline shape (handled by the site workspace).
- **A new versioned interchange** (the brief, `anomalica/brief/1`) joins the record format (0019) and digest format (0027) - here between synthesise (producer) and assemble (consumer).
- **0010 is unchanged in policy.** The brief realises 0010's "knowledge-graph data" prompt component; its hash is 0010's audit hash. No new staleness scheme.
- **0031 (per-record inspection pages) is distinct.** Those are per-record QA surfaces (every record, no threshold); the synthesise stage decides ENTITY pages via briefs. The two do not conflict.

## Scope

A new stage plus a new interchange. It reinforces 0008 and 0010 (a mechanism, not new policy), follows the 0034 split precedent (one job per stage), and aligns with 0035 (the threshold is the Phase-2 differentiator) and translation-directives (write N languages from one brief). The final threshold is gated on the algorithmic-evidence-scoring draft. The brief field-format is in [architecture/brief-format.md](../architecture/brief-format.md) (`anomalica/brief/1`), scaffolded now and filled from the synthesiser's first real brief.
