# 0041. Article proposals as an assimilator artefact; content and source briefs

Date: 2026-06-28
Status: accepted

Supersedes the page-selection half of [0036](0036-synthesise-stage-brief-as-writer-input.md) (the synthesiser's page-existence threshold). It does not edit 0036; 0036's brief mechanism and writer-only assembler stand.

## Context

[0036](0036-synthesise-stage-brief-as-writer-input.md) gave the synthesiser two coupled jobs: decide WHICH pages exist (a page-existence threshold) and emit the brief for each. The selection half, run as a pure claim-count floor, produced ~350 junk page proposals - an object cited once, a place mentioned in passing, a person quoted once. A raw count cannot tell "subject of the corpus" from "mentioned in it"; node type and source independence can (see [node-types.md, Page-worthiness](../architecture/node-types.md#page-worthiness-which-node-types-earn-a-page)).

Three changes follow: separate proposing a page from building it, give the per-record inspection surface ([0031](0031-per-record-inspection-pages.md)) the same brief→writer shape as entity pages, and broaden the scheduler to span every resource job.

## Decision

### Proposals - a first-class assimilator artefact

The assimilator, which already maintains the graph and holds the corroboration / independent-source counts, now also produces **proposals**: the set of nodes that earn a page, gated by the per-type editorial floor plus source independence pinned in [node-types.md](../architecture/node-types.md#page-worthiness-which-node-types-earn-a-page) (page-worthy vs high-bar types; a floor of distinct independent sources, not raw claim count). Proposals are a derived, rebuildable artefact beside the graph - rebuilt from it like the graph is rebuilt from digests.

This moves page-SELECTION out of the synthesiser (0036). Proposing is a graph-maintenance judgement - it needs the independence counts the assimilator owns - not a writing one, so it belongs with the graph, not the writer.

### Two brief types

- **Content brief** (`anomalica/brief/1`, unchanged): the graph slice for one ENTITY page. The synthesiser now narrows graph + proposals into one content brief per proposed page. It no longer decides existence - it builds the brief for each proposal.
- **Source brief** (new): the per-record view, built from the **fused digest** ([0039](0039-multi-model-digestion-canonical-reconciliation.md)) - one source's nodes and claims - feeding the per-record inspection page ([0031](0031-per-record-inspection-pages.md)). Parallel to the content brief: a brief that drives a writer, not a graph read.

### Assembler consumes both

Content briefs → entity articles; source briefs → per-record inspection pages. The assembler stays writer-only ([0008](0008-content-traceable-to-sources.md)/0036): it reads briefs, never the graph. Both page kinds are now brief→writer, so 0008 is enforced by construction on both surfaces.

### Scheduler over all resource jobs

The scheduler surfaces ALL resource jobs - ingest, digest, fuse, assimilate, graph maintenance (entity/claim curation), synthesise, assemble, embed - and paces them by capacity and value-per-effort. Surfacing graph maintenance (not just the AI-call stages) is the new part. The per-job **pre-run** cost/token-estimate detail (item count x model x price, used to pace and gate a run) is operational and lives in the private `operations` repository, not here (keep-spend-internal, per the inherited root rules); this record covers only the neutral scheduling shape. This is distinct from the per-record **notional cost at list price** (tokens x list price) - an after-the-fact per-artefact metric. As of 2026-06-29 it is NOT surfaced on the public site (Mark's reversal - he finds per-artefact usage/cost over-transparent); the data is kept in frontmatter and the AI-operation ledger for possible later surfacing (likely the internal workbench, TBD), not displayed publicly. It remains distinct from the pre-run estimate above, which is internal/operations regardless - do not conflate the two.

## Why

- **The discriminator a count lacks.** Type + independence is the editorial floor that kills the 350-junk problem; a count, of any type, cannot.
- **Proposing belongs with the graph.** The assimilator holds the corroboration and independent-source counts the floor reads; the synthesiser would have to re-derive them.
- **One page-building model.** Both entity pages and inspection pages become brief→writer, so 0008 is structural on both, and 0036's per-page staleness/audit hash applies to both brief types.
- **Source briefs make 0031 brief-driven.** The inspection surface gains the same staleness and traceability primitives as entity pages, from the fused digest.

## Consequences

- The synthesiser narrows: graph + proposals → content briefs. It no longer applies the page-existence threshold.
- The proposals gate is [node-types.md, Page-worthiness](../architecture/node-types.md#page-worthiness-which-node-types-earn-a-page); the tiers and floor numbers are the editorial calibration (the corpus-tuned defaults there).
- 0031 inspection pages are produced from source briefs (from fused digests), not from the digest directly.
- A second brief type joins the brief format; `architecture/brief-format.md` gains the source-brief shape alongside the content brief.
- The architecture diagram gains a **proposals** artefact beside the graph, the two brief types feeding the assembler, and the scheduler spanning all resource jobs (`reference/pipeline.mmd` + `reference/architecture.yaml`).
- **The final proposals threshold is still gated on evidence scoring**, exactly as 0036's threshold was: the structure (proposals as an artefact, the two-brief split) builds now; the data-driven floor calibrates when [algorithmic-evidence-scoring](drafts/algorithmic-evidence-scoring.md) pins. For 0035 Phase 1, pages stay hand-chosen.
- Scheduler cost/token detail stays in `operations` - this record does not document it.

## Scope

A reshape of the assimilate → synthesise → assemble stages: proposals become a first-class assimilator artefact, page-selection moves there from the synthesiser, a second (source) brief type joins, and the scheduler broadens to all resource jobs. Supersedes the page-selection half of 0036; retains its brief mechanism and writer-only assembler. Builds on 0039 (fused digests → source briefs), node-types.md (the page-worthiness floor), 0031 (inspection pages), and 0010/0008 (briefs, traceability). Numbers and tiers are the editorial calibration, not fixed here.
