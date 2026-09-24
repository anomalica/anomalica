# 0052. Field-level visibility of Ingest annotations in the pre-digest

Date: 2026-09-24
Status: accepted; partially implemented

## Context

[0019](0019-record-interchange-format.md) gives an Ingest two annotation
carriers: YAML mappings in HTML comments and inline `{{YAML}}`. The carrier says
where an annotation sits, not whether it is source context for the extraction
model. [0042](0042-pre-digest-stage-and-eval-only-highlights.md) makes the
materialised pre-digest the exact model input, but its producer currently removes
selected annotation names by regular expression and leaves others untouched.
PDF page and EPUB printed-page comments therefore reach the model; word times,
printed-page sequence state and Kindle source positions have explicit removal
rules. The Kindle rule is a narrow deployed case rather than a generic
interpretation of underscored fields. The recorded format's claim that
classification annotations are stripped is not implemented by the shared
producer either.

A block can mix two kinds of information. An image annotation's `file` identifies
stored media, while its `description` is useful model context. Making a whole
comment either visible or invisible would split those related fields or discard
one of them. Page numbers, Kindle source positions and word times must survive in
the Ingest for references, but need not appear among the words the model reads.

## Decision

Keep the two annotation carriers. Within a **body annotation**, prefix a YAML
field name with one underscore when that field is not part of the pre-digest:
`{{_t: 1.25}}`, `{{_kindle_position: 2147}}`, `<!-- _file_page: 4 -->`.
The underscore is part of a valid YAML key, not a new delimiter or a YAML tag.
It does not apply to frontmatter, ordinary Markdown, or literal source text.
An annotation parser recognises the carrier, parses its YAML, and interprets
`_name` as the semantic field `name` with model visibility off. Exactly one
leading underscore is reserved for this purpose; two spellings of the same
semantic field in one annotation are invalid. Nested fields work the same way.
The stored spelling is preserved for review and provenance; consumers interpret
the semantic field name after removing the prefix. Flat inline annotations use
one key each, so several simultaneous point coordinates use adjacent markers
rather than a nested mapping that collides with the `}}` terminator.

The pre-digest removes a hidden point field without consuming adjoining words
or paragraph breaks. If visible fields remain in a comment, it projects only
their model-relevant meaning; it does not dump the raw YAML indiscriminately.
If no visible fields remain, the comment contributes no model text. The stored
Ingest still contains the complete annotation. A speaker and a source coordinate
may therefore share one comment, with only the speaker reaching the model.
For dense word timing, an inline marker immediately before the word is still
appropriate; positions at paragraph starts and EPUB page turns are inline
point markers, not separate prose blocks.

```markdown
<!--
speaker: Jane
_start_seconds: 42.1
-->
{{_t: 42.1}}She {{_t: 42.4}}saw a light.

<!--
image:
  _file: abc123def4567.jpg
  description: "A map labels the observation site."
-->
```

The pre-digest retains Jane's attribution and the words, and renders the image
description as context; neither the time values nor the image filename reaches
the model. The image filename remains usable to locate the archived image.

**Exclusion regions are not ordinary hidden point fields.** A paired
`<!-- _irrelevant: start -->` / `<!-- _irrelevant: end -->` removes the markers
**and every enclosed block** from the pre-digest. A `[irrelevant]` speaker turn
likewise removes the entire turn. An image marked irrelevant removes its whole
model projection. These actions depend on the annotation's meaning; an
underscore alone cannot define the extent of text to remove. Paired highlight,
link, citation and external-passage markers likewise retain their existing
span-specific rules: removing a marker must not accidentally remove its words,
nor keep an external passage as the Record's own testimony. Span notes still
surface their authored text as context while withholding their internal ids.

Location fields are extracted from the stored Ingest before model-only fields
are removed. After claim extraction, deterministic alignment of a verbatim
quote to that Ingest and its source map attaches the appropriate page, source
position or time. A raw `kindle_position` is an edition-specific renderer
coordinate, not automatically a reader-visible Kindle Location. Printed-page
labels and physical PDF page ordinals also remain different coordinates. The
model must not be asked to reconstruct either from text stripped before its
call. A claim that cannot be aligned does not acquire a fabricated locator.

**Implementation status:** the generic rule remains a migration target. One
narrow slice is deployed: the ebook producer emits
`{{_kindle_position: 2147}}`, and preparation version 9 strips that form plus the
legacy Kindle block without consuming its paragraph. This explicit transform
does not make `_t`, `_file_page` or any other underscored key hidden. Existing
undressed fields and legacy `{{t:1.25}}` remain readable during the migration.
The canonical output form uses YAML's `: ` separator, including in future
word-timing markers. Newly materialised pre-digests record their preparation
version; stored pre-digests and bindings are not rewritten. No typed ebook or
audio evidence support follows from the Kindle projection change.

### Migration inventory

The migration spans transcript, PDF and ebook Records, including dense word
timing and source-position annotations. It is a preparation-version and
review-state migration, not a punctuation-only edit.

| Existing data | Intended model projection | Migration boundary |
|---|---|---|
| `t` | No coordinate syntax | The current legacy marker is already stripped. Emit `_t` only after generic readers support it and preserve the word-to-time map. |
| `file_page`, `printed_page` | No coordinate syntax | Emit `_file_page` and `_printed_page`; build the locator map first and preserve verbatim printed-page labels. This migration remains pending. |
| `printed_page_sequence` | No coordinate syntax | The current undressed field is already stripped by an explicit transform. Migrate to `_printed_page_sequence` after structural readers support it. |
| `kindle_position` | No coordinate syntax | The producer now emits `_kindle_position`, and preparation version 9 strips canonical and legacy forms. Preserve the edition-specific raw position; deterministic claim alignment and typed downstream evidence remain pending. |
| `chapter`, `chapter_title` | Printed source heading where it exists, not a duplicated machine label | Keep structural chapter identity for chunking and review. Suppress a marker only after proving its title is supplied as source text or otherwise retaining needed context. |
| `speaker`, `message`, `image` | Attribution and genuine image/text context | Preserve speaker turns and message provenance. Image `_file` and `_alt` stay available to readers; `description` and source `caption` retain their distinct model-context rules. |
| `irrelevant: start/end`, `[irrelevant]` speaker, image `irrelevant: true` | No excluded words, segment or image | Change prose markers to `_irrelevant` after all region parsers support them; exclusion takes precedence over visible fields inside the region/image. |
| `classification`, highlight/link/cites markers, external passages, span notes | No raw control syntax; retain only the content each type permits | Fix the current classification leak. Migrate the machine-only marker families without dropping their enclosed source words, except for external passages. Keep span-note text as context while withholding its id. |
| Redactions, illegible passages, authored keyed/keyless notes | Their faithful source/content context | Do not prefix or erase these merely because they use annotation delimiters. |

The inventory is a migration baseline, not a claim that every existing Record
needs a rewrite: the migrator must report exactly which recognised markers each
Record holds. A reader-facing Kindle Location cannot be inferred from a raw
`kindle_position` or a page count; if a citation needs one, preserve and verify
the source edition's full location map separately. Retain ASIN and Kindle content
version as edition evidence with the archived Asset rather than implying the
current `source_url` identifies immutable Kindle content.

## Consequences and implementation scope

1. **Inventory and contract.** Audit every active annotation family, nested
   field and existing model-preparation transformation against the actual corpus.
   Register which fields are source-only and which contribute attribution or
   image/note context. Keep the body grammar in
   [ingest-format.md](../architecture/ingest-format.md); the annotation inventory
   and transform belong with the shared pre-digest producer, not in separate
   handwritten strip lists in each component. Reject an unrecognised machine
   field instead of quietly passing it to the model or silently deleting it;
   retain the documented free-form authored content-note forms.
2. **Consumers before writers.** Teach the shared Ingest annotation parser and
   source-mapped pre-digest producer to understand both historical and underscored
   keys. Build the coordinate/source map from the complete stored Ingest *before*
   projecting model text, and assert that the mapped and unmapped preparations
   yield the same text. Version the changed preparation; keep historical
   content-addressed pre-digests and source maps intact. The deployed Kindle
   regular expression is a compatibility slice, not the shared parser. PDF/image
   page mapping currently requires `file_page` markers to survive in model input,
   and ebook chunking currently splits on `chapter` comments: both must instead
   read parsed structure without sending location syntax to the model. Digest
   claim alignment and the quote audit must read both notations during
   transition.
3. **Producers.** Retain the deployed inline `_kindle_position` emission, then
   update audio/video word-timing emitters, PDF/image page emitters and page
   repair/validation, EPUB pagebreaks, quality counters and reviewer-authored
   markers. Place EPUB page locations inline without altering the source words.
   Do not transfer the Kindle `element_id` into claims: it is renderer structure;
   the archived EPUB retains it. Mixed image mappings can mark `_file` and `_alt`
   while retaining a visible `description` and contextual `caption`. Review the
   handling of chapter labels, classification, highlights, links, cited works,
   external passages and span notes individually; a blanket rename would change
   their meaning.
4. **Workbench and downstream readers.** Update ingest rendering, page navigation,
   transcript timing/editor, image editing, review coverage, annotation-aware
   search/replacement, preview, server record parsing and any site/assembler
   consumer of the raw body. Hidden from the *model* is not hidden from reviewers:
   page and timing controls may still be shown without displaying raw markup.
   Assimilator and scheduler paths that recompute pre-digest hashes, verify
   quotes or validate PDF anchors must consume the same shared interpretation.
   Speaker attribution and image descriptions must survive unchanged in model
   meaning; literal annotation text must not enter extracted claims.
5. **Deterministic record migration.** Add a dry-run-first, idempotent migrator
   for current `ingests/store/*.md`, with an expected input blob/hash, explicit
   changed-record manifest, proposed Markdown diff and post-write re-parse. Only
   recognised annotation tokens are rewritten; never substitute source prose,
   alter acquired Asset bytes, change a Record's Selection/content hash, or
   silently rewrite historical `store/v1/` bodies. Preserve print-page sequence
   state, relative word timing, images, speaker turns, annotation spans, reviewer
   overlays and edition identity. Regenerate generated bodies from corrected
   Ingester producers where possible and replay human edits through the normal
   refresh path rather than replacing reviewed work with a raw extractor output.
6. **Review and freshness.** A body rewrite invalidates
   `review.json.reviewed_body_sha256`; mechanically transferred coverage is not a
   new human verdict. Rebase only provably equivalent observed spans, set/retain
   `review_carryover` and require verification where the binding or text changed.
   Regenerate the pre-digest and source map under the new preparation version,
   and make freshness compare the recorded preparation version and source-map
   binding as well as the pre-digest text hash. The Assimilator's current schema-1
   check compares only the text hash: stripping an already-stripped marker could
   otherwise appear current after the migration. Mark affected digests stale,
   then re-digest and reconcile graph/content only through their ordinary
   freshness paths. Model-backed re-digestion is separately cost-estimated and
   approval-gated; this decision authorises no batch calls.

Full acceptance still requires fixture coverage for a mixed visible/hidden
block, a mid-paragraph page turn, a Kindle-positioned paragraph, word-aligned
speech, an irrelevant region, an irrelevant image, authored notes, overlay spans
and a classification marking. Compare the prepared text to the exact model
payload; prove quote-to-Asset-page and quote-to-time/ebook-position alignment
across marker removal. A representative PDF, transcript and book must round-trip
through the Workbench with unchanged source prose and explicit review status.
No claim of public ebook/audio typed-anchor support follows until their own
digest coordinate and consumer contracts are defined and implemented.
