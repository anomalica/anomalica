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
date_published: 2023-07-26
source_type: pdf
---
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema` | string | yes | Format version. Always `anomalica/record/1` for this version. |
| `title` | string | yes | Document or episode title. Always quoted. |
| `date_published` | string or null | yes | When the original content was published. ISO 8601, precision varies: `2023`, `2023-07`, `2023-07-26`, or with time and zone. Set to `null` when the source is genuinely undated (e.g. an undated transcript or memo) - do not fabricate a fallback from file modification or ingestion dates, as a wrong date is worse provenance than an absent one. |
| `source_type` | string | yes | One of: `pdf`, `audio`, `video`, `web`, `ebook` |
| `publisher` | string | no | The entity that created the content (e.g. "CBS News", "The Debrief", "House Oversight Committee"). Not the hosting platform; distinct from `creators` (the human creator(s)). |
| `source_url` | string | no | URL where the source can be found |
| `source_id` | string | no | Stable platform-specific identifier (e.g. `youtube:ZBtMbBPzqHY`) |
| `fetched_url` | string | no | URL from which the content was actually retrieved, if different from source_url (e.g. a Wayback Machine archive URL) |
| `source_file` | string | no | For a record ingested from a local file (no URL), the original filename - the traceable origin where there is no `source_url` (e.g. an agency/FOIA filename like `DOW-UAP-D57-Mission-Report-Gulf-of-Aden-September-2020.pdf`). The file's bytes are archived at `sources/{content_hash}.{ext}`. |
| `provenance` | string | no | Set to `unknown` when a record has no recoverable acquisition origin (neither `source_url` nor `source_file`) - distinguishes a genuinely untraceable record from one merely not yet annotated. Absent when the origin is known. |
| `creators` | list | no | The human creator(s) of the record - the document's author(s), the video or podcast host(s)/presenter(s), or a channel owner who is a named person. Person names, canonical "Last, First Middle" preferred (the assimilator's matcher tolerates either ordering). Medium-neutral; distinct from `publisher` (the entity). Optional and reviewer-fillable: platform metadata often gives the publishing entity reliably but not the human host. Replaces the former written-document-only `authors`. |
| `content_hash` | string | no | SHA-256 that names the record's file in `store/` and identifies it. What it hashes is source-type dependent (see [Store](#store)): the source asset's bytes for `audio`/`video`/`pdf`, the extracted body text for `web`/`ebook`. |
| `source_hash` | string | no | Emitted by the `web` and `ebook` handlers: SHA-256 of the raw source asset (the post-render HTML for web, the EPUB bytes for ebook), locating `sources/{source_hash}.{ext}`. Differs from `content_hash`, which for these two types hashes the extracted body rather than the source bytes. `audio`/`video`/`pdf` do not emit it: their `content_hash` already hashes the source bytes, so the asset is at `sources/{content_hash}.{ext}`. (For ebook the same hash is also recorded in the verification sidecar's `sha256`; `source_hash` surfaces it in frontmatter so consumers need not open the gated sidecar.) |
| `snapshots` | list | no | Sibling capture artefacts produced alongside the main record. Each entry has `role` (well-known string), `hash` (sha256 of the artefact bytes), and `content_type` (MIME). Used for web records to expose PDF renders and frozen-page captures - see [Web record snapshots](#web-record-snapshots) below. |
| `pages` | integer | no | Page count for documents |
| `duration` | number | no | Duration in seconds for audio/video |
| `date_accessed` | string | no | When the source was fetched. ISO 8601 with timezone (always Zulu). |
| `date_extracted` | string | no | When the ingestion pipeline ran. ISO 8601 with timezone (always Zulu). |
| `copyright` | object | no | Copyright status (see the [copyright decision](../decisions/drafts/source-types-and-copyright.md)) |
| `classification` | string | no | Original security classification banner of the source, verbatim with surrounding parentheses stripped (e.g. `SECRET//REL TO USA, FVEY`). Present only for documents carrying a classification marking; absent otherwise. Portion-level markings that differ from the document banner are captured inline - see [Classification markings](#classification-markings). |
| `processing` | object | no | Processing metadata: handler, version, tools used, source characteristics |
| `media` | object | no | Summary of extracted media stored at `media/{record_hash}/`. Currently `{ count, total_bytes }`. Omitted when the record has no extracted media. |

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
| `[irrelevant]` | Content that doesn't belong in the record (ads, sponsor reads, off-topic asides). Reviewers can hide these segments from the rendered output. |

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

**Description-only.** A factual description with no extracted file. The value is a scalar string:

```markdown
<!-- image: Bar chart showing UAP reports by year from 2019 to 2023, with a sharp increase in 2021. -->
```

**With extracted file.** When the ingester has saved the image bytes alongside the record, the value is a mapping with at minimum a `file` field:

```markdown
<!--
image:
  file: abc123def4567.png
  alt: "Bar chart showing UAP reports by year"
-->
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | string | yes | The image's filename - bare, not a path. Format is `{img_hash}.{ext}` where `img_hash` is a 12-character hexadecimal SHA-256 prefix of the image bytes and `ext` is the file extension (`png`, `jpg`, `gif`, `svg`, `webp`). |
| `alt` | string | no | Alt text from the source (`<img alt="">` in EPUB/HTML). Omitted when the source provides no alt text. |
| `description` | string | no | Factual description of the image. Generated by a vision pass or human review, not by the ingester. Omitted when no description has been written. |

The `file` value is a bare filename so the body of the record stays self-contained and content-addressable. The full path on disk is `media/{record_hash}/{file}` relative to the ingests root, where `{record_hash}` is the hash of the record containing the annotation (the same value as the record's filename in `store/`). Embedding the record hash directly in the body would break the record_hash invariant for source types whose `content_hash` is computed from the body (ebook, web).

When the same image appears in multiple records, each record gets its own copy under its own `media/{record_hash}/` subdirectory. This keeps records self-contained for downstream consumers (workbench, assembler, digester) at the cost of duplication, which is small in practice (cover art, publisher logos).

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

## Inline annotations

For annotations that fall mid-sentence. The syntax is `{{YAML}}` - double curly braces containing valid YAML.

```markdown
The programme was conducted at {{redacted: ~2 words}} Air Force Base.

The date was {{illegible: possibly March 2004}} according to the memo.

{{Fravor: holds up photograph}} and showed us the evidence.

{{audience: laughter}}
```

The content inside `{{ }}` is parsed as YAML. A single key-value pair where the key describes what or who the annotation is about, and the value provides the detail. There is no fixed vocabulary of keys - the key is whatever makes sense in context.

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

The `store/` directory contains the actual record files, named by `content_hash` (see the frontmatter table). What `content_hash` hashes is source-type dependent: for `audio`/`video`/`pdf` it is the source file's bytes; for `web`/`ebook` it is the extracted body text. This provides deduplication: the same input always produces the same output path, regardless of where it was ingested from or what it was called.

Because `audio`/`video`/`pdf` hash the source bytes, their `content_hash` is stable across re-extraction - reprocessing the same source (for example an improved transcriber) keeps the same identity and does not orphan reviews. `web`/`ebook` hash the extracted body, so a re-extraction that changes the body changes `content_hash` and the store path. This source-anchored/body-anchored split is current behaviour, not a settled design; making it consistent across types is under reconciliation.

Idempotency: if `{hash}.md` exists, the ingester skips extraction.

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
date_published: 2023-07-26
creators:
  - Fravor, David
source_url: https://oversight.house.gov/...
source_type: pdf
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
date_published: 2020-09-08
source_url: https://youtube.com/watch?v=aB8zcAttP1E
source_type: video
source_id: youtube:aB8zcAttP1E
duration: 7200
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
date_published: 2004-11-14
source_type: pdf
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
