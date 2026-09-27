# Asset intake and Record release

This is the target for acquiring an Asset before deciding whether it should
become a Record. It amends the automatic whole-Asset Record rule in [decision
0051](../decisions/0051-asset-record-selection-and-evidence-identity.md). **It
is not yet deployed:** ingester runs currently create whole-Asset Records,
Workbench structuring requires an extracted temporary parent, and scheduler
discovers ingestion from transient queue stubs. An `incoming/` file is not a
registered Asset and a queue stub is not a Record definition.

## Ownership and sequence

Workbench is the private operator interface and exposes the same actions via
authenticated APIs. Its backend calls ingester-owned acquisition and PDF
inspection primitives rather than maintaining a second fetcher or archive
implementation. The ingests repository holds durable private metadata; exact
original bytes remain in `records/{asset_hash}.{ext}`. Scheduler discovers and
dispatches ready Records; it neither decides PDF boundaries nor grants rights.
Digester continues to require a separate human review of the generated Ingest.

1. **Acquire an Asset.** Accept a URL or local PDF, fetch/import without model
   extraction, verify file format and physical page count, hash the exact held
   bytes and archive them. Persist a separate Asset manifest keyed by byte hash
   even when no Record is created. Repeated bytes resolve to the same Asset;
   additional acquisitions can be recorded without rewriting the byte identity.
   Failure creates no registered Asset. Repository metadata records a source
   filename, not a machine path or `file://` URL.
2. **Inspect.** Workbench shows the PDF and physical pages, title, description,
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
`catalogue.description`, editable in Workbench. It is a human-facing description
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

Workbench defaults to **Records**, with a sibling **Assets** view that includes
Assets with zero Records. Assets supplies URL/local-PDF acquisition, metadata
and rights editing, physical-page inspection, Record definition and completion.
Adapt the existing Structure editor's page assignment and Selection checks, but
remove its extracted-parent and two-children requirements for this path. Local
page rendering can precede model extraction; exact source text and maps cannot
be claimed before extraction. APIs validate authenticated role, URI/fetch
boundaries and Asset bytes on the server, never trust client-supplied hashes or
archive paths, and compare-and-swap committed metadata changes.

Scheduler remains the resource monitor and dispatcher. Its new input is a ready
Record definition, not an Asset-complete flag. Existing transient intake jobs
and historical Records need an explicit legacy path during rollout, not silent
reinterpretation as reviewed definitions. The first asset-first release is PDF
only; other media may be registered as Assets without entering this new
ingestion queue.
