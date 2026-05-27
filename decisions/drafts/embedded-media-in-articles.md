# Embedded media in articles (images and video)

Date: 2026-05-01
Status: draft

## Context

Final assembled articles will benefit from embedded media alongside the prose. Two motivating examples:

- A page about a person should include a photograph of that person where one is available.
- A page about an event (the Nimitz encounter) should be able to embed the relevant video (the Tic Tac footage) inline.

The ingester landed image extraction on 2026-04-30 (this repository at `335d67f`, ingester at `2cb5944`). Images are now stored at `anomalica-ingests/media/{record_hash}/{img_hash}.{ext}` alongside the records that reference them, and the record-format spec describes the body annotation form. That solves the input side of the pipeline for images sourced from books and other ingested artefacts.

What is not yet specified is how media propagates from ingested records, through the digester, through the assembler, into the content repository, and onto the site.

## Open questions

**Propagation through the digester.** The digester currently extracts atomic factual claims with provenance pointers back to the records they came from. It does not have a concept of media. When the digester sees a record with image annotations, what does it do? Options include: track each image as a first-class node in the knowledge graph linked to the entities it depicts (person photographed, place shown), or carry images as a flat list of provenance assets attached to records without graph promotion, or ignore them at digester level and have the assembler reach back into the ingests repository for images at assembly time.

**Attaching media to graph entities.** The Tic Tac video belongs on the Nimitz encounter page, but the video is not "of the Nimitz encounter" in a content-addressable sense - it is a specific artefact that depicts the encounter. How does the system know that a given video file should appear on a given event's article? Probably this is a claim itself: "video file X depicts event Y", extracted or asserted explicitly. The same shape works for "photograph X is a likeness of person Y".

**Assembler responsibilities.** The assembler does not exist yet. When it does, it needs a rule for which media to include in which article. Plausible shape: the assembler queries the graph for media nodes attached to the article's central entity, applies a per-article cap (one photograph, one or two videos), and inlines them at canonical positions in the layout.

**Sourcing video.** The ingester only extracts images from EPUBs in its first pass. Video has no extraction pathway yet. Sources include direct download from primary sources (US government releases, news outlets) and embedded clips from web pages. Storage layout, transcoding policy, and the relationship between the ingester and a video-extraction pipeline are all open.

**Licensing and permission.** Media often carries explicit copyright (a press photograph of a witness, a news outlet's clip of the Tic Tac video as broadcast versus the raw government release). The existing copyright status field on records (`public_domain`, `open_licence`, `publicly_accessible`, `licensed`, `restricted`) was designed for the body of the record. Whether the same statuses apply per-media-item, or whether a media item inherits the record's copyright, or whether each media item carries its own status, is unspecified. Treat as related but separable from the propagation question above; the answer informs which media can be served publicly via `anomalica-content` and which must stay private inside `anomalica-ingests`.

## Implications

- The record-format spec already supports image annotations with a `description` field reserved for vision-pass or human-authored captions. That field becomes load-bearing if media appears on public articles - it is the alt text and the caption.
- The data model (`architecture/data-model.md`) does not currently describe media nodes. If media becomes graph-first, the model needs a media node type.
- The assembler design must account for media inclusion from the outset rather than treating it as a later extension.
- Video introduces a transcoding and hosting question that images do not: a single original may need multiple delivery formats (web-playable codec, thumbnails for preview). The content repository's role expands accordingly.

## Site-layer implications

(Added 2026-05-27 from anomalica-site after reading this draft.)

- The graph-first vs flat-provenance decision propagates directly to the assembler's frontmatter shape and therefore to the Hugo `single.html` template. Graph-first means a layout shaped as "media reference block alongside text reference block" - parallel structure mirroring the claim-provenance reference layout. Flat means the layout gets a hero image at the top and not much more. The choice is layout-shaping, not decorative.
- Video delivery splits into two camps: `<video>` tags pointing at MP4s in `static/` (durable, offline-capable, content the project hosts) versus embed iframes pointing at external hosts (YouTube/Vimeo - has copyright-laundering risk for clips the project does not own). The licensing question above feeds directly into which path is appropriate per item.
- The existing reference layout (one block per source with a workbench link) is the natural home for media references too. Same provenance shape: `record_hash + claim_id + workbench_url`.

## Status

Captured for later resolution. No decision yet. Worth revisiting once the digester pipeline stabilises and the assembler begins design.
