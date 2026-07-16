# Record Format

The record format is the interchange format between the ingester and the digester. Each ingested source produces one ingest - a `.md` file in this format.

See [architecture decision record 0019](../decisions/0019-record-interchange-format.md) for why this format was chosen.

The canonical machine-readable field list is [`reference/format-specs.yaml`](../reference/format-specs.yaml) (`types.ingest`); this document is its narrative companion (body grammar, parser behaviour, examples).

## Structure

A record file has three parts:

1. **Frontmatter** - YAML (a human-readable metadata format) block at the top, fenced with `---`. Document-level metadata.
2. **Content** - markdown text. The actual content as it naturally reads.
3. **Annotations** - either block-level (YAML inside HTML comments) or inline (`{{YAML}}`).

All annotations use YAML throughout - the same data format as the frontmatter. Block annotations for structural markers (page boundaries, speaker turns, images). Inline annotations for mid-sentence markers (redactions, illegible text, actions).

The first `---` fenced block is always the frontmatter. All HTML comments in the body are annotations - the ingester does not produce any other HTML comments. Text between annotations is content.

## Frontmatter

Required fields:

```yaml
---
schema: anomalica/record/1
title: "Document title"
source_type: pdf
provenance:
  publisher: "..."
  published_date: 2023-07-26
  source_url: "https://..."
---
```

Every frontmatter field - its type, whether it is required, which source types it applies to, and a description - is listed once in [`reference/format-specs.yaml`](../reference/format-specs.yaml) under `types.ingest`. That YAML is the canonical field list; this document does not repeat it. The hash fields (`content_hash`, `source_hash`) are explained in narrative under [Store](#store); the body-annotation sub-fields (image, chapter, snapshot roles) are specified in their sections below.

### Provenance

Every record carries a `provenance` block - the canonical home for source-origin metadata, consolidating what used to be scattered across separate top-level fields (`publisher`, `source_url`, `date_published`, `source_id`, `creators`, and the rest). One block, one source of truth ([decision 0043](../decisions/0043-canonical-provenance-block.md)).

```yaml
provenance:
  collection: "war.gov UFO reading room"      # curated grouping this record belongs to
  publisher: "Department of Energy"           # issuing body / channel / author-org (not the hosting platform)
  creators: ["Edward Teller"]                 # human author(s) / host(s), person names in natural order
  published_date: "1949-03"                   # the source's own publication or upload date (ISO 8601, may be partial)
  acquired_date: "2026-07-11T09:00:00Z"       # when Anomalica brought the source in
  source_url: "https://www.war.gov/..."       # canonical URL of the original
  fetched_url: "https://web.archive.org/..."  # the URL actually retrieved, when different from source_url
  source_file: "los-alamos-1949.pdf"          # original filename, for a source ingested from a local file with no URL
  identifiers:                                # native source identifiers, keyed by scheme
    virin: "..."
    youtube: "aB8zcAttP1E"
  description: "..."                           # the source's OWN blurb, verbatim - never AI-generated
```

Each source type fills what it has; a sub-field with no value is OMITTED, never set to null. Origin-unknown is simply the absence of `source_url`, `fetched_url`, `source_file`, and `identifiers` - there is no separate marker (this replaces the old scalar `provenance: unknown`).

Two boundaries are load-bearing:

- **Source facts, not subject facts.** Provenance is about the SOURCE - who issued it, when it was published, where to find it. A subject's incident place and incident date are NOT provenance; they are extracted as claims about place and event nodes, so they stay inside the scored, corroborated evidence model. `published_date` is strictly the source's publication or upload date.
- **Copyright is not mirrored here.** `copyright` (and `copyright.status`) is the single authoritative copyright field, top-level; provenance carries no `license`. `classification` likewise stays top-level. The `description` is the source's verbatim blurb, never AI-written - and reproducing a `licensed` or `restricted` source's blurb is itself reproduction, so it is omitted or truncated for those sources, exactly as the source text is gated.

A claim's authoritative provenance is a reference to its source record (the `record_id` it already carries); the digest may additionally denormalise `publisher` + `published_date` + `collection` onto a claim as a render cache, so an article renders "from a 1949 Department of Energy document" without a join. The cache is derived and refreshed on re-digest; the record's block is authoritative. See [data-model.md](data-model.md).

### The archived original

Every record whose source was archived carries `archived_ext` - the bare extension of that archived object, which lives at `sources/{content_hash}.{archived_ext}`. That pair is the whole address: consumers build it to fetch or play the source (the workbench serving a reviewer the audio behind a transcript, for instance).

**The extension is not derivable, and must never be re-derived from `container`.** `codec` and `container` under `processing.source` describe the STREAM; the extension is a property of the FILE. yt-dlp writes `.opus` while reporting `container: ogg`, and a file downloaded as `.ogg` reports an identical stream - so the same metadata legitimately backs both extensions. Before this field existed, 76 of 122 records said `container: ogg` against a `.opus` file on disk, and a container-derived URL 404'd for the majority of the library. There is no glob on the CDN, so a wrong extension is simply a miss. Write the extension down; never infer it.

`archived_ext` is also **distinct from `source_file`**, which is the ORIGINAL filename of a local-file ingest. They describe different files and may legitimately disagree: a video ingested from `interview.mkv` and archived audio-only carries `source_file: interview.mkv` alongside `archived_ext: opus`. That is correct, not an inconsistency - do not reconcile them.

### Web record snapshots

For `source_type: web` records, the ingester captures three artefacts from a single page load and lands each in the sibling `sources/` directory. The frontmatter exposes them like this:

```yaml
source_hash: sha256:904c041f...   # raw post-render HTML asset
snapshots:
  - role: page_render
    hash: sha256:82f42514...
    content_type: application/pdf
  - role: single_file
    hash: sha256:e7115739...
    content_type: text/html
```

| Role | What it is | Use it for |
|------|-----------|------------|
| (raw HTML via `source_hash`) | Post-render DOM, no external resources inlined | Fidelity check on the extraction. Renders unstyled in a sandboxed iframe because external CSS won't load - not the right surface for visual review. |
| `page_render` | Single-page PDF rendered at 1024 px wide, sized to the document's scrollHeight (no internal pagination) | Printing; PDF.js review panes. |
| `single_file` ("frozen page") | Self-contained HTML produced by `single-file-cli` with every external resource inlined as data URIs | **Canonical review surface.** Renders identically to the original page under `sandbox=""`. |

Consumers preferring fidelity should pick `single_file` first, fall back to `page_render`, and use the raw HTML only as a last resort.

Snapshot roles are an extensible registry. New roles can be added without bumping `schema` provided consumers ignore unknown roles. Known roles as of `anomalica/record/1`: `page_render`, `single_file`.

## Content

Standard markdown. Headings, paragraphs, lists, bold, italic, links, and tables all work as normal.

The body carries the extracted content only - the ingester does not inject the title into it. The title lives in frontmatter `title:`, which the workbench and consumers (the digester parses it from the frontmatter, not the body) read from there. For web records the page's own leading title heading - which trafilatura emits and which merely duplicates `title:` - is stripped; a source document's own in-content headings (e.g. a PDF's printed heading) are preserved as faithful content. The body may begin with an optional `*Published <date>*` stamp, omitted when the body already states the publication date in a byline or when the date is unknown.

## Block annotations

YAML inside HTML comments. Single-field annotations use inline comments. Multi-field annotations use multi-line comments. Used for structural markers that sit between content.

### Page boundary

```markdown
<!-- file_page: 2 -->
```

`file_page` is always the PDF page number (1-indexed from the start of the file). If the page has its own printed page number that differs, include `printed_page` on a separate line:

```markdown
<!-- file_page: 19 -->
<!-- printed_page: 15 -->
```

`printed_page` is omitted when there is no printed page number, or when it matches `file_page`.

For `ebook` records there is no fixed file pagination, so `file_page` does not apply. When the EPUB carries EPUB3 pagebreaks (`epub:type="pagebreak"` or `role="doc-pagebreak"`, whose `title` is the print-edition page), the ingester emits `printed_page` alone at each break position:

```markdown
<!-- printed_page: 15 -->
```

The label is taken verbatim from the pagebreak, so front-matter roman numerals (`iii`, `viii`) and index labels appear as-is. A page break can fall mid-paragraph, so the marker records where print page N begins in the reflowed text. EPUBs without pagebreaks carry no page markers and locate content by [chapter boundary](#chapter-boundary) only.

### Speaker change

An inline HTML comment marks when the speaker changes. All content until the next speaker annotation belongs to that speaker.

```markdown
<!-- speaker: David Fravor -->
```

The `speaker` value is the speaker's name, or `Speaker 1`, `Speaker 2`, etc. before human review has identified them.

Four bracketed tokens are reserved for non-individual sources:

| Token | Meaning |
|-------|---------|
| `[narrator]` | A voice-over narrator distinct from any on-camera speaker. |
| `[external footage]` | Audio from an inserted clip (news segment, archival recording, etc.) where the speaker isn't part of the primary recording. |
| `[group]` | Multiple people saying the same thing simultaneously - chants, unison answers from a committee, group responses. |
| `[irrelevant]` | Content that doesn't belong in the record (ads, sponsor reads, off-topic asides). Hidden from rendered output, and stripped before extraction so no claim is drawn from it (see [Irrelevant content](#irrelevant-content)). |

The brackets are part of the value. The ingester does not emit these tokens itself - they're applied by human reviewers in the workbench when the diarisation-assigned `Speaker N` is identified as one of these cases.

### Sentence-level timestamps

In `record/1` audio and video transcripts, each sentence starts on its own line prefixed with a `HH:MM:SS.D` timestamp (fixed 10 characters, one decimal place). An empty line indicates a paragraph break. Word-level `record/2` transcripts carry inline per-word markers instead and omit this line-start prefix - see [Word-level timestamps](#word-level-timestamps) below.

```markdown
<!-- speaker: David Fravor -->
00:01:45.2 We had been at sea for roughly two weeks.
00:01:48.7 I was the Commanding Officer of Strike Fighter Squadron Forty-One.
00:01:53.1 We were at the beginning of our workup cycle.

00:01:56.4 When we arrived at the location at 20,000 feet, the controller called merge plot.
```

The timestamp format is always `HH:MM:SS.D` - hours, minutes, seconds, and one decimal place (tenths of a second). This lines up in a fixed-width column for readability.

### Word-level timestamps

Records with `word_timestamps: true` (schema `anomalica/record/2`) carry timing on every word, not every sentence: an inline `{{t:SECONDS}}` marker (seconds from media start, two decimal places) sits immediately before each word.

```markdown
<!-- speaker: David Fravor -->
{{t:105.20}}We {{t:105.38}}had {{t:105.55}}been {{t:105.71}}at {{t:105.83}}sea {{t:106.10}}for {{t:106.34}}roughly {{t:106.78}}two {{t:107.01}}weeks.
```

These records do **not** carry the sentence-level `HH:MM:SS.D` line-start prefix: each line's first `{{t:}}` already gives its start, so the prefix is redundant. The one exception is a transcript segment for which the aligner produced no word-level timing - that line keeps a `HH:MM:SS.D` line-start stamp as its only timing and has no `{{t:}}` markers. Consumers that want plain prose strip the `{{t:}}` markers like any other annotation.

### Image

Marks a figure, chart, or photograph that appears in the source. Two forms.

**Description-only (inline).** A factual description or transcription with no extracted file. The value is a scalar string - this IS the `description` (image content, kept by the pre-digest and extractable), just with no `file`, `alt`, or `caption`:

```markdown
<!-- image: Bar chart showing UAP reports by year from 2019 to 2023, with a sharp increase in 2021. -->
```

**With extracted file.** When the ingester has saved the image bytes alongside the record, the value is a mapping with at minimum a `file` field:

```markdown
<!--
image:
  file: abc123def4567.png
  alt: "Portrait of a man in a dark suit"
  caption: "David Charles Grusch (Copyright (c) D. Grusch. Image may not be reproduced without permission.)"
-->
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | string | yes | The image's filename - bare, not a path. Format is `{img_hash}.{ext}` where `img_hash` is a 12-character hexadecimal SHA-256 prefix of the image bytes and `ext` is the file extension (`png`, `jpg`, `gif`, `svg`, `webp`). |
| `alt` | string | no | Alt text from the source (`<img alt="">` in EPUB/HTML). Omitted when the source provides no alt text. |
| `description` | string | no | A faithful transcription or factual description of what is IN the image - the text of a tweet or document screenshot, the figures in a chart, the words on a scanned page, or a plain description of a photo. Generated by a vision pass or human review, not by the ingester. Unlike the other image sub-fields this is CONTENT: the pre-digest renders it into the model input as an `[image: ...]` meta-note (see [the bracket meta-notation](#the-bracket-meta-notation)), so a claim can be drawn from what the image shows (a screenshotted tweet's text is a real statement). It must stay faithful to the image - transcription or factual description, never interpretation - so any claim drawn from it is honestly sourced. Omitted when no description has been written. |
| `caption` | string | no | The source's PRINTED caption for the image, verbatim - including any copyright or attribution line the source shows with it (e.g. `David Charles Grusch (Copyright (c) D. Grusch. Image may not be reproduced without permission.)`). Distinct from `alt` (the source's HTML alt attribute) and `description` (a generated factual description): the caption is what the source itself printed beneath the figure. It renders into the pre-digest as a `[caption: ...]` meta-note - context the model sees but the digester never extracts as a claim (attribution and copyright are not facts about the subject). Omitted when the source shows no caption. |
| `irrelevant` | boolean | no | Reviewer's keep/drop DISPLAY flag. Absent (the default) means keep/render; `true` marks an image not worth rendering (an advertisement, a decorative element, a stock photo unrelated to the subject). Mirrors the text mark-irrelevant convention - kept unless explicitly marked. When `true`, the image is excluded from the pre-digest (never extracted) AND skipped by the assembler/site (never rendered) - the mark drops it from both extraction and display. |

The `file` value is a bare filename so the body of the record stays self-contained and content-addressable. The full path on disk is `media/{record_hash}/{file}` relative to the ingests root, where `{record_hash}` is the hash of the record containing the annotation (the same value as the record's filename in `store/`). Embedding the record hash directly in the body would break the record_hash invariant for source types whose `content_hash` is computed from the body (ebook, web).

When the same image appears in multiple records, each record gets its own copy under its own `media/{record_hash}/` subdirectory. This keeps records self-contained for downstream consumers (workbench, assembler, digester) at the cost of duplication, which is small in practice (cover art, publisher logos).

**How images render into the pre-digest.** An image is not stripped to bare prose; it is rendered into the pre-digest as a `[...]` meta-note (see [the bracket meta-notation](#the-bracket-meta-notation)):

- `[image]` alone when the annotation has no description - signalling only that an image is present;
- `[image: DESCRIPTION]` when a description exists (the mapping's `description:` field, or the inline form's scalar value);
- followed by `[caption: CAPTION]` when a caption exists.

An image flagged `irrelevant: true` is excluded from the pre-digest entirely - the mark means dropped-from-extraction, not only dropped-from-display. The `file` and `alt` fields are storage and accessibility metadata and are not rendered. The whole annotation still stays in the record for the assembler to render the actual image; the `[...]` rendering is only how the image reaches the model.

So a tweet screenshot annotated as:

```markdown
<!--
image:
  file: 3a7c1e90b2d4.png
  description: "Tweet by @user, 3 May 2023: The Pentagon confirmed today that the 2004 Nimitz object remains unidentified."
  caption: "Screenshot, via a news report"
-->
```

reaches the model as `[image: Tweet by @user, 3 May 2023: The Pentagon confirmed today that the 2004 Nimitz object remains unidentified.] [caption: Screenshot, via a news report]`. The tweet text (a description) can become a claim; the `[caption: ...]` (attribution) is context the digester never extracts. The meta-versus-content rule is defined in full under [the bracket meta-notation](#the-bracket-meta-notation).

A reviewer's keep/drop choice for an image is the `irrelevant` flag on the same annotation (`irrelevant: true`; absent means keep), mirroring the text [mark-irrelevant convention](review-workbench.md#what-to-mark-irrelevant). A flagged image is excluded from the pre-digest entirely - the model never sees it - and skipped by the assembler/site when rendering: the mark drops the image from both extraction and display. Like other reviewer corrections, the who/when rides on the git commit that sets it, not an inline stamp:

```markdown
<!--
image:
  file: 9f2c1a0b4de8.jpg
  alt: "Advertisement banner"
  irrelevant: true
-->
```

### Chapter boundary

Marks the start of a chapter or top-level structural section in long-form documents (primarily ebooks).

```markdown
<!-- chapter: 3 -->
<!-- chapter_title: "DEDICATION" -->
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `chapter` | integer | yes | Sequential index of the chapter within the document, starting at 1. Counts every structural section the source defines, including front matter (cover, dedication, contents). |
| `chapter_title` | string | no | The chapter's title as given in the source. Always quoted. Omitted when the source provides no explicit title. |

These are structural markers, not rendered prose. Consumers typically use them for navigation (jump-to-chapter, table of contents construction) and suppress them when displaying the body. Where a `chapter_title` is present, the source itself usually also opens the chapter with a heading on the next non-empty line; consumers should not render the annotation as a duplicate of that heading.

### Block-level redaction

```markdown
<!--
redacted:
  extent: paragraph
-->
```

`extent` estimates how much was redacted: `words`, `sentence`, `paragraph`, or `page`.

### Irrelevant content

Content that is physically part of the source but does not belong in the record - a book's title page, table of contents, index, or glossary; a publisher's cross-sell advertisement; an off-topic aside. It is marked, never deleted: the mark is fully reversible and the source text stays intact in the ingest. What counts as irrelevant - the reviewer convention across every record type - is the canonical list in [review-workbench.md](review-workbench.md#what-to-mark-irrelevant); this section specifies the marker syntax.

The mechanism depends on the source shape.

**Prose records (web, ebook, pdf)** have no speakers or segments, so a paired HTML-comment region wraps the irrelevant block(s):

```markdown
Chapter Eleven closes the investigation.

<!-- irrelevant: start -->

## Also by this author

*Order the sequel, out this autumn from the same publisher.*

<!-- irrelevant: end -->

Appendix A lists the case files referenced above.
```

- **Block-aligned.** `start` and `end` each sit on their own annotation line and wrap whole blocks (paragraphs, headings, lists, tables) - never part of a sentence. There is no mid-sentence form; excluding a fragment of a sentence is not an irrelevant-marking case.
- **Non-nesting.** A region never contains another region: a `start` is closed by the next `end`.
- **Multiple regions** per record are allowed.
- **Verbatim and reversible.** The wrapped text is the source text unchanged; the two comment lines are the only addition, so removing them restores the record exactly.

Each marker is an ordinary single-field block annotation: `<!-- irrelevant: start -->` parses as the YAML mapping `{irrelevant: start}`, value `start` or `end`. Note the space after the colon that YAML requires - write `irrelevant: start`, not `irrelevant:start` (the latter parses as a bare string, not a mapping, and is invalid here).

**Audio and video transcripts** have no prose blocks to wrap, so they mark irrelevant spans by segment instead, through the reserved `[irrelevant]` speaker token (`<!-- speaker: [irrelevant] -->`; see [Speaker change](#speaker-change)). The region marker complements that token - it does not replace it: prose gets the region, transcripts get the speaker token.

**The digester strips both before extraction.** Before reading a record, the digester removes all irrelevant-marked content - both prose `irrelevant: start`/`end` regions and transcript `[irrelevant]` speaker segments - so the extraction model never sees it and no claim is drawn from it. This parallels the classification-marking strip ([Classification markings](#classification-markings)): a read-time transform only. The source text stays in the ingest and the reviewer's mark stays reversible; nothing is written back from the digester, so data still flows one direction. The strip is one step of the deterministic model-prep the digester applies before extraction to produce the **pre-digest** - the materialised, inspectable artefact that is the exact text the model reads ([0042](../decisions/0042-pre-digest-stage-and-eval-only-highlights.md)).

This is additive within `anomalica/record/1`: a consumer that does not recognise the region treats the wrapped text as ordinary content - the behaviour before the marker existed - so it needs no `schema` bump.

## Inline annotations

For annotations that fall mid-sentence. The syntax is `{{YAML}}` - double curly braces containing valid YAML.

```markdown
The programme was conducted at {{redacted: ~2 words}} Air Force Base.

The date was {{illegible: possibly March 2004}} according to the memo.

{{Fravor: holds up photograph}} and showed us the evidence.

{{audience: laughter}}
```

The content inside `{{ }}` is parsed as YAML, in one of two authored forms:

- **Keyed** - a single key-value pair where the key describes what or who the annotation is about and the value gives the detail (`{{Fravor: holds up photograph}}`). There is no fixed vocabulary of keys; the key is whatever makes sense in context.
- **Keyless** - a bare YAML scalar, for an unkeyed note that needs no subject (`{{laughs}}`, `{{applause}}`). The scalar is the whole note.

A small set of keys is *reserved* for machine-read markers rather than free-form annotation content: `t` (word-level timestamp), `highlight-start` / `highlight-end` ([Highlights](#highlights)), and `note-start` / `note-end` ([Span notes](#span-notes)). A consumer treating the body as prose strips the whole `{{...}}` family so a marker never breaks word matching. The extraction pipeline strips the `t` and `highlight-*` markers entirely (they carry no content); for `note-*` it strips the markers but preserves the note's text as context, exactly as it keeps the keyed and keyless content notes (see [Span notes](#span-notes) and [The bracket meta-notation](#the-bracket-meta-notation)).

### Why double curly braces

Single curly braces appear in source text (mathematics, code, template syntax). Double curly braces are extremely rare in natural text. This avoids false matches without requiring escape mechanisms.

### Values containing special characters

Since the content is YAML, values containing colons or commas need quoting:

```markdown
{{Fravor: "turned to the camera and said: look at this"}}
```

Standard YAML quoting rules apply.

### Classification markings

Declassified government documents carry security classification markings at two levels. Both are preserved.

**Document level.** The overall classification banner (`(SECRET//REL TO USA, FVEY)`, `(SECRET//NOFORN)`) goes in the frontmatter `classification` field, verbatim with the surrounding parentheses stripped. In-body repetitions of that same banner - the page headers and footers that restate it - are redundant with the frontmatter and stripped from the body.

**Portion level.** Markings that classify a specific portion and differ from the document banner (`(S//REL)`, `(U)`, `(S/RELIDO)` prefixing a paragraph or section heading) are preserved as an inline annotation at the start of the portion they govern:

```markdown
{{classification: U}} This paragraph was unclassified within an otherwise classified report.

{{classification: "S//REL"}} This paragraph carried its own portion marking.
```

The value is the marking verbatim, parentheses stripped, quoted when it contains special characters (the `//` and commas common in markings). A portion marking applies from its position until the next classification marking; the frontmatter `classification` is the default for any portion with no preceding marking. This lets a consumer attribute the classification of any portion - and therefore of a claim extracted from it - though doing so is optional.

Classification markings are never represented with strikethrough; strikethrough is reserved for text genuinely struck through in the source. Like every annotation, classification markings are metadata, not prose - consumers strip or interpret them before treating the body as text. The extraction pipeline in particular removes them before reading prose, so a marking never leaks into an extracted claim.

### Highlights

A highlight marks a span a reviewer judged significant - gold to keep, an example for training or evaluation, or simply something to flag. Highlights are authored in the workbench and stored in the record body, so they survive edits without a drifting sidecar, and they work in every record type.

A highlight is a pair of inline markers sharing a short opaque id:

```markdown
The {{highlight-start: a1}}remote viewers with the NSA{{highlight-end: a1}} were getting this.
```

The id lets highlights **overlap**: two spans that cross are told apart by their ids, so a close matches the right open even when another highlight opened in between.

```markdown
{{highlight-start: a1}}quick brown {{highlight-start: b2}}fox{{highlight-end: a1}} jumps{{highlight-end: b2}}
```

Ids are opaque, unique within a record, and minted by the authoring UI; reviewers never type these markers.

**Span extent and orphan handling.** A matched pair is bounded only by its own start and end markers - a highlight may span any range, including across paragraph breaks and speaker turns (a highlight over a multi-speaker back-and-forth is valid). An edit can delete one half of a pair: a `highlight-start` with no matching end auto-closes at the end of the body; a `highlight-end` with no live open is dropped. Parsers on both sides apply this, so a half-deleted marker never corrupts a record.

**Highlights are stripped from the pre-digest and never reach the extraction model.** Unlike the content notes above, a highlight carries no content - it is a reviewer's pointer, an evaluation and curation signal only. Letting the model see it would bias extraction and destroy its value as a blind recall signal ([0042](../decisions/0042-pre-digest-stage-and-eval-only-highlights.md)); the `{{t:}}` timestamp markers are stripped the same way. Authored content notes (`{{...}}`, keyed or keyless) are the exception - they are preserved into the pre-digest as context, exactly as bracket meta-notes are.

This is additive within `anomalica/record/1`: a consumer that does not recognise the markers treats the wrapped text as ordinary content, so it needs no `schema` bump.

### Span notes

A span note attaches free text to a word *range* - "what was on screen here", external context that spans a period the words alone do not carry. It is the ranged counterpart to the keyless point note (`{{laughs}}`, anchored to one spot): a span note has a start and an end the reviewer can drag to re-range.

A span note is a pair of inline markers sharing a short opaque id. `note-start` carries a YAML flow list `[id, text]`; `note-end` carries the id:

```markdown
{{note-start: [a1, "on-screen caption: the witness's own drawing of the craft"]}} ... spanned words ... {{note-end: a1}}
```

The flow list keeps the note flat - no nested braces to confuse the `}}` scan - and the text is quoted per YAML when it contains colons or quotes. Ids are opaque, unique within a record, and minted by the authoring UI; reviewers never type these markers. Overlap, extent, and orphan handling are the same as [Highlights](#highlights): spans are told apart by id and may cross speaker turns and paragraph breaks, an unmatched half auto-closes at the end of the body, and an end with no live open is dropped.

**Unlike a highlight, a span note carries content and is preserved into the pre-digest.** The markers (`note-start` / `note-end` and their ids) are stripped from prose - for search and display, and from the model input - but the note's *text* is re-surfaced into the pre-digest as a context note, exactly like the keyed and keyless content notes, so the model reads it as interpretive context. This is additive within `anomalica/record/1`: a consumer that does not recognise the markers treats the wrapped text as ordinary content, so it needs no `schema` bump.

## The bracket meta-notation

A square-bracket note - `[...]` - in the pre-digest is a *description of what is present*, not verbatim source content. It reaches the model as context, and the digester reads it as meta. It appears in two places:

- **Images**, rendered into the pre-digest from the [image annotation](#image): `[image]` alone, `[image: DESCRIPTION]`, and `[caption: CAPTION]`.
- **Transcript event notes** - non-verbal events such as laughter, applause, or an inaudible passage. These are now authored as keyless inline annotations (`{{laughs}}`, `{{applause}}`, `{{inaudible}}`; see [Inline annotations](#inline-annotations)); older records carry the legacy bracket form (`[laughs]`) pending migration. Either records what occurred, not words anyone spoke.

**The load-bearing rule: the meta framing is never a verbatim claim; genuine content described inside it still is.** The digester may use a `[...]` note as context, but must never turn the FRAMING into a spoken or written claim - `[laughs]` never becomes "someone laughed"; `[caption: Credit Getty]` never becomes an attribution claim; a bare `[image]` never becomes a claim. But genuine content that a description transcribes - `[image: the text of a screenshotted tweet]`, `[image: a chart's figures]` - is a real statement the source makes through that image, and stays extractable as a claim, sourced to the image. The brackets frame *where* content came from; the content inside a description is still content.

Because event notes appear only in transcripts (which carry no markdown links) and image notes are generated by the pre-digest with an `image:` or `caption:` prefix, `[...]` meta-notes do not collide with ordinary bracketed prose.

**Relationship to `{{...}}` inline annotations.** Reviewer-authored notes are all `{{...}}` now - keyed when the note has a subject (`{{Fravor: holds up photograph}}`, `{{classification: U}}`) and keyless for a bare event (`{{laughs}}`). The `[...]` bracket form is reserved for two non-authored uses: the speaker tokens (`[narrator]`, `[irrelevant]`, and similar) inside `<!-- speaker: -->` comments, and the image and caption meta the pre-digest renders from image annotations (`[image: ...]`, `[caption: ...]`). A bare `[...]` sitting in a stored record body that is neither of those is therefore *literal source content* (`[sic]`, an editor's `[bracketed]` clarification inside a quote), not an annotation - which is exactly why authored notes moved to `{{...}}`: to stop colliding with the brackets real source text contains. Where they are annotations, both forms are metadata, never prose, and both obey the never-a-verbatim-claim rule above.

## Parser behaviour

1. Extract the first `---` fenced block as frontmatter (standard markdown frontmatter).
2. Find all `<!-- ... -->` HTML comments in the body. Parse the content of each as YAML. All HTML comments are annotations.
3. Text between annotation blocks is content.
4. Within content blocks, scan for `{{...}}` patterns and parse the interior as YAML (inline annotations).

## Output directory structure

```
store/          # hash-named record files (source of truth)
  7bf2c20d...md
  7bf2c20d...verification.json
  e27169e8...md
  _pipeline_versions.yaml   # {media_type: current_version} manifest
  v1/                       # superseded records, retired here
    3211a96e...md
records/        # human-readable symlinks
  2023-07-26-pdf-fravor-written-statement.md -> ../store/7bf2c20d...md
  2020-09-08-video-lex-fridman-122-david-fravor.md -> ../store/e27169e8...md
media/          # extracted images, per-record subdirectories
  11c66b201...
    abc123def4567.png
    f80921a3b56c.jpg
  9a254b6ba...
    abc123def4567.png   # same image, separate copy per record
```

### Store

The `store/` directory contains the actual record files, named by `content_hash`. What `content_hash` hashes per source type, and how it links back to `sources/`, is defined once in the canonical hash chain ([`format-specs.yaml`](../reference/format-specs.yaml), `chain:`) and is not restated here.

Two behaviours follow from that per-type hashing. It deduplicates - the same input always produces the same store path. And it makes the source-anchored types stable across re-extraction (reprocessing with an improved transcriber keeps the same identity and does not orphan reviews), whereas the body-anchored types get a new `content_hash` whenever a re-extraction changes the body. Making this consistent across types is under reconciliation.

Idempotency: if `{hash}.md` exists, the ingester skips extraction.

Sidecars live next to the record in `store/`, named `{content_hash}.<kind>.json`:

- `{hash}.verification.json` - cloze proof-of-possession challenges (ingester's
  `shared/verification.py`; consumed by the workbench access gate). Present only
  for records whose copyright status gates access.
- `{hash}.review.json` - review-coverage spans and the reviewer verdict
  (`anomalica/review-coverage/N`, written by the workbench; read by the
  digester's review gate).
- `{hash}.highlights.json` - relevance-tuning ground truth
  (`anomalica/highlights/1`, written by the workbench tuning mode; read by the
  digester's grader). Span offsets are Unicode code points into the raw stored
  body (the verbatim text after the closing frontmatter fence); `body_sha256`
  pins the exact body the offsets index. See
  [relevance-tuning-mode](../decisions/drafts/relevance-tuning-mode.md).

### Versioning and supersession

Three orthogonal axes describe a record's generation, defined in full in
[0040](../decisions/0040-pipeline-versioning-and-supersession.md):

- `schema` (`anomalica/record/N`) is the on-disk FORMAT. A record/1 is not stale
  merely because record/2 exists as a format.
- `processing.pipeline_version` (an integer, per media type) is the extraction
  GENERATION. A record whose value is PRESENT and below the current version for
  its media type is STALE: a consumer badges it "outdated (vN of M)" and it is a
  backfill target, but it is still shown - it is the best available until
  re-ingested. An ABSENT value means "generation not declared" - no badge, not
  treated as 0 (so introducing the field does not flag the whole corpus). The
  current version per media type is published in `store/_pipeline_versions.yaml`
  (`{media_type: current_version}`), upserted by the ingester on every run.
- `processing.version` (the ingester's git short-hash) is fine-grained
  provenance, unchanged.

**Supersession** retires a prior record when a source is re-ingested, keyed on
LOGICAL source identity (`provenance.identifiers`, then `provenance.source_url` - the only identity
stable across re-downloads; a per-download `content_hash` is not). The new record
carries `supersedes: <old_content_hash>`; the prior record is stamped
`superseded_by: <new_content_hash>`, moved from `store/{hash}.md` to
`store/v1/{hash}.md`, and its `records/` symlink removed. The frontmatter flag is
the source of truth - a consumer HIDES any record carrying `superseded_by` (one
visible record per source); the `store/v1/` location is a derived convenience so
a non-recursive `store/*.md` glob excludes retired records. Supersession is
stamped across schema boundaries (a record/2 supersedes a record/1 of the same
source). It applies only when re-acquisition changes the `content_hash` (a fresh
download, or a web/ebook body change); re-extraction from the SAME asset keeps
the hash and is an in-place update at `store/{hash}.md`, not a second record. So
the browse list is always one-per-source. The `.v2`-suffixed word-timestamp
files are vestigial migration scaffolding, collapsed to the canonical
`store/{hash}.md` as a follow-up; see
[0040](../decisions/0040-pipeline-versioning-and-supersession.md).

### Records

The `records/` directory contains symlinks with human-readable names, pointing into `store/`. The naming convention is:

```
{date}-{source_type}-{slugified-title}.md
```

For example:
- `2023-07-26-pdf-fravor-written-statement.md`
- `2020-09-08-video-lex-fridman-122-david-fravor.md`
- `2024-08-20-ebook-imminent.md`
- `2009-pdf-nimitz-executive-summary.md`

The date, source_type, and title are taken from the record's frontmatter. The symlinks are regenerated from the store contents and can be deleted and rebuilt at any time.

### Media

The `media/` directory holds images extracted from sources (currently EPUB; PDF, web, and video frame extraction will follow). Layout:

```
media/{record_hash}/{img_hash}.{ext}
```

`record_hash` matches the record's filename in `store/`. `img_hash` is a 12-character SHA-256 prefix of the image bytes. `ext` is the source-supplied extension (`png`, `jpg`, `gif`, `svg`, `webp`).

Each record's images live in their own subdirectory. Images shared across records are duplicated rather than shared - see the [Image annotation](#image) section for the rationale.

A record's `media/` directory is omitted entirely when the record has no extracted media. Consumers should not assume every record has one.

Copyright status follows the parent record. If `copyright.status` is `licensed` or `restricted`, the images stay private. The assembler copies images into `content` only for records eligible for public serving (`public_domain`, `open_licence`, `publicly_accessible`).

## Examples

### PDF document

```markdown
---
schema: anomalica/record/1
title: "David Fravor Statement for the House Oversight Committee"
source_type: pdf
provenance:
  publisher: "House Oversight Committee"
  creators:
    - David Fravor
  published_date: 2023-07-26
  source_url: https://oversight.house.gov/...
content_hash: sha256:7bf2c20d...
pages: 3
---

<!-- file_page: 1 -->

David Fravor Statement for the House Oversight Committee.

I first want to thank you for the invitation to speak to this
committee on the UAP topic that has been in the news for the past
6 years and seems to be continuing to gain momentum.

<!-- file_page: 2 -->

As we proceeded to the west and as the air controller counted down
the range, we had nothing on our radars and were unaware of what
we were going to see when we arrived.

<!-- file_page: 3 -->

In closing, I would like to say that the Tic Tac Object that we
engaged in Nov 2004 was far superior to anything that we had at
the time, have today, or are looking to develop in the next 10+
years.
```

### Video transcript

```markdown
---
schema: anomalica/record/1
title: "Lex Fridman Podcast #122 - David Fravor"
source_type: video
provenance:
  publisher: "Lex Fridman"
  published_date: 2020-09-08
  source_url: https://youtube.com/watch?v=aB8zcAttP1E
  identifiers:
    youtube: aB8zcAttP1E
duration: 7200.48
content_hash: sha256:e27169e8...
---

<!-- speaker: Speaker 1 -->
00:01:23.0 So tell me about what happened in 2004.
00:01:25.4 You were a Navy pilot stationed on the Nimitz.

<!-- speaker: Speaker 2 -->
00:01:45.2 We had been at sea for roughly two weeks.
00:01:48.7 I was the Commanding Officer of Strike Fighter Squadron Forty-One.
00:01:53.1 We were at the beginning of our workup cycle.

00:01:56.4 {{action: Fravor gestures to indicate the size of the object}}
00:01:58.1 It was about the size of an F-18, roughly 40 feet long, with no wings, no exhaust plume.
```

### Freedom of Information Act document with redactions

```markdown
---
schema: anomalica/record/1
title: "Incident Report"
source_type: pdf
provenance:
  published_date: 2004-11-14
pages: 5
---

<!-- file_page: 1 -->

# Incident Report

On {{redacted: date in November 2004}}, personnel at {{redacted}}
observed an unidentified aerial object in restricted airspace.

<!--
redacted:
  extent: paragraph
-->

The object was tracked on radar for approximately 12 minutes
before {{redacted: ~5 words}}.

<!-- file_page: 2 -->

<!-- image: Grainy black and white photograph showing a small oblong object against a featureless sky. No scale reference visible. -->

The following personnel were present during the observation:

| Name | Rank | Role |
|------|------|------|
| {{redacted}} | Commander | Officer of the Watch |
| {{redacted}} | Lt. | Radar Operator |
```
