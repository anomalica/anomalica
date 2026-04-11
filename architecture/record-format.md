# Record Format

The record format is the interchange format between the ingester and the digester. Each ingested source produces one ingest - a `.md` file in this format.

See [architecture decision record 0019](../decisions/0019-record-interchange-format.md) for why this format was chosen.

## Structure

A record file has three parts:

1. **Frontmatter** - YAML (a human-readable metadata format) block at the top, fenced with `---`. Document-level metadata.
2. **Content** - markdown text. The actual content as it naturally reads.
3. **Annotations** - either block-level (YAML inside `<!-- anomalica ... -->` HTML comments) or inline (`{{YAML}}`).

All annotations use YAML throughout - the same data format as the frontmatter. Block annotations for structural markers (page boundaries, speaker turns, images). Inline annotations for mid-sentence markers (redactions, illegible text, actions).

The first `---` fenced block is always the frontmatter. All subsequent block annotations use `<!-- anomalica ... -->` HTML comment syntax. Text between blocks is content. The `anomalica` marker on the opening line distinguishes metadata comments from regular HTML comments.

## Frontmatter

Required fields:

```yaml
---
schema: anomalica/record/1
title: "Document title"
date: 2023-07-26
source_type: pdf
---
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema` | string | yes | Format version. Always `anomalica/record/1` for this version. |
| `title` | string | yes | Document or episode title |
| `date` | date | yes | Publication or recording date (ISO 8601) |
| `source_type` | string | yes | One of: `pdf`, `audio`, `video`, `web`, `ebook` |
| `source_url` | string | no | URL where the source can be found |
| `authors` | list | no | Authors for written documents |
| `speakers` | list | no | Speaker roster for audio/video (see below) |
| `content_hash` | string | no | SHA-256 cryptographic hash of the source file (a fingerprint that uniquely identifies the content) |
| `pages` | integer | no | Page count for documents |
| `duration` | number | no | Duration in seconds for audio/video |

### Speaker roster

For audio and video sources, the frontmatter includes a speaker list:

```yaml
speakers:
  - id: fravor
    name: David Fravor
    role: guest
    confirmed: true
  - id: lex
    name: Lex Fridman
    role: host
    confirmed: true
  - id: unknown1
    name: Unknown Speaker
    confirmed: false
```

`id` is a short alias used in speaker turn annotations. `confirmed` indicates whether a human has verified the speaker identification.

## Content

Standard markdown. Headings, paragraphs, lists, bold, italic, links, and tables all work as normal.

## Block annotations

YAML inside HTML comment blocks, marked with `anomalica` on the opening line. Used for structural markers that sit between content.

### Page boundary

```markdown
<!-- anomalica
file_page: 2
-->
```

`file_page` is always the PDF page number (1-indexed from the start of the file). If the page has its own printed page number that differs, include `printed_page`:

```markdown
<!-- anomalica
file_page: 19
printed_page: 15
-->
```

`printed_page` is omitted when there is no printed page number, or when it matches `file_page`.

### Speaker turn

All content after a speaker annotation until the next speaker annotation belongs to that speaker. The `speaker` value references an `id` from the frontmatter speaker roster.

```markdown
<!-- anomalica
speaker: fravor
time: 00:01:45
-->
We had been at sea for roughly 2 weeks.
```

`time` is in `HH:MM:SS` or `MM:SS` format.

### Image description

Factual description of a figure, chart, or photograph. The image itself is not extracted (copyright).

```markdown
<!-- anomalica
image: Bar chart showing UAP reports by year from 2019 to 2023,
  with a sharp increase in 2021.
-->
```

### Block-level redaction

```markdown
<!-- anomalica
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

## Parser behaviour

1. Extract the first `---` fenced block as frontmatter (standard markdown frontmatter).
2. Find all `<!-- anomalica ... -->` blocks in the body. The marker `anomalica` on the opening line distinguishes metadata from regular HTML comments. Parse the content between the markers as YAML.
3. Text between annotation blocks is content.
4. Within content blocks, scan for `{{...}}` patterns and parse the interior as YAML (inline annotations).

## Output directory structure

Record files are stored in a two-level structure:

```
output/
  store/          # hash-named files (source of truth)
    7bf2c20d...md
    7bf2c20d...meta.json
    e27169e8...md
    e27169e8...meta.json
  records/        # human-readable symlinks
    2023-07-26-pdf-fravor-written-statement.md -> ../store/7bf2c20d...md
    2020-09-08-audio-lex-fridman-122-david-fravor.md -> ../store/e27169e8...md
```

### Store

The `store/` directory contains the actual record files, named by the SHA-256 cryptographic hash of the source file (the same value as `content_hash` in the frontmatter). This provides deduplication: the same source file always produces the same output path, regardless of where it was ingested from or what it was called.

Each record has a companion `.meta.json` file with extraction metadata (token counts, timestamps).

Idempotency: if `{hash}.md` exists, the ingester skips extraction.

### Records

The `records/` directory contains symlinks with human-readable names, pointing into `store/`. The naming convention is:

```
{date}-{source_type}-{slugified-title}.md
```

For example:
- `2023-07-26-pdf-fravor-written-statement.md`
- `2020-09-08-audio-lex-fridman-122-david-fravor.md`
- `2024-08-20-ebook-imminent.md`
- `2009-pdf-nimitz-executive-summary.md`

The date, source_type, and title are taken from the record's frontmatter. The symlinks are regenerated from the store contents and can be deleted and rebuilt at any time.

## Examples

### PDF document

```markdown
---
schema: anomalica/record/1
title: David Fravor Statement for the House Oversight Committee
date: 2023-07-26
authors:
  - David Fravor
source_url: https://oversight.house.gov/...
source_type: pdf
content_hash: sha256:7bf2c20d...
pages: 3
---

<!-- anomalica
file_page: 1
-->

David Fravor Statement for the House Oversight Committee.

I first want to thank you for the invitation to speak to this
committee on the UAP topic that has been in the news for the past
6 years and seems to be continuing to gain momentum.

<!-- anomalica
file_page: 2
-->

As we proceeded to the west and as the air controller counted down
the range, we had nothing on our radars and were unaware of what
we were going to see when we arrived.

<!-- anomalica
file_page: 3
-->

In closing, I would like to say that the Tic Tac Object that we
engaged in Nov 2004 was far superior to anything that we had at
the time, have today, or are looking to develop in the next 10+
years.
```

### Audio transcript

```markdown
---
schema: anomalica/record/1
title: "Lex Fridman Podcast #122 - David Fravor"
date: 2020-09-08
source_url: https://youtube.com/watch?v=aB8zcAttP1E
source_type: audio
duration: 7200
speakers:
  - id: lex
    name: Lex Fridman
    role: host
    confirmed: true
  - id: fravor
    name: David Fravor
    role: guest
    confirmed: true
---

<!-- anomalica
speaker: lex
time: 00:01:23
-->
So tell me about what happened in 2004. You were a Navy pilot
stationed on the Nimitz.

<!-- anomalica
speaker: fravor
time: 00:01:45
-->
We had been at sea for roughly 2 weeks. I was the Commanding
Officer of Strike Fighter Squadron Forty-One. We were at the
beginning of our workup cycle.

{{action: Fravor gestures to indicate the size of the object}}

It was about the size of an F-18, roughly 40 feet long, with no
wings, no exhaust plume.
```

### Freedom of Information Act document with redactions

```markdown
---
schema: anomalica/record/1
title: Incident Report
date: 2004-11-14
source_type: pdf
pages: 5
---

<!-- anomalica
file_page: 1
-->

# Incident Report

On {{redacted: date in November 2004}}, personnel at {{redacted}}
observed an unidentified aerial object in restricted airspace.

<!-- anomalica
redacted:
  extent: paragraph
-->

The object was tracked on radar for approximately 12 minutes
before {{redacted: ~5 words}}.

<!-- anomalica
file_page: 2
-->

<!-- anomalica
image: Grainy black and white photograph showing a small oblong
  object against a featureless sky. No scale reference visible.
-->

The following personnel were present during the observation:

| Name | Rank | Role |
|------|------|------|
| {{redacted}} | Commander | Officer of the Watch |
| {{redacted}} | Lt. | Radar Operator |
```
