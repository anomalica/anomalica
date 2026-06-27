# 0031. Per-record extraction inspection pages (record article + facts breakdown)

Date: 2026-06-15
Status: accepted
Relates to: builds on 0027 (digest interchange format), 0010 (auditable assembly),
0021 (content review lifecycle) and 0014 (static site); uses the vocabulary fixed by
the data model (terminology) and node-types.md.

## Context

For every ingested record the digester produces a digest (0027) at
`digests/records/{name}.yaml` holding every node and every claim the
artificial-intelligence pipeline extracted from that record. Until now the only
site-facing output built from those digests was the per-entity encyclopaedia articles
(`/people/`, `/events/`, ...), each assembled across many records. There was no way, on
the site itself, to see what a single record yielded: which claims were extracted, which
entities, and - by their absence - what was dropped.

Reviewers need exactly that view. The question "go to an episode, read the story we
built from it, and see exactly what was stripped out" is a quality-assurance question
about one record. The workbench already shows the source, ingest and digest side by side
(0027), but that is the reviewer's own tool. This decision puts the extraction result on
the published static site as an inspection surface, with each claim linking back to its
review in the workbench.

### Terminology

The unit here is a **record**, not a source. In node-types.md a record is the artefact
that claims are extracted from - a podcast episode, a Freedom of Information Act
document, a congressional transcript, a video. In the data model a **source** is the producer
*role* - the person or organisation behind the record (GEIPAN, The Black Vault, Ross
Coulthart, the US Navy), not a node type and not the artefact. These pages are therefore
per-record. The `/sources/` path stays reserved for a possible future section of
producer pages (the track-record, correction-behaviour and independence properties that
the data model defines as source properties).

## Decision

### A per-record inspection page, distinct from entity pages

For every ingested record the site gains an inspection page under `/records/`. It has
two parts:

1. A record-level **article** - assembler-generated neutral prose (editorial style guide; 0008)
   narrating the record's content, built from that record's claims, with references.
2. A **facts breakdown**, collapsed by default - the record's extracted entities grouped
   by node type, and every claim rendered as a self-contained card. Each card carries a
   deep-link to that claim's review in the workbench.

This is a quality-assurance surface, not an encyclopaedia entity page. Record is a node
type and may later get a curated public entity page; if it does, that curated page is the
published surface and this remains the raw extraction-inspection one. The two do not
compete: the inspection page shows what was extracted from one record (quality
assurance); an entity page would be published encyclopaedia content. The ADR fixes that
they stay separate rather than merging into one per-record page.

### Marked noindex

Inspection pages are marked `noindex` and are not part of the public encyclopaedia. They
exist to make extraction human-inspectable, not to be read as content, so they are kept
out of search engines and out of the reader-facing taxonomy. They publish regardless of
review status, consistent with 0021: review is informational, never a gate.

### Naming

The surface is the **extraction inspection page** (or record inspection page),
deliberately distinct from two existing things called "review": the workbench's frozen
`single_file` "canonical review surface" (record-format.md), and 0021's human review of
*published articles*. Naming it this way keeps three distinct concepts from collapsing
into one word.

### Assembler: a record-level article mode

The assembler gains a record-level mode alongside the existing per-entity mode. It reuses
the same assembly prompt, validation and rendering, but the subject being assembled is
the record: the name is the record title, the claims block is *all* of the record's
claims (not one node's), and the related entities are the record's nodes. The input is
the per-record digest (0027). The auditable-assembly guarantees of 0010 (article hash,
prompt hash, prompt inspector) apply unchanged - a record article is auditable exactly
as an entity article is.

### Per-claim workbench deep-link

Each claim card links to the workbench at:

```
{workbench_base}/{public_hash}#claim-{claim_uuid}
```

where `public_hash` is the record's 56-character public hash (review-workbench.md: the
first 56 hex characters of the record's `content_hash`, the identifier used on
public-facing workbench surfaces, not sufficient on its own to fetch the ingest) and
`claim_uuid` is the claim's id from the digest. `workbench_base` comes from site config.
The fragment anchors the specific claim within that record's workbench view.

### Output and ownership

Per record the pipeline emits two things: (a) the record article (prose plus
references), and (b) a facts-and-entities frontmatter block that drives the facts
breakdown. These live in the content repository under a new mount/section; the site
repository owns rendering (`layouts/<section>/single.html`). The full pipeline step is:
per-record digest -> record article + inspection page, generated for every ingested
record alongside the per-entity articles.

## Consequences

- Every ingested record becomes human-inspectable on the site itself: read the assembled
  narrative and see the complete extracted facts and entities, with one click per claim
  to its workbench review.
- The pipeline gains a formal per-record output (digest -> record article + inspection
  page) parallel to its per-entity output. The assembler is reused through a new mode,
  not forked.
- `/records/` is occupied by inspection pages; `/sources/` stays free for future
  producer (source-role) pages.
- `noindex` keeps these pages out of search and out of the encyclopaedia; they carry no
  editorial weight and are not reader content.
- The content repository gains a new mount/section and the site gains
  `layouts/<section>/single.html` to render the two-part page.
- If Record later becomes a public entity node type, its curated page is a separate
  surface; this record fixes that the inspection page and any future entity page do not
  merge.

## Open / pending

- The `/records/` section name is confirmed.
- The assembler record-level mode is being firmed up with the assembler master;
  shape refinements feed back into this record.
- The exact content-repository mount path and section name are to be settled with the
  site workspace.
