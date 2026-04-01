# Record interchange format

Date: 2026-03-24
Status: draft

## Context

The ingester converts raw source material (PDFs, audio, video, ebooks, web pages) into a normalised format that the digester consumes. This format must handle government documents with tables and redactions, interview transcripts with speaker labels and timestamps, news articles, and books with chapter structure.

We evaluated DoclingDocument (IBM), Unstructured.io's element model, TEI, Apache Tika XHTML, Pandoc AST, and various JSON schemas from NLP pipelines. We also prototyped with DoclingDocument and found it adds significant structural bloat (self-references, duplicated fields, tree of JSON pointers) without benefit to the digester.

## Decision

Use markdown files with YAML annotations throughout:

- **YAML frontmatter** for document-level metadata
- **Markdown body** for content as it naturally reads
- **YAML block annotations** (fenced with `---`) for structural markers: page boundaries, speaker turns, image descriptions, block-level redactions
- **YAML inline annotations** (`{{YAML}}` in double curly braces) for mid-sentence markers: redactions, illegible text, non-verbal actions

YAML is the only data format used. Frontmatter is YAML, block annotations are YAML, inline annotations are YAML inside double curly braces. One syntax to learn, one parser to write.

The full specification is in [architecture/record-format.md](../architecture/record-format.md).

## Why not existing formats

- **DoclingDocument** (IBM): duplicates every text field (`orig` and `text`), uses JSON pointer cross-references for a tree structure the digester doesn't need. Designed for visual document layout (bounding boxes), irrelevant to knowledge extraction.
- **Unstructured.io elements**: breaks natural prose into separate JSON objects. No support for speaker turns or timestamps.
- **Custom JSON schema** (our initial approach): not human-readable. A 3-page statement becomes hundreds of lines of JSON with structural overhead.
- **TEI XML**: enormously complex. Thousands of pages of guidelines for a format that would carry mostly empty elements for our use case.

## Consequences

- The ingester produces `.md` files instead of `.json`
- The output is human-readable without tooling - open the file and read the document
- We control the specification and can extend it
- No external dependency on any schema project
- The parser is simple: split on `---`, try YAML parse, scan for `{{...}}`
- `docling-core` is no longer a dependency
