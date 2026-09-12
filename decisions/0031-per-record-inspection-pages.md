# 0031. Per-record extraction inspection pages (record article + facts breakdown)

Date: 2026-06-15
Status: accepted
Relates to: builds on 0027 (digest interchange format), 0010 (auditable assembly),
0021 (content review lifecycle) and 0014 (static site); uses the vocabulary fixed by
the data model (terminology) and node-types.md.

## Context

For every ingested record the digester produces a digest (0027) at
`digests/{name}.yaml` holding every node and every claim the
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
`single_file` "canonical review surface" (ingest-format.md), and 0021's human review of
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

## Amendment 2026-09-12: reviewed records become the public works section

This amendment supersedes the inspection-only, every-ingest, `noindex` and
separate-future-page decisions above. The extraction inspection surface remains
in the Workbench. The public site uses the existing record article as its one
reader-facing page for a reviewed source.

`/records/` replaces `/documents/` in public navigation. A document remains a
domain node for an information artefact discussed by the corpus; it no longer
earns a separate public listing or article merely by being a document node. A
record is the source artefact Anomalica actually holds and has reviewed. There
is no automatic document-node-to-record redirect because the two identities are
not one-to-one; a redirect is valid only where an explicit mapping names the
same work.

### Publication eligibility

A record page is emitted and indexed only when all of these are true at build
time:

- The record is live under `store/`, is not archived or superseded, and its
  current content hash is the one named by the selected digest.
- `store/{hash}.review.json` is a valid
  `anomalica/review-coverage/1` sidecar with finite
  `observed_coverage: 1.0`, `digestible: true` and `total_units > 0`.
- No `review_carryover` remains unresolved. A review at or after the carryover
  timestamp resolves it; otherwise the record requires verification again.
- The selected digest is current for that record: its `record.content_hash`
  names the live record and its `pre_digest.sha256` equals the hash produced by
  materialising the current record body with the shared pre-digest
  implementation. Missing legacy `pre_digest` fails closed. A differing
  `pre_digest.prep_version` alone is not stale when current materialisation
  produces the same hash. The digest's extraction-time `review_state` is
  provenance only and never decides publication.

Missing, malformed, version 0, partial and stale review state fails closed. A
build removes an existing public record page when it ceases to satisfy the gate.
No reviewer identity, review notes or spans cross into public content.

### Public record content

Every eligible page contains safe bibliographic metadata, a short description
and a neutral explanatory article assembled only from the record's claims. The
description and article are public derived writing, not the ingest's
`description`, raw body or source blurb. Citation-sized attributed quotations
remain public under the quotation policy. The facts-and-entities inspection
breakdown and reviewer deep-links stay in the Workbench rather than being
republished on the reader page.

The public metadata allow-list is the 56-character `record_hash`, title,
`source_type`, optional `document_type`, publisher, creators, publication date,
duration or page count, canonical public `source_url`, and effective copyright
display modes. It excludes the full content/source hash, verification data,
reviewer data, private or fetched paths, raw frontmatter, processing metadata,
word timestamps and the ingest's source-authored `description`.

The generated description, explanatory article, claim facts and supporting
quotations are public for every eligible record. Source reproduction is a
separate allow-list:

| Source object | Public when |
|---|---|
| Ingested source body | Effective `copyright.status` is `public_domain`, `open_licence` or `publicly_accessible`. |
| Self-hosted archived original | Effective `copyright.status` is `public_domain` or `open_licence`. |
| Self-hosted extracted media | Effective `copyright.media` is `public_domain` or `open_licence`; absent inherits the record status, unknown fails closed. |
| Publisher-hosted audio/video embed | Record status is `public_domain`, `open_licence` or `publicly_accessible`, and the canonical HTTPS source URL matches a supported provider. |
| Original-source link | A canonical public HTTP(S) `source_url` exists. Linking does not authorise copying its content. |

`licensed`, `restricted`, absent and unknown status never expose a source body,
self-hosted original, media or embed on the public site. Licence metadata alone
does not encode permission scope, so it cannot widen this allow-list. Such a
page shows only the derived explanation, safe metadata, supporting quotations
and an original-source link where one exists.

The allow-list is enforced before the content repository or static build receives
the source payload. Gated bytes, private object URLs and full possession hashes
must be absent from public Markdown, frontmatter, generated HTML, page resources,
search indexes and client data; hiding them in markup or JavaScript is a leak,
not access control.

The content boundary identifies this projection with `schema:
anomalica/public-record/1` and `content_kind: record`. Hugo reserves the
frontmatter field `kind`, so this schema must not use it. The projection expresses
`source_body`, `archived_original`, `media`, `provider_embed` and `external_link`
as independent `{mode, reason}` capabilities, not the legacy scalar
`source.display`. A denied capability carries no URL or payload; unknown or
inconsistent modes fail closed.
External-link permission is not coupled to permission to reproduce. The exact shape is in
[content-format.md](../architecture/content-format.md#public-record-pages).
