# Proposal: Replace triple-hyphen YAML blocks with HTML comment blocks

## Problem

The ingest format uses `---` delimiters to embed YAML metadata blocks inline within the markdown body. This collides with standard markdown, where `---` is a horizontal rule (thematic break). Any markdown editor or renderer interprets these blocks as horizontal rules followed by plain text, making the content uneditable in rich editors and incorrectly rendered in standard markdown viewers.

This became apparent when integrating a WYSIWYG markdown editor (Milkdown/ProseMirror) into the review workbench. The editor cannot distinguish between a page boundary marker and a horizontal rule.

## Current format

```markdown
---
schema: anomalica/record/1
title: "Example Document"
date: 2024-01-15
content_hash: sha256:abc123...
---

First page content here.

---
file_page: 2
printed_page: 2
---

Second page content here.

---
speaker: Ross Coulthart
time: 00:15:32
irrelevant: true
---

This is what the speaker said.
```

The top-level frontmatter block (first `---` pair) is standard markdown frontmatter and handled correctly by all tools. The inline blocks (page markers, speaker turns) are the problem.

## Proposed format

Replace the inline `---` delimited blocks with HTML comment blocks containing the same YAML content:

```markdown
---
schema: anomalica/record/1
title: "Example Document"
date: 2024-01-15
content_hash: sha256:abc123...
---

First page content here.

<!-- anomalica
file_page: 2
printed_page: 2
-->

Second page content here.

<!-- anomalica
speaker: Ross Coulthart
time: 00:15:32
irrelevant: true
-->

This is what the speaker said.
```

The word `anomalica` on the opening line of each comment block distinguishes metadata from regular HTML comments. The parser regex is `<!--\s*anomalica\n(.*?)-->` - no need for field detection or content heuristics.

## Why HTML comments with a marker

- **No collision with markdown syntax.** HTML comments are part of the HTML spec, supported in all markdown renderers, and have no ambiguity.
- **Invisible when rendered.** Markdown renderers and editors ignore HTML comments in output. The workbench preprocesses them into visual elements (page markers, speaker badges) as needed.
- **Preserved by editors.** WYSIWYG markdown editors (Milkdown, ProseMirror-based) preserve HTML comments in the document model without trying to interpret them.
- **Same content, different delimiters.** The YAML inside is identical. Only the wrapping changes from `---`/`---` to `<!-- anomalica`/`-->`.
- **Unambiguous parsing.** The `anomalica` marker makes it binary: a comment is either a metadata block or it isn't. No risk of false-matching a regular HTML comment that happens to contain a colon.
- **Simple regex.** `<!--\s*anomalica\n(.*?)-->` captures every metadata block with no ambiguity.

## Alternatives considered

**HTML comments without a marker** (`<!-- speaker: Ross Coulthart ... -->`). Works but requires content heuristics to distinguish metadata from regular HTML comments. Fragile if a regular comment happens to contain a colon-separated line.

**One comment per field** (`<!-- speaker: Ross Coulthart -->` on separate lines). Simpler regex but fields are disconnected - hard to tell which belong together as a group.

**JSON inside comments** (`<!-- {"speaker": "Ross Coulthart", "time": "00:15:32"} -->`). Parseable with `JSON.parse()` but less readable in raw view and inconsistent with the YAML-based frontmatter.

**Custom fenced code blocks** (` ```yaml:meta `). Would render as visible code blocks in editors, which is noisy.

**Keep triple-hyphen but restrict to frontmatter only.** Would require a completely different approach for inline metadata (perhaps line-based annotations). Larger change for unclear benefit.

## Migration

The change is mechanical:
1. Replace inline `\n---\n{yaml fields}\n---\n` blocks (not the first frontmatter pair) with `\n<!-- anomalica\n{yaml fields}\n-->\n`

This can be done with a script across all records in anomalica-ingests.

## What needs to change

| Component | Change |
|-----------|--------|
| **anomalica-ingester** | Output `<!-- -->` instead of `--- ---` for inline blocks |
| **anomalica-ingests** | One-time migration of existing records |
| **anomalica-workbench** | Update transcript parser, page marker preprocessor, and document store operations to use `<!-- anomalica -->` delimiters |
| **anomalica-digester** | Update record parser (when built) |
| **Record format spec** | Update `architecture/record-format.md` to document the new syntax |

## Risks

- **Existing tooling assumptions.** Anything that parses the current `---` format needs updating. The scope is documented in the table above.
- **Nested HTML comments.** HTML comments cannot be nested (`<!-- <!-- --> -->` is invalid). This is unlikely to be an issue since the content between comment delimiters is YAML fields, not arbitrary HTML.
- **Whitespace sensitivity.** The parser needs to handle variations in whitespace around the `<!--` and `-->` delimiters consistently.

## Recommendation

Adopt the HTML comment format. The collision with markdown horizontal rules is a fundamental problem that will keep causing issues as the tooling matures. The migration is low-risk and mechanical.
