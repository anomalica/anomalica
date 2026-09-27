# Asset intake and Record release

This is the target for acquiring an Asset before deciding whether it should
become a Record. It amends the automatic whole-Asset Record rule in [decision
0051](../decisions/0051-asset-record-selection-and-evidence-identity.md). **It
is not yet deployed:** ingester runs currently create whole-Asset Records,
Workbench structuring requires an extracted temporary parent, and scheduler
discovers ingestion from transient queue stubs. An `incoming/` file is not a
registered Asset and a queue stub is not a Record definition.

## Ownership and sequence

**Acquisition and catalogue** is the private operator interface and API for
submitting URLs or files, browsing followed channels and feeds, fetching bytes,
describing Assets, defining Record selections and releasing Records for ingest.
It is one logical service, not necessarily another repository or deployment.
Move the existing scheduler intake, channel/feed browsing and pre-ingest
download paths behind it; reuse the ingester's acquisition and archive
primitives rather than maintaining a second fetcher. Ingester then transforms
acquired, released selections without fetching again. Workbench owns review of
generated Ingests and digest/graph curation, not acquisition or initial page
structuring. Its existing structural page-selection code can be reused by the
acquisition interface. Scheduler discovers and dispatches ready Records and
monitors resources; it neither decides PDF boundaries nor grants rights.

The ingests repository holds durable private metadata. **Remote, rights-separated
object storage is the authoritative Asset archive in the target architecture,
including when an acquisition worker runs locally.** Acquisition stages bytes
temporarily, computes and checks their hash, writes the immutable remote object
and verifies it before registering the Asset as acquired. A worker may cache
bytes under `records/{asset_hash}.{ext}`; no Record or ingestion job depends on
that cache surviving. The existing `records/` folder is today's authoritative
local archive of originals and some processing sidecars. Its remote uploader
runs **after ingestion** and reads Record frontmatter, so it does not back up an
Asset without a Record. Migration must verify remote copies of existing
holdings before local storage can become only a cache; do not discard originals
on the assumption that a remote copy exists. Only openly redistributable Assets
go to the public delivery zone. Gated originals remain authenticated. The CDN
is a delivery layer, not a metadata store or a blanket publication decision.

1. **Acquire an Asset.** Accept a URL or uploaded PDF, fetch/import without model
   extraction, verify file format and physical page count, hash the exact held
   bytes and verify their remote archival copy. Persist a separate Asset manifest keyed by byte hash
   even when no Record is created. Repeated bytes resolve to the same Asset;
   additional acquisitions can be recorded without rewriting the byte identity.
   Failure creates no registered Asset. Repository metadata records a source
   filename, not a machine path or `file://` URL.
2. **Inspect.** Acquisition shows the PDF and physical pages, title, description,
   acquisition facts, rights and Records selecting it. An Asset may remain
   unstructured indefinitely; an image that will never be digested is still an
   Asset. Its metadata may change without changing its hash. An unselected Asset
   is not a graph Record or public Record page.
3. **Define Records.** Choose one whole PDF, one or more groups of complete
   physical PDF pages, or a supported composition across Assets. Reuse decision
   0051's canonical ordered Selection and server-side hash computation. Persist
   a distinct pre-ingest Record definition with title, optional document type,
   optional description, evidenced work dates and provenance. Do not invent a
   generated Ingest body or source map. Pages may be omitted or selected into
   several Records; neither grants independent evidential provenance. A single
   output is valid, including for a multi-page PDF.
4. **Complete inspection and release.** An explicit Asset-level inspected/complete
   decision means the editor has finished deciding whether to define Records; it
   does not mean every page was used. Only then may the editor mark each resulting
   Record separately **ready for ingest**. This freezes its ordered Selection
   and reviewed definition revision. Editing a released definition returns it
   to draft; changing Selection changes Record identity. Compare the viewed
   revision on every write. An Asset with zero Records may be completed with no
   ingestion jobs. Readiness is not a digestibility verdict.
5. **Ingest, review, digest.** Scheduler finds ready definitions and verifies
   their exact revision and every selected archived Asset before dispatch.
   Ingester produces the current `record/3` Markdown, page map and source map
   under the defined Record hash without fetching again or creating a default
   Record. Workbench's existing body-bound `review.json` verdict then governs
   digestion: only a current, complete, `digestible: true` review can make a
   digest job eligible. Structurally retired or superseded Records remain out.

The implementation needs a durable pre-ingest Record definition distinct from
the combined `record/3` Markdown/ingest envelope: an empty body must not
masquerade as a generated Ingest. The versioned schema, paths and atomic
definition-to-Ingest hand-off belong in `reference/format-specs.yaml` when its
producers and consumers are implemented together. Until then no consumer may
infer readiness from an Asset, queue stub or default whole-Asset Record.

## Descriptions, dates and rights

Both Asset and Record definitions have an optional private
`catalogue.description`, editable in Acquisition. It is a human-facing description
of that Asset or selected work, not an extraction input or a public source
quotation. An Asset description may be seeded from a landing-page blurb, with
the text's origin and URL recorded so it is not represented as words printed in
the PDF. A Record's description must describe its own selection rather than
inheriting the whole PDF's blurb indiscriminately. Source-supplied text may be
copied into that field by an editor where appropriate; neither description is
automatically published. The existing `provenance.description` remains the
source's own verbatim, reproduction-limited blurb and is **not** the editable
catalogue description.

The actual access instant, acquisition URL and source filename are separate
structured acquisition facts, not description prose. A publication date
supplied by a landing page is an observation about that page or container;
copy it to an individual Record's work publication date only when it describes
that selected work. Preserve evidenced date precision and omit unknown dates.

Rights are Asset-level authority. Anonymous public retrieval supports the
existing default `publicly_accessible`, **not** an open licence or public-domain
claim. The original remains gated, and public access does not establish the
right to send its contents to a hosted model. A local file without evidenced
rights defaults to `restricted`. Record definitions refer to the Asset's current
rights rather than granting their own. Explicit licences and third-party media
carve-outs require evidence and separate checks; a no-hold source must be
refused before archiving under the source-registration rule in
[ingest-format.md](ingest-format.md#copyright-status-what-a-source-gets-by-default).

## Surfaces and rollout

Acquisition defaults to a **Records** catalogue, with sibling **Assets** and
**Sources** views. Assets includes those with zero Records; Sources browses
followed channels, playlists and podcast feeds. Selecting a source item queues
acquisition, not ingestion. Assets supplies URL/file submission, metadata and
rights editing, physical-page inspection, Record definition and completion.
Adapt Workbench's existing Structure editor's page assignment and Selection
checks, but remove its extracted-parent and two-children requirements for this
path. Local page rendering can precede model extraction; exact source text and
maps cannot be claimed before extraction. Authenticated APIs validate role,
URI/fetch boundaries and Asset bytes on the server, never trust client-supplied
hashes or archive paths, and compare-and-swap committed metadata changes. The
same API and storage contract applies whether workers run locally or in a cloud
deployment; durable metadata never contains machine-specific paths.

Scheduler remains the resource monitor and dispatcher. Its ingest input is a
ready Record definition whose Asset bytes are acquired and verified, not an
acquisition request or Asset-complete flag. It may run an acquisition worker
under shared resource scheduling, but acquisition requests must not masquerade
as eligible ingest jobs. Existing transient intake jobs and historical Records
need an explicit migration or legacy path, not silent reinterpretation as
reviewed definitions. The first asset-first structuring release is PDF only;
other media may be acquired and catalogued without entering that queue.
